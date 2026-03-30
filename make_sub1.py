"""kmong_sub1.png - 좌측 굵은 카피 + 우측 대시보드 (Pretendard ExtraBold)"""
import os
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

HTML_PATH = os.path.abspath("dashboard.html")
EXCEL_PATH = os.path.abspath("sample_capture.xlsx")

FONT_DIR = os.path.join(os.environ['LOCALAPPDATA'], 'Microsoft', 'Windows', 'Fonts')

def font(weight, size):
    names = {
        'extrabold': 'Pretendard-ExtraBold.otf',
        'bold': 'Pretendard-Bold.otf',
        'semibold': 'Pretendard-SemiBold.otf',
        'medium': 'Pretendard-Medium.otf',
        'regular': 'Pretendard-Regular.otf',
    }
    return ImageFont.truetype(os.path.join(FONT_DIR, names[weight]), size)

# 대시보드 캡처
print("캡처 중...")
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1200, "height": 900}, device_scale_factor=2)
    page.goto(f"file:///{HTML_PATH.replace(os.sep, '/')}")
    page.wait_for_timeout(1000)
    page.set_input_files("#fileInput", EXCEL_PATH)
    page.wait_for_timeout(3500)
    page.evaluate("document.querySelector('.manage-bar').style.display='none'")
    page.wait_for_timeout(300)
    buf = page.screenshot(full_page=False)
    dashboard_img = Image.open(BytesIO(buf))
    browser.close()

# 배너 생성
W, H = 652, 488
img = Image.new('RGB', (W, H), (22, 23, 23))
d = ImageDraw.Draw(img)

# 우측 대시보드 (약간 축소)
dash = dashboard_img.resize((400, 300), Image.LANCZOS)
img.paste(dash, (245, 95))

# 좌측에서 오는 그라디언트 페이드
grad = Image.new('RGBA', (160, 300), (0,0,0,0))
gd = ImageDraw.Draw(grad)
for x in range(160):
    alpha = int(255 * (1 - x/160) ** 0.8)
    gd.line([(x, 0), (x, 300)], fill=(22, 23, 23, alpha))
fade = Image.alpha_composite(Image.new('RGBA', (160, 300), (0,0,0,0)), grad).convert('RGB')
img.paste(fade, (245, 95))

# 좌측 메인 카피 (Pretendard ExtraBold, 큰 사이즈)
GREEN = (0, 227, 150)
WHITE = (255, 255, 255)
GRAY = (168, 173, 183)
MUTED = (100, 105, 115)

# 초록색 사이드 바
d.rectangle([28, 72, 35, 225], fill=GREEN)

# 메인 타이틀 (Black, 크게, 줄간격 좁게)
f_main = font('extrabold', 46)
f_sub = font('semibold', 16)
f_desc = font('medium', 12)
f_small = font('regular', 11)
f_logo = font('bold', 13)

d.text((46, 65), '복잡한 엑셀,', font=f_main, fill=WHITE)
d.text((46, 118), '한눈에 보는', font=f_main, fill=WHITE)
d.text((46, 171), '대시보드로.', font=f_main, fill=GREEN)

# 서브 카피
d.text((46, 225), '파일 하나로 끝나는', font=f_sub, fill=GRAY)
d.text((46, 250), '엑셀 시각화 솔루션', font=f_sub, fill=GRAY)

# 포인트 리스트
features = ['서버 불필요', '데이터 보안', '즉시 시각화']
for i, feat in enumerate(features):
    fy = 305 + i * 30
    d.ellipse([46, fy+4, 56, fy+14], fill=GREEN)
    d.text((64, fy), feat, font=f_desc, fill=(210, 215, 220))

# 하단 로고
d.text((46, 445), 'Dashboard Builder', font=f_logo, fill=MUTED)

# 하단 우측 태그
tags = ['HTML 1개', '8가지 차트', '5가지 테마']
tx = 380
for i, tag in enumerate(tags):
    ty = 435 + i * 18
    d.text((tx, ty), '#' + tag, font=f_small, fill=MUTED)

img.save("kmong_sub1.png")
print("완료: kmong_sub1.png (652x488)")
