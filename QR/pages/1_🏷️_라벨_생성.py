"""
라벨 생성 — 토스 모바일 스타일
엑셀 업로드 → QR 대량 생성 → 유통기한 D-Day → 폼텍 PDF
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import io
from datetime import date
from typing import Optional
import pandas as pd
import qrcode
import streamlit as st
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from utils.style import inject_css, hero, card_start, card_end, stat_badges, footer, icon
from utils import db

st.set_page_config(page_title="라벨 생성", page_icon="📎", layout="wide")
inject_css()

# 사이드바 로고는 inject_css()에서 자동 주입

# ── 폼텍 규격 ──
LABEL_PRESETS = {
    "24칸 (3×8) · LQ-3105 — 가장 많이 쓰임": {"cols": 3, "rows": 8, "label_w": 63.5, "label_h": 33.9, "margin_left": 7.1, "margin_top": 12.0, "gap_x": 2.54, "gap_y": 0.0},
    "21칸 (3×7) · LQ-3107 — 큰 글씨": {"cols": 3, "rows": 7, "label_w": 63.5, "label_h": 38.1, "margin_left": 7.1, "margin_top": 15.1, "gap_x": 2.54, "gap_y": 0.0},
    "40칸 (4×10) · LQ-3112 — 소형": {"cols": 4, "rows": 10, "label_w": 47.5, "label_h": 26.9, "margin_left": 8.5, "margin_top": 11.0, "gap_x": 2.0, "gap_y": 0.0},
    "65칸 (5×13) · LQ-3100 — 미니": {"cols": 5, "rows": 13, "label_w": 38.1, "label_h": 21.2, "margin_left": 4.7, "margin_top": 11.0, "gap_x": 0.0, "gap_y": 0.0},
}

COLOR_DANGER = HexColor("#DC2626")
COLOR_GRAY = HexColor("#6B7280")


def make_qr(data: str, box_size: int = 6, color: str = "black") -> Image.Image:
    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=box_size, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    return qr.make_image(fill_color=color, back_color="white").convert("RGB")


def pil_to_reader(img: Image.Image) -> ImageReader:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return ImageReader(buf)


def calc_d_day(expiry_str) -> Optional[int]:
    if not expiry_str or pd.isna(expiry_str):
        return None
    try:
        return (pd.to_datetime(str(expiry_str)).date() - date.today()).days
    except Exception:
        return None


def build_pdf(records, preset, show_text=True, show_expiry=False, qr_prefix="", font_size_pt=7) -> bytes:
    cols, rows = preset["cols"], preset["rows"]
    per_page = cols * rows
    lw, lh = preset["label_w"] * mm, preset["label_h"] * mm
    ml, mt = preset["margin_left"] * mm, preset["margin_top"] * mm
    gx, gy = preset["gap_x"] * mm, preset["gap_y"] * mm
    _, page_h = A4

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)

    for idx, rec in enumerate(records):
        slot = idx % per_page
        if idx > 0 and slot == 0:
            c.showPage()

        col_i = slot % cols
        row_i = slot // cols
        x = ml + col_i * (lw + gx)
        y = page_h - mt - (row_i + 1) * lh - row_i * gy

        qr_data = qr_prefix + str(rec.get("qr", ""))
        if not qr_data:
            continue

        d_day = calc_d_day(rec.get("expiry", "")) if show_expiry else None
        is_expired = d_day is not None and d_day < 0
        is_danger = d_day is not None and 0 <= d_day <= 3
        is_warning = d_day is not None and 3 < d_day <= 7
        is_urgent = is_expired or is_danger

        if show_expiry and is_urgent:
            c.setStrokeColor(COLOR_DANGER)
            c.setLineWidth(1.5)
            c.rect(x + 0.5 * mm, y + 0.5 * mm, lw - 1 * mm, lh - 1 * mm, stroke=1, fill=0)
            c.setFillColor(COLOR_DANGER if is_expired else HexColor("#FEE2E2"))
            c.rect(x + 0.5 * mm, y + lh - 4.5 * mm, lw - 1 * mm, 4 * mm, stroke=0, fill=1)
            c.setFillColor(white if is_expired else COLOR_DANGER)
            bfs = min(6, font_size_pt - 1)
            c.setFont("Helvetica-Bold", bfs)
            bt = f"EXPIRED ({-d_day}d)" if is_expired else f"D-{d_day} URGENT"
            c.drawString(x + (lw - c.stringWidth(bt, "Helvetica-Bold", bfs)) / 2, y + lh - 3.8 * mm, bt)
            c.setFillColor(black)
        elif show_expiry and is_warning:
            c.setStrokeColor(HexColor("#F59E0B"))
            c.setLineWidth(1)
            c.rect(x + 0.5 * mm, y + 0.5 * mm, lw - 1 * mm, lh - 1 * mm, stroke=1, fill=0)
            c.setFillColor(HexColor("#FFFBEB"))
            c.rect(x + 0.5 * mm, y + lh - 4.5 * mm, lw - 1 * mm, 4 * mm, stroke=0, fill=1)
            c.setFillColor(HexColor("#92400E"))
            bfs = min(6, font_size_pt - 1)
            c.setFont("Helvetica-Bold", bfs)
            bt = f"D-{d_day}"
            c.drawString(x + (lw - c.stringWidth(bt, "Helvetica-Bold", bfs)) / 2, y + lh - 3.8 * mm, bt)
            c.setFillColor(black)

        pad = 1.5 * mm
        top_b = 4 * mm if (show_expiry and d_day is not None and d_day <= 7) else 0
        text_h = 3.5 * mm if show_text else 0
        exp_h = 3 * mm if (show_expiry and d_day is not None and d_day > 7) else 0
        qr_side = min(lw - pad * 2, lh - pad * 2 - text_h - exp_h - top_b)
        qr_x = x + (lw - qr_side) / 2
        qr_y = y + pad + text_h + exp_h

        qr_color = "#DC2626" if is_urgent else "black"
        c.drawImage(pil_to_reader(make_qr(qr_data, color=qr_color)), qr_x, qr_y, width=qr_side, height=qr_side)

        fs = min(font_size_pt, 5.5 if cols >= 5 else (6.5 if cols >= 4 else font_size_pt))
        if show_text:
            label = str(rec.get("text", rec.get("qr", "")))
            max_ch = max(8, int(lw / (1.8 * mm)))
            if len(label) > max_ch:
                label = label[: max_ch - 2] + ".."
            c.setFont("Helvetica", fs)
            c.setFillColor(COLOR_DANGER if is_urgent else black)
            tw = c.stringWidth(label, "Helvetica", fs)
            c.drawString(x + (lw - tw) / 2, y + 1 * mm + exp_h, label)
            c.setFillColor(black)

        if show_expiry and d_day is not None and d_day > 7:
            exp_str = str(rec.get("expiry", ""))[:10]
            efs = fs - 1
            c.setFont("Helvetica", efs)
            c.setFillColor(COLOR_GRAY)
            el = f"EXP {exp_str} (D-{d_day})"
            c.drawString(x + (lw - c.stringWidth(el, "Helvetica", efs)) / 2, y + 1 * mm, el)
            c.setFillColor(black)

    c.save()
    return buf.getvalue()


# ══════════════════════════════════════════════════════════════════════
# UI
# ══════════════════════════════════════════════════════════════════════

hero("QR 라벨 만들기", "엑셀 업로드 또는 직접 입력 → 폼텍 규격 PDF 즉시 생성")

# ── 파일 업로드 ──
st.markdown(f"""
<div style="font-size:1.15rem; font-weight:800; color:#191f28; margin:1.5rem 0 0.75rem; display:flex; align-items:center; gap:8px;">
    {icon("upload_file", 24, "#3182f6", 600)} 파일 업로드
</div>
""", unsafe_allow_html=True)

uploaded = st.file_uploader("엑셀(.xlsx) 또는 CSV 파일", type=["xlsx", "xls", "csv"], label_visibility="collapsed")

# 샘플 다운로드
sample_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "sample_input.xlsx")
if os.path.exists(sample_path):
    with open(sample_path, "rb") as f:
        st.download_button(
            "샘플 엑셀 다운로드 — 바로 테스트 가능",
            data=f.read(), file_name="sample_input.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

if not uploaded:
    # 안내 카드
    st.markdown(f"""
    <div class="toss-card" style="text-align:center; padding:2.5rem 1.5rem;">
        <div style="width:56px; height:56px; border-radius:16px; background:#f2f4f6;
                    display:inline-flex; align-items:center; justify-content:center; margin-bottom:0.75rem;">
            {icon("description", 32, "#8b95a1")}
        </div>
        <div style="font-size:1.05rem; font-weight:700; color:#191f28; margin-bottom:0.3rem;">
            엑셀 또는 CSV 파일을 올려주세요
        </div>
        <div style="font-size:0.88rem; color:#8b95a1; line-height:1.6;">
            QR코드로 만들 데이터가 포함된 파일<br>
            <b>유통기한 열</b>이 있으면 D-Day가 라벨에 자동 표시됩니다
        </div>
    </div>
    """, unsafe_allow_html=True)
    footer()
    st.stop()

# ── 파일 파싱 ──
try:
    df = pd.read_csv(uploaded) if uploaded.name.endswith(".csv") else pd.read_excel(uploaded, engine="openpyxl")
except Exception as e:
    st.error(f"파일을 읽을 수 없습니다: {e}")
    st.stop()

if df.empty:
    st.warning("빈 파일입니다.")
    st.stop()

st.markdown(f"""
<div class="toss-alert toss-alert-success">
    {icon("check_circle", 20, "#1a7f37")}
    <span><b>{len(df)}행 × {len(df.columns)}열</b> 로드 완료</span>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# 설정
# ══════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div style="font-size:1.15rem; font-weight:800; color:#191f28; margin:2rem 0 0.75rem; display:flex; align-items:center; gap:8px;">
    {icon("tune", 24, "#3182f6", 600)} 설정
</div>
""", unsafe_allow_html=True)

columns = list(df.columns)

col_l, col_r = st.columns(2)

with col_l:
    qr_col = st.selectbox("QR코드에 넣을 열", columns, index=0)
    show_text = st.checkbox("QR 아래 텍스트 표시", value=True)
    text_col = st.selectbox("표시할 텍스트 열", columns, index=min(1, len(columns) - 1)) if show_text and len(columns) > 1 else qr_col

    expiry_options = ["사용 안 함"] + columns
    expiry_sel = st.selectbox(f"유통기한 열 (D-Day 자동 표시)", expiry_options)
    show_expiry = expiry_sel != "사용 안 함"

with col_r:
    preset_name = st.selectbox("라벨지 규격", list(LABEL_PRESETS.keys()))
    font_size = st.slider("폰트 크기 (pt)", min_value=5, max_value=12, value=7)

    use_url = st.checkbox("QR에 관리 URL 포함", value=False)
    qr_prefix = ""
    if use_url:
        qr_prefix = st.text_input("서비스 URL", value="http://localhost:8501/QR_스캔?id=")

preset = LABEL_PRESETS[preset_name]
per_page = preset["cols"] * preset["rows"]
total = len(df)
pages = -(-total // per_page)

# ── 유통기한 분석 ──
if show_expiry:
    expired_n = sum(1 for _, r in df.iterrows() if (d := calc_d_day(r.get(expiry_sel))) is not None and d < 0)
    danger_n = sum(1 for _, r in df.iterrows() if (d := calc_d_day(r.get(expiry_sel))) is not None and 0 <= d <= 3)
    warning_n = sum(1 for _, r in df.iterrows() if (d := calc_d_day(r.get(expiry_sel))) is not None and 3 < d <= 7)

    stat_badges([(str(total), "총 라벨"), (str(pages), "페이지"), (str(expired_n), "만료"), (str(danger_n), "긴급"), (str(warning_n), "주의")])

    if expired_n > 0:
        st.markdown(f"""
        <div class="toss-alert toss-alert-danger">
            {icon("error", 20, "#d1242f")}
            <span>만료 상품 <b>{expired_n}건</b> — 라벨에 EXPIRED 경고가 자동 표시됩니다.</span>
        </div>
        """, unsafe_allow_html=True)
else:
    stat_badges([(str(total), "총 라벨"), (str(per_page), "페이지당"), (str(pages), "총 페이지")])

with st.expander("데이터 미리보기"):
    st.dataframe(df, use_container_width=True, height=250)

# ══════════════════════════════════════════════════════════════════════
# 미리보기
# ══════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div style="font-size:1.15rem; font-weight:800; color:#191f28; margin:2rem 0 0.75rem; display:flex; align-items:center; gap:8px;">
    {icon("preview", 24, "#3182f6", 600)} QR 미리보기
</div>
""", unsafe_allow_html=True)

preview_n = min(6, total)
cols_ui = st.columns(min(3, preview_n))
for i in range(preview_n):
    with cols_ui[i % len(cols_ui)]:
        row_data = df.iloc[i]
        data = str(row_data[qr_col])
        d_day = calc_d_day(row_data.get(expiry_sel, "")) if show_expiry else None
        is_urgent = d_day is not None and d_day <= 3

        qr_img = make_qr(qr_prefix + data, box_size=4, color="#d1242f" if is_urgent else "black")
        st.image(qr_img, use_container_width=True)

        if show_text:
            st.caption(f"<center>{str(row_data[text_col])[:18]}</center>", unsafe_allow_html=True)

        if d_day is not None:
            if d_day < 0:
                st.markdown(f'<center><span class="badge badge-red">EXPIRED</span></center>', unsafe_allow_html=True)
            elif d_day <= 3:
                st.markdown(f'<center><span class="badge badge-red">D-{d_day}</span></center>', unsafe_allow_html=True)
            elif d_day <= 7:
                st.markdown(f'<center><span class="badge badge-yellow">D-{d_day}</span></center>', unsafe_allow_html=True)
            else:
                st.markdown(f'<center><span class="badge badge-green">D-{d_day}</span></center>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# PDF 생성
# ══════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div style="font-size:1.15rem; font-weight:800; color:#191f28; margin:2rem 0 0.75rem; display:flex; align-items:center; gap:8px;">
    {icon("picture_as_pdf", 24, "#3182f6", 600)} PDF 다운로드
</div>
""", unsafe_allow_html=True)

records = []
for _, row in df.iterrows():
    rec = {"qr": str(row[qr_col]), "text": str(row[text_col])}
    if show_expiry:
        rec["expiry"] = str(row.get(expiry_sel, ""))
    records.append(rec)

pdf_bytes = build_pdf(records, preset, show_text=show_text, show_expiry=show_expiry, qr_prefix=qr_prefix, font_size_pt=font_size)

st.download_button(
    label=f"PDF 다운로드 · {pages}페이지 · {total}라벨",
    data=pdf_bytes, file_name="qr_labels.pdf", mime="application/pdf",
    use_container_width=True,
)

# ── DB 등록 ──
with st.expander("상품 DB에 일괄 등록 (재고 관리용)", expanded=False):
    name_col = st.selectbox("상품명 열", columns, index=min(1, len(columns) - 1), key="db_name")
    db_exp = st.selectbox("유통기한 열", ["없음"] + columns, key="db_exp")
    db_cat = st.selectbox("카테고리 열", ["없음"] + columns, key="db_cat")

    if st.button("DB에 일괄 등록", type="primary", use_container_width=True):
        db.bulk_import_items(
            df, id_col=qr_col, name_col=name_col,
            expiry_col=db_exp if db_exp != "없음" else "",
            category_col=db_cat if db_cat != "없음" else "",
        )
        st.success(f"{total}건 등록 완료!")

# ── 보안 배너 ──
st.markdown(f"""
<div class="security-banner">
    {icon("lock", 20, "#1a7f37")}
    <span>데이터는 브라우저에서만 처리됩니다. 외부 서버로 전송되지 않습니다.</span>
</div>
""", unsafe_allow_html=True)

footer()
