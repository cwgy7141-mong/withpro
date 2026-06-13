import os
import sys
import subprocess

# Ensure Pillow is installed
try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps
except ImportError:
    print("Installing Pillow...")
    subprocess.run([sys.executable, "-m", "pip", "install", "Pillow"], check=True)
    from PIL import Image, ImageDraw, ImageFont, ImageOps

def create_black_thumbnail():
    print("Generating withPRO black premium thumbnail (1932x828px)...")
    
    # Target size
    width = 1932
    height = 828
    
    # Create pure black image (matches the logo background)
    # Using #050505 for a slightly richer, premium black
    thumb_img = Image.new("RGBA", (width, height), (5, 5, 5, 255))
    draw = ImageDraw.Draw(thumb_img)
    
    # Find Windows system fonts
    font_path_bold = "C:\\Windows\\Fonts\\malgunbd.ttf" # Malgun Gothic Bold
    font_path_reg = "C:\\Windows\\Fonts\\malgun.ttf" # Malgun Gothic Regular
    
    if not os.path.exists(font_path_bold):
        font_path_bold = "arialbd.ttf" # Fallback
    if not os.path.exists(font_path_reg):
        font_path_reg = "arial.ttf" # Fallback
        
    try:
        font_logo_with = ImageFont.truetype(font_path_bold, 100)
        font_logo_pro = ImageFont.truetype(font_path_bold, 100)
        font_title = ImageFont.truetype(font_path_bold, 90)
        font_subtitle = ImageFont.truetype(font_path_reg, 36)
        font_badge = ImageFont.truetype(font_path_bold, 22)
    except IOError:
        print("System fonts not found. Using default fonts.")
        font_logo_with = font_logo_pro = font_title = font_subtitle = font_badge = ImageFont.load_default()
        
    # Colors
    brand_green = (76, 175, 80, 255) # Modern vibrant brand green #4CAF50 from their SVG
    white = (255, 255, 255, 255)
    soft_gray = (150, 160, 155, 255)
    
    # ------------------ DRAW CENTERED COMPOSITION ------------------
    # To make it look extremely premium, we will put the withPRO logo 
    # in the center, and the text "골프필드레슨" below it with elegant spacing.
    
    # 1. Calculate Logo dimensions
    logo_with_w = font_logo_with.getlength("with")
    logo_pro_w = font_logo_pro.getlength("PRO")
    total_logo_w = logo_with_w + 10 + logo_pro_w
    
    # Center coordinates for logo
    logo_x = int((width - total_logo_w) / 2)
    logo_y = 230 # Positioned in the upper half
    
    # Draw 'with' in White
    draw.text((logo_x, logo_y), "with", fill=white, font=font_logo_with)
    
    # Draw 'PRO' in Brand Green
    pro_x = int(logo_x + logo_with_w + 10)
    draw.text((pro_x, logo_y), "PRO", fill=brand_green, font=font_logo_pro)
    
    # Draw White Arc over 'PRO'
    arc_x0 = pro_x - 10
    arc_y0 = logo_y - 30
    arc_x1 = pro_x + int(logo_pro_w) + 10
    arc_y1 = logo_y + 20
    draw.arc([arc_x0, arc_y0, arc_x1, arc_y1], start=195, end=345, fill=white, width=6)
    
    # 2. Draw Separator Line or Badge
    badge_y = 410
    badge_text = "PREMIUM MATCHING SERVICE"
    badge_w = font_badge.getlength(badge_text)
    badge_x = int((width - badge_w) / 2)
    
    # Draw elegant thin line flanking the text on both sides
    line_y = badge_y + 16
    draw.line([(int(width/2) - int(badge_w/2) - 120, line_y), (int(width/2) - int(badge_w/2) - 20, line_y)], fill=(255, 255, 255, 60), width=2)
    draw.text((badge_x, badge_y), badge_text, fill=soft_gray, font=font_badge)
    draw.line([(int(width/2) + int(badge_w/2) + 20, line_y), (int(width/2) + int(badge_w/2) + 120, line_y)], fill=(255, 255, 255, 60), width=2)
    
    # 3. Draw Title "골프필드레슨"
    title_text = "골프필드레슨"
    title_w = font_title.getlength(title_text)
    title_x = int((width - title_w) / 2)
    title_y = 480 # Positioned below the logo
    
    # Draw title in pure White
    draw.text((title_x, title_y), title_text, fill=white, font=font_title)
    
    # Add a premium green dot at the end of the text
    dot_x = int(title_x + title_w + 15)
    dot_y = title_y + 60
    draw.ellipse([dot_x, dot_y, dot_x + 12, dot_y + 12], fill=brand_green)
    
    # 4. Draw Subtitle (Removed per user request)
    # subtitle_text = "KPGA · KLPGA 프로 매칭부터 필드 동반 라운딩까지"
    # subtitle_w = font_subtitle.getlength(subtitle_text)
    # subtitle_x = int((width - subtitle_w) / 2)
    # subtitle_y = 620
    # draw.text((subtitle_x, subtitle_y), subtitle_text, fill=soft_gray, font=font_subtitle)
    
    # Save the image
    output_path = "withpro_thumbnail_black.png"
    thumb_img.save(output_path, "PNG")
    print(f"Successfully generated black background thumbnail! Saved to {output_path}")

if __name__ == "__main__":
    create_black_thumbnail()
