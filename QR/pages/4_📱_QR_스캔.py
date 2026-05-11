"""
페이지 3: QR 스캔 랜딩
모바일에서 QR을 스캔하면 이 페이지가 열림
→ 해당 상품 정보 표시 + 즉시 입고/출고/점검/개봉 처리
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import date
import streamlit as st
from utils.style import inject_css, hero, card_start, card_end, status_badge, icon, footer
from utils import db

st.set_page_config(page_title="QR 스캔 | QR 라벨기", page_icon="📱", layout="wide")
inject_css()

# 사이드바 로고는 inject_css()에서 자동 주입

hero("QR 스캔 조회", "QR코드를 스캔하거나 고유번호를 입력하세요")

# ── URL 쿼리 파라미터 또는 수동 입력 ──
params = st.query_params
item_id = params.get("id", "")

card_start(f"{icon('qr_code_scanner', 20, '#3182f6')} 상품 조회")
item_id = st.text_input("고유번호", value=item_id, placeholder="QR 스캔 또는 직접 입력", key="scan_id")
card_end()

if not item_id:
    st.markdown(f"""
    <div class="toss-card" style="text-align:center; color:#6b7280;">
        <p style="margin:0;">{icon("qr_code_scanner", 48, "#b0b8c1")}</p>
        <p style="font-weight:500; color:#374151; margin:0.5rem 0;">
            스마트폰으로 QR코드를 스캔하면<br>자동으로 상품 정보가 표시됩니다
        </p>
    </div>
    """, unsafe_allow_html=True)
    footer()
    st.stop()

item = db.get_item(item_id)

if item is None:
    st.markdown(f"""
    <div class="toss-alert toss-alert-warning">
        {icon("warning", 20, "#9a6700")}
        <span><b>'{item_id}'</b> 상품을 찾을 수 없습니다.<br>
        재고관리 페이지에서 먼저 등록하거나, 라벨 생성 시 DB 등록을 해주세요.</span>
    </div>
    """, unsafe_allow_html=True)
    footer()
    st.stop()

# ── 상품 정보 카드 ──
card_start(f"{item['name']}")

col1, col2 = st.columns(2)
with col1:
    st.markdown(f"**고유번호:** `{item['item_id']}`")
    st.markdown(f"**카테고리:** {item['category'] or '-'}")
    st.markdown(f"**위치:** {item['location'] or '-'}")
    st.markdown(f"**메모:** {item.get('memo', '') or '-'}")

with col2:
    st.markdown(f"**재고:** {item['stock']}개")
    st.markdown(f"**안전재고:** {item['min_stock']}개")
    st.markdown(f"**상태:** {status_badge(item['status'])}", unsafe_allow_html=True)

    # 재고 부족 알림
    if int(item["stock"]) <= int(item["min_stock"]):
        st.markdown(f"""
        <div class="toss-alert toss-alert-danger">
            {icon("inventory_2", 20, "#d1242f")}
            <span>재고 부족! 주문이 필요합니다.</span>
        </div>
        """, unsafe_allow_html=True)

card_end()

# ── 유통기한 정보 ──
exp = str(item.get("expiry_date", ""))
opened = str(item.get("opened_date", ""))
shelf = int(item.get("opened_shelf_days", 0))

if exp:
    info = db.calc_expiry_status(exp, opened, shelf)
    color_map = {"green": "success", "orange": "warning", "red": "danger", "black": "danger"}
    alert_type = color_map.get(info["color"], "info")

    card_start(f"{icon('event_busy', 20, '#3182f6')} 유통기한 정보")
    st.markdown(f"**유통기한:** {exp} &nbsp; {status_badge(info['label'])}", unsafe_allow_html=True)
    if opened:
        st.markdown(f"**개봉일:** {opened} (사용가능: {shelf}일)")
    if info["alert"]:
        st.markdown(f'<div class="toss-alert toss-alert-{alert_type}">{icon("info", 20)} <span>{info["alert"]}</span></div>', unsafe_allow_html=True)

    # FIFO 경고
    fifo = db.get_fifo_warning(item_id)
    if fifo:
        st.markdown(f'<div class="toss-alert toss-alert-info">{icon("info", 20, "#0969da")} <span>{fifo}</span></div>', unsafe_allow_html=True)
    card_end()

# ── 빠른 액션 버튼 ──
card_start(f"{icon('task_alt', 20, '#3182f6')} 빠른 처리")
worker = st.text_input("작업자", key="scan_worker")

col_a, col_b, col_c, col_d = st.columns(4)

with col_a:
    if st.button("입고 +1", use_container_width=True, key="scan_in"):
        db.adjust_stock(item_id, +1, "입고", worker)
        st.success("입고 +1 완료")
        st.rerun()

with col_b:
    if st.button("출고 -1", use_container_width=True, key="scan_out"):
        db.adjust_stock(item_id, -1, "출고", worker)
        st.success("출고 -1 완료")
        st.rerun()

with col_c:
    if st.button("개봉 기록", use_container_width=True, key="scan_open"):
        db.upsert_item({"item_id": item_id, "opened_date": date.today().strftime("%Y-%m-%d")})
        db.add_log(item_id, "개봉", 0, worker, "개봉일 기록")
        st.success("개봉일 기록 완료")
        st.rerun()

with col_d:
    if st.button("점검 완료", use_container_width=True, key="scan_check"):
        db.add_log(item_id, "점검", 0, worker, "정기 점검 완료")
        st.success("점검 기록 완료")
        st.rerun()

# 수량 지정 입출고
with st.expander("수량 지정 입출고"):
    qty = st.number_input("수량", min_value=1, value=1, key="scan_qty")
    note = st.text_input("비고", key="scan_note")
    qc1, qc2 = st.columns(2)
    with qc1:
        if st.button(f"입고 +{qty}", key="scan_in_n", use_container_width=True):
            db.adjust_stock(item_id, +qty, "입고", worker, note)
            st.success(f"입고 +{qty} 완료")
            st.rerun()
    with qc2:
        if st.button(f"출고 -{qty}", key="scan_out_n", use_container_width=True):
            db.adjust_stock(item_id, -qty, "출고", worker, note)
            st.success(f"출고 -{qty} 완료")
            st.rerun()

card_end()

# ── 이 상품의 이력 ──
logs = db.load_logs()
item_logs = logs[logs["item_id"] == item_id].sort_values("timestamp", ascending=False)

if not item_logs.empty:
    card_start(f"{icon('history', 20, '#3182f6')} 이력 ({len(item_logs)}건)")
    display = item_logs[["timestamp", "action", "quantity", "worker", "note"]].copy()
    display.columns = ["시각", "구분", "수량", "작업자", "비고"]
    st.dataframe(display, use_container_width=True, height=250)
    card_end()

footer()
