import os
import sys
import subprocess

# Step 1: Ensure Pillow is installed
try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
except ImportError:
    print("Pillow is not installed. Installing Pillow...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "Pillow"], check=True)
        from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
        print("Pillow successfully installed!")
    except Exception as e:
        print(f"Failed to install Pillow: {e}")
        print("Please run 'pip install Pillow' manually.")
        sys.exit(1)

def create_thumbnail():
    print("Generating withPRO premium thumbnail (1932x828px)...")
    
    # Target size
    width = 1932
    height = 828
    
    # Check if the clean golf course background image exists
    bg_path = "golf_course_bg_clean.png"
    if not os.path.exists(bg_path):
        print(f"Error: {bg_path} not found in the current directory.")
        return

    # Load and fit/crop background to 1932x828
    bg_img = Image.open(bg_path)
    # Using ImageOps.fit to crop to the center at the target aspect ratio
    thumb_img = ImageOps.fit(bg_img, (width, height), Image.Resampling.LANCZOS)
    
    # Create dark gradient overlay for text readability (left to right fade)
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    
    # Create horizontal dark gradient from left (70% opacity) to right (25% opacity)
    # This helps white text pop on the left while showing the beautiful golf course on the right
    for x in range(width):
        if x < width // 2:
            # Stronger overlay on the left for text readability
            opacity = int(180 - (180 - 100) * (x / (width // 2)))
        else:
            # Softer overlay on the right to show the background course
            opacity = int(100 - (100 - 30) * ((x - width // 2) / (width // 2)))
        
        # Keep opacity within 0-255
        opacity = max(0, min(255, opacity))
        overlay_draw.line([(x, 0), (x, height)], fill=(11, 54, 33, opacity)) # Using rich forest green tone #0b3621
        
    # Composite the overlay onto the thumbnail image
    thumb_img = Image.alpha_composite(thumb_img.convert("RGBA"), overlay)
    draw = ImageDraw.Draw(thumb_img)
    
    # Setup fonts
    # Find Windows system fonts
    font_path_bold = "C:\\Windows\\Fonts\\malgunbd.ttf" # Malgun Gothic Bold
    font_path_reg = "C:\\Windows\\Fonts\\malgun.ttf" # Malgun Gothic Regular
    
    if not os.path.exists(font_path_bold):
        font_path_bold = "arialbd.ttf" # Fallback
    if not os.path.exists(font_path_reg):
        font_path_reg = "arial.ttf" # Fallback
        
    try:
        font_logo_with = ImageFont.truetype(font_path_bold, 75)
        font_logo_pro = ImageFont.truetype(font_path_bold, 75)
        font_title = ImageFont.truetype(font_path_bold, 95)
        font_subtitle = ImageFont.truetype(font_path_bold, 36)
        font_badge = ImageFont.truetype(font_path_bold, 24)
    except IOError:
        print("System fonts not found. Using default fonts.")
        font_logo_with = font_logo_pro = font_title = font_subtitle = font_badge = ImageFont.load_default()
        
    # Define colors
    mint_green = (0, 199, 117, 255)  # #00c775 (Accent)
    forest_green = (11, 54, 33, 255) # #0b3621 (Primary)
    white = (255, 255, 255, 255)
    shadow_color = (0, 0, 0, 150)
    
    # ------------------ DRAW LOGO (withPRO) ------------------
    logo_x = 100
    logo_y = 110
    
    # Draw 'with' in White
    draw.text((logo_x, logo_y), "with", fill=white, font=font_logo_with)
    # Get width of 'with' to position 'PRO'
    logo_with_w = font_logo_with.getlength("with")
    
    # Draw 'PRO' in Accent Mint Green
    pro_x = logo_x + logo_with_w + 5
    draw.text((pro_x, logo_y), "PRO", fill=mint_green, font=font_logo_pro)
    logo_pro_w = font_logo_pro.getlength("PRO")
    
    # Draw Logo Arc (curved path over 'PRO')
    # Let's draw a smooth white arc over PRO. In PIL, we draw a portion of an ellipse.
    # Arc bounding box: [x0, y0, x1, y1]
    arc_x0 = pro_x - 3
    arc_y0 = logo_y - 20
    arc_x1 = pro_x + logo_pro_w + 3
    arc_y1 = logo_y + 15
    
    # PIL draw.arc(xy, start, end, fill, width)
    # Drawing upper arc (from 200 degrees to 340 degrees)
    draw.arc([arc_x0, arc_y0, arc_x1, arc_y1], start=195, end=345, fill=white, width=6)
    
    # ------------------ DRAW BADGE (PREMIUM FIELD LESSON) ------------------
    badge_x = 100
    badge_y = 250
    badge_text = "PREMIUM FIELD MATCHING"
    badge_w = font_badge.getlength(badge_text)
    badge_padding_h = 16
    badge_padding_v = 8
    
    # Draw badge rounded background
    draw.rounded_rectangle(
        [badge_x, badge_y, badge_x + badge_w + badge_padding_h * 2, badge_y + 35 + badge_padding_v],
        radius=8,
        fill=(255, 255, 255, 35),
        outline=white,
        width=1.5
    )
    
    # Draw badge text
    draw.text((badge_x + badge_padding_h, badge_y + badge_padding_v - 1), badge_text, fill=white, font=font_badge)

    # ------------------ DRAW TITLE (골프필드레슨) ------------------
    title_x = 100
    title_y = 330
    title_text = "골프필드레슨"
    
    # Draw thick title shadow
    for offset_x in [-3, 0, 3]:
        for offset_y in [-3, 0, 3]:
            draw.text((title_x + offset_x, title_y + offset_y), title_text, fill=shadow_color, font=font_title)
            
    # Draw main title text
    draw.text((title_x, title_y), title_text, fill=white, font=font_title)
    
    # Draw Golf Emoji next to title
    title_w = font_title.getlength(title_text)
    
    # ------------------ DRAW SUBTITLE ------------------
    subtitle_x = 100
    subtitle_y = 480
    subtitle_text = "검증된 최고 실력의 프로들과 완벽한 필드 매칭"
    
    # Draw subtitle shadow
    draw.text((subtitle_x + 2, subtitle_y + 2), subtitle_text, fill=shadow_color, font=font_subtitle)
    # Draw subtitle text in white
    draw.text((subtitle_x, subtitle_y), subtitle_text, fill=white, font=font_subtitle)
    
    # Subtitle Line 2 (Highlight points)
    subtitle_y2 = 545
    subtitle_text2 = "● KPGA · KLPGA 프로 매칭   ● 18홀 실시간 밀착 피드백"
    draw.text((subtitle_x + 2, subtitle_y2 + 2), subtitle_text2, fill=shadow_color, font=font_subtitle)
    draw.text((subtitle_x, subtitle_y2), subtitle_text2, fill=mint_green, font=font_subtitle)
    
    # Save the thumbnail as PNG
    output_path = "withpro_thumbnail.png"
    thumb_img.save(output_path, "PNG")
    print(f"Successfully generated thumbnail! Saved to {output_path}")

if __name__ == "__main__":
    create_thumbnail()
