import os
from PIL import Image, ImageDraw, ImageFont

def draw_phone_mockup(canvas, screen_img, center_x, center_y, width=650, height=1300, corner_radius=50):
    draw = ImageDraw.Draw(canvas)
    
    # Outer frame box
    outer_box = [center_x - width//2, center_y - height//2, center_x + width//2, center_y + height//2]
    # Draw modern phone bezel (dark slate with silver highlight outline)
    draw.rounded_rectangle(outer_box, radius=corner_radius, fill=(30, 35, 45, 255), outline=(150, 160, 175, 255), width=6)
    
    # Screen inner dimensions (bezel is 14px)
    bezel = 14
    inner_w = width - bezel * 2
    inner_h = height - bezel * 2
    
    # Resize cropped screen image to fit inner screen size
    resized_screen = screen_img.resize((inner_w, inner_h), Image.Resampling.LANCZOS)
    
    # Create rounded corner mask for screen
    mask = Image.new("L", (inner_w, inner_h), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([0, 0, inner_w, inner_h], radius=corner_radius - bezel, fill=255)
    
    # Paste inner screen onto canvas
    canvas.paste(resized_screen, (center_x - inner_w//2, center_y - inner_h//2), mask)
    
    # Draw status bar speaker / camera notch at the top
    notch_w = 160
    notch_h = 30
    notch_box = [center_x - notch_w//2, center_y - height//2 + bezel + 4, center_x + notch_w//2, center_y - height//2 + bezel + notch_h]
    draw.rounded_rectangle(notch_box, radius=15, fill=(15, 15, 15, 255))
    
    # Draw camera lens reflection (a small dark circle)
    draw.ellipse([center_x - 30, center_y - height//2 + bezel + 10, center_x - 14, center_y - height//2 + bezel + 26], fill=(5, 15, 40, 255))

def create_premium_screenshot(input_path, output_path, title, subtitle):
    print(f"Generating premium screenshot from {input_path} -> {output_path}...")
    
    # Target resolution
    target_w = 1080
    target_h = 1920
    
    # Create canvas
    canvas = Image.new("RGBA", (target_w, target_h), (11, 15, 25, 255))
    draw = ImageDraw.Draw(canvas)
    
    # 1. Generate smooth vertical gradient background (Navy to Forest Green)
    for y in range(target_h):
        ratio = y / target_h
        # Navy (11, 24, 38) -> Forest Green (10, 48, 25)
        r = int(11 * (1 - ratio) + 10 * ratio)
        g = int(24 * (1 - ratio) + 48 * ratio)
        b = int(38 * (1 - ratio) + 25 * ratio)
        draw.line([(0, y), (target_w, y)], fill=(r, g, b, 255))
        
    # 2. Draw modern diagonal light stripe overlay for rich aesthetics
    overlay = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    # Draw a soft white diagonal band with low opacity
    overlay_draw.polygon([(0, 600), (target_w, 1100), (target_w, 1400), (0, 900)], fill=(255, 255, 255, 8))
    canvas = Image.alpha_composite(canvas, overlay)
    draw = ImageDraw.Draw(canvas)
    
    # 3. Setup Fonts
    font_path_bold = "C:\\Windows\\Fonts\\malgunbd.ttf"
    if not os.path.exists(font_path_bold):
        font_path_bold = "arialbd.ttf"
        
    try:
        font_title = ImageFont.truetype(font_path_bold, 54)
        font_sub = ImageFont.truetype(font_path_bold, 30)
    except IOError:
        font_title = font_sub = ImageFont.load_default()
        
    # 4. Render Marketing Text (Centered)
    title_w = font_title.getlength(title)
    title_x = (target_w - title_w) // 2
    title_y = 130
    draw.text((title_x, title_y), title, fill=(255, 255, 255, 255), font=font_title)
    
    sub_w = font_sub.getlength(subtitle)
    sub_x = (target_w - sub_w) // 2
    sub_y = 215
    brand_green = (76, 175, 80, 255) # matching brand green #4CAF50
    draw.text((sub_x, sub_y), subtitle, fill=brand_green, font=font_sub)
    
    # Draw elegant separator line
    draw.line([(target_w//2 - 50, 280), (target_w//2 + 50, 280)], fill=(255, 255, 255, 60), width=2)
    
    # 5. Crop and Load active screen UI
    orig_img = Image.open(input_path)
    
    # Crop the top 390x800 area from the guide image (mobile viewport aspect ratio)
    crop_w = 390
    crop_h = 800
    screen_crop = orig_img.crop((0, 0, crop_w, crop_h))
    
    # 6. Draw Smartphone Mockup containing the app screen crop
    phone_center_x = target_w // 2
    phone_center_y = 1140 # Positioned in the middle/lower half
    draw_phone_mockup(canvas, screen_crop, phone_center_x, phone_center_y, width=650, height=1300)
    
    # Save the output image
    canvas.convert("RGB").save(output_path, "PNG")
    print(f"Successfully saved premium screenshot to {output_path} ({target_w}x{target_h})")

if __name__ == "__main__":
    # Path settings
    amateur_src = "withpro_amateur_guide.png"
    pro_src = "withpro_프로가이드.png"
    if not os.path.exists(pro_src):
        pro_src = "withpro_pro_guide_app_mockup.png"
        
    create_premium_screenshot(
        amateur_src, 
        "withpro_screenshot_amateur.png", 
        "골프 매칭부터 필드 레슨까지", 
        "아마추어 회원 서비스 가이드"
    )
    
    create_premium_screenshot(
        pro_src, 
        "withpro_screenshot_pro.png", 
        "실시간 매칭 및 필드 레슨 피드백", 
        "프로 골퍼 서비스 가이드"
    )
