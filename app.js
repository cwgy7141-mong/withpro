// window.alert 및 window.confirm 커스텀 오버라이드 시스템 (withPRO 테마)
(function() {
    // 1. Inject Styles (Self-contained)
    const style = document.createElement('style');
    style.innerHTML = `
        .withpro-alert-backdrop {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(11, 54, 33, 0.4); /* Deep forest green translucent */
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
            z-index: 20000;
            display: flex;
            justify-content: center;
            align-items: center;
            opacity: 0;
            transition: opacity 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            padding: 20px;
            box-sizing: border-box;
        }
        .withpro-alert-backdrop.active {
            opacity: 1;
        }
        .withpro-alert-container {
            background: #ffffff;
            width: 100%;
            max-width: 340px;
            border-radius: 24px;
            padding: 24px;
            box-shadow: 0 20px 40px rgba(11, 54, 33, 0.15);
            border: 1px solid rgba(11, 54, 33, 0.08);
            transform: scale(0.9);
            transition: transform 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
            display: flex;
            flex-direction: column;
            align-items: stretch;
            box-sizing: border-box;
        }
        .withpro-alert-backdrop.active .withpro-alert-container {
            transform: scale(1);
        }
        .withpro-alert-header {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 16px;
        }
        .withpro-alert-icon {
            width: 24px;
            height: 24px;
            color: #00c775; /* Mint green */
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }
        .withpro-alert-title {
            font-size: 16px;
            font-weight: 700;
            color: #0b3621; /* Forest green */
            margin: 0;
            font-family: 'Pretendard', -apple-system, sans-serif;
            letter-spacing: -0.3px;
        }
        .withpro-alert-body {
            font-size: 15px;
            font-weight: 500;
            line-height: 1.5;
            color: #333d37;
            margin-bottom: 24px;
            white-space: pre-wrap;
            word-break: break-word;
            font-family: 'Pretendard', -apple-system, sans-serif;
        }
        .withpro-alert-actions {
            display: flex;
            gap: 8px;
        }
        .withpro-alert-button {
            flex: 1;
            background: #0b3621;
            color: #ffffff;
            border: none;
            padding: 14px 20px;
            font-size: 15px;
            font-weight: 600;
            border-radius: 14px;
            cursor: pointer;
            transition: all 0.2s ease;
            text-align: center;
            font-family: 'Pretendard', -apple-system, sans-serif;
            box-shadow: 0 4px 12px rgba(11, 54, 33, 0.15);
            outline: none;
        }
        .withpro-alert-button:hover {
            background: #124d32;
            transform: translateY(-1px);
            box-shadow: 0 6px 16px rgba(11, 54, 33, 0.2);
        }
        .withpro-alert-button:active {
            transform: translateY(1px);
            box-shadow: 0 2px 6px rgba(11, 54, 33, 0.1);
        }
        .withpro-alert-button.cancel {
            background: #f3f5f4;
            color: #5c645f;
            box-shadow: none;
        }
        .withpro-alert-button.cancel:hover {
            background: #e6eae8;
            transform: translateY(-1px);
        }
        .withpro-alert-button.cancel:active {
            transform: translateY(1px);
        }
    `;
    document.head.appendChild(style);

    // window.alert 오버라이드
    window.alert = function(message) {
        const backdrop = document.createElement('div');
        backdrop.className = 'withpro-alert-backdrop';

        const container = document.createElement('div');
        container.className = 'withpro-alert-container';

        const header = document.createElement('div');
        header.className = 'withpro-alert-header';

        const icon = document.createElement('div');
        icon.className = 'withpro-alert-icon';
        icon.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>`;

        const title = document.createElement('div');
        title.className = 'withpro-alert-title';
        title.innerText = '올앱의 메시지';

        header.appendChild(icon);
        header.appendChild(title);

        const body = document.createElement('div');
        body.className = 'withpro-alert-body';
        body.innerText = message;

        const actions = document.createElement('div');
        actions.className = 'withpro-alert-actions';

        const button = document.createElement('button');
        button.className = 'withpro-alert-button';
        button.innerText = '확인';

        actions.appendChild(button);
        container.appendChild(header);
        container.appendChild(body);
        container.appendChild(actions);
        backdrop.appendChild(container);

        // App container check (for centering in mobile layout frame)
        const appContainer = document.querySelector('.app-container');
        if (appContainer) {
            backdrop.style.position = 'absolute';
            backdrop.style.borderRadius = 'var(--radius-lg)';
            appContainer.appendChild(backdrop);
        } else {
            document.body.appendChild(backdrop);
        }

        setTimeout(() => {
            backdrop.classList.add('active');
        }, 10);

        button.focus();

        const closeAlert = () => {
            backdrop.classList.remove('active');
            setTimeout(() => {
                backdrop.remove();
            }, 250);
        };

        button.onclick = closeAlert;
        backdrop.onclick = (e) => {
            if (e.target === backdrop) {
                closeAlert();
            }
        };

        const handleKeyDown = (e) => {
            if (e.key === 'Escape' || e.key === 'Enter') {
                closeAlert();
                document.removeEventListener('keydown', handleKeyDown);
            }
        };
        document.addEventListener('keydown', handleKeyDown);
    };

    // 비동기 confirm 구현 함수
    window.withproConfirm = function(message) {
        return new Promise((resolve) => {
            const backdrop = document.createElement('div');
            backdrop.className = 'withpro-alert-backdrop';

            const container = document.createElement('div');
            container.className = 'withpro-alert-container';

            const header = document.createElement('div');
            header.className = 'withpro-alert-header';

            const icon = document.createElement('div');
            icon.className = 'withpro-alert-icon';
            icon.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>`;

            const title = document.createElement('div');
            title.className = 'withpro-alert-title';
            title.innerText = '올앱의 메시지';

            header.appendChild(icon);
            header.appendChild(title);

            const body = document.createElement('div');
            body.className = 'withpro-alert-body';
            body.innerText = message;

            const actions = document.createElement('div');
            actions.className = 'withpro-alert-actions';

            const cancelButton = document.createElement('button');
            cancelButton.className = 'withpro-alert-button cancel';
            cancelButton.innerText = '취소';

            const okButton = document.createElement('button');
            okButton.className = 'withpro-alert-button';
            okButton.innerText = '확인';

            actions.appendChild(cancelButton);
            actions.appendChild(okButton);
            container.appendChild(header);
            container.appendChild(body);
            container.appendChild(actions);
            backdrop.appendChild(container);

            const appContainer = document.querySelector('.app-container');
            if (appContainer) {
                backdrop.style.position = 'absolute';
                backdrop.style.borderRadius = 'var(--radius-lg)';
                appContainer.appendChild(backdrop);
            } else {
                document.body.appendChild(backdrop);
            }

            setTimeout(() => {
                backdrop.classList.add('active');
            }, 10);

            okButton.focus();

            const closeWithResult = (result) => {
                backdrop.classList.remove('active');
                setTimeout(() => {
                    backdrop.remove();
                }, 250);
                resolve(result);
            };

            okButton.onclick = () => closeWithResult(true);
            cancelButton.onclick = () => closeWithResult(false);
            
            backdrop.onclick = (e) => {
                if (e.target === backdrop) {
                    closeWithResult(false);
                }
            };

            const handleKeyDown = (e) => {
                if (e.key === 'Escape') {
                    closeWithResult(false);
                    document.removeEventListener('keydown', handleKeyDown);
                } else if (e.key === 'Enter') {
                    closeWithResult(true);
                    document.removeEventListener('keydown', handleKeyDown);
                }
            };
            document.addEventListener('keydown', handleKeyDown);
        });
    };
})();


const app = {
    // 결제 PG사 설정 ('html5_inicis': KG이니시스, 'tosspayments': 토스페이먼츠)
    DEFAULT_PG_PROVIDER: 'html5_inicis',

    // 보안 강화: 본인 예약 상세 정보 및 결제창 진입 시 이름과 전화번호의 정확한 수동 대조를 강제하기 위한 메모리 전용 세션 상태
    verifiedUserName: "",
    verifiedUserContact: "",
    verifiedBookings: [], // 현재 검증된 예약 신청 내역 리스트 (메모리에 보관하여 조회 성공 시에만 채워짐)

    maskContact: function(contact) {
        if (!contact) return "010-****-****";
        const clean = contact.replace(/[^0-9]/g, "");
        if (clean.length === 11) {
            return `${clean.slice(0, 3)}-****-${clean.slice(7)}`;
        } else if (clean.length === 10) {
            return `${clean.slice(0, 3)}-***-${clean.slice(6)}`;
        }
        return contact;
    },

    navigate: function(viewId) {
        // 보안 검증 강제: 결제 화면 진입 시 무조건 현재 세션에 수동 검증된 예약이 있는지 확인
        if (viewId === 'view-payment') {
            const reqId = localStorage.getItem('withpro_last_request_id');
            const hasVerified = app.verifiedBookings && app.verifiedBookings.some(b => b.id == reqId);
            if (!hasVerified) {
                alert("보안을 위해 [내 예약 확인] 메뉴에서 예약자 이름과 연락처를 먼저 정확히 입력해 주세요.");
                app.checkMyBookings();
                return;
            }
        }

        // 모든 뷰에서 active 클래스 제거
        document.querySelectorAll('.view').forEach(view => {
            view.classList.remove('active');
        });
        
        // 대상 뷰에 active 클래스 추가
        const targetView = document.getElementById(viewId);
        if (targetView) {
            targetView.classList.add('active');
            // 스크롤을 맨 위로 이동
            const content = targetView.querySelector('.content');
            if(content) {
                content.scrollTop = 0;
            }
        }
    },

    downloadGuide: function(type) {
        const filename = type === 'pro' ? 'withpro_pro_guide_app_mockup.png' : 'withpro_amateur_guide.png';
        const link = document.createElement('a');
        link.href = '/' + filename;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    },
    
    switchHomeTab: function(tabId) {
        // 1. 모든 탭 버튼에서 active 클래스 제거
        document.querySelectorAll('#view-home .tab-switch-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        
        // 2. 모든 탭 콘텐츠에서 active 클래스 제거
        document.querySelectorAll('#view-home .home-tab-content').forEach(content => {
            content.classList.remove('active');
        });
        
        // 3. 선택된 탭 버튼 활성화
        const targetBtn = document.getElementById(`btn-home-tab-${tabId}`);
        if (targetBtn) {
            targetBtn.classList.add('active');
        }
        
        // 4. 선택된 탭 콘텐츠 활성화
        const targetContent = document.getElementById(`home-tab-content-${tabId}`);
        if (targetContent) {
            targetContent.classList.add('active');
        }
    },
    
    init: function() {
        // 강력한 서비스 워커 및 로컬 캐시 강제 무효화 명령 (보안 패치 갱신용)
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.getRegistrations().then(function(registrations) {
                for (let registration of registrations) {
                    registration.update(); // 최신 정적 리소스로 강제 복구 지시
                }
            });
        }

        // 성별 토글 버튼 이벤트 연동
        const toggleGroups = document.querySelectorAll('.toggle-group');
        toggleGroups.forEach(group => {
            const btns = group.querySelectorAll('.toggle-btn');
            btns.forEach(btn => {
                btn.addEventListener('click', () => {
                    btns.forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                });
            });
        });


        // 프로 회원 레슨 가능 지역(다중 선택) 버튼 이벤트 연동
        const proGrid = document.querySelector('#view-pro .grid-3');
        if (proGrid) {
            const btns = proGrid.querySelectorAll('.grid-btn-simple');
            btns.forEach(btn => {
                btn.addEventListener('click', () => {
                    btn.classList.toggle('active');
                });
            });
        }

        // 프로 회원 레슨 가능 요일 이벤트 연동
        const dayGrid = document.getElementById('pro-days');
        if (dayGrid) {
            const btns = dayGrid.querySelectorAll('.day-btn');
            btns.forEach(btn => {
                btn.addEventListener('click', () => {
                    btn.classList.toggle('active');
                });
            });
        }

        // 라운딩 날짜 및 티오프 시간 카드 변경 시 텍스트 업데이트 연동
        const dateInput = document.getElementById('lesson-date');
        if (dateInput) {
            const handleDateChange = (e) => {
                app.updateDateDisplay(e.target.value);
            };
            dateInput.addEventListener('change', handleDateChange);
            dateInput.addEventListener('input', handleDateChange);
        }

        const timeInput = document.getElementById('lesson-time');
        if (timeInput) {
            let lastMinute = null;
            
            // 시간 선택 팝업이 열릴 때(포커스될 때) 기존 분(minute) 값을 저장합니다.
            timeInput.addEventListener('focus', () => {
                if (timeInput.value) {
                    lastMinute = timeInput.value.split(':')[1];
                } else {
                    lastMinute = null;
                }
            });

            const handleTimeChange = (e) => {
                const val = e.target.value;
                app.updateTimeDisplay(val);
                
                if (val) {
                    const currentMinute = val.split(':')[1];
                    // 분(minute) 값이 실제로 변경되었을 때만 사용자가 선택을 완료한 것으로 판단하여 팝업을 닫습니다.
                    if (lastMinute !== null && currentMinute !== lastMinute) {
                        setTimeout(() => {
                            e.target.blur();
                        }, 80);
                    }
                    lastMinute = currentMinute;
                }
            };
            timeInput.addEventListener('change', handleTimeChange);
            timeInput.addEventListener('input', handleTimeChange);
        }

        // picker-minute 옵션 동적 생성
        const minSelect = document.getElementById('picker-minute');
        if (minSelect && minSelect.options.length === 0) {
            for (let i = 0; i < 60; i++) {
                const val = String(i).padStart(2, '0');
                const opt = new Option(`${val}분`, val);
                minSelect.add(opt);
            }
        }

        // 비밀 이스터에그: 메인 홈 화면의 로고를 1초 내에 3번 연속 클릭하면 관리자 페이지로 이동
        let logoClicks = 0;
        let logoClickTimer;
        // 비밀 이스터에그: 메인 홈 화면 및 첫 선택 화면의 로고를 1초 내에 3번 연속 클릭하면 관리자 페이지로 이동
        document.querySelectorAll('.main-logo').forEach(logo => {
            logo.style.cursor = 'pointer'; // 클릭 가능함을 시각적으로 안내 (관리자 전용)
            logo.addEventListener('click', () => {
                logoClicks++;
                clearTimeout(logoClickTimer);
                
                if (logoClicks === 3) {
                    logoClicks = 0;
                    // 보안 수칙: 소스코드 노출 방지를 위해 평문 암호 키(?key=...) 없이 단순히 admin.html로만 이동합니다.
                    // 관리자님은 이미 본인 브라우저에 1회 로그인하셨기 때문에 자동 패스인되어 무점검 진입합니다.
                    window.location.href = 'admin.html';
                    return;
                }
                
                logoClickTimer = setTimeout(() => {
                    logoClicks = 0;
                }, 1000);
            });
        });

        // URL 쿼리 파라미터 파싱 및 화면 연동 (SMS 알림 링크 대응)
        const urlParams = new URLSearchParams(window.location.search);
        const reqIdParam = urlParams.get('id');
        const viewParam = urlParams.get('view');
        
        if (reqIdParam && viewParam !== 'pro-accept' && viewParam !== 'pro-pay-direct') {
            localStorage.setItem('withpro_last_request_id', reqIdParam);
        }
        
        if (viewParam === 'pro-accept') {
            const proIdParam = urlParams.get('pro_id');
            if (reqIdParam && proIdParam) {
                app.loadProAcceptView(reqIdParam, proIdParam);
            } else {
                app.navigate('view-home');
            }
        } else if (viewParam === 'pro-pay-direct') {
            const certParam = urlParams.get('cert');
            if (reqIdParam && certParam) {
                localStorage.setItem('withpro_pro_cert', certParam);
                app.loadProPayDirectView(reqIdParam, certParam);
            } else {
                app.navigate('view-home');
            }
        } else if (viewParam === 'my-bookings' || (reqIdParam && !viewParam)) {
            if (reqIdParam) {
                app.loadBookingDirectly(reqIdParam);
            } else {
                app.checkMyBookings();
            }
        }
    },
    
    requestLesson: async function() {
        const userName = document.getElementById('lesson-user-name') ? document.getElementById('lesson-user-name').value.trim() : "";
        const userContact = document.getElementById('lesson-user-contact') ? document.getElementById('lesson-user-contact').value.trim() : "";
        const golfCourse = document.getElementById('lesson-golf-course') ? document.getElementById('lesson-golf-course').value.trim() : "";
        const date = document.getElementById('lesson-date').value;
        const time = document.getElementById('lesson-time').value;
        
        if (!userName) {
            alert("신청자 이름을 입력해 주세요.");
            if (document.getElementById('lesson-user-name')) document.getElementById('lesson-user-name').focus();
            return;
        }
        if (!userContact) {
            alert("신청자 연락처를 입력해 주세요.");
            if (document.getElementById('lesson-user-contact')) document.getElementById('lesson-user-contact').focus();
            return;
        }
        if (!golfCourse) {
            alert("라운딩 골프장을 입력해 주세요.");
            if (document.getElementById('lesson-golf-course')) document.getElementById('lesson-golf-course').focus();
            return;
        }
        if (!date || !time) {
            alert("라운딩 일정과 시간을 모두 선택해 주세요.");
            return;
        }

        const consentChecked = document.getElementById('lesson-privacy-consent').checked;
        if (!consentChecked) {
            alert("개인정보 수집 및 이용 동의는 필수 항목입니다.");
            return;
        }

        try {
            // 서버에 레슨 요청을 보내고 앱 푸시 알림 트리거
            const response = await fetch('/api/request-lesson', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ userName, userContact, golfCourse, date, time })
            });
            const data = await response.json();
            
            // 예약 ID 로컬 스토리지에 저장
            if (data.id) {
                localStorage.setItem('withpro_last_request_id', data.id);
            }
            
            alert(data.message); // 서버에서 매칭 접수 결과 메시지 수신 및 표시
            
            // Firebase FCM 알림 연동 및 토큰 저장 시도
            app.initFirebase(userContact, 'regular');
            
            app.navigate('view-home');
        } catch(e) {
            alert('서버 오류가 발생했습니다.');
        }
    },
    
    handleProfilePicChange: function(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        const reader = new FileReader();
        reader.onload = function(e) {
            const preview = document.getElementById('pro-profile-preview');
            const placeholder = document.getElementById('pro-profile-placeholder');
            const container = document.querySelector('.profile-pic-container');
            
            preview.src = e.target.result;
            preview.style.display = 'block';
            placeholder.style.display = 'none';
            container.style.border = '2px solid var(--primary-color)';
        };
        reader.readAsDataURL(file);
    },
    
    registerPro: async function() {
        const name = document.getElementById('pro-name') ? document.getElementById('pro-name').value.trim() : "";
        const contact = document.getElementById('pro-contact') ? document.getElementById('pro-contact').value.trim() : "";
        const pin = document.getElementById('pro-pin') ? document.getElementById('pro-pin').value.trim() : "";
        const cert_type = document.getElementById('pro-cert-type') ? document.getElementById('pro-cert-type').value : "KPGA 투어프로";
        const cert_number = document.getElementById('pro-cert-num') ? document.getElementById('pro-cert-num').value.trim() : "";
        const profilePreview = document.getElementById('pro-profile-preview');
        const profile_pic = profilePreview.style.display === 'block' ? profilePreview.src : '';
        
        const dayNodes = document.querySelectorAll('#pro-days .day-btn.active');
        const available_days = Array.from(dayNodes).map(n => n.innerText).join(', ');

        const regionNodes = document.querySelectorAll('#view-pro .grid-btn-simple.active');
        const regions = Array.from(regionNodes).map(n => n.innerText).join(', ');

        // 필수 정보 유효성 검사 (입력 폼 순서대로 순차 검증)
        if (!profile_pic) {
            alert("프로필 사진을 등록해 주세요.");
            return;
        }

        if (!name) {
            alert("이름을 입력해 주세요.");
            if (document.getElementById('pro-name')) document.getElementById('pro-name').focus();
            return;
        }

        if (!contact) {
            alert("전화번호를 입력해 주세요.");
            if (document.getElementById('pro-contact')) document.getElementById('pro-contact').focus();
            return;
        }

        if (!pin) {
            alert("간편 비밀번호(핀번호)를 입력해 주세요.");
            if (document.getElementById('pro-pin')) document.getElementById('pro-pin').focus();
            return;
        }

        if (pin.length < 4 || isNaN(pin)) {
            alert("간편 비밀번호는 4~6자리의 숫자로 입력해 주세요.");
            if (document.getElementById('pro-pin')) document.getElementById('pro-pin').focus();
            return;
        }

        if (!cert_number) {
            alert("회원번호를 입력해 주세요.");
            if (document.getElementById('pro-cert-num')) document.getElementById('pro-cert-num').focus();
            return;
        }

        if (!available_days) {
            alert("레슨이 가능한 요일을 최소 하나 이상 선택해 주세요.");
            return;
        }

        if (!regions) {
            alert("레슨이 가능한 활동 지역을 최소 하나 이상 선택해 주세요.");
            return;
        }

        const consentChecked = document.getElementById('pro-privacy-consent').checked;
        if (!consentChecked) {
            alert("개인정보 수집 및 서비스 이용약관 동의는 필수 항목입니다.");
            return;
        }

        try {
            const response = await fetch('/api/register/pro', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, contact, cert_type, cert_number, profile_pic, available_days, regions, pin })
            });
            const data = await response.json();
            
            // 회원 가입 완료 시 자동 로그인 처리 및 My Page 진입 유도
            localStorage.setItem('withpro_pro_cert', cert_number);
            
            alert("프로 회원 가입 신청이 성공적으로 접수되었습니다! ⛳\n\n제출해 주신 회원 자격 심사(KPGA/KLPGA 회원 인증) 완료 후 즉시 정식으로 레슨 매칭 활동이 가능합니다.\n\n승인 심사는 통상 1~2영업일이 소요되며, 완료되는 대로 등록된 연락처로 신속히 안내해 드리겠습니다. 올앱 파트너로 함께해 주셔서 진심으로 감사드립니다.");
            
            // Firebase FCM 알림 연동 및 토큰 저장 시도
            app.initFirebase(contact, 'pro');
            
            app.navigate('view-home');
        } catch(e) {
            alert('서버 오류가 발생했습니다.');
        }
    },

    updateDateDisplay: function(value) {
        const display = document.getElementById('display-date');
        if (!value) {
            display.innerText = "날짜를 선택해 주세요";
            display.classList.add('placeholder');
            return;
        }
        
        const date = new Date(value);
        const days = ['일', '월', '화', '수', '목', '금', '토'];
        const yyyy = date.getFullYear();
        const mm = String(date.getMonth() + 1).padStart(2, '0');
        const dd = String(date.getDate()).padStart(2, '0');
        const day = days[date.getDay()];
        
        display.innerText = `${yyyy}년 ${mm}월 ${dd}일 (${day})`;
        display.classList.remove('placeholder');
    },
    
    updateTimeDisplay: function(value) {
        const display = document.getElementById('display-time');
        if (!value) {
            display.innerText = "시간을 선택해 주세요";
            display.classList.add('placeholder');
            return;
        }
        
        const parts = value.split(':');
        let hour = parseInt(parts[0], 10);
        const min = parts[1];
        const ampm = hour >= 12 ? '오후' : '오전';
        if (hour > 12) hour -= 12;
        if (hour === 0) hour = 12;
        
        display.innerText = `${ampm} ${String(hour).padStart(2, '0')}:${min}`;
        display.classList.remove('placeholder');
    },

    loadBookingDirectly: async function(reqId) {
        const container = document.getElementById('my-bookings-container');
        app.navigate('view-my-bookings');
        
        container.innerHTML = `
            <div class="matching-loading-box">
                <div class="loading-spinner" style="border-top-color: var(--primary-color);"></div>
                <p class="overlay-subtitle">예약 정보를 불러오는 중입니다...</p>
            </div>
        `;
        
        try {
            const response = await fetch(`/api/lesson/status?id=${encodeURIComponent(reqId)}`);
            if (!response.ok) {
                throw new Error("조회 실패");
            }
            
            const data = await response.json();
            if (!data || data.error) {
                throw new Error(data.error || "예약을 찾을 수 없습니다.");
            }
            
            // 본인 확인 인증 세션 설정
            app.verifiedUserName = data.user_name || "고객";
            app.verifiedUserContact = data.user_contact || "";
            app.verifiedBookings = [data];
            
            localStorage.setItem('withpro_last_request_id', data.id);
            
            // 예약 내역 단건 렌더링
            const status = data.status || '매칭 대기중';
            let cardHtml = '';
            
            if (status === '매칭 대기중') {
                cardHtml = `
                    <div class="my-booking-card" style="width: 100%; text-align: left; box-sizing: border-box; margin: 0;">
                        <div class="booking-badge-row">
                            <span class="booking-title">${app.escapeHtml(data.golf_course)}</span>
                            <span class="booking-status-tag wait">매칭 대기중</span>
                        </div>
                        <ul class="booking-details-list">
                            <li class="booking-detail-item">
                                <span class="booking-detail-label">라운딩 일시</span>
                                <span class="booking-detail-value">${app.escapeHtml(data.lesson_date)} (${app.escapeHtml(data.lesson_time)})</span>
                            </li>
                            <li class="booking-detail-item">
                                <span class="booking-detail-label">신청자명</span>
                                <span class="booking-detail-value">${app.escapeHtml(data.user_name || '이름 없음')}</span>
                            </li>
                        </ul>
                        <div style="font-size: 13px; color: var(--text-sub); line-height: 1.5; font-weight: 500; text-align: center; background-color: #f3f4f6; padding: 12px; border-radius: 8px;">
                            🔔 매칭이 완료되면 결제 요청 알림이 발송됩니다.
                        </div>
                    </div>
                `;
            } else if (status === '프로 수락 대기중') {
                cardHtml = `
                    <div class="my-booking-card" style="width: 100%; text-align: left; box-sizing: border-box; border-color: #fde68a; background: linear-gradient(180deg, #fffdf8 0%, #ffffff 100%); margin: 0;">
                        <div class="booking-badge-row">
                            <span class="booking-title">${app.escapeHtml(data.golf_course)}</span>
                            <span class="booking-status-tag wait" style="background-color: #fffbeb; color: #b45309; border-color: #fde68a;">수락 대기중</span>
                        </div>
                        <ul class="booking-details-list">
                            <li class="booking-detail-item">
                                <span class="booking-detail-label">라운딩 일시</span>
                                <span class="booking-detail-value">${app.escapeHtml(data.lesson_date)} (${app.escapeHtml(data.lesson_time)})</span>
                            </li>
                            <li class="booking-detail-item">
                                <span class="booking-detail-label">배정 프로</span>
                                <span class="booking-detail-value" style="color: #b45309; font-weight: 700;">KPGA/KLPGA 회원 프로 (수락 대기)</span>
                            </li>
                        </ul>
                        <div style="font-size: 13.5px; color: #b45309; line-height: 1.5; font-weight: 600; text-align: center; background-color: #fffbeb; padding: 12px; border-radius: 8px; border: 1px solid #fde68a;">
                            🔔 프로님이 수락하는 즉시 결제 링크가 자동으로 활성화됩니다.
                        </div>
                    </div>
                `;
            } else if (status === '매칭완료') {
                cardHtml = `
                    <div class="my-booking-card" style="width: 100%; text-align: left; box-sizing: border-box; margin: 0;">
                        <div class="booking-badge-row">
                            <span class="booking-title">${app.escapeHtml(data.golf_course)}</span>
                            <span class="booking-status-tag paid">매칭 완료</span>
                        </div>
                        <ul class="booking-details-list">
                            <li class="booking-detail-item">
                                <span class="booking-detail-label">라운딩 일정</span>
                                <span class="booking-detail-value">${app.escapeHtml(data.lesson_date)} (${app.escapeHtml(data.lesson_time)})</span>
                            </li>
                            <li class="booking-detail-item">
                                <span class="booking-detail-label">정산 방식</span>
                                <span class="booking-detail-value" style="color: var(--primary-color); font-weight: 800;">현장 직거래 (55만 원)</span>
                            </li>
                        </ul>
                        <div style="font-size: 13px; color: #065f46; background-color: #ECFDF5; padding: 10px; border-radius: 8px; text-align: center; font-weight: 600;">
                            프로 수락 시 예약이 즉시 최종 확정됩니다.
                        </div>
                    </div>
                `;
            } else if (status === '결제완료') {
                const isDirect = data.pay_method === '현장직거래';
                cardHtml = `
                    <div class="my-booking-card" style="width: 100%; text-align: left; box-sizing: border-box; border-color: #a7f3d0; background: linear-gradient(180deg, #FCFDFD 0%, #FFFFFF 100%); margin: 0;">
                        <div class="booking-badge-row">
                            <span class="booking-title" style="color: #065f46;">${app.escapeHtml(data.golf_course)}</span>
                            <span class="booking-status-tag paid">예약 완료</span>
                        </div>
                        <p style="font-size: 13.5px; color: #065f46; line-height: 1.5; margin-bottom: 12px; font-weight: 600; background-color: #ECFDF5; padding: 10px; border-radius: 8px; text-align: center;">
                            ${isDirect ? '🎉 프로님이 예약을 수락하여 매칭이 최종 확정되었습니다!' : '🎉 예약금 결제가 정상 승인되어 최종 확정되었습니다!'}
                        </p>
                        <ul class="booking-details-list">
                            <li class="booking-detail-item">
                                <span class="booking-detail-label">라운딩 일시</span>
                                <span class="booking-detail-value">${app.escapeHtml(data.lesson_date)} (${app.escapeHtml(data.lesson_time)})</span>
                            </li>
                            <li class="booking-detail-item">
                                <span class="booking-detail-label">${isDirect ? '정산 방식' : '결제 수단'}</span>
                                <span class="booking-detail-value">${isDirect ? '현장 직거래 (라운딩 종료 후 프로님께 레슨비 550,000원 직접 정산)' : app.escapeHtml(data.pay_method || '간편결제')}</span>
                            </li>
                        </ul>
                        ${app.getReviewSectionHtml(data)}
                    </div>
                `;
            }
            
            let htmlContent = `
                <div style="display: flex; flex-direction: column; gap: 16px; width: 100%; text-align: left;">
                    ${cardHtml}
                    <button class="btn btn-secondary full-width" style="margin-top: 10px; padding: 12px; font-weight: 700; border-radius: 8px; border: 1.5px solid var(--border-color); background: white;" onclick="localStorage.removeItem('withpro_last_request_id'); app.checkMyBookings();">
                        다른 번호로 조회하기
                    </button>
                </div>
            `;
            container.innerHTML = htmlContent;

            // 추가 개선: 만약 상태가 '매칭완료'이고 결제 버튼이 존재하는 상황이라면 바로 결제창을 띄워주는 UX 제공
            if (status === '매칭완료') {
                app.openPaymentView(data.id);
            }
            
        } catch (e) {
            container.innerHTML = `
                <div class="matching-loading-box">
                    <div style="font-size: 48px; margin-bottom: 16px;">⚠️</div>
                    <h3 class="overlay-title">조회 중 오류가 발생했습니다</h3>
                    <p class="overlay-subtitle" style="margin-bottom: 20px;">서버와의 통신이 원활하지 않거나 예약 정보를 찾을 수 없습니다.</p>
                    <button class="btn btn-secondary" onclick="app.checkMyBookings()">일반 조회로 이동</button>
                </div>
            `;
        }
    },

    checkMyBookings: async function() {
        // [내 예약 확인] 클릭 시 무조건 기존 수동 조회/인증 세션을 초기화하여 캐시 자동 통과를 원천 차단
        app.verifiedUserName = "";
        app.verifiedUserContact = "";
        app.verifiedBookings = [];

        const container = document.getElementById('my-bookings-container');
        app.navigate('view-my-bookings');
        
        container.innerHTML = `
            <div class="matching-loading-box" style="padding: 10px 0;">
                <div style="font-size: 40px; margin-bottom: 12px;">🔍</div>
                <h3 class="overlay-title" style="margin-bottom: 6px; font-size: 17px; font-weight: 800;">예약 신청 내역 확인</h3>
                <p class="overlay-subtitle" style="margin-bottom: 20px; font-size: 13px;">예약 시 입력하신 이름과 연락처를 입력해 주세요.</p>
                
                <div class="lookup-form" style="width: 100%; text-align: left; background: white; border: 1px solid var(--border-color); border-radius: var(--radius-lg); padding: 18px; box-sizing: border-box; margin-bottom: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.03);">
                    <div class="form-group" style="margin-bottom: 12px;">
                        <label style="font-size: 13px; font-weight: 700; color: var(--text-main); display: block; margin-bottom: 6px;">예약자 이름</label>
                        <input type="text" id="lookup-user-name" placeholder="신청자 실명을 입력해 주세요" style="width: 100%; padding: 12px 14px; border-radius: 8px; border: 1px solid var(--border-color); font-size: 14px; box-sizing: border-box; font-weight: 500;">
                    </div>
                    <div class="form-group" style="margin-bottom: 16px;">
                        <label style="font-size: 13px; font-weight: 700; color: var(--text-main); display: block; margin-bottom: 6px;">예약자 연락처</label>
                        <input type="text" id="lookup-user-contact" placeholder="연락처를 입력해 주세요 (예: 010-1234-5678)" style="width: 100%; padding: 12px 14px; border-radius: 8px; border: 1px solid var(--border-color); font-size: 14px; box-sizing: border-box; font-weight: 500;">
                    </div>
                    <button class="btn btn-primary" onclick="app.lookupMyBookings()" style="width: 100%; padding: 12px; font-size: 15px; font-weight: 700; border-radius: 8px; background-color: var(--primary-color); border: none; color: white; cursor: pointer; box-shadow: 0 4px 10px rgba(11, 54, 33, 0.1);">
                        실시간 예약내역 조회
                    </button>
                </div>
                
                <div style="font-size: 13px; color: var(--text-sub); font-weight: 500;">
                    아직 예약 내역이 없으신가요? 
                    <a href="#" onclick="event.preventDefault(); app.navigate('view-regular');" style="color: var(--primary-color); font-weight: 700; text-decoration: underline; margin-left: 4px;">신규 매칭 신청하기 →</a>
                </div>
            </div>
        `;
    },

    lookupMyBookings: async function() {
        const nameInput = document.getElementById('lookup-user-name');
        const contactInput = document.getElementById('lookup-user-contact');
        
        const name = nameInput ? nameInput.value.trim() : "";
        const contact = contactInput ? contactInput.value.trim() : "";
        
        if (!name) {
            alert("예약자 이름을 입력해 주세요.");
            if (nameInput) nameInput.focus();
            return;
        }
        
        if (!contact) {
            alert("연락처를 입력해 주세요.");
            if (contactInput) contactInput.focus();
            return;
        }
        
        const container = document.getElementById('my-bookings-container');
        container.innerHTML = `
            <div class="matching-loading-box">
                <div class="loading-spinner" style="border-top-color: var(--primary-color);"></div>
                <p class="overlay-subtitle">서버에서 예약 정보를 조회하는 중입니다...</p>
            </div>
        `;
        
        try {
            const response = await fetch('/api/lesson/lookup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, contact })
            });
            
            if (!response.ok) {
                throw new Error("조회 실패");
            }
            
            const list = await response.json();
            
            if (list.length === 0) {
                container.innerHTML = `
                    <div class="matching-loading-box">
                        <div style="font-size: 48px; margin-bottom: 16px;">⚠️</div>
                        <h3 class="overlay-title" style="margin-bottom: 8px;">조회된 예약 내역이 없습니다</h3>
                        <p class="overlay-subtitle" style="margin-bottom: 24px;">입력하신 정보가 올바른지 확인하거나 신규 매칭을 신청해 주세요.</p>
                        <div class="grid-2 gap-2" style="display: flex; gap: 10px; width: 100%;">
                            <button class="btn btn-secondary" style="flex: 1; padding: 12px; border-radius: 8px; font-weight: 700; border: 1.5px solid var(--border-color); background: white;" onclick="localStorage.removeItem('withpro_last_request_id'); app.checkMyBookings();">다시 입력</button>
                            <button class="btn btn-primary" style="flex: 1; padding: 12px; border-radius: 8px; font-weight: 700;" onclick="app.navigate('view-regular')">매칭 신청하기</button>
                        </div>
                    </div>
                `;
                return;
            }
            
            // 보안 강화: 수동 본인 확인(조회)에 성공한 이름, 연락처 및 예약 목록을 메모리 세션에 기록
            app.verifiedUserName = name;
            app.verifiedUserContact = contact;
            app.verifiedBookings = list;

            // 첫 번째로 조회된 예약 ID를 최근 예약 ID로 저장하여 UX 개선 (캐싱용으로 유지하되, 무조건 대조 필수)
            localStorage.setItem('withpro_last_request_id', list[0].id);
            
            // 예약 내역 렌더링
            let htmlContent = `
                <div style="display: flex; flex-direction: column; gap: 16px; width: 100%; text-align: left;">
                    <div class="lookup-success-badge" style="display: flex; align-items: center; justify-content: center; gap: 6px; padding: 10px; border-radius: 8px; background-color: var(--active-bg); color: var(--primary-color); font-weight: 700; font-size: 13.5px; text-align: center;">
                        ✨ 총 ${list.length}건의 실시간 필드레슨 예약을 확인했습니다!
                    </div>
            `;
            
            list.forEach(data => {
                const status = data.status || '매칭 대기중';
                let cardHtml = '';
                
                if (status === '매칭 대기중') {
                    cardHtml = `
                        <div class="my-booking-card" style="width: 100%; text-align: left; box-sizing: border-box; margin: 0;">
                            <div class="booking-badge-row">
                                <span class="booking-title">${app.escapeHtml(data.golf_course)}</span>
                                <span class="booking-status-tag wait">매칭 대기중</span>
                            </div>
                            <ul class="booking-details-list">
                                <li class="booking-detail-item">
                                    <span class="booking-detail-label">라운딩 일시</span>
                                    <span class="booking-detail-value">${app.escapeHtml(data.lesson_date)} (${app.escapeHtml(data.lesson_time)})</span>
                                </li>
                                <li class="booking-detail-item">
                                    <span class="booking-detail-label">신청자명</span>
                                    <span class="booking-detail-value">${app.escapeHtml(data.user_name || '이름 없음')}</span>
                                </li>
                            </ul>
                            <div style="font-size: 13px; color: var(--text-sub); line-height: 1.5; font-weight: 500; text-align: center; background-color: #f3f4f6; padding: 12px; border-radius: 8px;">
                                🔔 매칭이 완료되면 결제 요청 알림이 발송됩니다.
                            </div>
                        </div>
                    `;
                } else if (status === '프로 수락 대기중') {
                    cardHtml = `
                        <div class="my-booking-card" style="width: 100%; text-align: left; box-sizing: border-box; border-color: #fde68a; background: linear-gradient(180deg, #fffdf8 0%, #ffffff 100%); margin: 0;">
                            <div class="booking-badge-row">
                                <span class="booking-title">${app.escapeHtml(data.golf_course)}</span>
                                <span class="booking-status-tag wait" style="background-color: #fffbeb; color: #b45309; border-color: #fde68a;">수락 대기중</span>
                            </div>
                            <ul class="booking-details-list">
                                <li class="booking-detail-item">
                                    <span class="booking-detail-label">라운딩 일시</span>
                                    <span class="booking-detail-value">${app.escapeHtml(data.lesson_date)} (${app.escapeHtml(data.lesson_time)})</span>
                                </li>
                                <li class="booking-detail-item">
                                    <span class="booking-detail-label">배정 프로</span>
                                    <span class="booking-detail-value" style="color: #b45309; font-weight: 700;">KPGA/KLPGA 회원 프로 (수락 대기)</span>
                                </li>
                            </ul>
                            <div style="font-size: 13.5px; color: #b45309; line-height: 1.5; font-weight: 600; text-align: center; background-color: #fffbeb; padding: 12px; border-radius: 8px; border: 1px solid #fde68a;">
                                🔔 프로님이 수락하는 즉시 결제 링크가 자동으로 활성화됩니다.
                            </div>
                        </div>
                    `;
                } else if (status === '매칭완료') {
                    cardHtml = `
                        <div class="my-booking-card" style="width: 100%; text-align: left; box-sizing: border-box; margin: 0;">
                            <div class="booking-badge-row">
                                <span class="booking-title">${app.escapeHtml(data.golf_course)}</span>
                                <span class="booking-status-tag paid">매칭 완료</span>
                            </div>
                            <ul class="booking-details-list">
                                <li class="booking-detail-item">
                                    <span class="booking-detail-label">라운딩 일정</span>
                                    <span class="booking-detail-value">${app.escapeHtml(data.lesson_date)} (${app.escapeHtml(data.lesson_time)})</span>
                                </li>
                                <li class="booking-detail-item">
                                    <span class="booking-detail-label">정산 방식</span>
                                    <span class="booking-detail-value" style="color: var(--primary-color); font-weight: 800;">현장 직거래 (55만 원)</span>
                                </li>
                            </ul>
                            <div style="font-size: 13px; color: #065f46; background-color: #ECFDF5; padding: 10px; border-radius: 8px; text-align: center; font-weight: 600;">
                                프로 수락 시 예약이 즉시 최종 확정됩니다.
                            </div>
                        </div>
                    `;
                } else if (status === '결제완료') {
                    const isDirect = data.pay_method === '현장직거래';
                    cardHtml = `
                        <div class="my-booking-card" style="width: 100%; text-align: left; box-sizing: border-box; border-color: #a7f3d0; background: linear-gradient(180deg, #FCFDFD 0%, #FFFFFF 100%); margin: 0;">
                            <div class="booking-badge-row">
                                <span class="booking-title" style="color: #065f46;">${app.escapeHtml(data.golf_course)}</span>
                                <span class="booking-status-tag paid">예약 완료</span>
                            </div>
                            <p style="font-size: 13.5px; color: #065f46; line-height: 1.5; margin-bottom: 12px; font-weight: 600; background-color: #ECFDF5; padding: 10px; border-radius: 8px; text-align: center;">
                                ${isDirect ? '🎉 프로님이 예약을 수락하여 매칭이 최종 확정되었습니다!' : '🎉 예약금 결제가 정상 승인되어 최종 확정되었습니다!'}
                            </p>
                            <ul class="booking-details-list">
                                <li class="booking-detail-item">
                                    <span class="booking-detail-label">라운딩 일시</span>
                                    <span class="booking-detail-value">${app.escapeHtml(data.lesson_date)} (${app.escapeHtml(data.lesson_time)})</span>
                                </li>
                                <li class="booking-detail-item">
                                    <span class="booking-detail-label">${isDirect ? '정산 방식' : '결제 수단'}</span>
                                    <span class="booking-detail-value">${isDirect ? '현장 직거래 (라운딩 종료 후 프로님께 레슨비 550,000원 직접 정산)' : app.escapeHtml(data.pay_method || '간편결제')}</span>
                                </li>
                            </ul>
                            ${app.getReviewSectionHtml(data)}
                        </div>
                    `;
                }
                
                htmlContent += cardHtml;
            });
            
            htmlContent += `
                    <button class="btn btn-secondary full-width" style="margin-top: 10px; padding: 12px; font-weight: 700; border-radius: 8px; border: 1.5px solid var(--border-color); background: white;" onclick="localStorage.removeItem('withpro_last_request_id'); app.checkMyBookings();">
                        다른 번호로 조회하기
                    </button>
                </div>
            `;
            container.innerHTML = htmlContent;
            
        } catch (e) {
            container.innerHTML = `
                <div class="matching-loading-box">
                    <div style="font-size: 48px; margin-bottom: 16px;">⚠️</div>
                    <h3 class="overlay-title">조회 중 오류가 발생했습니다</h3>
                    <p class="overlay-subtitle" style="margin-bottom: 20px;">서버와의 통신이 원활하지 않습니다.</p>
                    <button class="btn btn-secondary" onclick="app.checkMyBookings()">다시 시도</button>
                </div>
            `;
        }
    },

    openPaymentView: function(bookingId) {
        if (!bookingId) {
            alert("예약 식별 정보가 올바르지 않습니다.");
            app.checkMyBookings();
            return;
        }
        
        // 보안 검증: 현재 수동 인증을 거친 예약 목록 중에 이 ID가 실제로 존재하는지 대조
        const booking = app.verifiedBookings && app.verifiedBookings.find(b => b.id == bookingId);
        if (!booking) {
            alert("보안을 위해 [내 예약 확인] 메뉴에서 예약자 이름과 연락처를 먼저 정확히 입력하고 예약 내역을 조회해 주세요.");
            app.checkMyBookings();
            return;
        }
        
        // 검증 통과 시 해당 예약 ID를 기기에 임시 보관 (결제 요청용)
        localStorage.setItem('withpro_last_request_id', bookingId);
        
        // 쿠폰 상태 초기화
        app.appliedCouponCode = null;
        app.couponDiscount = 0;
        
        const couponInput = document.getElementById('coupon-code-input');
        if (couponInput) couponInput.value = '';
        const couponMsg = document.getElementById('coupon-message');
        if (couponMsg) {
            couponMsg.style.display = 'none';
            couponMsg.innerText = '';
        }
        
        const priceDiv = document.querySelector('.payment-summary-card .payment-price');
        if (priceDiv) priceDiv.innerText = '50,000원';
        
        const payBtn = document.querySelector('.bottom-action button');
        if (payBtn) payBtn.innerText = '50,000원 결제하기';
        
        app.navigate('view-payment');
        app.switchPayMethod('card');
    },

    applyCoupon: async function() {
        const input = document.getElementById('coupon-code-input');
        const msgDiv = document.getElementById('coupon-message');
        if (!input || !msgDiv) return;
        
        const code = input.value.trim().toUpperCase();
        if (!code) {
            msgDiv.style.color = '#ef4444';
            msgDiv.innerText = '⚠️ 쿠폰 코드를 입력해 주세요.';
            msgDiv.style.display = 'block';
            return;
        }
        
        const reqId = localStorage.getItem('withpro_last_request_id');
        const booking = app.verifiedBookings && app.verifiedBookings.find(b => b.id == reqId);
        if (!booking) {
            msgDiv.style.color = '#ef4444';
            msgDiv.innerText = '⚠️ 예약 조회 정보가 유효하지 않습니다.';
            msgDiv.style.display = 'block';
            return;
        }
        
        msgDiv.style.color = '#4b5563';
        msgDiv.innerText = '⏳ 쿠폰 검증 중...';
        msgDiv.style.display = 'block';
        
        try {
            const response = await fetch('/api/coupon/validate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    code: code,
                    contact: booking.user_contact,
                    req_id: reqId
                })
            });
            
            const resData = await response.json();
            if (!response.ok) {
                msgDiv.style.color = '#ef4444';
                msgDiv.innerText = `❌ ${resData.error || '유효하지 않은 쿠폰입니다.'}`;
                return;
            }
            
            app.appliedCouponCode = code;
            app.couponDiscount = resData.discount_amount || 0;
            
            const finalPrice = Math.max(0, 50000 - app.couponDiscount);
            
            msgDiv.style.color = '#059669';
            msgDiv.innerText = `✓ ${app.couponDiscount.toLocaleString()}원 할인 쿠폰이 적용되었습니다.`;
            
            const priceDiv = document.querySelector('.payment-summary-card .payment-price');
            if (priceDiv) priceDiv.innerText = `${finalPrice.toLocaleString()}원`;
            
            const payBtn = document.querySelector('.bottom-action button');
            if (payBtn) payBtn.innerText = `${finalPrice.toLocaleString()}원 결제하기`;
            
        } catch (e) {
            msgDiv.style.color = '#ef4444';
            msgDiv.innerText = '❌ 서버 통신 중 오류가 발생했습니다.';
        }
    },

    switchPayMethod: function(method) {
        app.selectedPayMethod = method; // 선택된 수단 저장
        
        // 모든 탭 해제
        document.querySelectorAll('.pay-tab').forEach(btn => btn.classList.remove('active'));
        document.querySelectorAll('.pay-detail-panel').forEach(panel => panel.classList.remove('active'));
        
        if (method === 'card') {
            document.querySelector('.payment-methods-tabs button:nth-child(1)').classList.add('active');
            document.getElementById('pay-detail-card').classList.add('active');
        } else if (method === 'transfer') {
            document.querySelector('.payment-methods-tabs button:nth-child(2)').classList.add('active');
            document.getElementById('pay-detail-transfer').classList.add('active');
        }
    },

    executePayment: function() {
        const method = app.selectedPayMethod || 'card';
        let payMethodText = '신용카드';
        let pgProvider = app.DEFAULT_PG_PROVIDER; // 기본 설정된 PG사 사용
        let payMethodCode = 'card';      // 기본 수단 (신용카드)
        
        if (method === 'card') {
            const cardSelect = document.getElementById('pay-card-company');
            const cardName = cardSelect ? cardSelect.value : '신용카드';
            payMethodText = `${cardName} (신용카드)`;
            pgProvider = app.DEFAULT_PG_PROVIDER;
            payMethodCode = 'card';
        } else if (method === 'transfer') {
            const bankSelect = document.getElementById('pay-bank-name');
            const bankName = bankSelect ? bankSelect.value : '계좌이체';
            payMethodText = `${bankName} (실시간 계좌이체)`;
            pgProvider = app.DEFAULT_PG_PROVIDER;
            payMethodCode = 'trans';
        }
        
        // 포트원 라이브러리 정상 주입 확인
        if (typeof IMP === 'undefined') {
            alert("결제 모듈이 아직 로드되지 않았습니다. 새로고침 후 다시 시도해 주세요.");
            return;
        }
        
        // 포트원 가상 가맹점 번호로 전역 초기화
        IMP.init("imp30206856");
        
        const reqId = localStorage.getItem('withpro_last_request_id');
        // 결제 실행 보안 검증: 현재 수동 인증을 통과하여 세션에 있는 예약 건인지 다시 한 번 대조
        const booking = app.verifiedBookings && app.verifiedBookings.find(b => b.id == reqId);
        if (!booking) {
            alert("보안을 위해 [내 예약 확인] 메뉴에서 예약자 이름과 연락처를 다시 한 번 정확히 입력해 주세요.");
            app.checkMyBookings();
            return;
        }

        const merchantUid = `withpro_${reqId}_${Date.now()}`;
        
        // 할인 적용된 결제 금액 계산
        const amount = Math.max(0, 50000 - (app.couponDiscount || 0));

        // 포트원 결제창 호출 및 처리 (실제 본인인증 완료된 사용자의 이름과 연락처 주입)
        IMP.request_pay({
            pg: pgProvider,
            pay_method: payMethodCode,
            merchant_uid: merchantUid,
            name: "올앱 필드레슨 서비스 이용료",
            amount: amount,
            buyer_name: booking.user_name,
            buyer_tel: booking.user_contact,
            m_redirect_url: window.location.origin + "/index.html?view=my-bookings" // 모바일 결제 리다이렉트 대응
        }, async function(rsp) {
            if (rsp.success) {
                // 로딩 스피너 활성화
                const loadingOverlay = document.getElementById('payment-loading-overlay');
                if (loadingOverlay) loadingOverlay.classList.add('active');
                
                try {
                    const response = await fetch('/api/lesson/payment-complete', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ 
                            id: reqId, 
                            pay_method: payMethodText,
                            imp_uid: rsp.imp_uid,
                            merchant_uid: rsp.merchant_uid,
                            coupon_code: app.appliedCouponCode,
                            discount_amount: app.couponDiscount || 0,
                            paid_amount: amount
                        })
                    });
                    
                    if (loadingOverlay) loadingOverlay.classList.remove('active');
                    
                    if (!response.ok) {
                        throw new Error("결제 처리 API 통신 실패");
                    }
                    
                    // 성공 팝업 결제 수단 및 금액 명시
                    const successSubtitle = document.querySelector('#payment-success-overlay .success-subtitle');
                    if (successSubtitle) {
                        successSubtitle.innerHTML = `${amount.toLocaleString()}원 이용료 결제가 <strong>${app.escapeHtml(payMethodText)}</strong>으로 성공적으로 처리되었습니다.<br>필드레슨 매칭이 최종 확정되었습니다.`;
                    }
                    
                    document.getElementById('payment-success-overlay').classList.add('active');
                    
                    // Confetti 애니메이션 기동
                    app.launchConfetti();
                    
                } catch(e) {
                    if (loadingOverlay) loadingOverlay.classList.remove('active');
                    alert("결제 승인은 완료되었으나 상태 변경 처리에 실패했습니다. 고객센터로 문의해 주세요.");
                }
            } else {
                alert("결제가 승인되지 않았거나 취소되었습니다: " + rsp.error_msg);
            }
        });
    },

    closeSuccessOverlay: function() {
        document.getElementById('payment-success-overlay').classList.remove('active');
        // 내 예약 확인 현황 리프레시 및 이동
        app.checkMyBookings();
    },

    launchConfetti: function() {
        const container = document.getElementById('confetti-container');
        container.innerHTML = '';
        const colors = ['#FFC700', '#FF0055', '#00FF66', '#0064FF', '#FF00FF', '#00FFFF'];
        
        for (let i = 0; i < 50; i++) {
            const particle = document.createElement('div');
            particle.classList.add('confetti-particle');
            
            // 랜덤 속성 설정
            particle.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
            particle.style.left = Math.random() * 100 + '%';
            particle.style.top = -10 - (Math.random() * 20) + 'px';
            particle.style.transform = `rotate(${Math.random() * 360}deg)`;
            
            // 크기 랜덤화
            const size = 6 + Math.random() * 8;
            particle.style.width = size + 'px';
            particle.style.height = size + 'px';
            
            // 애니메이션 딜레이 및 재생 속도
            particle.style.animationDelay = Math.random() * 0.5 + 's';
            particle.style.animationDuration = 1.5 + Math.random() * 1.5 + 's';
            
            container.appendChild(particle);
        }
    },

    escapeHtml: function(str) {
        if (!str) return '';
        return str
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    },

    loginPro: async function() {
        const phoneInput = document.getElementById('login-pro-phone');
        const pinInput = document.getElementById('login-pro-pin');
        
        const phone = phoneInput ? phoneInput.value.trim() : "";
        const pin = pinInput ? pinInput.value.trim() : "";
        
        if (!phone) {
            alert("휴대폰 번호를 입력해 주세요.");
            if (phoneInput) phoneInput.focus();
            return;
        }
        
        if (!pin) {
            alert("간편 비밀번호(핀번호)를 입력해 주세요.");
            if (pinInput) pinInput.focus();
            return;
        }
        
        const toast = document.getElementById('pro-toast');
        if (toast) {
            toast.innerText = "🔒 보안 로그인 중...";
            toast.classList.add('show');
        }
        
        try {
            const response = await fetch('/api/pro/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ phone, pin })
            });
            
            if (toast) toast.classList.remove('show');
            
            const data = await response.json();
            
            if (!response.ok) {
                alert(data.error || "로그인에 실패했습니다.");
                return;
            }
            
            const cert = data.cert_number;
            if (cert) {
                localStorage.setItem('withpro_pro_cert', cert);
                if (toast) {
                    toast.innerText = "✨ 로그인 성공: 마이페이지 이동!";
                    toast.classList.add('show');
                    setTimeout(() => {
                        toast.classList.remove('show');
                        app.openProMyPage(cert);
                    }, 800);
                } else {
                    app.openProMyPage(cert);
                }
            }
        } catch(e) {
            if (toast) toast.classList.remove('show');
            alert("로그인 서버와 통신 중 오류가 발생했습니다. 다시 시도해 주세요.");
        }
    },

    openProMyPage: async function(cert) {
        // 1. 네비게이션 강제 수행 (view-pro-mypage 직접 활성화)
        document.querySelectorAll('.view').forEach(view => {
            view.classList.remove('active');
        });
        const targetView = document.getElementById('view-pro-mypage');
        if (targetView) {
            targetView.classList.add('active');
            const content = targetView.querySelector('.content');
            if (content) content.scrollTop = 0;
        }

        const statusContainer = document.getElementById('pro-status-container');
        const matchesContainer = document.getElementById('pro-matches-container');

        statusContainer.innerHTML = `
            <div class="matching-loading-box" style="padding: 30px 0;">
                <div class="loading-spinner" style="border-top-color: var(--primary-color); width: 36px; height: 36px;"></div>
                <p class="overlay-subtitle" style="font-size: 13px;">프로 프로필을 불러오는 중...</p>
            </div>
        `;
        matchesContainer.innerHTML = '';

        try {
            const response = await fetch(`/api/pro/profile?cert=${encodeURIComponent(cert)}`);
            if (response.status === 404) {
                localStorage.removeItem('withpro_pro_cert');
                alert("등록된 프로 정보를 찾을 수 없습니다. 다시 가입 신청해 주세요.");
                document.querySelectorAll('.view').forEach(view => {
                    view.classList.remove('active');
                });
                document.getElementById('view-pro').classList.add('active');
                return;
            }

            if (!response.ok) {
                throw new Error("서버 연동 오류");
            }

            const data = await response.json();
            const profile = data.profile;
            const matches = data.matches;

            // Firebase FCM 알림 연동 및 토큰 저장 시도
            if (profile && profile.contact) {
                app.initFirebase(profile.contact, 'pro');
            }

            // 1. 프로필 상태 카드 바인딩
            const hasProfilePic = !!profile.profile_pic;
            const completedRounds = matches.filter(m => m.status === '결제완료').length;
            const isExcellent = completedRounds >= 2;
            const excellentBadgeHtml = isExcellent ? `
                <span class="pro-excellent-badge" style="font-size: 11px; background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%); color: #fff; padding: 3px 8px; border-radius: 8px; font-weight: 800; display: inline-flex; align-items: center; gap: 3px; box-shadow: 0 2px 6px rgba(255, 215, 0, 0.3); letter-spacing: -0.2px; margin-left: 4px; vertical-align: middle;">🏆 우수</span>
            ` : '';

            if (profile.status === '승인완료') {
                statusContainer.innerHTML = `
                    <div class="status-card active" style="display: flex; align-items: center; gap: 20px; background: linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%); border-color: #A7F3D0; padding: 20px; border-radius: var(--radius-lg);">
                        ${hasProfilePic ? `
                        <div class="profile-pic-display" style="width: 76px; height: 76px; border-radius: 50%; border: 3px solid #ffffff; box-shadow: 0 4px 10px rgba(0,0,0,0.08); overflow: hidden; flex-shrink: 0;">
                            <img src="${profile.profile_pic}" style="width: 100%; height: 100%; object-fit: cover;">
                        </div>` : ''}
                        <div class="profile-info-display" style="flex: 1;">
                            <div style="font-size: 18px; font-weight: 800; color: #065f46; display: flex; align-items: center; gap: 4px; margin-bottom: 4px;">
                                <span>${app.escapeHtml(profile.name)} 프로</span>
                                ${excellentBadgeHtml}
                            </div>
                            <div style="font-size: 13px; color: #047857; font-weight: 600; margin-bottom: 6px;">
                                자격번호: ${app.escapeHtml(profile.cert_number)}
                            </div>
                            <div style="font-size: 12.5px; color: #065f46; font-weight: 500; line-height: 1.4;">
                                🎉 정식 자격 심사가 완료되어 활성화 상태입니다.
                            </div>
                        </div>
                    </div>
                `;
                document.getElementById('pro-settings-section').style.display = 'block';

                // 2. 활동 가능 요일 버튼 체크 상태 바인딩
                const activeDays = profile.available_days ? profile.available_days.split(',').map(s => s.trim()) : [];
                document.querySelectorAll('#pro-mypage-days .day-btn').forEach(btn => {
                    if (activeDays.includes(btn.innerText)) {
                        btn.classList.add('active');
                    } else {
                        btn.classList.remove('active');
                    }
                });

                // 3. 활동 가능 지역 버튼 체크 상태 바인딩
                const activeRegions = profile.regions ? profile.regions.split(',').map(s => s.trim()) : [];
                document.querySelectorAll('#pro-mypage-regions .grid-btn-simple').forEach(btn => {
                    if (activeRegions.includes(btn.innerText)) {
                        btn.classList.add('active');
                    } else {
                        btn.classList.remove('active');
                    }
                });

            } else if (profile.status === '정지') {
                statusContainer.innerHTML = `
                    <div class="status-card error" style="display: flex; align-items: center; gap: 20px; background: linear-gradient(135deg, #FEF2F2 0%, #FEE2E2 100%); border-color: #FCA5A5; padding: 20px; border-radius: var(--radius-lg); border-style: solid; border-width: 1px;">
                        ${hasProfilePic ? `
                        <div class="profile-pic-display" style="width: 76px; height: 76px; border-radius: 50%; border: 3px solid #ffffff; box-shadow: 0 4px 10px rgba(0,0,0,0.08); overflow: hidden; flex-shrink: 0;">
                            <img src="${profile.profile_pic}" style="width: 100%; height: 100%; object-fit: cover;">
                        </div>` : ''}
                        <div class="profile-info-display" style="flex: 1;">
                            <div style="font-size: 18px; font-weight: 800; color: #991b1b; display: flex; align-items: center; gap: 4px; margin-bottom: 4px;">
                                <span>${app.escapeHtml(profile.name)} 프로 (활동 정지 🚨)</span>
                                ${excellentBadgeHtml}
                            </div>
                            <div style="font-size: 13px; color: #b91c1c; font-weight: 600; margin-bottom: 6px;">
                                자격번호: ${app.escapeHtml(profile.cert_number)}
                            </div>
                            <div style="font-size: 12.5px; color: #991b1b; font-weight: 500; line-height: 1.4;">
                                🚨 라운딩 다음 날 수수료 미납으로 인해 파트너 활동이 정지되었습니다. 미납된 수수료 결제를 완료하시면 즉시 정지가 해제됩니다.
                            </div>
                        </div>
                    </div>
                `;
                document.getElementById('pro-settings-section').style.display = 'block';

                // 2. 활동 가능 요일 버튼 체크 상태 바인딩
                const activeDays = profile.available_days ? profile.available_days.split(',').map(s => s.trim()) : [];
                document.querySelectorAll('#pro-mypage-days .day-btn').forEach(btn => {
                    if (activeDays.includes(btn.innerText)) {
                        btn.classList.add('active');
                    } else {
                        btn.classList.remove('active');
                    }
                });

                // 3. 활동 가능 지역 버튼 체크 상태 바인딩
                const activeRegions = profile.regions ? profile.regions.split(',').map(s => s.trim()) : [];
                document.querySelectorAll('#pro-mypage-regions .grid-btn-simple').forEach(btn => {
                    if (activeRegions.includes(btn.innerText)) {
                        btn.classList.add('active');
                    } else {
                        btn.classList.remove('active');
                    }
                });
            } else {
                statusContainer.innerHTML = `
                    <div class="status-card wait" style="display: flex; align-items: center; gap: 20px; background: linear-gradient(135deg, #FFFDF5 0%, #FFF9E6 100%); border-color: #FDE68A; padding: 20px; border-radius: var(--radius-lg);">
                        ${hasProfilePic ? `
                        <div class="profile-pic-display" style="width: 76px; height: 76px; border-radius: 50%; border: 3px solid #ffffff; box-shadow: 0 4px 10px rgba(0,0,0,0.08); overflow: hidden; flex-shrink: 0;">
                            <img src="${profile.profile_pic}" style="width: 100%; height: 100%; object-fit: cover;">
                        </div>` : ''}
                        <div class="profile-info-display" style="flex: 1;">
                            <div style="font-size: 18px; font-weight: 800; color: #92400E; display: flex; align-items: center; gap: 4px; margin-bottom: 4px;">
                                <span>${app.escapeHtml(profile.name)} 프로</span>
                                ${excellentBadgeHtml}
                            </div>
                            <div style="font-size: 13px; color: #B45309; font-weight: 600; margin-bottom: 6px;">
                                자격번호: ${app.escapeHtml(profile.cert_number)}
                            </div>
                            <div style="font-size: 12.5px; color: #B45309; font-weight: 500; line-height: 1.4;">
                                ⏳ KPGA/KLPGA 회원 자격 심사가 안전하게 진행 중입니다. (1~2일 소요)
                            </div>
                        </div>
                    </div>
                `;
                document.getElementById('pro-settings-section').style.display = 'none';
            }

            // 4. 매칭 내역 리스트 바인딩
            if (matches.length === 0) {
                matchesContainer.innerHTML = `
                    <div class="empty-state" style="background: white; border: 1px solid var(--border-color); border-radius: var(--radius-lg); padding: 40px 20px; text-align: center;">
                        <span class="empty-icon" style="font-size: 32px; display: block; margin-bottom: 12px;">⛳</span>
                        <p style="font-size: 14px; color: var(--text-sub); font-weight: 500;">현재 프로님께 배정된 실시간 매칭 기록이 없습니다.</p>
                    </div>
                `;
            } else {
                const todayStr = app.getKstTodayStr();
                matchesContainer.innerHTML = matches.map(match => {
                    let statusBadge = '';
                    let actionButtonHtml = '';
                    if (match.status === '매칭완료') {
                        statusBadge = `<span class="pro-match-status-badge wait">결제 대기중</span>`;
                    } else if (match.status === '결제완료') {
                        statusBadge = `<span class="pro-match-status-badge paid">예약 완료 💰</span>`;
                        
                        if (match.pro_pay_status === '결제완료') {
                            statusBadge += `<span class="pro-match-status-badge paid" style="margin-left: 4px; background-color: #d1fae5; color: #065f46;">수수료 납부완료 ✅</span>`;
                        } else {
                            if (match.lesson_date < todayStr) {
                                statusBadge += `<span class="pro-match-status-badge wait" style="margin-left: 4px; background-color: #fee2e2; color: #991b1b;">수수료 미납 🚨</span>`;
                                actionButtonHtml = `
                                    <div style="margin-top: 12px; padding: 12px; background-color: #fff5f5; border: 1px solid #fee2e2; border-radius: 8px;">
                                        <p style="font-size: 12px; color: #b91c1c; font-weight: 700; margin: 0 0 8px 0; line-height: 1.4;">
                                            ⚠️ 라운딩 완료 다음 날 수수료 50,000원 입금이 완료되지 않으면 파트너 프로 활동이 정지됩니다.
                                        </p>
                                        <button class="btn btn-primary full-width" style="padding: 10px; font-size: 13px; background-color: #dc2626; border: none; font-weight: 700; width: 100%; box-sizing: border-box;" onclick="app.payProCommission('${match.id}', '${match.user_name || '골퍼'}')">
                                            수수료 50,000원 결제하기
                                        </button>
                                    </div>
                                `;
                            } else {
                                statusBadge += `<span class="pro-match-status-badge wait" style="margin-left: 4px; background-color: #f3f4f6; color: #4b5563;">수수료 납부대기 ⏳</span>`;
                                actionButtonHtml = `
                                    <div style="margin-top: 12px; padding: 12px; background-color: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px;">
                                        <p style="font-size: 12px; color: #166534; font-weight: 700; margin: 0 0 8px 0; line-height: 1.4;">
                                            ℹ️ 라운딩 예정 건입니다. 수수료를 미리 결제하실 수 있습니다.
                                        </p>
                                        <button class="btn btn-primary full-width" style="padding: 10px; font-size: 13px; background-color: var(--primary-color); border: none; font-weight: 700; width: 100%; box-sizing: border-box;" onclick="app.payProCommission('${match.id}', '${match.user_name || '골퍼'}')">
                                            수수료 50,000원 결제하기
                                        </button>
                                    </div>
                                `;
                            }
                        }
                    }
                    return `
                        <div class="pro-match-card">
                            <div class="pro-match-header">
                                <span class="pro-match-amateur">👤 ${app.escapeHtml(match.user_name || '골퍼')} (${app.escapeHtml(match.user_contact || '-')})</span>
                                ${statusBadge}
                            </div>
                            <ul class="pro-match-details">
                                <li class="pro-match-detail-item">
                                    <span class="pro-match-detail-label">⛳ 라운딩 골프장</span>
                                    <span class="pro-match-detail-value">${app.escapeHtml(match.golf_course)}</span>
                                </li>
                                <li class="pro-match-detail-item">
                                    <span class="pro-match-detail-label">📅 라운딩 일자</span>
                                    <span class="pro-match-detail-value">${app.escapeHtml(match.lesson_date)}</span>
                                </li>
                                <li class="pro-match-detail-item">
                                    <span class="pro-match-detail-label">⏰ 티오프 시간</span>
                                    <span class="pro-match-detail-value">${app.escapeHtml(match.lesson_time)}</span>
                                </li>
                            </ul>
                            ${actionButtonHtml}
                        </div>
                    `;
                }).join('');
            }

        } catch (e) {
            statusContainer.innerHTML = `
                <div class="matching-loading-box" style="padding: 30px 0;">
                    <div style="font-size: 32px; margin-bottom: 8px;">⚠️</div>
                    <p class="overlay-subtitle" style="font-size: 13px; color: var(--text-muted);">정보를 불러오지 못했습니다.</p>
                </div>
            `;
        }
    },

    getKstTodayStr: function() {
        const d = new Date();
        const utc = d.getTime() + (d.getTimezoneOffset() * 60000);
        const kst = new Date(utc + (9 * 60 * 60 * 1000));
        const yyyy = kst.getFullYear();
        let mm = kst.getMonth() + 1;
        let dd = kst.getDate();
        if (mm < 10) mm = '0' + mm;
        if (dd < 10) dd = '0' + dd;
        return `${yyyy}-${mm}-${dd}`;
    },

    payProCommission: async function(reqId, amateurName, certParam) {
        if (typeof IMP === 'undefined') {
            alert("결제 모듈이 아직 로드되지 않았습니다. 새로고침 후 다시 시도해 주세요.");
            return;
        }
        
        // Initialize IMP
        IMP.init("imp30206856");
        
        const cert = certParam || localStorage.getItem('withpro_pro_cert');
        if (!cert) {
            alert("프로 로그인 정보가 만료되었습니다. 다시 로그인 해 주세요.");
            return;
        }
        
        const merchantUid = `withpro_pro_${reqId}_${Date.now()}`;
        
        IMP.request_pay({
            pg: app.DEFAULT_PG_PROVIDER,
            pay_method: 'card',
            merchant_uid: merchantUid,
            name: `올앱 프로 라운딩 수수료 (${amateurName}님 매칭 건)`,
            amount: 50000,
            m_redirect_url: window.location.origin + "/index.html?view=pro-mypage"
        }, async function(rsp) {
            if (rsp.success) {
                try {
                    const response = await fetch('/api/pro/payment-complete', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ 
                            id: reqId, 
                            pay_method: '신용카드',
                            imp_uid: rsp.imp_uid,
                            merchant_uid: rsp.merchant_uid,
                            cert: cert
                        })
                    });
                    
                    if (!response.ok) {
                        throw new Error("결제 처리 API 통신 실패");
                    }
                    
                    alert("수수료 결제가 성공적으로 완료되었습니다! 파트너 정지 상태가 해제되었습니다.");
                    app.openProMyPage(cert);
                } catch(e) {
                    alert("결제 승인은 완료되었으나 상태 변경 처리에 실패했습니다. 고객센터로 문의해 주세요.");
                }
            } else {
                alert(`결제에 실패하였습니다. 에러 내용: ${rsp.error_msg}`);
            }
        });
    },

    updateProProfile: async function() {
        const cert = localStorage.getItem('withpro_pro_cert');
        if (!cert) return;

        const dayNodes = document.querySelectorAll('#pro-mypage-days .day-btn.active');
        const available_days = Array.from(dayNodes).map(n => n.innerText).join(', ');

        const regionNodes = document.querySelectorAll('#pro-mypage-regions .grid-btn-simple.active');
        const regions = Array.from(regionNodes).map(n => n.innerText).join(', ');

        if (!available_days) {
            alert("레슨이 가능한 요일을 최소 하나 이상 선택해 주세요.");
            return;
        }

        if (!regions) {
            alert("레슨이 가능한 활동 지역을 최소 하나 이상 선택해 주세요.");
            return;
        }

        try {
            const response = await fetch('/api/pro/update-profile', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ cert, available_days, regions })
            });
            const data = await response.json();
            if (!response.ok) {
                alert(data.error || '수정에 실패했습니다.');
                return;
            }

            // 미니 슬라이딩 토스트 띄우기
            const toast = document.getElementById('pro-toast');
            toast.innerText = "✨ 레슨 활동 설정이 성공적으로 저장되었습니다!";
            toast.classList.add('show');
            setTimeout(() => {
                toast.classList.remove('show');
            }, 2500);

        } catch (e) {
            alert('서버 통신 중 오류가 발생했습니다.');
        }
    },

    loadProPayDirectView: async function(reqId, cert) {
        app.navigate('view-pro-pay-direct');
        const container = document.getElementById('pro-pay-direct-container');
        if (!container) return;

        container.innerHTML = `
            <div class="matching-loading-box">
                <div class="loading-spinner" style="border-top-color: var(--primary-color);"></div>
                <p class="overlay-subtitle">결제 정보를 불러오는 중입니다...</p>
            </div>
        `;

        try {
            const response = await fetch(`/api/lesson/status?id=${reqId}`);
            if (!response.ok) {
                throw new Error("정보를 찾을 수 없습니다.");
            }
            const data = await response.json();

            if (data.pro_pay_status === '결제완료') {
                container.innerHTML = `
                    <div class="matching-loading-box">
                        <div style="font-size: 48px; margin-bottom: 16px;">✅</div>
                        <h3 class="overlay-title" style="margin-bottom: 8px;">결제 완료</h3>
                        <p class="overlay-subtitle" style="margin-bottom: 24px;">이미 해당 라운딩의 플랫폼 이용 수수료(5만 원) 결제가 완료되었습니다.</p>
                        <button class="btn btn-primary" onclick="app.openProMyPage('${app.escapeHtml(cert)}')">프로 마이페이지로 이동</button>
                    </div>
                `;
                return;
            }

            container.innerHTML = `
                <div class="my-booking-card" style="margin-top: 12px; border-color: var(--primary-color);">
                    <div class="booking-badge-row" style="margin-bottom: 12px;">
                        <span class="booking-title" style="font-size: 19px; color: var(--primary-color); font-weight: 800;">플랫폼 수수료 결제 🏌️‍♂️</span>
                        <span class="booking-status-tag cancel" style="background-color: #FEE2E2; color: #DC2626; border-color: rgba(220,38,38,0.15); border: 1.5px solid;">수수료 미결제</span>
                    </div>
                    <p style="font-size: 14.5px; color: #4B5563; line-height: 1.6; margin-bottom: 20px; font-weight: 500;">
                        라운딩 완료에 따른 플랫폼 이용 수수료(5만 원)를 결제해 주세요. 결제가 완료되면 파트너 프로 정지 상태가 즉시 해제됩니다.
                    </p>
                    
                    <div style="background-color: #FAFAFA; border: 1px solid var(--border-color); border-radius: 12px; padding: 16px; margin-bottom: 24px;">
                        <h4 style="font-size: 14px; font-weight: 700; margin-bottom: 12px; color: #111827;">라운딩 상세 정보</h4>
                        <ul class="booking-details-list" style="margin: 0; border: none; padding: 0;">
                            <li class="booking-detail-item" style="margin-bottom: 10px;">
                                <span class="booking-detail-label">라운딩 골프장</span>
                                <span class="booking-detail-value" style="font-weight: 700; color: var(--text-main);">${app.escapeHtml(data.golf_course)}</span>
                            </li>
                            <li class="booking-detail-item" style="margin-bottom: 10px;">
                                <span class="booking-detail-label">라운딩 일정</span>
                                <span class="booking-detail-value" style="font-weight: 700; color: var(--text-main);">${app.escapeHtml(data.lesson_date)} (${app.escapeHtml(data.lesson_time)})</span>
                            </li>
                            <li class="booking-detail-item" style="margin-bottom: 10px;">
                                <span class="booking-detail-label">아마추어 고객</span>
                                <span class="booking-detail-value">${app.escapeHtml(data.user_name || '아마추어')} 님</span>
                            </li>
                            <li class="booking-detail-item" style="margin-bottom: 0;">
                                <span class="booking-detail-label">결제 금액</span>
                                <span class="booking-detail-value" style="color: var(--accent-color); font-weight: 700; font-size: 16px;">50,000원</span>
                            </li>
                        </ul>
                    </div>
                    
                    <button class="btn btn-primary full-width" style="padding: 14px; font-size: 16px; font-weight: 700;" onclick="app.payProCommission('${reqId}', '${app.escapeHtml(data.user_name || '아마추어')}', '${app.escapeHtml(cert)}')">수수료 50,000원 결제하기</button>
                    <button class="btn btn-secondary full-width mt-2" style="border: 1.5px solid var(--border-color); background: white; color: #4B5563; padding: 12px;" onclick="app.openProMyPage('${app.escapeHtml(cert)}')">마이페이지로 이동</button>
                </div>
            `;

        } catch (e) {
            container.innerHTML = `
                <div class="matching-loading-box">
                    <div style="font-size: 48px; margin-bottom: 16px;">⚠️</div>
                    <h3 class="overlay-title" style="margin-bottom: 8px;">정보 로드 실패</h3>
                    <p class="overlay-subtitle" style="margin-bottom: 24px;">매칭 정보를 불러오는 데 실패하였습니다. 다시 시도해 주세요.</p>
                    <button class="btn btn-secondary" onclick="app.loadProPayDirectView('${reqId}', '${app.escapeHtml(cert)}')">다시 시도</button>
                </div>
            `;
        }
    },

    loadProAcceptView: async function(reqId, proId) {
        app.navigate('view-pro-accept');
        const container = document.getElementById('pro-accept-container');
        if (!container) return;

        container.innerHTML = `
            <div class="matching-loading-box">
                <div class="loading-spinner" style="border-top-color: var(--primary-color);"></div>
                <p class="overlay-subtitle">매칭 정보를 불러오는 중입니다...</p>
            </div>
        `;

        try {
            const response = await fetch(`/api/lesson/status?id=${reqId}`);
            if (!response.ok) {
                throw new Error("정보를 찾을 수 없습니다.");
            }
            const data = await response.json();

            if (data.status !== '프로 수락 대기중') {
                container.innerHTML = `
                    <div class="matching-loading-box">
                        <div style="font-size: 48px; margin-bottom: 16px;">✨</div>
                        <h3 class="overlay-title" style="margin-bottom: 8px;">처리 완료된 매칭</h3>
                        <p class="overlay-subtitle" style="margin-bottom: 24px;">이미 수락/거절 처리가 완료되었거나 만료된 매칭 요청입니다.</p>
                        <button class="btn btn-primary" onclick="app.navigate('view-home')">홈으로 이동</button>
                    </div>
                `;
                return;
            }

            container.innerHTML = `
                <div class="my-booking-card" style="margin-top: 12px; border-color: var(--primary-color);">
                    <div class="booking-badge-row" style="margin-bottom: 12px;">
                        <span class="booking-title" style="font-size: 19px; color: var(--primary-color); font-weight: 800;">신규 필드레슨 배정 제안 🏌️‍♂️</span>
                        <span class="booking-status-tag wait" style="background-color: var(--active-bg); color: var(--primary-color); border-color: rgba(11,54,33,0.15);">수락 대기중</span>
                    </div>
                    <p style="font-size: 14.5px; color: #4B5563; line-height: 1.6; margin-bottom: 20px; font-weight: 500;">
                        프로님의 소중한 스케줄에 맞춰 아래의 라운딩 필드레슨 요청이 배정되었습니다. 일정을 확인하신 후 수락 여부를 결정해 주세요.
                    </p>
                    
                    <div style="background-color: #FAFAFA; border: 1px solid var(--border-color); border-radius: 12px; padding: 16px; margin-bottom: 24px;">
                        <h4 style="font-size: 14px; font-weight: 700; margin-bottom: 12px; color: #111827;">라운딩 상세 정보</h4>
                        <ul class="booking-details-list" style="margin: 0; border: none; padding: 0;">
                            <li class="booking-detail-item" style="margin-bottom: 10px;">
                                <span class="booking-detail-label">라운딩 골프장</span>
                                <span class="booking-detail-value" style="font-weight: 700; color: var(--text-main);">${app.escapeHtml(data.golf_course)}</span>
                            </li>
                            <li class="booking-detail-item" style="margin-bottom: 10px;">
                                <span class="booking-detail-label">라운딩 일정</span>
                                <span class="booking-detail-value" style="font-weight: 700; color: var(--text-main);">${app.escapeHtml(data.lesson_date)} (${app.escapeHtml(data.lesson_time)})</span>
                            </li>
                            <li class="booking-detail-item" style="margin-bottom: 10px;">
                                <span class="booking-detail-label">아마추어 고객</span>
                                <span class="booking-detail-value">${app.escapeHtml(data.user_name || '아마추어')} 님</span>
                            </li>
                            <li class="booking-detail-item" style="margin-bottom: 0;">
                                <span class="booking-detail-label">현장 정산 레슨비</span>
                                <span class="booking-detail-value" style="color: var(--accent-color); font-weight: 700; font-size: 16px;">550,000원</span>
                            </li>
                        </ul>
                    </div>

                    <div style="font-size: 13.5px; color: var(--text-sub); line-height: 1.5; padding: 12px; border-radius: 8px; background-color: var(--input-bg); margin-bottom: 24px; font-weight: 500;">
                        💡 <strong>알아두세요:</strong> 프로 수락 즉시 매칭이 최종 확정(예약 완료)됩니다. 레슨비(55만 원)는 라운딩 종료 후 현장에서 직접 정산받으시며, 코스 내 프로님 제반 비용(그린피/카트비/캐디피)은 고객 전액 부담 조건입니다.
                    </div>

                    <div class="grid-2 gap-2" style="display: flex; gap: 10px;">
                        <button class="btn btn-secondary" style="flex: 1; padding: 14px; border-radius: 12px; font-size: 16px; font-weight: 700; border: 1.5px solid var(--border-color); background-color: white; color: #5c645f; cursor: pointer;" onclick="app.submitProAccept(false, '${reqId}', '${proId}')">거절하기</button>
                        <button class="btn btn-primary" style="flex: 1; padding: 14px; border-radius: 12px; font-size: 16px; font-weight: 700; background-color: var(--primary-color); border: none; color: white; cursor: pointer; box-shadow: 0 4px 12px rgba(11,54,33,0.15);" onclick="app.submitProAccept(true, '${reqId}', '${proId}')">수락하기</button>
                    </div>
                </div>
            `;
        } catch (e) {
            container.innerHTML = `
                <div class="matching-loading-box">
                    <div style="font-size: 48px; margin-bottom: 16px;">⚠️</div>
                    <h3 class="overlay-title">오류가 발생했습니다</h3>
                    <p class="overlay-subtitle" style="margin-bottom: 20px;">매칭 정보를 불러오는 데 실패했습니다.</p>
                    <button class="btn btn-secondary" onclick="app.loadProAcceptView('${reqId}', '${proId}')">다시 시도</button>
                </div>
            `;
        }
    },

    submitProAccept: async function(accept, reqId, proId) {
        try {
            const response = await fetch('/api/lesson/pro-accept', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id: reqId, pro_id: proId, accept: accept })
            });
            if (!response.ok) {
                throw new Error("처리 실패");
            }
            
            const container = document.getElementById('pro-accept-container');
            if (accept) {
                container.innerHTML = `
                    <div class="matching-loading-box" style="padding: 40px 10px; text-align: center;">
                        <div style="font-size: 64px; margin-bottom: 20px; animation: bounce 1s infinite alternate;">🏌️‍♂️</div>
                        <h3 class="overlay-title" style="margin-bottom: 12px; font-size: 22px; color: var(--primary-color);">매칭 제안 수락 완료!</h3>
                        <p class="overlay-subtitle" style="margin-bottom: 30px; font-size: 15px; line-height: 1.5;">
                            필드레슨 매칭 수락이 정상적으로 완료되었습니다.<br>
                            매칭이 <strong>최종 확정</strong>되었습니다. 마이페이지 배정 내역에서 실시간 상태를 확인하실 수 있으며, 고객님께 매칭 확정 안내 SMS가 즉시 발송되었습니다.
                        </p>
                        <button class="btn btn-primary" style="background-color: var(--primary-color); border: none; padding: 12px 30px; border-radius: 8px; color: white;" onclick="app.navigate('view-home')">홈으로 이동</button>
                    </div>
                `;
            } else {
                container.innerHTML = `
                    <div class="matching-loading-box" style="padding: 40px 10px; text-align: center;">
                        <div style="font-size: 64px; margin-bottom: 20px;">🤝</div>
                        <h3 class="overlay-title" style="margin-bottom: 12px; font-size: 22px; color: #4B5563;">제안 거절 완료</h3>
                        <p class="overlay-subtitle" style="margin-bottom: 30px; font-size: 15px; line-height: 1.5;">
                            배정 제안을 정중히 거절하셨습니다.<br>
                            운영진이 프로님의 일정에 맞는 더 어울리는 라운딩으로 조율하여 빠른 시일 내에 다시 제안해 드리겠습니다.
                        </p>
                        <button class="btn btn-secondary" style="border: 1.5px solid var(--border-color); background: white; color: #4B5563; padding: 12px 30px; border-radius: 8px;" onclick="app.navigate('view-home')">홈으로 이동</button>
                    </div>
                `;
            }
        } catch (e) {
            alert('요청 처리 중 오류가 발생했습니다.');
        }
    },

    logoutPro: async function() {
        if (await window.withproConfirm("프로 마이페이지에서 로그아웃 하시겠습니까?")) {
            localStorage.removeItem('withpro_pro_cert');
            app.navigate('view-home');
        }
    },

    initFirebase: async function(contact, type) {
        if (typeof firebase === 'undefined') {
            console.log("[Firebase] Firebase SDK가 웹페이지에 포함되지 않아 시뮬레이션 모드를 유지합니다.");
            return;
        }
        
        try {
            // 1. 서버로부터 Firebase 웹 구성 데이터 조회
            const cfgResponse = await fetch('/api/firebase-config');
            if (!cfgResponse.ok) {
                console.log("[Firebase] 서버 연동 정보 조회를 실패하여 시뮬레이션 모드로 가동합니다.");
                return;
            }
            const config = await cfgResponse.json();
            
            if (!config || !config.apiKey) {
                console.log("[Firebase] 등록된 Firebase 웹 클라이언트 설정이 없습니다. 시뮬레이션 모드 유지.");
                return;
            }
            
            // 2. Firebase 앱 동적 초기화
            if (firebase.apps.length === 0) {
                firebase.initializeApp(config);
            }
            
            // 3. 백그라운드 서비스 워커 명시적 등록
            if ('serviceWorker' in navigator) {
                try {
                    const registration = await navigator.serviceWorker.register('/firebase-messaging-sw.js');
                    console.log("[Firebase] 서비스 워커 등록 성공:", registration);
                } catch(swErr) {
                    console.error("[Firebase] 서비스 워커 등록 실패:", swErr);
                }
            }
            
            const messaging = firebase.messaging();
            
            // 4. 알림 권한 요청 및 FCM 토큰 획득
            const permission = await Notification.requestPermission();
            if (permission === 'granted') {
                console.log("[Firebase] 알림 권한 획득 성공.");
                
                const tokenOptions = {};
                if (config.vapidKey) {
                    tokenOptions.vapidKey = config.vapidKey;
                }
                
                const token = await messaging.getToken(tokenOptions);
                if (token) {
                    console.log("[Firebase] 실시간 FCM 토큰 획득 성공:", token);
                    
                    // 5. 서버로 토큰 전송하여 저장
                    await fetch('/api/save-fcm-token', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ contact: contact, token: token, type: type })
                    });
                    
                    // 수령된 토큰을 디버깅 편의를 위해 임시 로컬스토리지에 캐싱
                    localStorage.setItem('withpro_my_fcm_token', token);
                }
            } else {
                console.log("[Firebase] 알림 권한이 거부되었습니다.");
            }
        } catch(e) {
            console.log("[Firebase] 클라이언트 설정 및 토큰 등록 실패:", e);
        }
    },

    showPrivacyModal: function(type) {
        const modal = document.getElementById('privacy-modal');
        const titleEl = document.getElementById('privacy-title');
        const bodyEl = document.getElementById('privacy-body');
        
        let title = '';
        let content = '';
        
        if (type === 'privacy') {
            title = '개인정보 수집 및 이용 동의';
            content = `
                <h4>1. 개인정보 수집 목적</h4>
                <p>올앱은 레슨 매칭 서비스 제공, 당사자 간 연락 지원, 알림 서비스(SMS, Push) 발송을 위해 개인정보를 수집합니다.</p>
                
                <h4>2. 수집하는 개인정보 항목</h4>
                <p>필수 항목: 이름, 연락처(휴대폰 번호), 라운딩 골프장, 날짜 및 시간</p>
                
                <h4>3. 개인정보의 보유 및 이용 기간</h4>
                <p>수집된 개인정보는 서비스 목적 달성 후 혹은 이용자 요구 시 즉시 파기됩니다. 단, 관계 법령에 따라 보존할 필요가 있는 경우 해당 기간 동안 안전하게 보관됩니다.</p>
                
                <h4>4. 동의 거부 권리</h4>
                <p>귀하는 개인정보 수집 및 이용에 동의하지 않을 권리가 있습니다. 단, 동의하지 않으실 경우 필드레슨 매칭 서비스 신청이 불가능합니다.</p>
            `;
        } else {
            title = '개인정보 수집 및 이용 동의';
            content = `
                <h4>1. 개인정보 수집 목적</h4>
                <p>올앱은 프로 파트너 등록 심사, 레슨 매칭 제안 및 알림(SMS, Push) 발송, 아마추어 예약 고객과의 레슨 일정 조율 및 비상 시 긴급 연락 지원을 위해 개인정보를 수집합니다.</p>
                
                <h4>2. 수집하는 개인정보 항목</h4>
                <p>필수 항목: 이름, 연락처(휴대폰 번호), 간편 비밀번호(핀번호), 자격증 종류 및 회원번호, 프로필 사진, 활동 가능 지역 및 요일</p>
                
                <h4>3. 개인정보의 보유 및 이용 기간</h4>
                <p>수집된 개인정보는 서비스 제공 목적이 달성되거나 파트너 탈퇴 또는 요구 시 즉시 안전하게 파기됩니다. 단, 관련 법령의 규정에 따라 보존할 필요가 있는 경우 해당 기간 동안 안전하게 분리 보관됩니다.</p>
                
                <h4>4. 동의 거부 권리</h4>
                <p>귀하는 개인정보 수집 및 이용에 동의하지 않을 권리가 있습니다. 단, 동의하지 않으실 경우 올앱 파트너 프로 등록 및 필드레슨 매칭 제안 수령이 불가능합니다.</p>
            `;
        }
        
        titleEl.innerText = title;
        bodyEl.innerHTML = content;
        modal.classList.add('active');
    },
    
    closePrivacyModal: function() {
        document.getElementById('privacy-modal').classList.remove('active');
    },

    openCustomTimePicker: function() {
        const modal = document.getElementById('custom-time-picker-modal');
        if (!modal) return;
        
        // 현재 설정된 시간 값 파싱하여 선택기 초기화
        const currentVal = document.getElementById('lesson-time').value;
        let ampm = 'AM';
        let hour = 7;
        let minute = '00';
        
        if (currentVal) {
            const parts = currentVal.split(':');
            let h = parseInt(parts[0], 10);
            minute = parts[1];
            if (h >= 12) {
                ampm = 'PM';
                if (h > 12) h -= 12;
            } else if (h === 0) {
                h = 12;
            }
            hour = h;
        }
        
        document.getElementById('picker-ampm').value = ampm;
        document.getElementById('picker-hour').value = String(hour);
        document.getElementById('picker-minute').value = String(minute);
        
        modal.classList.add('active');
        modal.style.display = 'flex';
    },
    
    closeCustomTimePicker: function() {
        const modal = document.getElementById('custom-time-picker-modal');
        if (modal) {
            modal.classList.remove('active');
            modal.style.display = 'none';
        }
    },
    
    applyCustomTimePicker: function() {
        const ampm = document.getElementById('picker-ampm').value;
        let hour = parseInt(document.getElementById('picker-hour').value, 10);
        const minute = document.getElementById('picker-minute').value;
        
        if (ampm === 'PM' && hour < 12) {
            hour += 12;
        } else if (ampm === 'AM' && hour === 12) {
            hour = 0;
        }
        
        const formattedTime = `${String(hour).padStart(2, '0')}:${minute}`;
        
        const timeInput = document.getElementById('lesson-time');
        if (timeInput) {
            timeInput.value = formattedTime;
            // dispatch change event to trigger listeners and display update
            timeInput.dispatchEvent(new Event('change'));
        }
        
        app.closeCustomTimePicker();
    },

    getReviewSectionHtml: function(data) {
        return '';
    },

    reviewRatings: {},
    setReviewRating: function(id, rating) {
        app.reviewRatings[id] = rating;
        const card = document.getElementById(`review-form-${id}`);
        if (!card) return;
        const stars = card.querySelectorAll('.star-item');
        stars.forEach((star, idx) => {
            if (idx < rating) {
                star.style.color = '#fbbf24';
            } else {
                star.style.color = '#d1d5db';
            }
        });
    },

    submitReview: async function(bookingId) {
        const textInput = document.getElementById(`review-text-${bookingId}`);
        if (!textInput) return;
        
        const reviewText = textInput.value.trim();
        if (reviewText.length < 5) {
            alert("후기 내용을 최소 5자 이상 입력해 주세요.");
            textInput.focus();
            return;
        }
        
        const rating = app.reviewRatings[bookingId] || 5;
        
        try {
            const response = await fetch('/api/lesson/submit-review', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    id: bookingId,
                    review_text: reviewText,
                    review_rating: rating
                })
            });
            
            const resData = await response.json();
            if (!response.ok) {
                alert(`오류: ${resData.error || '후기 등록 실패'}`);
                return;
            }
            if (resData.coupon_code) {
                alert("소중한 후기가 등록되었습니다! 오픈 이벤트 3만원 할인 쿠폰이 발급되었습니다.");
            } else {
                alert(resData.message || "소중한 후기가 등록되었습니다!");
            }
            
            const reqIdParam = new URLSearchParams(window.location.search).get('id');
            if (reqIdParam && reqIdParam == bookingId) {
                app.loadBookingDirectly(bookingId);
            } else {
                if (app.verifiedUserName && app.verifiedUserContact) {
                    const nameInput = document.getElementById('lookup-user-name');
                    const contactInput = document.getElementById('lookup-user-contact');
                    if (nameInput) nameInput.value = app.verifiedUserName;
                    if (contactInput) contactInput.value = app.verifiedUserContact;
                    app.lookupMyBookings();
                } else {
                    location.reload();
                }
            }
        } catch (e) {
            alert("서버 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.");
        }
    }
};

// DOM 로드 완료 후 초기화
document.addEventListener('DOMContentLoaded', () => {
    app.init();
});

// 브라우저 뒤로가기/앞으로가기 및 BF Cache(Back-Forward Cache) 복원 시 자동 보안 검증 강제 (우회 노출 전면 차단)
window.addEventListener('pageshow', (event) => {
    const currentActiveView = document.querySelector('.view.active');
    if (currentActiveView) {
        const viewId = currentActiveView.id;
        if (viewId === 'view-my-bookings' || viewId === 'view-payment') {
            // 예약 상세나 결제 뷰가 활성화되어 있는데 메모리 내 검증 세션이 없다면 즉시 본인 확인 폼으로 강제 리다이렉트
            if (!app.verifiedBookings || app.verifiedBookings.length === 0) {
                app.checkMyBookings();
            }
        }
    }
});
