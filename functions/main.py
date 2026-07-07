import datetime
import json
import logging
import os
import threading
from urllib.parse import urlparse, parse_qs

import firebase_admin
from firebase_admin import credentials, firestore, messaging
from firebase_functions import https_fn, scheduler_fn, options

# Initialize Firebase Admin SDK
# Under Google Cloud Functions, this automatically uses the correct service credentials.
try:
    firebase_admin.initialize_app()
except ValueError:
    pass  # Already initialized

class LazyFirestore:
    def __init__(self):
        self._client = None
    def __getattr__(self, name):
        if self._client is None:
            self._client = firestore.client()
        return getattr(self._client, name)

db = LazyFirestore()


# ==========================================
# 📱 SMS and Kakao Alimtalk settings (Loaded from .env)
# ==========================================
SMS_PROVIDER = os.environ.get("SMS_PROVIDER", "none")
SMS_API_KEY = os.environ.get("SMS_API_KEY", "")
SMS_API_SECRET = os.environ.get("SMS_API_SECRET", "")
SMS_USER_ID = os.environ.get("SMS_USER_ID", "")
SMS_SENDER_NUMBER = os.environ.get("SMS_SENDER_NUMBER", "")
KAKAO_SENDER_KEY = os.environ.get("KAKAO_SENDER_KEY", "")
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")

ADMIN_SECRET_KEY = "withpro123"

# Kakao templates
KAKAO_TPL_LESSON_REQUESTED = "KA01TP260703142423232bOZ7Y7LbJPm"
KAKAO_TPL_MATCH_PROPOSAL = "KA01TP260703142719277lwSWCnovrkb"
KAKAO_TPL_MATCH_SUCCESS = "KA01TP260703142908479UFKi4EGWn7q"
KAKAO_TPL_MATCH_CONFIRMED = "KA01TP260703143048865jMgfLrtWr6j"
KAKAO_TPL_PRO_PAYMENT_REQUEST = "KA01TP2607031432357217x5MA6C9fyF"
KAKAO_TPL_PRO_COMMISSION_DUE = "KA01TP260703143403037MUCoupAcCp8"
KAKAO_TPL_AMATEUR_REVIEW_REQUEST_WITH_COUPON = "UI_6516"
KAKAO_TPL_AMATEUR_REVIEW_REQUEST_WITHOUT_COUPON = "UI_6517"

# Helpers for formatting dates
def get_now_kst():
    kst = datetime.timezone(datetime.timedelta(hours=9))
    return datetime.datetime.now(kst)

def get_timestamp_str(dt=None):
    if dt is None:
        dt = get_now_kst()
    return dt.strftime("%Y-%m-%d %H:%M:%S")

# Discord notification helper
def send_discord_notification(title, fields):
    if not DISCORD_WEBHOOK_URL or DISCORD_WEBHOOK_URL.startswith("YOUR_"):
        return
    
    embed = {
        "title": title,
        "color": 736558,
        "fields": [],
        "footer": {
            "text": "withPRO 실시간 알림 시스템"
        }
    }
    
    for name, value in fields.items():
        embed["fields"].append({
            "name": name,
            "value": str(value),
            "inline": True
        })
        
    payload = {
        "content": "🔔 @everyone 실시간 알림이 도착했습니다!",
        "embeds": [embed]
    }
    
    def send_webhook():
        try:
            import urllib.request
            req = urllib.request.Request(
                DISCORD_WEBHOOK_URL,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req, timeout=3) as response:
                pass
        except Exception as e:
            logging.error(f"[디스코드 알림 발송 실패] {e}")
            
    # Run in a background thread to prevent blocking
    threading.Thread(target=send_webhook, daemon=True).start()

# Alimtalk helpers
def send_aligo_alimtalk(receiver, tpl_code, subject, message, link=None):
    if not SMS_API_KEY or not SMS_USER_ID or not SMS_SENDER_NUMBER or not KAKAO_SENDER_KEY:
        logging.info("[Aligo Alimtalk] Config missing. Skipping.")
        return False
        
    import urllib.request
    import urllib.parse
    
    # 1. Generate Token first
    try:
        token_url = "https://kakaoapi.aligo.in/akv10/token/create/30/i/"
        token_payload = {
            "apikey": SMS_API_KEY,
            "userid": SMS_USER_ID
        }
        token_data = urllib.parse.urlencode(token_payload).encode("utf-8")
        token_req = urllib.request.Request(token_url, data=token_data)
        
        with urllib.request.urlopen(token_req, timeout=5) as token_res:
            token_res_data = json.loads(token_res.read().decode("utf-8"))
            if str(token_res_data.get("code")) != "0":
                logging.error(f"[Aligo Alimtalk Token Error] Failed: {token_res_data}")
                return False
            token = token_res_data.get("token")
    except Exception as te:
        logging.error(f"[Aligo Alimtalk Token Exception] {te}")
        return False

    # 2. Send Alimtalk using the Token
    url = "https://kakaoapi.aligo.in/akv10/alimtalk/send/"
    payload = {
        "apikey": SMS_API_KEY,
        "userid": SMS_USER_ID,
        "token": token,
        "sender": SMS_SENDER_NUMBER,
        "senderkey": KAKAO_SENDER_KEY,
        "tpl_code": tpl_code,
        "receiver_1": receiver,
        "subject_1": subject,
        "message_1": message,
        "failover": "Y",
        "fsubject_1": subject,
        "fmessage_1": message
    }
    
    if link:
        button_info = {
            "button": [
                {
                    "name": "자세히 보기",
                    "linkType": "WL",
                    "linkUrl1": link,
                    "linkUrl2": link
                }
            ]
        }
        payload["button_1"] = json.dumps(button_info)
        
    try:
        data = urllib.parse.urlencode(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, timeout=5) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            if str(res_data.get("result_code")) == "1" or res_data.get("code") == 0:
                logging.info(f"[Aligo Alimtalk] Success: {receiver}")
                return True
            else:
                logging.error(f"[Aligo Alimtalk] Failed: {res_data}")
                return False
    except Exception as e:
        logging.error(f"[Aligo Alimtalk] Error: {e}")
        return False

def send_solapi_alimtalk(receiver, template_id, message, link=None, variables=None):
    if not SMS_API_KEY or not SMS_API_SECRET or not SMS_SENDER_NUMBER or not KAKAO_SENDER_KEY:
        logging.info("[Solapi Alimtalk] Config missing. Skipping.")
        return False
        
    import time
    import uuid
    import hmac
    import hashlib
    import urllib.request
    
    now = time.strftime('%Y-%m-%dT%H:%M:%S.000Z', time.gmtime())
    salt = str(uuid.uuid4().hex)
    combined = now + salt
    signature = hmac.new(
        SMS_API_SECRET.encode('utf-8'),
        combined.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    auth_header = f"HMAC-SHA256 apiKey={SMS_API_KEY}, date={now}, salt={salt}, signature={signature}"
    url = "https://api.solapi.com/messages/v4/send"
    
    payload = {
        "message": {
            "to": receiver,
            "from": SMS_SENDER_NUMBER,
            "type": "ATA",
            "kakaoOptions": {
                "pfId": KAKAO_SENDER_KEY,
                "templateId": template_id
            }
        }
    }
    if variables:
        payload["message"]["kakaoOptions"]["variables"] = variables
    
    if link:
        payload["message"]["kakaoOptions"]["buttons"] = [
            {
                "buttonName": "자세히 보기",
                "buttonType": "WL",
                "linkMo": link,
                "linkPc": link
            }
        ]
        
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Authorization", auth_header)
        req.add_header("Content-Type", "application/json")
        
        with urllib.request.urlopen(req, timeout=5) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            if "messageId" in res_data or "groupId" in res_data or str(res_data.get("statusCode")) in ["2000", "3000"]:
                logging.info(f"[Solapi Alimtalk] Success: {receiver}")
                return True
            else:
                logging.error(f"[Solapi Alimtalk] Failed: {res_data}")
                return False
    except Exception as e:
        logging.error(f"[Solapi Alimtalk] Error: {e}")
        return False

# Dispatch Push Notification helper
def dispatch_push_notification(receiver, title, body, link=None, template_type=None, variables=None):
    if not receiver:
        return
        
    import threading
    
    def run_dispatch():
        try:
            clean_receiver = "".join(filter(str.isdigit, receiver))
            
            # Mirror notification to Discord
            fields = {
                "수신 대상": f"{clean_receiver}",
                "알림 제목": title,
                "알림 내용": body
            }
            if link:
                fields["이동 링크"] = link
            send_discord_notification(f"📱 [withPRO App Push] {title}", fields)
            
            # Formulate potential formats for the contact query
            formats = [receiver]
            if clean_receiver not in formats:
                formats.append(clean_receiver)
            
            if len(clean_receiver) == 11 and clean_receiver.startswith("010"):
                formatted = f"{clean_receiver[:3]}-{clean_receiver[3:7]}-{clean_receiver[7:]}"
                if formatted not in formats:
                    formats.append(formatted)
            elif len(clean_receiver) == 10 and clean_receiver.startswith("01"):
                formatted = f"{clean_receiver[:3]}-{clean_receiver[3:6]}-{clean_receiver[6:]}"
                if formatted not in formats:
                    formats.append(formatted)
            
            # Try FCM Push via Firebase Messaging SDK
            fcm_token = None
            try:
                # 1. Search regular_users using indexed queries
                for fmt in formats:
                    reg_users = db.collection("regular_users").where("contact", "==", fmt).limit(1).get()
                    if reg_users:
                        fcm_token = reg_users[0].to_dict().get("fcm_token")
                        if fcm_token:
                            break
                            
                # 2. Search pro_users if not found
                if not fcm_token:
                    for fmt in formats:
                        pro_users = db.collection("pro_users").where("contact", "==", fmt).limit(1).get()
                        if pro_users:
                            fcm_token = pro_users[0].to_dict().get("fcm_token")
                            if fcm_token:
                                break
                
                if fcm_token:
                    message = messaging.Message(
                        notification=messaging.Notification(
                            title=title,
                            body=body
                        ),
                        data={
                            "click_action": link if link else "https://withpro.kr"
                        },
                        token=fcm_token
                    )
                    response = messaging.send(message)
                    logging.info(f"[Firebase FCM] Push Notification Sent! Response: {response}")
            except Exception as e:
                logging.error(f"[Firebase FCM] Push Notification Failed: {e}")
                
            # Kakao Alimtalk Failover
            if SMS_PROVIDER != "none" and template_type:
                talk_message = f"[{title}]\n{body}"
                tpl_code = None
                
                if template_type == "lesson_requested":
                    tpl_code = KAKAO_TPL_LESSON_REQUESTED
                elif template_type == "match_proposal":
                    tpl_code = KAKAO_TPL_MATCH_PROPOSAL
                elif template_type == "match_success":
                    tpl_code = KAKAO_TPL_MATCH_SUCCESS
                elif template_type == "match_confirmed":
                    tpl_code = KAKAO_TPL_MATCH_CONFIRMED
                elif template_type == "pro_commission_due":
                    tpl_code = KAKAO_TPL_PRO_COMMISSION_DUE
                elif template_type == "pro_payment_request":
                    tpl_code = KAKAO_TPL_PRO_PAYMENT_REQUEST
                elif template_type == "amateur_review_request_with_coupon":
                    tpl_code = KAKAO_TPL_AMATEUR_REVIEW_REQUEST_WITH_COUPON
                elif template_type == "amateur_review_request_without_coupon":
                    tpl_code = KAKAO_TPL_AMATEUR_REVIEW_REQUEST_WITHOUT_COUPON
                    
                if tpl_code:
                    if SMS_PROVIDER == "aligo":
                        send_aligo_alimtalk(clean_receiver, tpl_code, title, talk_message, link)
                    elif SMS_PROVIDER == "solapi":
                        send_solapi_alimtalk(clean_receiver, tpl_code, talk_message, link, variables)
                else:
                    logging.info(f"[Kakao Alimtalk] No template mapping for: {template_type}")
        except Exception as ex:
            logging.error(f"[dispatch_push_notification Background Error] {ex}")

    # Run in a background thread to prevent blocking the API response
    threading.Thread(target=run_dispatch, daemon=True).start()

# CORS and Response helper
def create_response(data, status=200):
    return https_fn.Response(
        json.dumps(data, ensure_ascii=False),
        status=status,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization"
        }
    )

# Clean phone formatting helper
def clean_phone(phone_str):
    if not phone_str:
        return ""
    return "".join([ch for ch in phone_str if ch.isdigit()])

# ==========================================
# 🔥 MAIN HTTP ENDPOINT (api Router)
# ==========================================
@https_fn.on_request(cors=options.CorsOptions(cors_origins="*", cors_methods=["GET", "POST", "OPTIONS"]))
def api(req: https_fn.Request) -> https_fn.Response:
    # Handle preflight OPTIONS request
    if req.method == "OPTIONS":
        return https_fn.Response(
            status=204,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
                "Access-Control-Max-Age": "3600"
            }
        )

    parsed_url = urlparse(req.url)
    # Get relative path (e.g., /api/register/regular)
    path = parsed_url.path
    # Strip any trailing slashes
    if path.endswith("/"):
        path = path[:-1]
        
    logging.info(f"Received API request path: {path}, method: {req.method}")
    
    # ----------------------------------------------------
    # GET /api/firebase-config
    # ----------------------------------------------------
    if path == "/api/firebase-config" and req.method == "GET":
        config = {}
        # 1. Try reading from Firestore first
        try:
            settings_doc = db.collection("system_settings").document("firebase_web_config").get()
            if settings_doc.exists:
                config = settings_doc.to_dict()
        except Exception as e:
            logging.error(f"Failed to read config from Firestore: {e}")
            
        # 2. Fallback to local file if Firestore is empty or doesn't have apiKey
        if not config or not config.get("apiKey") or "mock-api-key" in config.get("apiKey", ""):
            web_config_path = "firebase-web-config.json"
            if not os.path.exists(web_config_path):
                web_config_path = "../firebase-web-config.json" # try root directory
                
            if os.path.exists(web_config_path):
                try:
                    with open(web_config_path, "r", encoding="utf-8") as f:
                        config = json.load(f)
                except Exception as e:
                    logging.error(f"Failed to read web config: {e}")
        return create_response(config)

    # ----------------------------------------------------
    # GET /api/admin/firebase-status
    # ----------------------------------------------------
    elif path == "/api/admin/firebase-status" and req.method == "GET":
        key = req.args.get('key')
        if key != ADMIN_SECRET_KEY:
            return create_response({'error': 'Unauthorized'}, 401)
            
        client_configured = False
        
        # 1. Check Firestore
        try:
            settings_doc = db.collection("system_settings").document("firebase_web_config").get()
            if settings_doc.exists:
                cfg = settings_doc.to_dict()
                if cfg.get('apiKey') and cfg.get('messagingSenderId') and "mock-api-key" not in cfg.get('apiKey', ""):
                    client_configured = True
        except Exception:
            pass
            
        # 2. Fallback to file check
        if not client_configured:
            web_config_path = "firebase-web-config.json"
            if not os.path.exists(web_config_path):
                web_config_path = "../firebase-web-config.json"
                
            if os.path.exists(web_config_path):
                try:
                    with open(web_config_path, "r", encoding="utf-8") as f:
                        cfg = json.load(f)
                        if cfg.get('apiKey') and cfg.get('messagingSenderId') and "mock-api-key" not in cfg.get('apiKey', ""):
                            client_configured = True
                except Exception:
                    pass
                
        return create_response({
            'client_configured': client_configured,
            'admin_initialized': True # Always True in serverless since initialized in global scope
        })

    # ----------------------------------------------------
    # GET /api/admin/data
    # ----------------------------------------------------
    elif path == "/api/admin/data" and req.method == "GET":
        key = req.args.get('key')
        if key != ADMIN_SECRET_KEY:
            return create_response({'error': 'Unauthorized'}, 401)
            
        try:
            # Query all regular users
            reg_users = []
            for doc in db.collection("regular_users").order_by("created_at", direction=firestore.Query.DESCENDING).get():
                d = doc.to_dict()
                d["id"] = doc.id
                reg_users.append(d)
                
            # Query all pro users
            pro_users = []
            for doc in db.collection("pro_users").order_by("created_at", direction=firestore.Query.DESCENDING).get():
                d = doc.to_dict()
                d["id"] = doc.id
                pro_users.append(d)
                
            # Query all lesson requests
            lesson_requests = []
            for doc in db.collection("lesson_requests").order_by("created_at", direction=firestore.Query.DESCENDING).get():
                d = doc.to_dict()
                d["id"] = doc.id
                lesson_requests.append(d)
                
            return create_response({
                'regular_users': reg_users,
                'pro_users': pro_users,
                'lesson_requests': lesson_requests
            })
        except Exception as e:
            return create_response({'error': str(e)}, 500)

    # ----------------------------------------------------
    # GET /api/lesson/status
    # ----------------------------------------------------
    elif path == "/api/lesson/status" and req.method == "GET":
        req_id = req.args.get('id')
        if not req_id:
            return create_response({'error': 'Missing ID'}, 400)
            
        try:
            doc = db.collection("lesson_requests").document(req_id).get()
            if not doc.exists:
                return create_response({'error': 'Not Found'}, 404)
                
            row = doc.to_dict()
            row["id"] = doc.id
            
            coupon_already_issued = False
            user_contact = row.get('user_contact')
            if user_contact:
                user_phone_clean = clean_phone(user_contact)
                # Find if coupon with code WITHPRO30 was already issued to this user
                issued_coupons = db.collection("lesson_requests")\
                                   .where("issued_coupon_code", "==", "WITHPRO30")\
                                   .get()
                                   
                for ic in issued_coupons:
                    ic_data = ic.to_dict()
                    if ic_data.get('user_contact') and clean_phone(ic_data.get('user_contact')) == user_phone_clean:
                        coupon_already_issued = True
                        break
                        
            row['coupon_already_issued'] = coupon_already_issued
            return create_response(row)
        except Exception as e:
            return create_response({'error': str(e)}, 500)

    # ----------------------------------------------------
    # GET /api/pro/profile
    # ----------------------------------------------------
    elif path == "/api/pro/profile" and req.method == "GET":
        cert = req.args.get('cert')
        if not cert:
            return create_response({'error': 'Missing Certificate Number'}, 400)
            
        try:
            # Query pro by cert_number
            pro_docs = db.collection("pro_users").where("cert_number", "==", cert).limit(1).get()
            if not pro_docs:
                return create_response({'error': 'Pro Not Found'}, 404)
                
            pro_doc = pro_docs[0]
            pro_data = pro_doc.to_dict()
            pro_data["id"] = pro_doc.id
            
            # Fetch matched lessons
            matches = []
            match_docs = db.collection("lesson_requests")\
                           .where("matched_pro_id", "==", pro_doc.id)\
                           .order_by("created_at", direction=firestore.Query.DESCENDING)\
                           .get()
                           
            for m in match_docs:
                md = m.to_dict()
                md["id"] = m.id
                matches.append(md)
                
            return create_response({
                'profile': pro_data,
                'matches': matches
            })
        except Exception as e:
            return create_response({'error': str(e)}, 500)

    # ----------------------------------------------------
    # GET /api/pro/login-by-phone
    # ----------------------------------------------------
    elif path == "/api/pro/login-by-phone" and req.method == "GET":
        phone = req.args.get('phone')
        if not phone:
            return create_response({'error': '전화번호를 입력해주세요.'}, 400)
            
        clean_input = phone.replace('-', '').strip()
        
        try:
            pro_docs = db.collection("pro_users").get()
            matched_user = None
            for p in pro_docs:
                pd = p.to_dict()
                if pd.get("contact"):
                    db_contact = pd.get("contact").replace("-", "").strip()
                    if db_contact == clean_input:
                        matched_user = pd
                        break
                        
            if not matched_user:
                return create_response({'error': '등록된 프로 정보를 찾을 수 없습니다.'}, 404)
                
            return create_response({'status': 'success', 'cert_number': matched_user.get('cert_number')})
        except Exception as e:
            return create_response({'error': str(e)}, 500)

    # ----------------------------------------------------
    # GET /api/pro/latest-phone
    # ----------------------------------------------------
    elif path == "/api/pro/latest-phone" and req.method == "GET":
        try:
            pro_docs = db.collection("pro_users").order_by("created_at", direction=firestore.Query.DESCENDING).limit(1).get()
            phone = "010-1234-5678"
            if pro_docs:
                phone = pro_docs[0].to_dict().get("contact", "010-1234-5678")
            return create_response({'phone': phone})
        except Exception as e:
            return create_response({'error': str(e)}, 500)

    # ----------------------------------------------------
    # POST /api/register/regular
    # ----------------------------------------------------
    elif path == "/api/register/regular" and req.method == "POST":
        try:
            data = req.get_json()
            name = data.get('name')
            contact = data.get('contact')
            gender = data.get('gender')
            region = data.get('region')
            
            created_at = get_timestamp_str()
            
            # Save user
            doc_ref = db.collection("regular_users").document()
            doc_ref.set({
                "name": name,
                "contact": contact,
                "gender": gender,
                "region": region,
                "created_at": created_at
            })
            
            # Send Discord Alert
            fields = {
                "이름": name,
                "연락처": contact,
                "성별": gender,
                "희망 지역": region
            }
            send_discord_notification("👤 새로운 일반 회원 가입 완료", fields)
            
            return create_response({'status': 'success', 'message': '일반 회원 가입이 완료되었습니다.'})
        except Exception as e:
            return create_response({'error': str(e)}, 500)

    # ----------------------------------------------------
    # POST /api/register/pro
    # ----------------------------------------------------
    elif path == "/api/register/pro" and req.method == "POST":
        try:
            data = req.get_json()
            name = data.get('name')
            contact = data.get('contact')
            cert_type = data.get('cert_type')
            cert_number = data.get('cert_number')
            profile_pic = data.get('profile_pic')
            available_days = data.get('available_days')
            regions = data.get('regions')
            pin = data.get('pin', '1234')
            
            created_at = get_timestamp_str()
            
            doc_ref = db.collection("pro_users").document()
            doc_ref.set({
                "name": name,
                "contact": contact,
                "cert_type": cert_type,
                "cert_number": cert_number,
                "profile_pic": profile_pic,
                "available_days": available_days,
                "regions": regions,
                "pin": pin,
                "status": "승인대기",
                "created_at": created_at
            })
            
            # Discord notify
            fields = {
                "이름": name,
                "연락처": contact,
                "자격증 종류": cert_type,
                "회원 번호": cert_number,
                "활동 가능 요일": available_days,
                "활동 가능 지역": regions
            }
            send_discord_notification("🏌️‍♂️ 새로운 프로 회원 등록 신청", fields)
            
            return create_response({'status': 'success', 'message': '프로 회원 가입이 완료되었습니다.'})
        except Exception as e:
            return create_response({'error': str(e)}, 500)

    # ----------------------------------------------------
    # POST /api/lesson/pro-accept
    # ----------------------------------------------------
    elif path == "/api/lesson/pro-accept" and req.method == "POST":
        try:
            data = req.get_json()
            req_id = data.get('id')
            pro_id = data.get('pro_id')
            accept = data.get('accept', False)
            
            if not req_id or not pro_id:
                return create_response({'error': 'Missing ID or Pro ID'}, 400)
                
            req_ref = db.collection("lesson_requests").document(str(req_id))
            req_doc = req_ref.get()
            
            pro_ref = db.collection("pro_users").document(str(pro_id))
            pro_doc = pro_ref.get()
            
            if not req_doc.exists or not pro_doc.exists:
                return create_response({'error': 'Request or Pro Not Found'}, 404)
                
            req_data = req_doc.to_dict()
            pro_data = pro_doc.to_dict()
            
            if accept:
                # Update lesson request to finalized match (cash direct payment)
                req_ref.update({
                    "status": "결제완료",
                    "pay_method": "현장직거래",
                    "paid_amount": 0
                })
                
                pro_name = pro_data.get('name', '배정 프로')
                pro_cert = pro_data.get('cert_number', '-')
                pro_contact = pro_data.get('contact', '-')
                
                # Discord Alert
                fields = {
                    "신청 고객": f"{req_data.get('user_name', '아마추어')} ({req_data.get('user_contact', '-')})",
                    "골프장": req_data.get('golf_course'),
                    "라운딩 날짜": req_data.get('lesson_date'),
                    "티오프 시간": req_data.get('lesson_time'),
                    "매칭 프로": f"{pro_name} (자격번호: {pro_cert})",
                    "매칭 상태": "최종 확정 (현장 직거래)",
                    "레슨비": "550,000원 (현장 직접 정산)",
                    "플랫폼 수수료": "50,000원 (프로 사후 납부)"
                }
                send_discord_notification("🏌️‍♂️ 필드레슨 매칭 최종 확정 (현장 직거래)", fields)
                
                # App Push to amateur customer
                customer_title = "🎉 필드레슨 매칭 최종 확정!"
                customer_body = f"[withPRO] '{req_data.get('golf_course')}' 필드레슨 매칭이 최종 확정되었습니다.\n- 배정 프로: {pro_name} 프로님 ({pro_contact})\n현장 레슨비는 라운딩 종료 후 프로님께 직접 결제(55만 원)해 주시면 됩니다."
                customer_link = f"https://withpro.kr/index.html?view=my-bookings&id={req_id}"
                dispatch_push_notification(
                    req_data.get('user_contact'), 
                    customer_title, 
                    customer_body, 
                    customer_link, 
                    template_type="match_success",
                    variables={
                        "#{고객명}": req_data.get('user_name', '아마추어'),
                        "#{프로명}": pro_name,
                        "#{프로연락처}": pro_contact
                    }
                )
            else:
                # Reject match
                req_ref.update({
                    "status": "매칭 대기중",
                    "matched_pro_id": None
                })
                
                fields = {
                    "골프장": req_data.get('golf_course'),
                    "라운딩 날짜": req_data.get('lesson_date'),
                    "티오프 시간": req_data.get('lesson_time'),
                    "거절 프로": pro_data.get('name', '배정 프로'),
                    "매칭 상태": "매칭 거절 (재매칭 대기중)"
                }
                send_discord_notification("❌ 프로 매칭 거절 (재매칭 대기중)", fields)
                
            return create_response({'status': 'success'})
        except Exception as e:
            return create_response({'error': str(e)}, 500)

    # ----------------------------------------------------
    # POST /api/request-lesson
    # ----------------------------------------------------
    elif path == "/api/request-lesson" and req.method == "POST":
        try:
            data = req.get_json()
            user_name = data.get('userName', '아마추어')
            user_contact = data.get('userContact', '010-0000-0000')
            user_id = data.get('user_id', 'APP_USER')
            golf_course = data.get('golfCourse')
            date = data.get('date')
            time = data.get('time')
            
            created_at = get_timestamp_str()
            
            # Save lesson request
            doc_ref = db.collection("lesson_requests").document()
            doc_ref.set({
                "user_id": user_id,
                "user_name": user_name,
                "user_contact": user_contact,
                "golf_course": golf_course,
                "lesson_date": date,
                "lesson_time": time,
                "status": "매칭 대기중",
                "matched_pro_id": None,
                "pro_pay_status": "미납",
                "pro_notified": 0,
                "review_notified": 0,
                "discount_amount": 0,
                "paid_amount": 50000,
                "issued_coupon_status": "없음",
                "created_at": created_at
            })
            inserted_id = doc_ref.id
            
            # Auto register regular user if not exists
            reg_users = db.collection("regular_users").where("name", "==", user_name).where("contact", "==", user_contact).limit(1).get()
            if not reg_users:
                region = golf_course.split()[0] if golf_course else ''
                db.collection("regular_users").document().set({
                    "name": user_name,
                    "contact": user_contact,
                    "region": region,
                    "created_at": created_at
                })
                
            # App Push to amateur customer
            title = "⛳ 필드레슨 매칭 요청 접수 완료"
            body = f"[withPRO] {user_name}님, '{golf_course}' 골프장 필드레슨 매칭 요청이 안전하게 접수되었습니다. 일정에 맞는 최고의 프로님을 배정 후 즉시 알림톡 또는 앱 푸시 알림으로 알려드리겠습니다."
            user_link = f"https://withpro.kr/index.html?view=my-bookings&id={inserted_id}"
            dispatch_push_notification(
                user_contact, 
                title, 
                body, 
                user_link, 
                template_type="lesson_requested",
                variables={
                    "#{고객명}": user_name,
                    "#{골프장}": golf_course
                }
            )
            
            # Discord Notify
            fields = {
                "신청자명": user_name,
                "연락처": user_contact,
                "골프장": golf_course,
                "라운딩 날짜": date,
                "티오프 시간": time,
                "매칭 대상 ID": user_id
            }
            send_discord_notification("⛳ 새로운 필드레슨 매칭 신청 접수", fields)
            
            # Returns success response
            return create_response({
                'status': 'success',
                'id': inserted_id,
                'message': '⛳ 필드레슨 매칭 신청이 성공적으로 접수되었습니다!\n\nwithPRO를 믿고 소중한 라운딩 정보를 등록해 주셔서 진심으로 감사드립니다.\n\n골퍼님의 일정과 지역에 꼭 맞는 최고의 KPGA/KLPGA 프로님을 매칭하기 위해 최선을 다하고 있습니다. 매칭이 성사되는 대로 앱 푸시 알림을 통해 가장 먼저 기쁜 소식을 전해 드리겠습니다.\n\n오늘도 기분 좋은 하루 보내시고, 설레는 마음으로 라운딩을 준비해 보세요. 감사합니다!'
            })
        except Exception as e:
            return create_response({'error': str(e)}, 500)

    # ----------------------------------------------------
    # POST /api/admin/match
    # ----------------------------------------------------
    elif path == "/api/admin/match" and req.method == "POST":
        try:
            data = req.get_json()
            key = data.get('key')
            req_id = data.get('id')
            pro_id = data.get('pro_id')
            
            if key != ADMIN_SECRET_KEY:
                return create_response({'error': 'Unauthorized'}, 401)
                
            if not req_id or not pro_id:
                return create_response({'error': 'Missing ID or Pro ID'}, 400)
                
            req_ref = db.collection("lesson_requests").document(str(req_id))
            pro_ref = db.collection("pro_users").document(str(pro_id))
            
            req_doc = req_ref.get()
            pro_doc = pro_ref.get()
            
            if not req_doc.exists or not pro_doc.exists:
                return create_response({'error': 'Request or Pro Not Found'}, 404)
                
            req_data = req_doc.to_dict()
            pro_data = pro_doc.to_dict()
            
            # Update status to pending pro acceptance
            req_ref.update({
                "status": "프로 수락 대기중",
                "matched_pro_id": str(pro_id)
            })
            
            pro_name = pro_data.get('name', '배정 프로')
            pro_cert = pro_data.get('cert_number', '-')
            
            # Discord Notify
            fields = {
                "신청 고객": f"{req_data.get('user_name', '아마추어')}",
                "골프장": req_data.get('golf_course'),
                "라운딩 날짜": req_data.get('lesson_date'),
                "티오프 시간": req_data.get('lesson_time'),
                "배정 프로": f"{pro_name} (자격번호: {pro_cert})",
                "매칭 상태": "프로 수락 대기중"
            }
            send_discord_notification("🏌️‍♂️ 필드레슨 프로 배정 완료 (프로 수락 대기중)", fields)
            
            # Send propose push to pro
            if pro_data.get('contact'):
                pro_title = "🏌️‍♂️ 새로운 필드레슨 배정 제안"
                pro_body = f"[withPRO] {pro_name} 프로님, 새로운 필드레슨 매칭이 배정되었습니다.\n- 골프장: {req_data.get('golf_course')}\n- 일정: {req_data.get('lesson_date')} {req_data.get('lesson_time')}\n수락 여부를 확인하시고 최종 결정을 선택해 주세요."
                pro_link = f"https://withpro.kr/index.html?view=pro-accept&id={req_id}&pro_id={pro_id}"
                dispatch_push_notification(
                    pro_data.get('contact'), 
                    pro_title, 
                    pro_body, 
                    pro_link, 
                    template_type="match_proposal",
                    variables={
                        "#{프로명}": pro_name,
                        "#{골프장}": req_data.get('golf_course', ''),
                        "#{일정}": f"{req_data.get('lesson_date', '')} {req_data.get('lesson_time', '')}"
                    }
                )
                
            return create_response({'status': 'success', 'message': '프로 배정 및 매칭 제안 수락 대기 처리가 완료되었습니다.'})
        except Exception as e:
            return create_response({'error': str(e)}, 500)

    # ----------------------------------------------------
    # POST /api/coupon/validate
    # ----------------------------------------------------
    elif path == "/api/coupon/validate" and req.method == "POST":
        return create_response({'error': '쿠폰 기능은 현재 지원하지 않습니다.'}, 400)

    # ----------------------------------------------------
    # POST /api/lesson/submit-review
    # ----------------------------------------------------
    elif path == "/api/lesson/submit-review" and req.method == "POST":
        return create_response({'error': '후기 등록 기능은 현재 지원하지 않습니다.'}, 400)

    # ----------------------------------------------------
    # POST /api/lesson/payment-complete
    # ----------------------------------------------------
    elif path == "/api/lesson/payment-complete" and req.method == "POST":
        try:
            data = req.get_json()
            req_id = data.get('id')
            pay_method = data.get('pay_method')
            imp_uid = data.get('imp_uid')
            coupon_code = data.get('coupon_code')
            discount_amount = data.get('discount_amount', 0)
            paid_amount = data.get('paid_amount', 50000)
            
            if not req_id:
                return create_response({'error': 'Missing ID'}, 400)
                
            req_ref = db.collection("lesson_requests").document(str(req_id))
            req_doc = req_ref.get()
            if not req_doc.exists:
                return create_response({'error': 'Lesson request not found'}, 404)
                
            req_data = req_doc.to_dict()
            
            # Consume coupon if coupon_code was used
            if coupon_code and req_data.get('user_contact'):
                user_phone = clean_phone(req_data.get('user_contact'))
                # Find the coupon request document
                coupon_docs = db.collection("lesson_requests")\
                                .where("issued_coupon_code", "==", coupon_code)\
                                .where("issued_coupon_status", "==", "사용가능")\
                                .get()
                                
                for cd in coupon_docs:
                    c_data = cd.to_dict()
                    if c_data.get('user_contact') and clean_phone(c_data.get('user_contact')) == user_phone:
                        db.collection("lesson_requests").document(cd.id).update({
                            "issued_coupon_status": "사용완료"
                        })
                        break
                        
            # Update status to finalized match
            req_ref.update({
                "status": "결제완료",
                "pay_method": pay_method,
                "imp_uid": imp_uid,
                "coupon_code": coupon_code,
                "discount_amount": discount_amount,
                "paid_amount": paid_amount
            })
            
            # Fetch pro details
            pro_row = None
            if req_data.get('matched_pro_id'):
                pro_doc = db.collection("pro_users").document(str(req_data.get('matched_pro_id'))).get()
                if pro_doc.exists:
                    pro_row = pro_doc.to_dict()
                    
            paid_val = paid_amount
            disc_val = discount_amount
            coup_val = coupon_code
            
            price_text = f"{paid_val:,}원"
            if coup_val:
                price_text += f" (쿠폰 적용: {coup_val} -{disc_val:,}원 할인)"
                
            # Discord Notify
            fields = {
                "골프장": req_data.get('golf_course'),
                "라운딩 날짜": req_data.get('lesson_date'),
                "티오프 시간": req_data.get('lesson_time'),
                "결제 금액": price_text,
                "결제 수단": pay_method if pay_method else "간편결제",
                "포트원 거래번호": imp_uid if imp_uid else "시뮬레이션",
                "매칭 상태": "결제 완료 (최종 확정)"
            }
            send_discord_notification("💰 필드레슨 이용료 결제 완료 (최종 확정)", fields)
            
            # Notify Pro
            if pro_row and pro_row.get('contact'):
                pro_name = pro_row.get('name', '프로')
                customer_name = req_data.get('user_name', '아마추어 고객')
                customer_contact = req_data.get('user_contact', '-')
                
                pro_title = "⛳ 필드레슨 매칭 최종 확정!"
                pro_body = f"[withPRO] {pro_name} 프로님, 필드레슨 매칭이 최종 확정되었습니다.\n- 아마추어 고객명: {customer_name}\n- 고객 연락처: {customer_contact}\n- 골프장: {req_data.get('golf_course')}\n- 일정: {req_data.get('lesson_date')} {req_data.get('lesson_time')}\n라운딩 전 고객님께 가벼운 인사 전화를 드려 주세요."
                dispatch_push_notification(
                    pro_row.get('contact'), 
                    pro_title, 
                    pro_body, 
                    template_type="match_confirmed",
                    variables={
                        "#{프로명}": pro_name,
                        "#{고객명}": customer_name,
                        "#{고객연락처}": customer_contact,
                        "#{골프장}": req_data.get('golf_course', ''),
                        "#{일정}": f"{req_data.get('lesson_date', '')} {req_data.get('lesson_time', '')}"
                    }
                )
                
            return create_response({'status': 'success', 'message': '결제가 완료되었습니다.'})
        except Exception as e:
            return create_response({'error': str(e)}, 500)

    # ----------------------------------------------------
    # POST /api/pro/payment-complete
    # ----------------------------------------------------
    elif path == "/api/pro/payment-complete" and req.method == "POST":
        try:
            data = req.get_json()
            req_id = data.get('id')
            cert = data.get('cert')
            pay_method = data.get('pay_method')
            imp_uid = data.get('imp_uid')
            
            if not req_id or not cert:
                return create_response({'error': 'Missing ID or Cert'}, 400)
                
            # Verify pro
            pro_docs = db.collection("pro_users").where("cert_number", "==", cert).limit(1).get()
            if not pro_docs:
                return create_response({'error': 'Pro Not Found'}, 404)
                
            pro_doc = pro_docs[0]
            pro_data = pro_doc.to_dict()
            pro_id = pro_doc.id
            pro_name = pro_data.get('name', '레슨 프로')
            pro_contact = pro_data.get('contact', '-')
            
            # Update commission status in lesson request
            req_ref = db.collection("lesson_requests").document(str(req_id))
            req_doc = req_ref.get()
            if not req_doc.exists:
                return create_response({'error': 'Lesson request not found'}, 404)
                
            req_ref.update({
                "pro_pay_status": "결제완료",
                "pro_pay_method": pay_method,
                "pro_imp_uid": imp_uid
            })
            
            req_data = req_doc.to_dict()
            
            # Check if this pro still has any unpaid past lessons
            today_str = get_now_kst().strftime("%Y-%m-%d")
            
            unpaid_docs = db.collection("lesson_requests")\
                            .where("matched_pro_id", "==", pro_id)\
                            .where("status", "==", "결제완료")\
                            .where("lesson_date", "<", today_str)\
                            .get()
                            
            unpaid_count = 0
            for ud in unpaid_docs:
                ud_data = ud.to_dict()
                # Skip current request just in case it wasn't written to Firestore index yet
                if ud.id == req_id:
                    continue
                if ud_data.get("pro_pay_status") != "결제완료":
                    unpaid_count += 1
                    
            # If no unpaid lessons left, restore pro status
            if unpaid_count == 0:
                db.collection("pro_users").document(pro_id).update({
                    "status": "승인완료"
                })
                
            # Discord Notify
            fields = {
                "프로명": pro_name,
                "연락처": pro_contact,
                "골프장": req_data.get('golf_course'),
                "라운딩 날짜": req_data.get('lesson_date'),
                "결제 금액": "50,000원",
                "결제 수단": pay_method if pay_method else "신용카드",
                "포트원 거래번호": imp_uid if imp_uid else "시뮬레이션",
                "남은 미납 건수": str(unpaid_count),
                "프로 활동 상태": "승인 완료 (정식 파트너)" if unpaid_count == 0 else "정지 유지 (추가 미납 있음)"
            }
            send_discord_notification("💰 파트너 프로 라운딩 수수료 결제 완료", fields)
            
            return create_response({'status': 'success', 'message': '수수료 결제가 완료되었습니다.'})
        except Exception as e:
            return create_response({'error': str(e)}, 500)

    # ----------------------------------------------------
    # POST /api/admin/approve-pro
    # ----------------------------------------------------
    elif path == "/api/admin/approve-pro" and req.method == "POST":
        try:
            data = req.get_json()
            key = data.get('key')
            pro_id = data.get('id')
            
            if key != ADMIN_SECRET_KEY:
                return create_response({'error': 'Unauthorized'}, 401)
                
            if not pro_id:
                return create_response({'error': 'Missing ID'}, 400)
                
            pro_ref = db.collection("pro_users").document(str(pro_id))
            pro_doc = pro_ref.get()
            if not pro_doc.exists:
                return create_response({'error': 'Pro not found'}, 404)
                
            pro_ref.update({"status": "승인완료"})
            pro_data = pro_doc.to_dict()
            
            # Discord Notify
            fields = {
                "프로명": pro_data.get('name', '레슨 프로'),
                "연락처": pro_data.get('contact', '-'),
                "회원번호": pro_data.get('cert_number'),
                "승인 상태": "승인 완료 (활동 개시 가능)"
            }
            send_discord_notification("🏌️‍♂️ KPGA/KLPGA 회원 프로 파트너 심사 승인 완료", fields)
            
            return create_response({'status': 'success', 'message': '프로 회원 승인이 완료되었습니다.'})
        except Exception as e:
            return create_response({'error': str(e)}, 500)

    # ----------------------------------------------------
    # POST /api/admin/delete
    # ----------------------------------------------------
    elif path == "/api/admin/delete" and req.method == "POST":
        try:
            data = req.get_json()
            key = data.get('key')
            item_type = data.get('type')
            item_id = data.get('id')
            
            if key != ADMIN_SECRET_KEY:
                return create_response({'error': 'Unauthorized'}, 401)
                
            if not item_type or not item_id:
                return create_response({'error': 'Missing type or id'}, 400)
                
            collection_map = {
                'user': 'regular_users',
                'pro': 'pro_users',
                'request': 'lesson_requests'
            }
            
            col_name = collection_map.get(item_type)
            if not col_name:
                return create_response({'error': 'Invalid type'}, 400)
                
            db.collection(col_name).document(str(item_id)).delete()
            
            # Discord Alert
            send_discord_notification("🗑️ 관리자 데이터 삭제 실행", {
                "삭제 대상 구분": item_type,
                "삭제 대상 ID": str(item_id)
            })
            
            return create_response({'status': 'success', 'message': '성공적으로 삭제되었습니다.'})
        except Exception as e:
            return create_response({'error': str(e)}, 500)

    # ----------------------------------------------------
    # POST /api/pro/update-profile
    # ----------------------------------------------------
    elif path == "/api/pro/update-profile" and req.method == "POST":
        try:
            data = req.get_json()
            cert = data.get('cert')
            days = data.get('available_days')
            regions = data.get('regions')
            
            if not cert:
                return create_response({'error': 'Missing Certificate Number'}, 400)
                
            pro_docs = db.collection("pro_users").where("cert_number", "==", cert).limit(1).get()
            if not pro_docs:
                return create_response({'error': 'Pro Not Found'}, 404)
                
            pro_doc = pro_docs[0]
            db.collection("pro_users").document(pro_doc.id).update({
                "available_days": days,
                "regions": regions
            })
            
            return create_response({'status': 'success', 'message': '활동 정보가 수시 수정되었습니다.'})
        except Exception as e:
            return create_response({'error': str(e)}, 500)

    # ----------------------------------------------------
    # POST /api/save-fcm-token
    # ----------------------------------------------------
    elif path == "/api/save-fcm-token" and req.method == "POST":
        try:
            data = req.get_json()
            contact = data.get('contact')
            token = data.get('token')
            user_type = data.get('type')
            
            if not contact or not token:
                return create_response({'error': 'Missing contact or token'}, 400)
                
            clean_contact = contact.replace('-', '').strip()
            
            # Query and update fcm_token
            col_name = "pro_users" if user_type == "pro" else "regular_users"
            docs = db.collection(col_name).get()
            
            updated = False
            for d in docs:
                d_data = d.to_dict()
                if d_data.get("contact") and d_data.get("contact").replace("-", "").strip() == clean_contact:
                    db.collection(col_name).document(d.id).update({"fcm_token": token})
                    updated = True
                    
            if updated:
                return create_response({'status': 'success', 'message': 'FCM 토큰이 안전하게 등록되었습니다.'})
            else:
                return create_response({'status': 'error', 'message': '일치하는 회원을 찾지 못했습니다.'}, 404)
        except Exception as e:
            return create_response({'error': str(e)}, 500)

    # ----------------------------------------------------
    # POST /api/save-firebase-config
    # ----------------------------------------------------
    elif path == "/api/save-firebase-config" and req.method == "POST":
        try:
            data = req.get_json()
            key = data.get('key')
            config = data.get('config')
            
            if key != ADMIN_SECRET_KEY:
                return create_response({'error': 'Unauthorized'}, 401)
                
            # 1. Save to Firestore (works in read-only environment)
            db.collection("system_settings").document("firebase_web_config").set(config)
            
            # 2. Attempt to write to local file (fails in GCF, which is fine since we catch it)
            try:
                with open("firebase-web-config.json", "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=4)
            except Exception as e:
                logging.info(f"Local file write skipped (normal in read-only GCF): {e}")
                
            return create_response({'status': 'success', 'message': '클라이언트 웹 앱 설정이 안전하게 저장되었습니다.'})
        except Exception as e:
            return create_response({'error': str(e)}, 500)

    # ----------------------------------------------------
    # POST /api/save-firebase-service-account
    # ----------------------------------------------------
    elif path == "/api/save-firebase-service-account" and req.method == "POST":
        # Always return success in Firebase functions context since we don't need manual secret account injection
        return create_response({'status': 'success', 'message': 'Firebase Functions에서 실행 중이므로 비공개 키 관리가 생략되며 자동 보안 적용 상태입니다.'})

    # ----------------------------------------------------
    # POST /api/admin/firebase-test-push
    # ----------------------------------------------------
    elif path == "/api/admin/firebase-test-push" and req.method == "POST":
        try:
            data = req.get_json()
            key = data.get('key')
            token = data.get('token')
            title = data.get('title', '테스트 푸시')
            body = data.get('body', '이것은 withPRO 실시간 테스트 알림입니다.')
            
            if key != ADMIN_SECRET_KEY:
                return create_response({'error': 'Unauthorized'}, 401)
                
            if not token:
                return create_response({'error': 'FCM 토큰이 없습니다.'}, 400)
                
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data={
                    "click_action": "https://withpro.kr"
                },
                token=token
            )
            response = messaging.send(message)
            return create_response({'status': 'success', 'message': f'실시간 푸시 발송 완료! Response: {response}'})
        except Exception as e:
            return create_response({'error': str(e)}, 500)

    # ----------------------------------------------------
    # POST /api/pro/login
    # ----------------------------------------------------
    elif path == "/api/pro/login" and req.method == "POST":
        try:
            data = req.get_json()
            phone = data.get('phone')
            pin = data.get('pin')
            
            if not phone or not pin:
                return create_response({'error': '휴대폰 번호와 비밀번호(핀번호)를 입력해주세요.'}, 400)
                
            clean_phone_input = phone.replace('-', '').strip()
            
            pro_docs = db.collection("pro_users").get()
            matched_user = None
            matched_id = None
            for p in pro_docs:
                pd = p.to_dict()
                if pd.get("contact") and pd.get("contact").replace("-", "").strip() == clean_phone_input:
                    matched_user = pd
                    matched_id = p.id
                    break
                    
            if not matched_user:
                return create_response({'error': '등록된 프로 정보를 찾을 수 없습니다. 다시 가입 신청해 주세요.'}, 404)
                
            db_pin = matched_user.get('pin', '1234')
            if str(db_pin).strip() != str(pin).strip():
                return create_response({'error': '비밀번호(핀번호)가 일치하지 않습니다.'}, 401)
                
            return create_response({
                'status': 'success',
                'cert_number': matched_user.get('cert_number'),
                'message': '로그인에 성공했습니다.'
            })
        except Exception as e:
            return create_response({'error': str(e)}, 500)

    # ----------------------------------------------------
    # POST /api/lesson/lookup
    # ----------------------------------------------------
    elif path == "/api/lesson/lookup" and req.method == "POST":
        try:
            data = req.get_json()
            name = data.get('name')
            contact = data.get('contact')
            
            if not name or not contact:
                return create_response({'error': '예약자 이름과 연락처를 모두 입력해주세요.'}, 400)
                
            clean_contact_input = contact.replace('-', '').strip()
            
            # Lookup lesson requests
            lesson_docs = db.collection("lesson_requests").where("user_name", "==", name.strip()).get()
            matched_requests = []
            for l in lesson_docs:
                ld = l.to_dict()
                if ld.get("user_contact") and ld.get("user_contact").replace("-", "").strip() == clean_contact_input:
                    ld["id"] = l.id
                    matched_requests.append(ld)
                    
            # Sort by created_at DESC (manually since we filter in code)
            matched_requests.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            
            return create_response(matched_requests)
        except Exception as e:
            return create_response({'error': str(e)}, 500)
            
    else:
        return create_response({"error": "Not Found"}, 404)

# ==========================================
# ⏰ BACKGROUND SCHEDULED FUNCTION (check_pro_commissions)
# ==========================================
@scheduler_fn.on_schedule(
    schedule="0 9 * * *",
    timezone=scheduler_fn.Timezone("Asia/Seoul")
)
def check_pro_commissions_scheduled(event: scheduler_fn.ScheduledEvent) -> None:
    logging.info("[check_pro_commissions_scheduled] Scheduler triggered.")
    try:
        now_kst = get_now_kst()
        
        # Prevent notifications during night hours (before 9 AM KST)
        if now_kst.hour < 9:
            logging.info("Skipping nighttime notification checker.")
            return

        today_str = now_kst.strftime("%Y-%m-%d")
        yesterday_str = (now_kst - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Retrieve lesson requests that are finalized, where rounding was today or earlier, and pro has not paid commission.
        lessons_ref = db.collection("lesson_requests")\
                        .where("status", "==", "결제완료")\
                        .where("lesson_date", "<=", today_str)\
                        .get()
                        
        for doc in lessons_ref:
            row = doc.to_dict()
            req_id = doc.id
            pro_pay_status = row.get("pro_pay_status")
            
            # Check if pro commission is unpaid
            if pro_pay_status == "결제완료":
                continue
                
            pro_id = row.get("matched_pro_id")
            if not pro_id:
                continue
                
            # Fetch pro details
            pro_doc = db.collection("pro_users").document(str(pro_id)).get()
            if not pro_doc.exists:
                continue
                
            pro_data = pro_doc.to_dict()
            pro_name = pro_data.get("name", "프로")
            pro_contact = pro_data.get("contact")
            pro_status = pro_data.get("status")
            pro_cert = pro_data.get("cert_number", "")
            
            pro_notified = row.get("pro_notified", 0)
            lesson_date = row.get("lesson_date")
            golf_course = row.get("golf_course")
            
            # Process only if rounding was yesterday or earlier
            if lesson_date <= yesterday_str:
                if pro_notified == 0:
                    title = "📢 [withPRO] 라운딩 완료 및 플랫폼 수수료 결제 안내"
                    body = f"[withPRO] {pro_name} 프로님, 어제 {lesson_date} {golf_course} 라운딩이 완료되었습니다. 오늘까지 플랫폼 이용 수수료(5만원) 결제를 완료해 주시기 바랍니다. 미결제 시 파트너 활동이 정지(매칭 배정 불가) 처리될 수 있습니다. 아래 버튼을 눌러 즉시 결제해 주세요."
                    pro_link = f"https://withpro.kr/index.html?view=pro-pay-direct&id={req_id}&cert={pro_cert}"
                    dispatch_push_notification(
                        pro_contact, 
                        title, 
                        body, 
                        pro_link, 
                        template_type="pro_payment_request",
                        variables={
                            "#{프로명}": pro_name,
                            "#{일정}": lesson_date,
                            "#{골프장}": golf_course
                        }
                    )
                    db.collection("lesson_requests").document(req_id).update({"pro_notified": 1})
                    
                elif pro_notified == 1:
                    # Suspend pro
                    if pro_status != "정지":
                        db.collection("pro_users").document(str(pro_id)).update({"status": "정지"})
                        send_discord_notification("🚨 파트너 프로 활동 정지 (수수료 미납)", {
                            "pro_name": pro_name,
                            "pro_contact": pro_contact,
                            "golf_course": golf_course,
                            "lesson_date": lesson_date,
                            "reason": "수수료(5만원) 미납으로 인한 정지"
                        })
                        
                    title = "🚨 [withPRO] 라운딩 수수료 미납 및 파트너 정지 안내"
                    body = f"[withPRO] {pro_name} 프로님, {lesson_date} {golf_course} 라운딩이 완료되었습니다. 기한 내 수수료 5만원 입금이 확인되지 않아 파트너 프로 활동이 정지되었습니다. 5만원 입금이 완료될 때까지 활동 정지 및 매칭 배정 불가 상태가 유지됩니다. 아래 버튼을 눌러 수수료를 즉시 결제하시면 즉시 정지가 해제됩니다."
                    pro_link = f"https://withpro.kr/index.html?view=pro-pay-direct&id={req_id}&cert={pro_cert}"
                    dispatch_push_notification(
                        pro_contact, 
                        title, 
                        body, 
                        pro_link, 
                        template_type="pro_commission_due",
                        variables={
                            "#{프로명}": pro_name,
                            "#{일정}": lesson_date,
                            "#{골프장}": golf_course
                        }
                    )
                    db.collection("lesson_requests").document(req_id).update({"pro_notified": 2})
                    
    except Exception as e:
        logging.error(f"[check_pro_commissions_scheduled Error] {e}")
