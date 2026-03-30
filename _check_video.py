from playwright.sync_api import sync_playwright
from PIL import Image
from io import BytesIO
import os

mp4 = os.path.abspath('ani.mp4').replace('\\', '/')
html_content = f'<html><body style="margin:0;background:#000"><video id="v" src="file:///{mp4}" muted autoplay></video></body></html>'
tmp = os.path.abspath('_tmp_check.html')
with open(tmp, 'w') as f:
    f.write(html_content)

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    page = b.new_page(viewport={'width': 600, 'height': 600})
    page.goto('file:///' + tmp.replace('\\', '/'))
    page.wait_for_timeout(1000)
    buf = page.screenshot()
    b.close()

img = Image.open(BytesIO(buf))
w, h = img.size
points = {
    'top-left(10,10)': img.getpixel((10, 10)),
    'top-right': img.getpixel((w-10, 10)),
    'bottom-left': img.getpixel((10, h-10)),
    'bottom-right': img.getpixel((w-10, h-10)),
    'center': img.getpixel((w//2, h//2)),
}
for k, v in points.items():
    print(f'{k}: #{v[0]:02x}{v[1]:02x}{v[2]:02x}')

os.remove(tmp)
