"""대시보드에 샘플 엑셀을 자동 업로드하고 스크린샷 캡처 (652x488)"""
import os
from playwright.sync_api import sync_playwright
from PIL import Image

HTML_PATH = os.path.abspath("dashboard.html")
EXCEL_PATH = os.path.abspath("sample_capture.xlsx")
OUT_PATH = os.path.abspath("kmong_main.png")

# 652x488 비율 = 1.336:1
# 뷰포트를 이 비율에 맞추고 2x 스케일로 선명하게 캡처
VW, VH = 652, 488

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": VW, "height": VH}, device_scale_factor=2)

    page.goto(f"file:///{HTML_PATH.replace(os.sep, '/')}")
    page.wait_for_timeout(1000)

    # 파일 업로드
    page.set_input_files("#fileInput", EXCEL_PATH)
    page.wait_for_timeout(3500)

    # 위젯 관리바 숨기기 (깔끔하게)
    page.evaluate("document.querySelector('.manage-bar').style.display='none'")
    page.wait_for_timeout(200)

    # 뷰포트 크기 그대로 캡처 (2x 해상도)
    page.screenshot(path=OUT_PATH, full_page=False)
    browser.close()

# 정확히 652x488로 리사이즈
img = Image.open(OUT_PATH)
img = img.resize((652, 488), Image.LANCZOS)
img.save(OUT_PATH, quality=95)
print(f"캡처 완료: {OUT_PATH} ({img.size[0]}x{img.size[1]})")
