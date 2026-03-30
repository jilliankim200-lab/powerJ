"""고해상도 ICO 생성 + 바탕화면 바로가기"""
import os
from PIL import Image, ImageDraw, ImageFilter

def create_icon():
    sizes = [16, 24, 32, 48, 64, 128, 256]
    images = []

    for sz in sizes:
        # 4배 크기로 그린 후 축소 (안티앨리어싱)
        ss = sz * 4
        img = Image.new('RGBA', (ss, ss), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)

        # 배경: 둥근 사각형 (#00A15D)
        r = ss // 4
        d.rounded_rectangle([0, 0, ss - 1, ss - 1], radius=r, fill=(0, 161, 93, 255))

        # 막대 3개 (흰색) - 비율 조정
        pad_x = ss * 0.25
        pad_b = ss * 0.22  # 하단 패딩
        bar_w = ss * 0.14
        gap = ss * 0.05

        bars = [
            (pad_x, ss * 0.38),                          # bar1: 짧은
            (pad_x + bar_w + gap, ss * 0.56),             # bar2: 긴
            (pad_x + (bar_w + gap) * 2, ss * 0.28),       # bar3: 중간
        ]
        for bx, bh in bars:
            d.rounded_rectangle(
                [bx, ss - pad_b - bh, bx + bar_w, ss - pad_b],
                radius=max(2, ss // 32),
                fill=(255, 255, 255, 255)
            )

        # 고품질 축소
        img = img.resize((sz, sz), Image.LANCZOS)
        images.append(img)

    ico_path = os.path.join(os.path.dirname(__file__), 'dashboard.ico')
    images[-1].save(ico_path, format='ICO', sizes=[(s, s) for s in sizes], append_images=images[:-1])
    print(f'ICO 생성: {ico_path}')
    return ico_path


# 2) 바탕화면 바로가기 생성
def create_shortcut(ico_path):
    try:
        import winshell
        from win32com.client import Dispatch
    except ImportError:
        # winshell 없으면 vbs로 생성
        create_shortcut_vbs(ico_path)
        return

    desktop = winshell.desktop()
    shortcut_path = os.path.join(desktop, 'Dashboard Builder.lnk')
    target = os.path.abspath(os.path.join(os.path.dirname(__file__), 'dashboard.html'))

    shell = Dispatch('WScript.Shell')
    sc = shell.CreateShortCut(shortcut_path)
    sc.Targetpath = target
    sc.WorkingDirectory = os.path.dirname(target)
    sc.IconLocation = ico_path
    sc.save()
    print(f'바로가기 생성: {shortcut_path}')


def create_shortcut_vbs(ico_path):
    import subprocess
    desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
    target = os.path.abspath(os.path.join(os.path.dirname(__file__), 'dashboard.html'))
    shortcut_path = os.path.join(desktop, 'Dashboard Builder.lnk')

    vbs = f'''Set oWS = WScript.CreateObject("WScript.Shell")
Set oLink = oWS.CreateShortCut("{shortcut_path}")
oLink.TargetPath = "{target}"
oLink.WorkingDirectory = "{os.path.dirname(target)}"
oLink.IconLocation = "{ico_path}"
oLink.Save
'''
    vbs_path = os.path.join(os.path.dirname(__file__), '_mkshortcut.vbs')
    with open(vbs_path, 'w', encoding='utf-8') as f:
        f.write(vbs)

    subprocess.run(['cscript', '//nologo', vbs_path], check=True)
    os.remove(vbs_path)
    print(f'바로가기 생성: {shortcut_path}')


if __name__ == '__main__':
    ico = create_icon()
    create_shortcut(ico)
