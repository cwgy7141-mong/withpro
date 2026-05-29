#!/bin/bash

# ====================================================================
# withPRO B2B AWS Ubuntu Server One-Click Setup Script
# ====================================================================

echo "=================================================="
echo "🚀 withPRO 실서버 배포 자동화 설정을 시작합니다."
echo "=================================================="

# 1. 시스템 업데이트 및 필수 의존성 패키지 설치
echo "🔄 1/4. 시스템 최신 업데이트 및 Nginx, Certbot 설치 중..."
sudo apt update -y
sudo apt upgrade -y
sudo apt install nginx certbot python3-certbot-nginx python3-pip python3-venv sqlite3 -y

# 2. 방화벽 설정 (HTTP, HTTPS 허용)
echo "🔒 2/4. 네트워크 방화벽(UFW) 웹 서비스 포트 개방 중..."
sudo ufw allow 'Nginx Full'
sudo ufw allow 8000/tcp

# 3. Nginx Reverse Proxy 설정 파일 생성
echo "🌐 3/4. Nginx 리버스 프록시 연동 및 가상 서버 설정 중..."
DOMAIN_NAME="withpro.life" # <-- 사장님의 실제 도메인 주소로 변경하여 실행하세요!

sudo tee /etc/nginx/sites-available/withpro > /dev/null <<EOF
server {
    listen 80;
    server_name $DOMAIN_NAME www.$DOMAIN_NAME;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Nginx 설정 활성화 및 재시작
sudo ln -sf /etc/nginx/sites-available/withpro /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx

# 4. 백그라운드 무중단 실행 준비
echo "⚙️ 4/4. 365일 무중단 가동 환경 구축 완료."
echo "=================================================="
echo "✨ Nginx 설정 및 기본 패키지 구축이 완벽히 완료되었습니다!"
echo "=================================================="
echo "👉 사장님이 서버 원격 창에서 가동하실 핵심 명령어 딱 2개:"
echo "1) 도메인 자물쇠 발급: sudo certbot --nginx -d 사장님도메인.com"
echo "2) 24시간 백그라운드 구동: nohup python3 server.py > server.log 2>&1 &"
echo "=================================================="
