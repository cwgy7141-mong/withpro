import os
from PIL import Image, ImageDraw, ImageFont

def generate_new_icon():
    print("Generating new app icon with larger text...")
    width = 1024
    height = 1024
    
    # Create background canvas with signature dark navy (#0b0f19)
    icon_img = Image.new("RGBA", (width, height), (11, 15, 25, 255))
    draw = ImageDraw.Draw(icon_img)
    
    # Font path resolution (Windows Malgun Gothic Bold, fallback to Arial Bold)
    font_path = "C:\\Windows\\Fonts\\malgunbd.ttf"
    if not os.path.exists(font_path):
        font_path = "arialbd.ttf"
        
    # Target width of the logo inside the 1024x1024 icon
    target_logo_width = 620
    spacing = 15
    
    # Dynamically find the best font size to match target width
    font_size = 100
    while True:
        try:
            font = ImageFont.truetype(font_path, font_size)
        except IOError:
            font = ImageFont.load_default()
            break
            
        w_with = font.getlength("with")
        w_pro = font.getlength("PRO")
        total_w = w_with + spacing + w_pro
        
        if total_w >= target_logo_width:
            break
        font_size += 2
        
    print(f"Calculated optimal font size: {font_size}px")
    font_logo = ImageFont.truetype(font_path, font_size)
    
    # Recalculate dimensions with final font size
    w_with = font_logo.getlength("with")
    w_pro = font_logo.getlength("PRO")
    total_w = w_with + spacing + w_pro
    
    # Center coordinates
    start_x = int((width - total_w) / 2)
    try:
        bbox = font_logo.getbbox("withPRO")
        font_h = bbox[3] - bbox[1]
    except AttributeError:
        font_h = font_size
        
    # Offset slightly up for visual balance with the arc
    logo_y = int((height - font_h) / 2) - 20
    
    # Define colors
    brand_green = (76, 175, 80, 255) # Modern vibrant brand green #4CAF50
    white = (255, 255, 255, 255)
    
    # Draw 'with' in White
    draw.text((start_x, logo_y), "with", fill=white, font=font_logo)
    
    # Draw 'PRO' in Brand Green
    pro_x = int(start_x + w_with + spacing)
    draw.text((pro_x, logo_y), "PRO", fill=brand_green, font=font_logo)
    
    # Draw White Arc over 'PRO'
    arc_offset_x = 10
    arc_x0 = pro_x - arc_offset_x
    arc_y0 = logo_y - int(font_size * 0.22)
    arc_x1 = pro_x + int(w_pro) + arc_offset_x
    arc_y1 = logo_y + int(font_size * 0.18)
    
    arc_width = 7 # Increased thickness for premium feel at large size
    draw.arc([arc_x0, arc_y0, arc_x1, arc_y1], start=195, end=345, fill=white, width=arc_width)
    
    # Target paths
    paths = [
        "app_icon.png",
        "android-app/app/src/main/res/drawable/ic_launcher.png"
    ]
    
    # Save the 1024x1024 images
    for p in paths:
        # Create directory if not exists
        os.makedirs(os.path.dirname(p) if os.path.dirname(p) else '.', exist_ok=True)
        icon_img.save(p, "PNG")
        print(f"Saved {p} ({width}x{height})")
        
    # Create and save 512x512 version
    icon_512 = icon_img.resize((512, 512), Image.Resampling.LANCZOS)
    icon_512.save("app_icon_512.png", "PNG")
    print("Saved app_icon_512.png (512x512)")

if __name__ == "__main__":
    generate_new_icon()
