"""
페이지 1.5: 모바일 현장 입력 + 이미지 OCR 인식
- 엑셀 없이 폰에서 직접 입력
- 카메라/이미지로 유통기한 자동 인식 (EasyOCR)
- 다중 상품 입력 → QR 라벨 PDF 즉시 생성
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import io
import re
from datetime import date, datetime
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

from utils.style import inject_css, hero, card_start, card_end, stat_badges, icon, footer
from utils import db

st.set_page_config(page_title="모바일 입력 | 칼퇴보장 QR 라벨기", page_icon="📱", layout="wide")
inject_css()

# 사이드바 로고는 inject_css()에서 자동 주입

# ── 모바일 최적화 CSS ──
st.markdown("""
<style>
/* 모바일 큰 버튼 */
.mobile-btn .stButton > button {
    width: 100% !important;
    min-height: 56px !important;
    font-size: 1.1rem !important;
    border-radius: 14px !important;
    font-weight: 600 !important;
}

/* 입력 필드 크게 */
.stTextInput input, .stNumberInput input, .stDateInput input {
    font-size: 1rem !important;
    padding: 0.6rem !important;
}

/* 상품 카드 */
.item-card {
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    border-radius: 14px;
    padding: 0.75rem;
    margin-bottom: 0.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.item-card .name { font-weight: 600; color: #111827; }
.item-card .sub { font-size: 0.8rem; color: #6b7280; }

/* OCR 결과 */
.ocr-result {
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    border-radius: 14px;
    padding: 1rem;
    margin: 0.5rem 0;
}
.ocr-date {
    font-size: 1.5rem;
    font-weight: 700;
    color: #1e40af;
    text-align: center;
    margin: 0.5rem 0;
}
</style>
""", unsafe_allow_html=True)

hero("모바일 현장 입력", "엑셀 없이 폰으로 즉석 입력 · 사진으로 유통기한 자동 인식")

# ══════════════════════════════════════════════════════════════════════
# 폼텍 규격 & 유틸
# ══════════════════════════════════════════════════════════════════════
LABEL_PRESETS = {
    "폼텍 24칸 (3×8)": {"cols": 3, "rows": 8, "label_w": 63.5, "label_h": 33.9, "margin_left": 7.1, "margin_top": 12.0, "gap_x": 2.54, "gap_y": 0.0},
    "폼텍 40칸 (4×10)": {"cols": 4, "rows": 10, "label_w": 47.5, "label_h": 26.9, "margin_left": 8.5, "margin_top": 11.0, "gap_x": 2.0, "gap_y": 0.0},
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
    if not expiry_str or pd.isna(expiry_str) or str(expiry_str).strip() == "":
        return None
    try:
        return (pd.to_datetime(str(expiry_str)).date() - date.today()).days
    except Exception:
        return None


def build_pdf_simple(records, preset) -> bytes:
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

        qr_data = str(rec.get("qr", ""))
        if not qr_data:
            continue

        d_day = calc_d_day(rec.get("expiry", ""))
        is_urgent = d_day is not None and d_day <= 3

        # 위험 표시
        if is_urgent:
            c.setStrokeColor(COLOR_DANGER)
            c.setLineWidth(1.5)
            c.rect(x + 0.5 * mm, y + 0.5 * mm, lw - 1 * mm, lh - 1 * mm, stroke=1, fill=0)
            c.setFillColor(HexColor("#FEE2E2"))
            c.rect(x + 0.5 * mm, y + lh - 4.5 * mm, lw - 1 * mm, 4 * mm, stroke=0, fill=1)
            c.setFillColor(COLOR_DANGER)
            c.setFont("Helvetica-Bold", 6)
            bt = f"EXPIRED ({-d_day}d)" if d_day < 0 else f"D-{d_day} URGENT"
            c.drawString(x + (lw - c.stringWidth(bt, "Helvetica-Bold", 6)) / 2, y + lh - 3.8 * mm, bt)
            c.setFillColor(black)

        # QR
        pad = 1.5 * mm
        top_b = 4 * mm if is_urgent else 0
        text_h = 3.5 * mm
        exp_h = 3 * mm if (d_day is not None and not is_urgent) else 0
        qr_side = min(lw - pad * 2, lh - pad * 2 - text_h - exp_h - top_b)
        qr_x = x + (lw - qr_side) / 2
        qr_y = y + pad + text_h + exp_h

        qr_color = "#DC2626" if is_urgent else "black"
        c.drawImage(pil_to_reader(make_qr(qr_data, color=qr_color)), qr_x, qr_y, width=qr_side, height=qr_side)

        # 상품명
        name = str(rec.get("name", qr_data))[:20]
        c.setFont("Helvetica", 6.5)
        c.setFillColor(COLOR_DANGER if is_urgent else black)
        tw = c.stringWidth(name, "Helvetica", 6.5)
        c.drawString(x + (lw - tw) / 2, y + 1 * mm + exp_h, name)
        c.setFillColor(black)

        # 유통기한
        if d_day is not None and not is_urgent:
            exp_str = str(rec.get("expiry", ""))[:10]
            c.setFont("Helvetica", 5.5)
            c.setFillColor(COLOR_GRAY)
            el = f"EXP {exp_str} (D-{d_day})"
            c.drawString(x + (lw - c.stringWidth(el, "Helvetica", 5.5)) / 2, y + 1 * mm, el)
            c.setFillColor(black)

    c.save()
    return buf.getvalue()


# ══════════════════════════════════════════════════════════════════════
# OCR 함수
# ══════════════════════════════════════════════════════════════════════
# 날짜 패턴 정규식
DATE_PATTERNS = [
    (r'(\d{4})[.\-/\s](\d{1,2})[.\-/\s](\d{1,2})', 'YYYY-MM-DD'),
    (r'(\d{2})[.\-/\s](\d{1,2})[.\-/\s](\d{1,2})', 'YY-MM-DD'),
    (r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일', 'YYYY년MM월DD일'),
    (r'EXP[:\s]*(\d{4})(\d{2})(\d{2})', 'EXP:YYYYMMDD'),
    (r'EXP[:\s]*(\d{2})(\d{2})(\d{2})', 'EXP:YYMMDD'),
    (r'(\d{4})(\d{2})(\d{2})', 'YYYYMMDD'),
]


def extract_dates_from_text(text: str) -> list[str]:
    """텍스트에서 날짜 패턴을 찾아 YYYY-MM-DD 형식으로 반환."""
    dates = []
    for pattern, fmt in DATE_PATTERNS:
        for m in re.finditer(pattern, text):
            try:
                groups = m.groups()
                y, mo, d = int(groups[0]), int(groups[1]), int(groups[2])
                if y < 100:
                    y += 2000
                if 1 <= mo <= 12 and 1 <= d <= 31 and 2020 <= y <= 2040:
                    date_str = f"{y:04d}-{mo:02d}-{d:02d}"
                    if date_str not in dates:
                        dates.append(date_str)
            except (ValueError, IndexError):
                continue
    return dates


def run_ocr(image: Image.Image) -> tuple[str, list[str]]:
    """EasyOCR로 이미지에서 텍스트 추출 → 날짜 패턴 파싱."""
    try:
        import easyocr
    except ImportError:
        return "", []

    import numpy as np
    img_array = np.array(image)

    # EasyOCR 리더 (캐싱)
    if "ocr_reader" not in st.session_state:
        with st.spinner("AI 모델 로딩 중... (최초 1회만)"):
            st.session_state["ocr_reader"] = easyocr.Reader(["ko", "en"], gpu=False)

    reader = st.session_state["ocr_reader"]
    results = reader.readtext(img_array)
    full_text = " ".join([r[1] for r in results])
    dates = extract_dates_from_text(full_text)
    return full_text, dates


# ══════════════════════════════════════════════════════════════════════
# 세션 상태 초기화
# ══════════════════════════════════════════════════════════════════════
if "mobile_items" not in st.session_state:
    st.session_state["mobile_items"] = []

items = st.session_state["mobile_items"]

# ══════════════════════════════════════════════════════════════════════
# 탭 구성
# ══════════════════════════════════════════════════════════════════════
tab_manual, tab_ocr, tab_bulk = st.tabs([
    "직접 입력",
    "사진 인식 (OCR)",
    "대량 생성",
])

# ── 탭 1: 직접 입력 ──
with tab_manual:
    card_start("상품 정보 입력")

    item_id = st.text_input("관리번호 (고유)", placeholder="예: MILK-001", key="m_id")
    item_name = st.text_input("상품명", placeholder="예: 서울우유 1L", key="m_name")

    mc1, mc2 = st.columns(2)
    with mc1:
        item_expiry = st.date_input("유통기한", value=None, key="m_expiry")
    with mc2:
        item_loc = st.text_input("보관위치", placeholder="예: 냉장고A 2단", key="m_loc")

    item_cat = st.text_input("카테고리", placeholder="예: 유제품", key="m_cat")

    st.markdown('<div class="mobile-btn">', unsafe_allow_html=True)
    if st.button("목록에 추가", type="primary", use_container_width=True, key="add_item"):
        if not item_id or not item_name:
            st.error("관리번호와 상품명은 필수입니다.")
        else:
            exp_str = item_expiry.strftime("%Y-%m-%d") if item_expiry else ""
            items.append({
                "id": item_id, "name": item_name,
                "expiry": exp_str, "location": item_loc,
                "category": item_cat,
            })
            st.session_state["mobile_items"] = items
            st.success(f"'{item_name}' 추가 완료 (총 {len(items)}건)")
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    card_end()

# ── 탭 2: 사진 인식 (OCR) ──
with tab_ocr:
    card_start(f"{icon('photo_camera', 20, '#3182f6')} 사진으로 유통기한 자동 인식")
    st.markdown(f"""
    <div class="toss-alert toss-alert-info">
        {icon("photo_camera", 20, "#0969da")}
        <span>상품 뒷면의 유통기한이 적힌 부분을 찍거나 이미지를 올려주세요.<br>
        <b>AI가 날짜를 자동으로 읽어냅니다.</b> (EasyOCR · 무료 · 오프라인)</span>
    </div>
    """, unsafe_allow_html=True)

    # 이미지 입력 (카메라 또는 파일)
    input_method = st.radio("입력 방법", [
        "이미지 파일 업로드",
        "카메라 촬영",
    ], horizontal=True, key="ocr_method")

    img = None
    if "카메라" in input_method:
        cam_img = st.camera_input("카메라로 유통기한 촬영", key="ocr_cam")
        if cam_img:
            img = Image.open(cam_img)
    else:
        uploaded_img = st.file_uploader("이미지 파일", type=["jpg", "jpeg", "png", "bmp"], key="ocr_file")
        if uploaded_img:
            img = Image.open(uploaded_img)

    if img:
        st.image(img, caption="업로드된 이미지", use_container_width=True)

        # OCR 실행
        try:
            import easyocr
            ocr_available = True
        except ImportError:
            ocr_available = False

        if ocr_available:
            with st.spinner("AI가 글자를 읽고 있습니다..."):
                full_text, dates = run_ocr(img)

            if full_text:
                with st.expander("인식된 전체 텍스트", expanded=False):
                    st.code(full_text)

            if dates:
                st.markdown(f"""
                <div class="ocr-result">
                    <div style="text-align:center; font-size:0.85rem; color:#1e40af; font-weight:500;">
                        {icon("task_alt", 20, "#1e40af")} 유통기한을 인식했습니다!
                    </div>
                    <div class="ocr-date">{dates[0]}</div>
                </div>
                """, unsafe_allow_html=True)

                if len(dates) > 1:
                    st.info(f"여러 날짜가 감지되었습니다: {', '.join(dates)}")

                # 자동 입력 폼
                st.divider()
                st.markdown(f'<div style="font-size:1.15rem; font-weight:800; color:#191f28; margin:2rem 0 0.75rem; display:flex; align-items:center; gap:8px;">{icon("edit", 24, "#3182f6", 600)} 인식된 날짜로 상품 등록</div>', unsafe_allow_html=True)
                ocr_id = st.text_input("관리번호", placeholder="예: PROD-001", key="ocr_id")
                ocr_name = st.text_input("상품명", placeholder="예: 매일우유 900ml", key="ocr_name")
                selected_date = st.selectbox("인식된 유통기한", dates, key="ocr_date")
                ocr_loc = st.text_input("보관위치", placeholder="예: 냉장고B", key="ocr_loc")

                st.markdown('<div class="mobile-btn">', unsafe_allow_html=True)
                if st.button("이 상품을 목록에 추가", type="primary", use_container_width=True, key="ocr_add"):
                    if not ocr_id or not ocr_name:
                        st.error("관리번호와 상품명은 필수입니다.")
                    else:
                        items.append({
                            "id": ocr_id, "name": ocr_name,
                            "expiry": selected_date, "location": ocr_loc,
                            "category": "",
                        })
                        st.session_state["mobile_items"] = items
                        st.success(f"'{ocr_name}' 추가 (유통기한: {selected_date})")
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.warning("날짜 패턴을 찾지 못했습니다. 직접 입력해주세요.")
                st.caption("지원 형식: 2026.04.01, 2026-04-01, 2026년4월1일, EXP:20260401 등")
        else:
            st.markdown(f"""
            <div class="toss-alert toss-alert-warning">
                {icon("warning", 20, "#9a6700")}
                <span><b>EasyOCR이 설치되지 않았습니다.</b><br>
                터미널에서 <code>pip install easyocr</code> 를 실행해주세요.<br>
                설치 후 페이지를 새로고침하면 OCR 기능을 사용할 수 있습니다.</span>
            </div>
            """, unsafe_allow_html=True)

            # OCR 없이 수동 날짜 입력
            st.divider()
            st.markdown(f'<div style="font-size:1.15rem; font-weight:800; color:#191f28; margin:2rem 0 0.75rem; display:flex; align-items:center; gap:8px;">{icon("edit", 24, "#3182f6", 600)} 수동으로 직접 입력</div>', unsafe_allow_html=True)
            manual_date = st.text_input("유통기한 직접 입력 (YYYY-MM-DD)", key="ocr_manual_date")
            if manual_date:
                dates_found = extract_dates_from_text(manual_date)
                if dates_found:
                    st.success(f"입력된 날짜: {dates_found[0]}")

    card_end()

# ── 탭 3: 대량 생성 ──
with tab_bulk:
    card_start(f"{icon('tag', 20, '#3182f6')} 대량 자동 생성")
    st.markdown(f"""
    <div class="toss-alert toss-alert-info">
        {icon("info", 20, "#0969da")}
        <span><b>귀찮음 제로 모드</b> — 상품명과 개수만 입력하세요!<br>
        자동으로 우유_01, 우유_02, ... 고유번호가 생성됩니다.</span>
    </div>
    """, unsafe_allow_html=True)

    bulk_name = st.text_input("상품명", value="상품", key="bulk_name")
    bulk_count = st.number_input("개수", min_value=1, max_value=500, value=10, key="bulk_count")
    bulk_expiry = st.date_input("유통기한 (전체 동일)", value=None, key="bulk_expiry")

    st.markdown('<div class="mobile-btn">', unsafe_allow_html=True)
    if st.button(f"{bulk_count}개 자동 생성", type="primary", use_container_width=True, key="bulk_gen"):
        digits = len(str(bulk_count))
        exp_str = bulk_expiry.strftime("%Y-%m-%d") if bulk_expiry else ""
        for i in range(1, int(bulk_count) + 1):
            num = str(i).zfill(digits)
            items.append({
                "id": f"{bulk_name}_{num}", "name": f"{bulk_name}_{num}",
                "expiry": exp_str, "location": "", "category": "",
            })
        st.session_state["mobile_items"] = items
        st.success(f"{bulk_count}개 생성 완료! (총 {len(items)}건)")
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    card_end()

# ══════════════════════════════════════════════════════════════════════
# 입력된 상품 목록 & PDF 생성
# ══════════════════════════════════════════════════════════════════════
st.divider()

if items:
    card_start(f"{icon('smartphone', 20, '#3182f6')} 입력된 상품 목록 ({len(items)}건)")

    for i, item in enumerate(items):
        d_day = calc_d_day(item.get("expiry", ""))
        d_day_text = ""
        d_day_color = "#6b7280"
        if d_day is not None:
            if d_day < 0:
                d_day_text = f"<span style='color:#DC2626; font-weight:700;'>EXPIRED</span>"
            elif d_day <= 3:
                d_day_text = f"<span style='color:#DC2626; font-weight:700;'>D-{d_day}</span>"
            elif d_day <= 7:
                d_day_text = f"<span style='color:#F59E0B; font-weight:600;'>D-{d_day}</span>"
            else:
                d_day_text = f"<span style='color:#16A34A;'>D-{d_day}</span>"

        exp_display = item.get("expiry", "") or "-"
        st.markdown(f"""
        <div class="item-card">
            <div>
                <div class="name">{item['name']}</div>
                <div class="sub">{item['id']} · EXP: {exp_display} {d_day_text} · {item.get('location', '') or '-'}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # 삭제 옵션
    col_del1, col_del2 = st.columns(2)
    with col_del1:
        del_idx = st.number_input("삭제할 번호 (1부터)", min_value=1, max_value=max(1, len(items)), value=1, key="del_idx")
    with col_del2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("해당 항목 삭제", key="del_one"):
            items.pop(int(del_idx) - 1)
            st.session_state["mobile_items"] = items
            st.rerun()

    if st.button("전체 초기화", key="del_all"):
        st.session_state["mobile_items"] = []
        st.rerun()

    card_end()

    # ── PDF 생성 ──
    card_start(f"{icon('download', 20, '#3182f6')} 라벨 PDF 생성")

    preset_name = st.selectbox("라벨지 규격", list(LABEL_PRESETS.keys()), key="pdf_preset")
    preset = LABEL_PRESETS[preset_name]
    per_page = preset["cols"] * preset["rows"]
    total = len(items)
    pages = -(-total // per_page)

    stat_badges([(str(total), "총 라벨"), (str(per_page), "페이지당"), (str(pages), "총 페이지")])

    # records 변환
    records = [{"qr": it["id"], "name": it["name"], "expiry": it.get("expiry", "")} for it in items]
    pdf_bytes = build_pdf_simple(records, preset)

    st.markdown('<div class="big-btn-wrap mobile-btn">', unsafe_allow_html=True)
    st.download_button(
        label=f"PDF 라벨 생성 (무료) — {pages}페이지 · {total}라벨",
        data=pdf_bytes, file_name="qr_labels.pdf", mime="application/pdf",
        use_container_width=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # DB 등록 옵션
    if st.checkbox("재고관리 DB에도 등록", key="db_register"):
        if st.button("DB 일괄 등록", type="primary", use_container_width=True, key="db_save"):
            for it in items:
                db.upsert_item({
                    "item_id": it["id"], "name": it["name"],
                    "category": it.get("category", ""),
                    "expiry_date": it.get("expiry", ""),
                    "location": it.get("location", ""),
                    "stock": 1, "min_stock": 5, "status": "정상",
                })
                db.add_log(it["id"], "입고", 1, note="모바일 등록")
            st.success(f"{total}건 DB 등록 완료!")

    card_end()
else:
    st.markdown(f"""
    <div class="toss-card" style="text-align:center; color:#6b7280;">
        <p style="margin:0;">{icon("edit", 40, "#b0b8c1")}</p>
        <p style="font-weight:500; color:#374151; margin:0.5rem 0 0.25rem;">
            위 탭에서 상품을 입력하세요
        </p>
        <p style="font-size:0.8rem; margin:0;">
            직접 입력 · 사진 OCR · 대량 생성 중 선택
        </p>
    </div>
    """, unsafe_allow_html=True)

# ── 보안 배너 ──
st.markdown(f"""
<div class="security-banner">
    {icon("lock", 20, "#1a7f37")}
    <span>입력한 데이터는 브라우저에서만 처리됩니다. 외부 서버로 전송되지 않습니다.</span>
</div>
""", unsafe_allow_html=True)

footer()
