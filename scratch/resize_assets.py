import os
from PIL import Image

workspace = r"c:\Users\cwgy\OneDrive\바탕 화면\withpro"
icon_path = os.path.join(workspace, "app_icon.png")
icon_out = os.path.join(workspace, "app_icon_512.png")

if os.path.exists(icon_path):
    try:
        with Image.open(icon_path) as img:
            # 512 x 512 크기 변환 (ANTIALIAS 또는 Resampling.LANCZOS)
            resampled = img.resize((512, 512), Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.ANTIALIAS)
            resampled.save(icon_out, "PNG")
            print("Successfully resized app_icon.png to 512x512 and saved as app_icon_512.png")
    except Exception as e:
        print(f"Error resizing icon: {e}")
else:
    print(f"File not found: {icon_path}")

# 1024 x 500 배너 만들기 (검은색 배경에 로고 배치)
banner_out = os.path.join(workspace, "banner_1024_500.png")
try:
    # 1024x500 검은색 캔버스 생성
    canvas = Image.new("RGBA", (1024, 500), (11, 15, 25, 255)) # withPRO 시그니처 딥네이비 색상 #0b0f19
    
    # 원본 로고를 중앙에 배치하기 위해 원본 로고 로드
    # brain 내 아티팩트 혹은 바탕화면에 있는 원본 로고 이미지들을 찾아본다
    logo_candidates = [
        os.path.join(workspace, "logo.svg"), # svg는 pillow에서 직접 열 수 없음
        os.path.join(workspace, "app_icon.png") # 아이콘을 중앙에 작게 배치하는 방식
    ]
    
    logo_path = os.path.join(workspace, "app_icon.png")
    if os.path.exists(logo_path):
        with Image.open(logo_path) as logo:
            # 로고 크기를 300x300 정도로 조절하여 중앙에 얹기
            logo_resized = logo.resize((260, 260), Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.ANTIALIAS)
            # 중앙 위치 계산
            offset = ((1024 - 260) // 2, (500 - 260) // 2)
            canvas.paste(logo_resized, offset, logo_resized if logo_resized.mode in ('RGBA', 'LA') else None)
            canvas.save(banner_out, "PNG")
            print("Successfully created banner_1024_500.png with logo pasted in center")
except Exception as e:
    print(f"Error creating banner: {e}")
