import http.server
import socketserver
import sqlite3
import json
import os
import threading
import sys
from urllib.parse import urlparse

# Force stdout and stderr to use utf-8 encoding and flush immediately (prevent background buffering and encoding errors on Windows)
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(line_buffering=True, encoding='utf-8')
    except Exception:
        pass
if hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(line_buffering=True, encoding='utf-8')
    except Exception:
        pass

PORT = int(os.environ.get('PORT', 8000))
DB_NAME = "withpro.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # 일반 회원 테이블
    c.execute('''
        CREATE TABLE IF NOT EXISTS regular_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            contact TEXT,
            gender TEXT,
            region TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # 프로 회원 테이블
    c.execute('''
        CREATE TABLE IF NOT EXISTS pro_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            contact TEXT,
            cert_number TEXT,
            available_days TEXT,
            regions TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    try:
        c.execute("ALTER TABLE pro_users ADD COLUMN available_days TEXT")
    except sqlite3.OperationalError:
        pass # Column might already exist
    try:
        c.execute("ALTER TABLE pro_users ADD COLUMN status TEXT DEFAULT '승인대기'")
    except sqlite3.OperationalError:
        pass # Column might already exist
    try:
        c.execute("ALTER TABLE pro_users ADD COLUMN cert_type TEXT")
    except sqlite3.OperationalError:
        pass # Column might already exist
    try:
        c.execute("ALTER TABLE pro_users ADD COLUMN profile_pic TEXT")
    except sqlite3.OperationalError:
        pass # Column might already exist
    try:
        c.execute("ALTER TABLE pro_users ADD COLUMN pin TEXT DEFAULT '1234'")
    except sqlite3.OperationalError:
        pass # Column might already exist
        
    # 레슨 요청 테이블
    c.execute('''
        CREATE TABLE IF NOT EXISTS lesson_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            golf_course TEXT,
            lesson_date TEXT,
            lesson_time TEXT,
            status TEXT DEFAULT '매칭 대기중',
            matched_pro_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    try:
        c.execute("ALTER TABLE lesson_requests ADD COLUMN status TEXT DEFAULT '매칭 대기중'")
    except sqlite3.OperationalError:
        pass # Column might already exist
    try:
        c.execute("ALTER TABLE lesson_requests ADD COLUMN matched_pro_id INTEGER")
    except sqlite3.OperationalError:
        pass # Column might already exist
    try:
        c.execute("ALTER TABLE lesson_requests ADD COLUMN user_name TEXT")
    except sqlite3.OperationalError:
        pass # Column might already exist
    try:
        c.execute("ALTER TABLE lesson_requests ADD COLUMN user_contact TEXT")
    except sqlite3.OperationalError:
        pass # Column might already exist
    try:
        c.execute("ALTER TABLE lesson_requests ADD COLUMN pay_method TEXT")
    except sqlite3.OperationalError:
        pass # Column might already exist
    try:
        c.execute("ALTER TABLE lesson_requests ADD COLUMN imp_uid TEXT")
    except sqlite3.OperationalError:
        pass # Column might already exist
    try:
        c.execute("ALTER TABLE regular_users ADD COLUMN fcm_token TEXT")
    except sqlite3.OperationalError:
        pass # Column might already exist
    try:
        c.execute("ALTER TABLE pro_users ADD COLUMN fcm_token TEXT")
    except sqlite3.OperationalError:
        pass # Column might already exist
    try:
        c.execute("ALTER TABLE lesson_requests ADD COLUMN pro_pay_status TEXT DEFAULT '미납'")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE lesson_requests ADD COLUMN pro_pay_method TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE lesson_requests ADD COLUMN pro_imp_uid TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE lesson_requests ADD COLUMN pro_notified INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
        
    conn.commit()
    conn.close()

# 디스코드 웹훅 알림 설정 (생성한 디스코드 웹훅 URL을 여기에 붙여넣으세요)
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1506978226092638208/hgh7I430irA_S4jy2AG9VCHDc44mKxTlsA-p2GBjM1y7o02qfyTcA_MsnBYh6RyqmTWA"

# ==========================================
# 📱 실제 SMS 및 카카오 알림톡 발송 연동 설정
# ==========================================
# 실제 카카오 알림톡(실패 시 대체 문자 발송)을 전송받으시려면 아래 설정을 채워주세요.
# 1. 알리고(Aligo) 이용 시: SMS_PROVIDER = "aligo" 로 설정 후 API 키, 아이디, 등록된 발신번호 입력
# 2. 솔라피(Solapi) 이용 시: SMS_PROVIDER = "solapi" 로 설정 후 API 키, Secret 키, 등록된 발신번호 입력
SMS_PROVIDER = "aligo"       # 'aligo', 'solapi', 'none' 중 선택
SMS_API_KEY = "7y38cjghrwi6qvn5z2aoivu2cntcvu72"            # 알리고의 API key 또는 솔라피의 API key
SMS_API_SECRET = ""         # 솔라피 이용 시에만 사용 (Secret Key)
SMS_USER_ID = "cwgy71"            # 알리고 이용 시에만 사용 (알리고 ID)
SMS_SENDER_NUMBER = "01041428686"      # KISA에 등록된 본인의 발신 전화번호 (예: '021234567' 또는 '01012345678')

# 카카오톡 비즈니스 채널 발신 프로필 키 (알리고의 senderkey 또는 솔라피의 pfId)
KAKAO_SENDER_KEY = "02887bec62408a96f4135c5dfc72d4597c6b6e9b"       # 예: "a1b2c3d4e5f6..." (알리고) 또는 "KA01PF123456..." (솔라피)

# 승인받은 알림톡 템플릿 코드 매핑 (본인의 알림톡 템플릿 코드에 맞게 설정하세요)
KAKAO_TPL_LESSON_REQUESTED = "UI_6115"  # 레슨 신청 완료 알림 (예: "tpl_lesson_req")
KAKAO_TPL_MATCH_PROPOSAL = "UI_6119"    # 프로에게 매칭 제안 알림 (예: "tpl_match_prop")
KAKAO_TPL_MATCH_SUCCESS = "UI_6120"     # 매칭 성공/결제 대기 알림 (예: "tpl_match_success")
KAKAO_TPL_MATCH_CONFIRMED = "UI_6121"   # 결제 완료/매칭 최종 확정 알림 (예: "tpl_match_confirm")
KAKAO_TPL_PRO_COMMISSION_DUE = "UI_xxxx" # 프로 수수료 미납 및 정지 안내 알림 (알리고 등록 필요, 예: "UI_xxxx")

def send_aligo_alimtalk(receiver, tpl_code, subject, message, link=None):
    if not SMS_API_KEY or not SMS_USER_ID or not SMS_SENDER_NUMBER or not KAKAO_SENDER_KEY:
        print("[Aligo Alimtalk] API key, User ID, Sender Number, or Sender Key is missing. Skipping.", flush=True)
        return False
        
    url = "https://apis.aligo.in/akv10/alimtalk/send/"
    
    # 알림톡 기본 전송 정보
    payload = {
        "key": SMS_API_KEY,
        "userid": SMS_USER_ID,
        "sender": SMS_SENDER_NUMBER,
        "senderkey": KAKAO_SENDER_KEY,
        "tpl_code": tpl_code,
        "receiver_1": receiver,
        "subject_1": subject,
        "message_1": message,
        "failover": "Y",                # 대체 발송 사용
        "fsubject_1": subject,          # 대체 발송 제목
        "fmessage_1": message           # 대체 발송 내용
    }
    
    # 링크가 있고 버튼을 지원하는 경우 버튼 페이로드 추가 (보통 알림톡 템플릿 심사 시 지정한 형식과 같아야 함)
    if link:
        button_info = {
            "button": [
                {
                    "name": "자세히 보기",
                    "linkType": "WL",
                    "linkUrl1": link, # Mobile Web Link
                    "linkUrl2": link  # PC Web Link
                }
            ]
        }
        payload["button_1"] = json.dumps(button_info)
        
    try:
        import urllib.request
        import urllib.parse
        data = urllib.parse.urlencode(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, timeout=5) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            if str(res_data.get("result_code")) == "1" or res_data.get("code") == 0:
                print(f"[Aligo Alimtalk] 알림톡 전송 요청 성공: {receiver} (대체 발송 활성화)", flush=True)
                return True
            else:
                print(f"[Aligo Alimtalk] 알림톡 전송 요청 실패: {res_data}", flush=True)
                return False
    except Exception as e:
        print(f"[Aligo Alimtalk] 에러 발생: {e}", flush=True)
        return False

def send_solapi_alimtalk(receiver, template_id, message, link=None):
    if not SMS_API_KEY or not SMS_API_SECRET or not SMS_SENDER_NUMBER or not KAKAO_SENDER_KEY:
        print("[Solapi Alimtalk] API Key, Secret, Sender Number, or Profile Key is missing. Skipping.", flush=True)
        return False
        
    import time
    import uuid
    import hmac
    import hashlib
    import urllib.request
    
    # 솔라피 REST API HMAC 인증 생성
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
    
    # 대체 발송 본문(text) 포함 (알림톡 실패 시 자동으로 문자로 대체 전송됨)
    payload = {
        "message": {
            "to": receiver,
            "from": SMS_SENDER_NUMBER,
            "text": message,  # 알림톡 실패 시 대체 발송되는 LMS/SMS 메시지 내용
            "type": "ATA",
            "kakaoOptions": {
                "pfId": KAKAO_SENDER_KEY,
                "templateId": template_id
            }
        }
    }
    
    if link:
        # 알림톡 버튼 정보 추가 (템플릿에 버튼이 정의되어 승인받은 경우에만 작동)
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
            if str(res_data.get("statusCode")) in ["2000", "3000"] or "messageId" in res_data.get("description", "") or "messageId" in str(res_data):
                print(f"[Solapi Alimtalk] 알림톡 전송 요청 성공: {receiver} (대체 발송 활성화)", flush=True)
                return True
            else:
                print(f"[Solapi Alimtalk] 알림톡 전송 요청 실패: {res_data}", flush=True)
                return False
    except Exception as e:
        print(f"[Solapi Alimtalk] 에러 발생: {e}", flush=True)
        return False

def dispatch_push_notification(receiver, title, body, link=None, template_type=None):
    if not receiver:
        return
    
    clean_receiver = "".join(filter(str.isdigit, receiver))
    
    # 디스코드 실시간 모니터링 알림으로도 동시에 미러링해서 편하게 모니터링 가능하도록 유지
    fields = {
        "수신 대상": f"{clean_receiver}",
        "알림 제목": title,
        "알림 내용": body
    }
    if link:
        fields["이동 링크"] = link
    send_discord_notification(f"📱 [withPRO App Push] {title}", fields)
    
    # 1. 24시간 실시간 FCM 진짜 앱 푸시 전송 (Firebase Admin SDK 연동 상태 시)
    if FIREBASE_INIT:
        try:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            # 일반 회원 또는 프로 회원 중 연락처가 일치하는 유저의 FCM 토큰 조회
            c.execute("SELECT fcm_token FROM regular_users WHERE REPLACE(contact, '-', '') = ? AND fcm_token IS NOT NULL ORDER BY id DESC LIMIT 1", (clean_receiver,))
            row = c.fetchone()
            if not row:
                c.execute("SELECT fcm_token FROM pro_users WHERE REPLACE(contact, '-', '') = ? AND fcm_token IS NOT NULL ORDER BY id DESC LIMIT 1", (clean_receiver,))
                row = c.fetchone()
            
            conn.close()
            
            if row and row[0]:
                fcm_token = row[0]
                # FCM 푸시 메시지 객체 생성
                message = messaging.Message(
                    notification=messaging.Notification(
                        title=title,
                        body=body
                    ),
                    data={
                        "click_action": link if link else "http://localhost:8000"
                    },
                    token=fcm_token
                )
                # 전송 실행
                response = messaging.send(message)
                print(f"[Firebase FCM] 푸시 알림 전송 완료! Response: {response}", flush=True)
        except Exception as e:
            print(f"[Firebase FCM] 푸시 알림 전송 실패: {e}", flush=True)
            
    # 2. 카카오 알림톡 및 대체 문자 전송 연동 추가
    if SMS_PROVIDER != "none" and template_type:
        # 알림톡 본문에 타이틀과 내용을 결합
        talk_message = f"[{title}]\n{body}"
        tpl_code = None
        
        # 템플릿 코드 매칭
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
            
        # 템플릿 코드가 설정되어 있는 경우 알림톡 전송 시도
        if tpl_code:
            if SMS_PROVIDER == "aligo":
                send_aligo_alimtalk(clean_receiver, tpl_code, title, talk_message, link)
            elif SMS_PROVIDER == "solapi":
                send_solapi_alimtalk(clean_receiver, tpl_code, talk_message, link)
        else:
            print(f"[Kakao Alimtalk] 템플릿 코드가 정의되지 않았습니다 (타입: {template_type}). 발송을 스킵합니다.", flush=True)
            
    # 가상 앱 PUSH API 연동 콘솔 시뮬레이션 출력
    print(f"\n==================================================", flush=True)
    print(f"🔵 [withPRO App Push API 호출]", flush=True)
    print(f"수신 대상: {clean_receiver} (앱 인증 유저)", flush=True)
    print(f"알림 타이틀: {title}", flush=True)
    print(f"알림 바디: {body}", flush=True)
    if link:
        print(f"랜딩 링크: {link}", flush=True)
    if template_type:
        print(f"알림 템플릿 타입: {template_type}", flush=True)
    print(f"==================================================\n", flush=True)

# 관리자 대시보드 비밀 비밀번호
ADMIN_SECRET_KEY = "withpro123"

# ==========================================
# 🔥 Firebase Admin SDK 서비스 연동 설정 (FCM 푸시)
# ==========================================
FIREBASE_INIT = False

def reload_firebase_admin():
    global FIREBASE_INIT
    try:
        if os.path.exists("firebase-service-account.json"):
            import firebase_admin
            from firebase_admin import credentials, messaging
            try:
                default_app = firebase_admin.get_app()
                firebase_admin.delete_app(default_app)
            except ValueError:
                pass # Not initialized yet
            cred = credentials.Certificate("firebase-service-account.json")
            firebase_admin.initialize_app(cred)
            FIREBASE_INIT = True
            print("[Firebase] 서비스가 성공적으로 초기화/리로드되었습니다! 실시간 FCM 앱 푸시 활성화.", flush=True)
            return True, "success"
        else:
            FIREBASE_INIT = False
            print("[Firebase] 'firebase-service-account.json' 파일이 없어 가상 시뮬레이션 모드로 가동합니다.", flush=True)
            return False, "file_not_found"
    except Exception as e:
        FIREBASE_INIT = False
        print(f"[Firebase] 초기화 오류 (가상 시뮬레이션 모드 가동): {e}", flush=True)
        return False, str(e)

# 초기 실행 시도
reload_firebase_admin()

def send_discord_notification(title, fields):
    if not DISCORD_WEBHOOK_URL or DISCORD_WEBHOOK_URL.startswith("YOUR_"):
        return
    
    # 딥 포레스트 그린 테마 색상 (#0B3D2E -> Dec 736558)
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
            # Add explicit timeout to prevent hanging if network is slow/blocked
            with urllib.request.urlopen(req, timeout=3) as response:
                pass
        except Exception as e:
            print(f"[디스코드 알림 발송 실패] {e}")
            
    # Run in a background thread to prevent blocking the single-threaded HTTP server
    threading.Thread(target=send_webhook, daemon=True).start()

def check_pro_commissions():
    import time
    import datetime
    import sqlite3
    # Wait for the server to spin up
    time.sleep(5)
    print("[check_pro_commissions] Background commission checker thread started.", flush=True)
    while True:
        try:
            # Get current date in KST (UTC+9)
            kst = datetime.timezone(datetime.timedelta(hours=9))
            now_kst = datetime.datetime.now(kst)
            today_str = now_kst.strftime("%Y-%m-%d")

            conn = sqlite3.connect(DB_NAME)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            # Find lesson requests where status is '결제완료' (finalized match by amateur)
            # and the lesson_date is past (less than today_str)
            # and pro has not paid commission yet (pro_pay_status != '결제완료')
            c.execute("""
                SELECT lr.*, pu.name as pro_name, pu.contact as pro_contact, pu.status as pro_status
                FROM lesson_requests lr
                JOIN pro_users pu ON lr.matched_pro_id = pu.id
                WHERE lr.status = '결제완료'
                  AND lr.lesson_date < ?
                  AND (lr.pro_pay_status IS NULL OR lr.pro_pay_status != '결제완료')
            """, (today_str,))
            unpaid_lessons = c.fetchall()

            for row in unpaid_lessons:
                req_id = row['id']
                pro_id = row['matched_pro_id']
                pro_contact = row['pro_contact']
                pro_name = row['pro_name']
                golf_course = row['golf_course']
                lesson_date = row['lesson_date']

                # 1. Update pro status to '정지' in DB if not already suspended
                if row['pro_status'] != '정지':
                    c.execute("UPDATE pro_users SET status = '정지' WHERE id = ?", (pro_id,))
                    # Send a discord notification about the suspension
                    send_discord_notification("🚨 파트너 프로 활동 정지 (수수료 미납)", {
                        "프로명": pro_name,
                        "연락처": pro_contact,
                        "미납 라운딩": f"{golf_course} ({lesson_date})",
                        "사유": "라운딩 다음 날 수수료(5만원) 미납으로 인한 정지"
                    })

                # 2. Check if we already sent the push notification for this request
                if not row['pro_notified']:
                    title = "🚨 [withPRO] 라운딩 수수료 미납 및 파트너 정지 안내"
                    body = f"[withPRO] {pro_name} 프로님, {lesson_date} {golf_course} 라운딩이 완료되었습니다. 다음날인 오늘까지 수수료 5만원 입금이 확인되지 않아 파트너 프로 활동이 정지되었습니다. 5만원 입금이 되지 않으면 파트너 프로로서 정지(활동 정지 및 매칭 배정 불가) 상태가 유지됩니다. 마이페이지에서 결제를 완료하시면 즉시 정지가 해제됩니다."
                    pro_link = "https://withpro.life/index.html?view=pro-mypage"
                    dispatch_push_notification(pro_contact, title, body, pro_link, template_type="pro_commission_due")
                    c.execute("UPDATE lesson_requests SET pro_notified = 1 WHERE id = ?", (req_id,))

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[check_pro_commissions background thread error] {e}", flush=True)

        # Run every 60 seconds
        time.sleep(60)

class MyRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # 정적 파일 서빙 시 강력한 캐시 무효화 헤더 강제 이식 (모바일 웹뷰 및 브라우저 캐시 무력화)
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def do_GET(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path == '/api/firebase-config':
            config = {}
            if os.path.exists("firebase-web-config.json"):
                try:
                    with open("firebase-web-config.json", "r", encoding="utf-8") as f:
                        config = json.load(f)
                except Exception:
                    pass
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(config).encode('utf-8'))
            return
            
        elif parsed_path.path == '/api/admin/firebase-status':
            from urllib.parse import parse_qs
            query_params = parse_qs(parsed_path.query)
            key = query_params.get('key', [None])[0]
            
            if key != ADMIN_SECRET_KEY:
                self.send_response(401)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Unauthorized'}).encode('utf-8'))
                return
                
            client_configured = False
            if os.path.exists("firebase-web-config.json"):
                try:
                    with open("firebase-web-config.json", "r", encoding="utf-8") as f:
                        cfg = json.load(f)
                        if cfg.get('apiKey') and cfg.get('messagingSenderId'):
                            client_configured = True
                except Exception:
                    pass
                    
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'client_configured': client_configured,
                'admin_initialized': FIREBASE_INIT
            }).encode('utf-8'))
            return

        elif parsed_path.path == '/firebase-messaging-sw.js':
            config = {}
            if os.path.exists("firebase-web-config.json"):
                try:
                    with open("firebase-web-config.json", "r", encoding="utf-8") as f:
                        config = json.load(f)
                except Exception:
                    pass
            
            config_str = json.dumps(config)
            sw_code = f"""importScripts('https://www.gstatic.com/firebasejs/8.10.1/firebase-app.js');
importScripts('https://www.gstatic.com/firebasejs/8.10.1/firebase-messaging.js');

const firebaseConfig = {config_str};

if (firebaseConfig && firebaseConfig.apiKey) {{
    firebase.initializeApp(firebaseConfig);
    const messaging = firebase.messaging();
    
    messaging.onBackgroundMessage(function(payload) {{
        console.log('[firebase-messaging-sw.js] Background message received:', payload);
        const notificationTitle = payload.notification.title;
        const notificationOptions = {{
            body: payload.notification.body,
            icon: '/logo.svg',
            data: payload.data
        }};
        self.registration.showNotification(notificationTitle, notificationOptions);
    }});
}} else {{
    console.log('[firebase-messaging-sw.js] Firebase config is empty, background messaging is disabled.');
}}
"""
            self.send_response(200)
            self.send_header('Content-Type', 'application/javascript')
            self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
            self.end_headers()
            self.wfile.write(sw_code.encode('utf-8'))
            return

        elif parsed_path.path == '/api/admin/data':
            from urllib.parse import parse_qs
            query_params = parse_qs(parsed_path.query)
            key = query_params.get('key', [None])[0]
            
            if key != ADMIN_SECRET_KEY:
                self.send_response(401)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Unauthorized'}).encode('utf-8'))
                return
            
            try:
                conn = sqlite3.connect(DB_NAME)
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                
                c.execute("SELECT * FROM regular_users ORDER BY id DESC")
                regular_users = [dict(row) for row in c.fetchall()]
                
                c.execute("SELECT * FROM pro_users ORDER BY id DESC")
                pro_users = [dict(row) for row in c.fetchall()]
                
                c.execute("SELECT * FROM lesson_requests ORDER BY id DESC")
                lesson_requests = [dict(row) for row in c.fetchall()]
                
                conn.close()
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'regular_users': regular_users,
                    'pro_users': pro_users,
                    'lesson_requests': lesson_requests
                }).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
            return
            
        elif parsed_path.path == '/api/lesson/status':
            from urllib.parse import parse_qs
            query_params = parse_qs(parsed_path.query)
            req_id = query_params.get('id', [None])[0]
            
            if not req_id:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Missing ID'}).encode('utf-8'))
                return
            
            try:
                conn = sqlite3.connect(DB_NAME)
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                c.execute("SELECT * FROM lesson_requests WHERE id = ?", (req_id,))
                row = c.fetchone()
                conn.close()
                
                if not row:
                    self.send_response(404)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': 'Not Found'}).encode('utf-8'))
                    return
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(dict(row)).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
            return

        elif parsed_path.path == '/api/pro/profile':
            from urllib.parse import parse_qs
            query_params = parse_qs(parsed_path.query)
            cert = query_params.get('cert', [None])[0]
            
            if not cert:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Missing Certificate Number'}).encode('utf-8'))
                return
            
            try:
                conn = sqlite3.connect(DB_NAME)
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                c.execute("SELECT * FROM pro_users WHERE cert_number = ?", (cert,))
                pro_row = c.fetchone()
                
                if not pro_row:
                    conn.close()
                    self.send_response(404)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': 'Pro Not Found'}).encode('utf-8'))
                    return
                
                pro_data = dict(pro_row)
                
                # 매칭된 레슨 요청 리스트 조회
                c.execute("SELECT * FROM lesson_requests WHERE matched_pro_id = ? ORDER BY id DESC", (pro_data['id'],))
                matches = [dict(row) for row in c.fetchall()]
                
                conn.close()
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'profile': pro_data,
                    'matches': matches
                }).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
            return

        elif parsed_path.path == '/api/pro/login-by-phone':
            from urllib.parse import parse_qs
            query_params = parse_qs(parsed_path.query)
            phone = query_params.get('phone', [None])[0]
            
            if not phone:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': '전화번호를 입력해주세요.'}).encode('utf-8'))
                return
            
            clean_input = phone.replace('-', '').strip()
            
            try:
                conn = sqlite3.connect(DB_NAME)
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                c.execute("SELECT cert_number, contact FROM pro_users ORDER BY id DESC")
                rows = c.fetchall()
                conn.close()
                
                matched_row = None
                for row in rows:
                    if row['contact']:
                        db_contact = row['contact'].replace('-', '').strip()
                        if db_contact == clean_input:
                            matched_row = row
                            break
                
                if not matched_row:
                    self.send_response(404)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': '등록된 프로 정보를 찾을 수 없습니다.'}).encode('utf-8'))
                    return
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'success', 'cert_number': matched_row['cert_number']}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
            return

        elif parsed_path.path == '/api/pro/latest-phone':
            try:
                conn = sqlite3.connect(DB_NAME)
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                c.execute("SELECT contact FROM pro_users ORDER BY id DESC LIMIT 1")
                row = c.fetchone()
                conn.close()
                
                phone = row['contact'] if row else "010-1234-5678"
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'phone': phone}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
            return
            
        super().do_GET()

    def do_POST(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/register/regular':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("INSERT INTO regular_users (name, contact, gender, region) VALUES (?, ?, ?, ?)",
                      (data.get('name'), data.get('contact'), data.get('gender'), data.get('region')))
            conn.commit()
            conn.close()
            
            # 디스코드 알림 발송
            fields = {
                "이름": data.get('name'),
                "연락처": data.get('contact'),
                "성별": data.get('gender'),
                "희망 지역": data.get('region')
            }
            send_discord_notification("👤 새로운 일반 회원 가입 완료", fields)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'success', 'message': '일반 회원 가입이 완료되었습니다.'}).encode('utf-8'))
            
        elif parsed_path.path == '/api/register/pro':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("INSERT INTO pro_users (name, contact, cert_type, cert_number, profile_pic, available_days, regions, pin) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                      (data.get('name'), data.get('contact'), data.get('cert_type'), data.get('cert_number'), data.get('profile_pic'), data.get('available_days'), data.get('regions'), data.get('pin', '1234')))
            conn.commit()
            conn.close()
            
            # 디스코드 알림 발송
            fields = {
                "이름": data.get('name', '프로'),
                "연락처": data.get('contact', '010-0000-0000'),
                "자격증 종류": data.get('cert_type', 'KPGA 투어프로'),
                "회원 번호": data.get('cert_number'),
                "활동 가능 요일": data.get('available_days'),
                "활동 가능 지역": data.get('regions')
            }
            send_discord_notification("🏌️‍♂️ 새로운 프로 회원 등록 신청", fields)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'success', 'message': '프로 회원 가입이 완료되었습니다.'}).encode('utf-8'))
            
        elif parsed_path.path == '/api/lesson/pro-accept':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            req_id = data.get('id')
            pro_id = data.get('pro_id')
            accept = data.get('accept', False)
            
            if not req_id or not pro_id:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Missing ID or Pro ID'}).encode('utf-8'))
                return
                
            try:
                conn = sqlite3.connect(DB_NAME)
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                
                if accept:
                    c.execute("UPDATE lesson_requests SET status = '매칭완료' WHERE id = ? AND matched_pro_id = ?", (req_id, pro_id))
                    
                    c.execute("SELECT * FROM lesson_requests WHERE id = ?", (req_id,))
                    row = c.fetchone()
                    
                    c.execute("SELECT * FROM pro_users WHERE id = ?", (pro_id,))
                    pro_row = c.fetchone()
                    
                    conn.commit()
                    conn.close()
                    
                    if row:
                        pro_name = pro_row['name'] if pro_row else "배정 프로"
                        pro_cert = pro_row['cert_number'] if pro_row else "-"
                        
                        # 디스코드 알림 발송
                        fields = {
                            "신청 고객": f"{row['user_name'] if row['user_name'] else '아마추어'} ({row['user_contact'] if row['user_contact'] else '-'})",
                            "골프장": row['golf_course'],
                            "라운딩 날짜": row['lesson_date'],
                            "티오프 시간": row['lesson_time'],
                            "매칭 프로": f"{pro_name} (자격번호: {pro_cert})",
                            "매칭 상태": "매칭 완료 (결제 대기중)",
                            "예약금": "50,000원"
                        }
                        send_discord_notification("🏌️‍♂️ 필드레슨 프로 매칭 수락 완료 & 결제 대기", fields)
                        
                        # 아마추어 고객 앱 PUSH 발송
                        pro_contact = pro_row['contact'] if pro_row else "-"
                        customer_title = "🎉 필드레슨 프로 매칭 성공!"
                        customer_body = f"[withPRO] '{row['golf_course']}' 필드레슨 프로 매칭이 성공적으로 완료되었습니다.\n- 배정 프로: {pro_name} 프로님 ({pro_contact})\n예약을 최종 확정하시려면 아래 예약금 결제(50,000원)를 완료해 주세요."
                        proto = self.headers.get('X-Forwarded-Proto', 'http')
                        host_header = self.headers.get('Host', 'localhost:8000')
                        customer_link = f"{proto}://{host_header}/index.html?view=my-bookings&id={row['id']}"
                        dispatch_push_notification(row['user_contact'], customer_title, customer_body, customer_link, template_type="match_success")
                else:
                    c.execute("UPDATE lesson_requests SET status = '매칭 대기중', matched_pro_id = NULL WHERE id = ? AND matched_pro_id = ?", (req_id, pro_id))
                    
                    c.execute("SELECT * FROM lesson_requests WHERE id = ?", (req_id,))
                    row = c.fetchone()
                    
                    c.execute("SELECT * FROM pro_users WHERE id = ?", (pro_id,))
                    pro_row = c.fetchone()
                    
                    conn.commit()
                    conn.close()
                    
                    if row:
                        pro_name = pro_row['name'] if pro_row else "배정 프로"
                        # 디스코드 알림 발송
                        fields = {
                            "골프장": row['golf_course'],
                            "라운딩 날짜": row['lesson_date'],
                            "티오프 시간": row['lesson_time'],
                            "거절 프로": pro_name,
                            "매칭 상태": "매칭 거절 (재매칭 대기중)"
                        }
                        send_discord_notification("❌ 프로 매칭 거절 (재매칭 대기중)", fields)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'success'}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
            return

        elif parsed_path.path == '/api/request-lesson':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            user_name = data.get('userName', '아마추어')
            user_contact = data.get('userContact', '010-0000-0000')
            
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            
            # 레슨 매칭 신청 정보 저장
            c.execute("INSERT INTO lesson_requests (user_id, user_name, user_contact, golf_course, lesson_date, lesson_time) VALUES (?, ?, ?, ?, ?, ?)",
                      (data.get('user_id', 'APP_USER'), user_name, user_contact, data.get('golfCourse'), data.get('date'), data.get('time')))
            inserted_id = c.lastrowid
            
            # 일반 회원 테이블에 존재하지 않는 경우 자동 등록 (일반 회원 내역 연동)
            c.execute("SELECT id FROM regular_users WHERE name = ? AND contact = ?", (user_name, user_contact))
            if not c.fetchone():
                region = data.get('golfCourse', '').split()[0] if data.get('golfCourse') else ''
                c.execute("INSERT INTO regular_users (name, contact, region) VALUES (?, ?, ?)",
                          (user_name, user_contact, region))
            
            conn.commit()
            conn.close()
            
            # 앱 푸시 알림 발송
            title = "⛳ 필드레슨 매칭 요청 접수 완료"
            body = f"[withPRO] {data.get('userName', '아마추어')}님, '{data.get('golfCourse')}' 골프장 필드레슨 매칭 요청이 안전하게 접수되었습니다. 일정에 맞는 최고의 프로님을 배정 후 즉시 알림톡 또는 앱 푸시 알림으로 알려드리겠습니다."
            proto = self.headers.get('X-Forwarded-Proto', 'http')
            host_header = self.headers.get('Host', 'localhost:8000')
            user_link = f"{proto}://{host_header}/index.html?view=my-bookings&id={inserted_id}"
            dispatch_push_notification(data.get('userContact'), title, body, user_link, template_type="lesson_requested")
            
            # 디스코드 알림 발송
            fields = {
                "신청자명": data.get('userName', '아마추어'),
                "연락처": data.get('userContact', '010-0000-0000'),
                "골프장": data.get('golfCourse'),
                "라운딩 날짜": data.get('date'),
                "티오프 시간": data.get('time'),
                "매칭 대상 ID": data.get('user_id', 'APP_USER')
            }
            send_discord_notification("⛳ 새로운 필드레슨 매칭 신청 접수", fields)
            
            # 1일(86400초) 뒤에 매칭 실패 알림 전송 (시뮬레이션)
            def send_fail_notification():
                print(f"\n==================================================")
                print(f"[withPRO PUSH API 호출 - 매칭 실패] 대상: {data.get('userName', '아마추어')}님 ({data.get('userContact', '010-0000-0000')})")
                print(f"메시지: '현재 매칭가능한 프로님이 안계십니다'")
                print(f"==================================================\n")
            
            # 실제 운영에서는 백그라운드 작업(Celery 등)이나 86400초를 사용하지만,
            # 테스트를 위해 코드는 86400초(1일)로 설정해둡니다.
            timer = threading.Timer(86400, send_fail_notification)
            timer.start()

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'status': 'success', 
                'id': inserted_id,
                'message': '⛳ 필드레슨 매칭 신청이 성공적으로 접수되었습니다!\n\nwithPRO를 믿고 소중한 라운딩 정보를 등록해 주셔서 진심으로 감사드립니다.\n\n골퍼님의 일정과 지역에 꼭 맞는 최고의 KPGA/KLPGA 프로님을 매칭하기 위해 최선을 다하고 있습니다. 매칭이 성사되는 대로 앱 푸시 알림을 통해 가장 먼저 기쁜 소식을 전해 드리겠습니다.\n\n오늘도 기분 좋은 하루 보내시고, 설레는 마음으로 라운딩을 준비해 보세요. 감사합니다!'
            }).encode('utf-8'))

        elif parsed_path.path == '/api/admin/match':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            key = data.get('key')
            req_id = data.get('id')
            pro_id = data.get('pro_id')
            
            if key != ADMIN_SECRET_KEY:
                self.send_response(401)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Unauthorized'}).encode('utf-8'))
                return
                
            if not req_id or not pro_id:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Missing ID or Pro ID'}).encode('utf-8'))
                return
                
            try:
                conn = sqlite3.connect(DB_NAME)
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                c.execute("UPDATE lesson_requests SET status = '프로 수락 대기중', matched_pro_id = ? WHERE id = ?", (pro_id, req_id))
                c.execute("SELECT * FROM lesson_requests WHERE id = ?", (req_id,))
                row = c.fetchone()
                
                c.execute("SELECT * FROM pro_users WHERE id = ?", (pro_id,))
                pro_row = c.fetchone()
                
                conn.commit()
                conn.close()
                if row:
                    pro_name = pro_row['name'] if pro_row else "배정 프로"
                    pro_cert = pro_row['cert_number'] if pro_row else "-"
                    
                    # 디스코드 알림 발송 (프로 배정 상태)
                    fields = {
                        "신청 고객": f"{row['user_name'] if row['user_name'] else '아마추어'}",
                        "골프장": row['golf_course'],
                        "라운딩 날짜": row['lesson_date'],
                        "티오프 시간": row['lesson_time'],
                        "배정 프로": f"{pro_name} (자격번호: {pro_cert})",
                        "매칭 상태": "프로 수락 대기중"
                    }
                    send_discord_notification("🏌️‍♂️ 필드레슨 프로 배정 완료 (프로 수락 대기중)", fields)
                    
                    # 프로에게 매칭 제안 앱 PUSH 전송
                    if pro_row and pro_row['contact']:
                        pro_title = "🏌️‍♂️ 새로운 필드레슨 배정 제안"
                        pro_body = f"[withPRO] {pro_name} 프로님, 새로운 필드레슨 매칭이 배정되었습니다.\n- 골프장: {row['golf_course']}\n- 일정: {row['lesson_date']} {row['lesson_time']}\n수락 여부를 확인하시고 최종 결정을 선택해 주세요."
                        proto = self.headers.get('X-Forwarded-Proto', 'http')
                        host_header = self.headers.get('Host', 'localhost:8000')
                        pro_link = f"{proto}://{host_header}/index.html?view=pro-accept&id={row['id']}&pro_id={pro_id}"
                        dispatch_push_notification(pro_row['contact'], pro_title, pro_body, pro_link, template_type="match_proposal")
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'success', 'message': '프로 배정 및 매칭 제안 수락 대기 처리가 완료되었습니다.'}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))

        elif parsed_path.path == '/api/lesson/payment-complete':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            req_id = data.get('id')
            
            if not req_id:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Missing ID'}).encode('utf-8'))
                return
                
            try:
                conn = sqlite3.connect(DB_NAME)
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                # 결제 수단 및 포트원 결제번호(imp_uid) 저장
                c.execute("UPDATE lesson_requests SET status = '결제완료', pay_method = ?, imp_uid = ? WHERE id = ?", (data.get('pay_method'), data.get('imp_uid'), req_id))
                c.execute("SELECT * FROM lesson_requests WHERE id = ?", (req_id,))
                row = c.fetchone()
                
                pro_row = None
                if row and row['matched_pro_id']:
                    c.execute("SELECT * FROM pro_users WHERE id = ?", (row['matched_pro_id'],))
                    pro_row = c.fetchone()
                
                conn.commit()
                conn.close()
                
                if row:
                    # 디스코드 알림 발송
                    fields = {
                        "골프장": row['golf_course'],
                        "라운딩 날짜": row['lesson_date'],
                        "티오프 시간": row['lesson_time'],
                        "결제 금액": "50,000원",
                        "결제 수단": row['pay_method'] if row['pay_method'] else "간편결제",
                        "포트원 거래번호": row['imp_uid'] if row['imp_uid'] else "시뮬레이션",
                        "매칭 상태": "결제 완료 (최종 확정)"
                    }
                    send_discord_notification("💰 필드레슨 예약금 결제 완료 (최종 확정)", fields)
                    
                    # 프로에게 매칭 최종 확정 안내 (신청인 이름 & 연락처 포함) 앱 PUSH 전송
                    if pro_row and pro_row['contact']:
                        pro_name = pro_row['name'] if pro_row['name'] else "프로"
                        customer_name = row['user_name'] if row['user_name'] else "아마추어 고객"
                        customer_contact = row['user_contact'] if row['user_contact'] else "-"
                        
                        pro_title = "⛳ 필드레슨 매칭 최종 확정!"
                        pro_body = f"[withPRO] {pro_name} 프로님, 필드레슨 매칭이 최종 확정되었습니다.\n- 아마추어 고객명: {customer_name}\n- 고객 연락처: {customer_contact}\n- 골프장: {row['golf_course']}\n- 일정: {row['lesson_date']} {row['lesson_time']}\n라운딩 전 고객님께 가벼운 인사 전화를 드려 주세요."
                        dispatch_push_notification(pro_row['contact'], pro_title, pro_body, template_type="match_confirmed")
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'success', 'message': '결제가 완료되었습니다.'}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))

        elif parsed_path.path == '/api/pro/payment-complete':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            req_id = data.get('id')
            cert = data.get('cert')
            
            if not req_id or not cert:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Missing ID or Cert'}).encode('utf-8'))
                return
                
            try:
                conn = sqlite3.connect(DB_NAME)
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                
                # Verify pro
                c.execute("SELECT * FROM pro_users WHERE cert_number = ?", (cert,))
                pro_row = c.fetchone()
                if not pro_row:
                    conn.close()
                    self.send_response(404)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': 'Pro Not Found'}).encode('utf-8'))
                    return
                
                pro_id = pro_row['id']
                pro_name = pro_row['name'] if pro_row['name'] else "레슨 프로"
                pro_contact = pro_row['contact'] if pro_row['contact'] else "-"
                
                # Update lesson request's pro pay status
                c.execute("UPDATE lesson_requests SET pro_pay_status = '결제완료', pro_pay_method = ?, pro_imp_uid = ? WHERE id = ? AND matched_pro_id = ?", 
                          (data.get('pay_method'), data.get('imp_uid'), req_id, pro_id))
                
                # Fetch request details for notifications
                c.execute("SELECT * FROM lesson_requests WHERE id = ?", (req_id,))
                req_row = c.fetchone()
                
                # Check if this pro still has any unpaid past lessons
                import datetime
                kst = datetime.timezone(datetime.timedelta(hours=9))
                now_kst = datetime.datetime.now(kst)
                today_str = now_kst.strftime("%Y-%m-%d")
                
                c.execute("""
                    SELECT COUNT(*) FROM lesson_requests
                    WHERE matched_pro_id = ?
                      AND status = '결제완료'
                      AND lesson_date < ?
                      AND (pro_pay_status IS NULL OR pro_pay_status != '결제완료')
                """, (pro_id, today_str))
                unpaid_count = c.fetchone()[0]
                
                # If no other unpaid lessons, restore status to '승인완료'
                if unpaid_count == 0:
                    c.execute("UPDATE pro_users SET status = '승인완료' WHERE id = ?", (pro_id,))
                    
                conn.commit()
                conn.close()
                
                # Send Discord Notification
                if req_row:
                    fields = {
                        "프로명": pro_name,
                        "연락처": pro_contact,
                        "골프장": req_row['golf_course'],
                        "라운딩 날짜": req_row['lesson_date'],
                        "결제 금액": "50,000원",
                        "결제 수단": data.get('pay_method') if data.get('pay_method') else "신용카드",
                        "포트원 거래번호": data.get('imp_uid') if data.get('imp_uid') else "시뮬레이션",
                        "남은 미납 건수": str(unpaid_count),
                        "프로 활동 상태": "승인 완료 (정식 파트너)" if unpaid_count == 0 else "정지 유지 (추가 미납 있음)"
                    }
                    send_discord_notification("💰 파트너 프로 라운딩 수수료 결제 완료", fields)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'success', 'message': '수수료 결제가 완료되었습니다.'}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))

        elif parsed_path.path == '/api/admin/approve-pro':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            key = data.get('key')
            pro_id = data.get('id')
            
            if key != ADMIN_SECRET_KEY:
                self.send_response(401)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Unauthorized'}).encode('utf-8'))
                return
                
            if not pro_id:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Missing ID'}).encode('utf-8'))
                return
                
            try:
                conn = sqlite3.connect(DB_NAME)
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                c.execute("UPDATE pro_users SET status = '승인완료' WHERE id = ?", (pro_id,))
                c.execute("SELECT * FROM pro_users WHERE id = ?", (pro_id,))
                row = c.fetchone()
                conn.commit()
                conn.close()
                
                if row:
                    # 디스코드 알림 발송
                    fields = {
                        "프로명": row['name'] if row['name'] else "레슨 프로",
                        "연락처": row['contact'] if row['contact'] else "-",
                        "회원번호": row['cert_number'],
                        "승인 상태": "승인 완료 (활동 개시 가능)"
                    }
                    send_discord_notification("🏌️‍♂️ KPGA/KLPGA 회원 프로 파트너 심사 승인 완료", fields)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'success', 'message': '프로 회원 승인이 완료되었습니다.'}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))

        elif parsed_path.path == '/api/admin/delete':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            key = data.get('key')
            item_type = data.get('type') # 'request', 'pro', 'user'
            item_id = data.get('id')
            
            if key != ADMIN_SECRET_KEY:
                self.send_response(401)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Unauthorized'}).encode('utf-8'))
                return
                
            if not item_type or not item_id:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Missing type or id'}).encode('utf-8'))
                return
                
            try:
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                
                if item_type == 'user':
                    c.execute("DELETE FROM regular_users WHERE id = ?", (item_id,))
                elif item_type == 'pro':
                    c.execute("DELETE FROM pro_users WHERE id = ?", (item_id,))
                elif item_type == 'request':
                    c.execute("DELETE FROM lesson_requests WHERE id = ?", (item_id,))
                else:
                    conn.close()
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': 'Invalid type'}).encode('utf-8'))
                    return
                    
                conn.commit()
                conn.close()
                
                # Send Discord Notification
                send_discord_notification("🗑️ 관리자 데이터 삭제 실행", {
                    "삭제 대상 구분": item_type,
                    "삭제 대상 ID": str(item_id)
                })
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'success', 'message': '성공적으로 삭제되었습니다.'}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))

        elif parsed_path.path == '/api/pro/update-profile':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            cert = data.get('cert')
            days = data.get('available_days')
            regions = data.get('regions')
            
            if not cert:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Missing Certificate Number'}).encode('utf-8'))
                return
                
            try:
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute("UPDATE pro_users SET available_days = ?, regions = ? WHERE cert_number = ?", (days, regions, cert))
                conn.commit()
                conn.close()
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'success', 'message': '활동 정보가 수시 수정되었습니다.'}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
        elif parsed_path.path == '/api/save-fcm-token':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            contact = data.get('contact')
            token = data.get('token')
            user_type = data.get('type') # 'regular' or 'pro'
            
            if not contact or not token:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Missing contact or token'}).encode('utf-8'))
                return
                
            clean_contact = contact.replace('-', '').strip()
            try:
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                if user_type == 'pro':
                    # 프로 테이블에 등록된 연락처 기준으로 FCM 토큰 저장
                    c.execute("UPDATE pro_users SET fcm_token = ? WHERE REPLACE(contact, '-', '') = ?", (token, clean_contact))
                else:
                    # 일반 회원 테이블에 등록된 연락처 기준으로 FCM 토큰 저장
                    c.execute("UPDATE regular_users SET fcm_token = ? WHERE REPLACE(contact, '-', '') = ?", (token, clean_contact))
                conn.commit()
                conn.close()
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'success', 'message': 'FCM 토큰이 안전하게 등록되었습니다.'}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
        elif parsed_path.path == '/api/save-firebase-config':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            key = data.get('key')
            config = data.get('config')
            
            if key != ADMIN_SECRET_KEY:
                self.send_response(401)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Unauthorized'}).encode('utf-8'))
                return
                
            try:
                with open("firebase-web-config.json", "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=4)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'success', 'message': '클라이언트 웹 앱 설정이 안전하게 저장되었습니다.'}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
                
        elif parsed_path.path == '/api/save-firebase-service-account':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            key = data.get('key')
            service_account_str = data.get('service_account')
            
            if key != ADMIN_SECRET_KEY:
                self.send_response(401)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Unauthorized'}).encode('utf-8'))
                return
                
            try:
                sa_data = json.loads(service_account_str)
                
                with open("firebase-service-account.json", "w", encoding="utf-8") as f:
                    json.dump(sa_data, f, indent=4)
                
                success, msg = reload_firebase_admin()
                
                if success:
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'status': 'success', 'message': '서비스 계정 비공개 키가 성공적으로 등록 및 활성화되었습니다!'}).encode('utf-8'))
                else:
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': f'Firebase 초기화 오류: {msg}'}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': f'비공개 키 파싱 실패: {str(e)}'}).encode('utf-8'))
                
        elif parsed_path.path == '/api/admin/firebase-test-push':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            key = data.get('key')
            token = data.get('token')
            title = data.get('title', '테스트 푸시')
            body = data.get('body', '이것은 withPRO 실시간 테스트 알림입니다.')
            
            if key != ADMIN_SECRET_KEY:
                self.send_response(401)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Unauthorized'}).encode('utf-8'))
                return
                
            if not token:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'FCM 토큰이 없습니다.'}).encode('utf-8'))
                return
                
            if not FIREBASE_INIT:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Firebase Admin SDK가 활성화되지 않았습니다. 먼저 서비스 비공개 키를 등록하세요.'}).encode('utf-8'))
                return
                
            try:
                proto = self.headers.get('X-Forwarded-Proto', 'http')
                host_header = self.headers.get('Host', 'localhost:8000')
                click_action_url = f"{proto}://{host_header}"
                
                from firebase_admin import messaging
                message = messaging.Message(
                    notification=messaging.Notification(
                        title=title,
                        body=body
                    ),
                    data={
                        "click_action": click_action_url
                    },
                    token=token
                )
                response = messaging.send(message)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'success', 'message': f'실시간 푸시 발송 완료! Response: {response}'}).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
                
        elif parsed_path.path == '/api/pro/login':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            phone = data.get('phone')
            pin = data.get('pin')
            
            if not phone or not pin:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': '휴대폰 번호와 비밀번호(핀번호)를 입력해주세요.'}).encode('utf-8'))
                return
                
            clean_phone = phone.replace('-', '').strip()
            
            try:
                conn = sqlite3.connect(DB_NAME)
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                c.execute("SELECT * FROM pro_users ORDER BY id DESC")
                rows = c.fetchall()
                conn.close()
                
                matched_user = None
                for row in rows:
                    if row['contact']:
                        db_contact = row['contact'].replace('-', '').strip()
                        if db_contact == clean_phone:
                            matched_user = row
                            break
                            
                if not matched_user:
                    self.send_response(404)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': '등록된 프로 정보를 찾을 수 없습니다. 다시 가입 신청해 주세요.'}).encode('utf-8'))
                    return
                    
                # 핀 번호 검증 (기존 유저는 기본값 '1234'로 검증)
                db_pin = matched_user['pin'] if 'pin' in matched_user.keys() and matched_user['pin'] else '1234'
                if str(db_pin).strip() != str(pin).strip():
                    self.send_response(401)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': '비밀번호(핀번호)가 일치하지 않습니다.'}).encode('utf-8'))
                    return
                    
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'status': 'success', 
                    'cert_number': matched_user['cert_number'],
                    'message': '로그인에 성공했습니다.'
                }).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
                
        elif parsed_path.path == '/api/lesson/lookup':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            name = data.get('name')
            contact = data.get('contact')
            
            if not name or not contact:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': '예약자 이름과 연락처를 모두 입력해주세요.'}).encode('utf-8'))
                return
                
            clean_contact = contact.replace('-', '').strip()
            
            try:
                conn = sqlite3.connect(DB_NAME)
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                # 연락처와 이름이 일치하는 예약 내역 조회
                c.execute("SELECT * FROM lesson_requests WHERE user_name = ? ORDER BY id DESC", (name.strip(),))
                rows = c.fetchall()
                conn.close()
                
                matched_requests = []
                for row in rows:
                    if row['user_contact']:
                        db_contact = row['user_contact'].replace('-', '').strip()
                        if db_contact == clean_contact:
                            matched_requests.append(dict(row))
                            
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(matched_requests).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
        else:
            self.send_error(404, "Not Found")

if __name__ == '__main__':
    init_db()
    # Start background commission checker thread
    import threading
    threading.Thread(target=check_pro_commissions, daemon=True).start()
    # Reuse address to prevent address already in use error during frequent restarts
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), MyRequestHandler) as httpd:
        print(f"서버가 시작되었습니다! 브라우저에서 http://localhost:{PORT} 로 접속하세요.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n서버가 종료되었습니다.")
