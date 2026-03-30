"""크몽 메인 이미지 + 서브 이미지 생성 (652x488)"""
import os
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw, ImageFont

HTML_PATH = os.path.abspath("dashboard.html")
EXCEL_PATH = os.path.abspath("sample_capture.xlsx")

def get_font(name, size):
    paths = {
        'bold': 'C:/Windows/Fonts/malgunbd.ttf',
        'regular': 'C:/Windows/Fonts/malgun.ttf',
    }
    try:
        return ImageFont.truetype(paths.get(name, paths['regular']), size)
    except:
        return ImageFont.load_default()

def capture_dashboard(page, theme='midnight', hide_manage=True, full_page=False):
    """테마 변경 후 스크린샷 캡처, PIL Image 반환"""
    if theme != 'midnight':
        page.evaluate(f"document.querySelector('[data-t=\"{theme}\"]').click()")
        page.wait_for_timeout(800)
    if hide_manage:
        page.evaluate("document.querySelector('.manage-bar').style.display='none'")
    page.wait_for_timeout(300)
    buf = page.screenshot(full_page=full_page)
    if hide_manage:
        page.evaluate("document.querySelector('.manage-bar').style.display=''")
    from io import BytesIO
    return Image.open(BytesIO(buf))

def draw_rounded_rect(d, xy, radius, fill):
    x0, y0, x1, y1 = xy
    d.rounded_rectangle(xy, radius=radius, fill=fill)

def add_text_with_shadow(d, pos, text, font, fill, shadow_color=(0,0,0,120), offset=2):
    x, y = pos
    d.text((x+offset, y+offset), text, fill=shadow_color, font=font)
    d.text((x, y), text, fill=fill, font=font)

def make_banner_1(dashboard_img):
    """메인 배너: 대시보드 + 홍보 문구 오버레이"""
    W, H = 652, 488
    img = Image.new('RGBA', (W, H), (0,0,0,0))

    # 대시보드 스크린샷 배경 (약간 어둡게)
    bg = dashboard_img.resize((W, H), Image.LANCZOS).convert('RGBA')
    dark = Image.new('RGBA', (W, H), (0,0,0,140))
    bg = Image.alpha_composite(bg, dark)
    img.paste(bg, (0, 0))

    d = ImageDraw.Draw(img)

    # 상단 배지
    draw_rounded_rect(d, (W//2-80, 30, W//2+80, 58), 14, (0, 161, 93, 230))
    badge_font = get_font('bold', 14)
    d.text((W//2-48, 34), 'HTML 파일 1개', fill=(255,255,255), font=badge_font)

    # 메인 카피
    title_font = get_font('bold', 36)
    sub_font = get_font('bold', 20)
    desc_font = get_font('regular', 13)

    add_text_with_shadow(d, (W//2-160, 80), '엑셀만 올리면', title_font, (255,255,255))
    add_text_with_shadow(d, (W//2-200, 130), '대시보드가 자동완성', title_font, (0, 227, 150))

    # 서브 카피
    d.text((W//2-145, 190), '서버 없이, 설치 없이, 더블클릭만', font=sub_font, fill=(200,200,200))

    # 하단 기능 태그들
    tags = ['8가지 차트', '5가지 테마', '이미지 저장', '드래그 정렬', '그룹 집계']
    tag_font = get_font('bold', 11)
    tag_y = 440
    total_w = len(tags) * 100 + (len(tags)-1) * 8
    start_x = (W - total_w) // 2
    for i, tag in enumerate(tags):
        tx = start_x + i * 108
        draw_rounded_rect(d, (tx, tag_y, tx+100, tag_y+30), 15, (255,255,255,30))
        tw = d.textlength(tag, font=tag_font)
        d.text((tx + (100-tw)//2, tag_y+7), tag, fill=(255,255,255), font=tag_font)

    return img.convert('RGB')

def make_banner_2(dashboard_img):
    """서브 배너: 좌측 문구 + 우측 대시보드"""
    W, H = 652, 488
    img = Image.new('RGB', (W, H), (22, 23, 23))
    d = ImageDraw.Draw(img)

    # 우측에 대시보드 (기울어진 느낌은 어려우니 그냥 축소 배치)
    dash = dashboard_img.resize((380, 285), Image.LANCZOS)
    img.paste(dash, (260, 100))

    # 우측 대시보드 위에 반투명 그라디언트 (좌측에서 오는)
    grad = Image.new('RGBA', (120, 285), (0,0,0,0))
    gd = ImageDraw.Draw(grad)
    for x in range(120):
        alpha = int(255 * (1 - x/120))
        gd.line([(x, 0), (x, 285)], fill=(22, 23, 23, alpha))
    img.paste(Image.alpha_composite(Image.new('RGBA', (120, 285), (0,0,0,0)), grad).convert('RGB'), (260, 100))

    # 좌측 문구
    title_font = get_font('bold', 28)
    sub_font = get_font('bold', 16)
    desc_font = get_font('regular', 12)

    # 초록색 악센트 바
    d.rectangle([30, 80, 36, 160], fill=(0, 227, 150))

    d.text((50, 80), '복잡한 엑셀,', font=title_font, fill=(255,255,255))
    d.text((50, 120), '한눈에 보는', font=title_font, fill=(255,255,255))
    d.text((50, 160), '대시보드로.', font=title_font, fill=(0, 227, 150))

    d.text((50, 220), '파일 하나로 끝나는', font=sub_font, fill=(168,173,183))
    d.text((50, 245), '엑셀 시각화 솔루션', font=sub_font, fill=(168,173,183))

    # 하단 포인트
    features = ['서버 불필요', '데이터 보안', '즉시 시각화']
    for i, f in enumerate(features):
        fy = 310 + i * 32
        d.ellipse([50, fy+4, 60, fy+14], fill=(0, 227, 150))
        d.text((68, fy), f, font=desc_font, fill=(200,200,200))

    # 하단 로고 영역
    d.text((50, 440), 'Dashboard Builder', font=get_font('bold', 14), fill=(100,100,100))

    return img

def make_banner_3(dashboard_imgs):
    """서브 배너: 테마 쇼케이스 (5개 테마 미리보기)"""
    W, H = 652, 488
    img = Image.new('RGB', (W, H), (22, 23, 23))
    d = ImageDraw.Draw(img)

    title_font = get_font('bold', 24)
    sub_font = get_font('regular', 13)

    d.text((W//2-100, 20), '5가지 테마 지원', font=title_font, fill=(255,255,255))
    d.text((W//2-120, 55), '원클릭으로 분위기를 바꿔보세요', font=sub_font, fill=(168,173,183))

    theme_names = ['Midnight', 'Purple', 'Ocean', 'Rose', 'Ember']
    theme_colors = [(0,161,93), (139,92,246), (6,182,212), (244,63,94), (249,115,22)]

    # 5개 테마 미리보기를 2행으로 배치
    # 상단 3개, 하단 2개
    thumb_w, thumb_h = 190, 142
    gap = 12

    # 상단 3개
    for i in range(3):
        tx = 18 + i * (thumb_w + gap)
        ty = 90
        thumb = dashboard_imgs[i].resize((thumb_w, thumb_h), Image.LANCZOS)
        img.paste(thumb, (tx, ty))
        # 테마 이름 + 컬러 도트
        d.ellipse([tx, ty+thumb_h+6, tx+10, ty+thumb_h+16], fill=theme_colors[i])
        d.text((tx+16, ty+thumb_h+4), theme_names[i], font=get_font('regular', 11), fill=(168,173,183))

    # 하단 2개 (중앙 정렬)
    for i in range(2):
        tx = 18 + 100 + i * (thumb_w + gap)
        ty = 260
        thumb = dashboard_imgs[3+i].resize((thumb_w, thumb_h), Image.LANCZOS)
        img.paste(thumb, (tx, ty))
        d.ellipse([tx, ty+thumb_h+6, tx+10, ty+thumb_h+16], fill=theme_colors[3+i])
        d.text((tx+16, ty+thumb_h+4), theme_names[3+i], font=get_font('regular', 11), fill=(168,173,183))

    # 하단 문구
    d.text((W//2-60, 450), 'Dashboard Builder', font=get_font('bold', 12), fill=(80,80,80))

    return img

def make_banner_4(dashboard_img):
    """서브 배너: 기능 하이라이트"""
    W, H = 652, 488
    img = Image.new('RGB', (W, H), (15, 15, 20))
    d = ImageDraw.Draw(img)

    title_font = get_font('bold', 22)
    feat_title = get_font('bold', 14)
    feat_desc = get_font('regular', 11)

    # 상단
    d.text((W//2-80, 20), '이런 기능이?', font=title_font, fill=(0, 227, 150))

    # 중앙에 대시보드 작게
    dash = dashboard_img.resize((280, 210), Image.LANCZOS)
    dx = W//2 - 140
    dy = 60
    img.paste(dash, (dx, dy))

    # 기능 카드 4개 (하단 2x2)
    features = [
        ('자동 분석', '엑셀 구조를 자동 파악\n헤더, 날짜, 금액 인식'),
        ('8가지 차트', '막대/라인/파이/도넛\n영역/산점도/카드/리스트'),
        ('그룹 집계', '카테고리별 합계/건수\n자동 계산'),
        ('이미지 저장', '대시보드를 PNG로\n한 번에 다운로드'),
    ]
    card_w, card_h = 145, 90
    card_gap = 10
    for i, (title, desc) in enumerate(features):
        cx = 85 + (i % 2) * (card_w + card_gap + 120)
        cy = 300 + (i // 2) * (card_h + card_gap)
        draw_rounded_rect(d, (cx, cy, cx+card_w+100, cy+card_h), 10, (32,32,32))
        d.text((cx+12, cy+10), title, font=feat_title, fill=(0, 227, 150))
        d.text((cx+12, cy+35), desc, font=feat_desc, fill=(168,173,183))

    return img

# ===== 메인 실행 =====
print("브라우저 시작...")
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1200, "height": 900}, device_scale_factor=2)

    page.goto(f"file:///{HTML_PATH.replace(os.sep, '/')}")
    page.wait_for_timeout(1000)
    page.set_input_files("#fileInput", EXCEL_PATH)
    page.wait_for_timeout(3500)

    # Midnight 캡처
    print("Midnight 테마 캡처...")
    img_midnight = capture_dashboard(page, 'midnight')

    # 다른 테마들 캡처
    theme_imgs = [img_midnight]
    for t in ['purple', 'ocean', 'rose', 'ember']:
        print(f"{t} 테마 캡처...")
        theme_imgs.append(capture_dashboard(page, t))

    browser.close()

print("배너 1 생성 (메인)...")
b1 = make_banner_1(img_midnight)
b1.save("kmong_main.png")

print("배너 2 생성 (좌측 문구)...")
b2 = make_banner_2(img_midnight)
b2.save("kmong_sub1.png")

print("배너 3 생성 (테마 쇼케이스)...")
b3 = make_banner_3(theme_imgs)
b3.save("kmong_sub2.png")

print("배너 4 생성 (기능 하이라이트)...")
b4 = make_banner_4(img_midnight)
b4.save("kmong_sub3.png")

# 모두 652x488로 리사이즈
for fname in ["kmong_main.png", "kmong_sub1.png", "kmong_sub2.png", "kmong_sub3.png"]:
    im = Image.open(fname)
    if im.size != (652, 488):
        im = im.resize((652, 488), Image.LANCZOS)
        im.save(fname)

print("\n모든 배너 생성 완료!")
print("  kmong_main.png  - 메인 (대시보드 + 홍보문구)")
print("  kmong_sub1.png  - 서브1 (좌측 문구 + 우측 대시보드)")
print("  kmong_sub2.png  - 서브2 (5가지 테마 쇼케이스)")
print("  kmong_sub3.png  - 서브3 (기능 하이라이트)")
