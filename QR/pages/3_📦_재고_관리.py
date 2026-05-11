"""
페이지 2: 재고 관리
상품 목록 조회 · 입출고 처리 · 위치 관리 · 상품 등록/수정/삭제
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime
import streamlit as st
import pandas as pd
from utils.style import inject_css, hero, card_start, card_end, stat_badges, status_badge, icon, footer
from utils import db

st.set_page_config(page_title="재고 관리 | QR 라벨기", page_icon="📦", layout="wide")
inject_css()

# 사이드바 로고는 inject_css()에서 자동 주입

hero("재고 관리", "상품 등록 · 입출고 처리 · 위치 관리 · 재고 현황")

items_df = db.load_items()
total = len(items_df)

# ── 상단 통계 ──
if total > 0:
    total_stock = int(items_df["stock"].sum())
    low = len(items_df[items_df["stock"] <= items_df["min_stock"]])
    zero = len(items_df[items_df["stock"] == 0])
    stat_badges([
        (str(total), "등록 상품"), (str(total_stock), "총 재고"),
        (str(low), "재고 부족"), (str(zero), "재고 없음"),
    ])

# ── 탭 구성 ──
tab_list, tab_inout, tab_add = st.tabs([
    "상품 목록",
    "입고/출고",
    "상품 등록",
])

# ── 탭 1: 상품 목록 ──
with tab_list:
    if total == 0:
        st.markdown(f"""
        <div class="toss-alert toss-alert-info">
            {icon("info", 20, "#0969da")}
            <span>등록된 상품이 없습니다. '상품 등록' 탭이나 '라벨 생성' 페이지에서 등록하세요.</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        # 필터
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            search = st.text_input(f"{icon('search', 16)} 검색 (ID 또는 이름)", key="search")
        with col_f2:
            categories = ["전체"] + sorted(items_df["category"].unique().tolist())
            cat_filter = st.selectbox("카테고리", categories, key="cat_filter")
        with col_f3:
            status_opts = ["전체", "정상", "주의", "위험", "폐기"]
            status_filter = st.selectbox("상태", status_opts, key="status_filter")

        filtered = items_df.copy()
        if search:
            filtered = filtered[
                filtered["item_id"].str.contains(search, case=False, na=False) |
                filtered["name"].str.contains(search, case=False, na=False)
            ]
        if cat_filter != "전체":
            filtered = filtered[filtered["category"] == cat_filter]
        if status_filter != "전체":
            filtered = filtered[filtered["status"] == status_filter]

        # 테이블 표시
        if filtered.empty:
            st.markdown(f"""
            <div class="toss-alert toss-alert-warning">
                {icon("warning", 20, "#9a6700")}
                <span>조건에 맞는 상품이 없습니다.</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            display_df = filtered[["item_id", "name", "category", "stock", "min_stock", "location", "status", "expiry_date"]].copy()
            display_df.columns = ["고유번호", "상품명", "카테고리", "재고", "안전재고", "위치", "상태", "유통기한"]
            st.dataframe(display_df, use_container_width=True, height=400)

            # 개별 상품 상세/수정
            st.divider()
            item_ids = filtered["item_id"].tolist()
            selected_id = st.selectbox("상세 조회할 상품 선택", item_ids, key="detail_select")

            if selected_id:
                item = db.get_item(selected_id)
                if item is not None:
                    card_start(f"상품 상세 — {item['name']}")
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown(f"**고유번호:** `{item['item_id']}`")
                        st.markdown(f"**상품명:** {item['name']}")
                        st.markdown(f"**카테고리:** {item['category']}")
                        st.markdown(f"**위치:** {item['location'] or '-'}")
                    with c2:
                        st.markdown(f"**재고:** {item['stock']}개 (안전재고: {item['min_stock']})")
                        st.markdown(f"**상태:** {status_badge(item['status'])}", unsafe_allow_html=True)
                        st.markdown(f"**유통기한:** {item['expiry_date'] or '-'}")
                        if item.get("opened_date"):
                            st.markdown(f"**개봉일:** {item['opened_date']} (사용가능: {item['opened_shelf_days']}일)")
                    st.markdown(f"**메모:** {item.get('memo', '-')}")

                    # 수정 폼
                    with st.expander("수정하기"):
                        new_name = st.text_input("상품명", value=item["name"], key="edit_name")
                        new_cat = st.text_input("카테고리", value=item["category"], key="edit_cat")
                        new_loc = st.text_input("위치", value=item["location"], key="edit_loc")
                        new_min = st.number_input("안전재고", value=int(item["min_stock"]), min_value=0, key="edit_min")
                        new_exp = st.text_input("유통기한 (YYYY-MM-DD)", value=item["expiry_date"], key="edit_exp")
                        new_memo = st.text_area("메모", value=item.get("memo", ""), key="edit_memo")

                        ec1, ec2 = st.columns(2)
                        with ec1:
                            if st.button("저장", type="primary", key="save_edit"):
                                db.upsert_item({
                                    "item_id": selected_id, "name": new_name, "category": new_cat,
                                    "location": new_loc, "min_stock": new_min, "expiry_date": new_exp,
                                    "memo": new_memo,
                                })
                                db.add_log(selected_id, "수정", 0, note="상품 정보 수정")
                                st.success("저장 완료!")
                                st.rerun()
                        with ec2:
                            if st.button("삭제", type="secondary", key="delete_item"):
                                db.delete_item(selected_id)
                                db.add_log(selected_id, "삭제", 0, note="상품 삭제")
                                st.warning("삭제 완료.")
                                st.rerun()
                    card_end()

# ── 탭 2: 입고/출고 ──
with tab_inout:
    if total == 0:
        st.markdown(f"""
        <div class="toss-alert toss-alert-info">
            {icon("info", 20, "#0969da")}
            <span>등록된 상품이 없습니다.</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        card_start(f"{icon('swap_horiz', 20, '#3182f6')} 입고 / 출고 처리")
        io_col1, io_col2 = st.columns(2)

        with io_col1:
            item_ids = items_df["item_id"].tolist()
            item_names = items_df["name"].tolist()
            options = [f"{iid} — {name}" for iid, name in zip(item_ids, item_names)]
            selected = st.selectbox("상품 선택", options, key="io_select")
            sel_id = selected.split(" — ")[0] if selected else ""
            sel_item = db.get_item(sel_id)
            if sel_item is not None:
                st.markdown(f"현재 재고: **{sel_item['stock']}개**")

        with io_col2:
            action = st.radio("처리 유형", ["입고 (+)", "출고 (-)"], horizontal=True, key="io_action")
            qty = st.number_input("수량", min_value=1, value=1, key="io_qty")
            worker = st.text_input("작업자", key="io_worker")
            note = st.text_input("비고", key="io_note")

        if st.button("처리 실행", type="primary", key="io_execute", use_container_width=True):
            if sel_id:
                delta = qty if "입고" in action else -qty
                act = "입고" if "입고" in action else "출고"
                db.adjust_stock(sel_id, delta, act, worker, note)
                st.success(f"{act} 완료: {sel_id} → {delta:+d}개")
                st.rerun()
        card_end()

        # 최근 이력
        logs = db.load_logs()
        if not logs.empty:
            card_start(f"{icon('history', 20, '#3182f6')} 최근 입출고 이력")
            recent = logs.sort_values("timestamp", ascending=False).head(20)
            display_logs = recent[["timestamp", "item_id", "action", "quantity", "worker", "note"]].copy()
            display_logs.columns = ["시각", "고유번호", "구분", "수량", "작업자", "비고"]
            st.dataframe(display_logs, use_container_width=True, height=300)
            card_end()

# ── 탭 3: 상품 등록 ──
with tab_add:
    card_start(f"{icon('add', 20, '#3182f6')} 새 상품 등록")
    ac1, ac2 = st.columns(2)
    with ac1:
        new_id = st.text_input("고유번호 (QR 데이터)", key="add_id")
        new_name = st.text_input("상품명", key="add_name")
        new_cat = st.text_input("카테고리", key="add_cat")
        new_loc = st.text_input("위치 (예: A구역 3번선반)", key="add_loc")
    with ac2:
        new_stock = st.number_input("초기 재고", min_value=0, value=1, key="add_stock")
        new_min = st.number_input("안전재고", min_value=0, value=5, key="add_min")
        new_exp = st.text_input("유통기한 (YYYY-MM-DD)", key="add_exp")
        new_shelf = st.number_input("개봉 후 사용가능일", min_value=0, value=0, key="add_shelf", help="0이면 해당 없음")
    new_memo = st.text_area("메모", key="add_memo")

    if st.button("등록", type="primary", key="add_submit", use_container_width=True):
        if not new_id or not new_name:
            st.error("고유번호와 상품명은 필수입니다.")
        else:
            db.upsert_item({
                "item_id": new_id, "name": new_name, "category": new_cat,
                "location": new_loc, "stock": new_stock, "min_stock": new_min,
                "expiry_date": new_exp, "opened_shelf_days": new_shelf,
                "status": "정상", "memo": new_memo,
            })
            db.add_log(new_id, "입고", new_stock, note="신규 등록")
            st.success(f"'{new_name}' 등록 완료!")
            st.rerun()
    card_end()

footer()
