"""
페이지 4: 대시보드
유통기한 현황 · 재고 알림 · 입출고 통계 · 전체 현황 한눈에
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime, date
import streamlit as st
import pandas as pd
from utils.style import inject_css, hero, card_start, card_end, stat_badges, status_badge, icon, footer
from utils import db

st.set_page_config(page_title="대시보드 | QR 라벨기", page_icon="📊", layout="wide")
inject_css()

# 사이드바 로고는 inject_css()에서 자동 주입

hero("대시보드", f"전체 현황 한눈에 · {date.today().strftime('%Y년 %m월 %d일')}")

items_df = db.load_items()
logs_df = db.load_logs()
total = len(items_df)

if total == 0:
    st.markdown(f"""
    <div class="toss-alert toss-alert-info">
        {icon("info", 20, "#0969da")}
        <span>등록된 상품이 없습니다. 라벨 생성 또는 재고 관리에서 상품을 먼저 등록하세요.</span>
    </div>
    """, unsafe_allow_html=True)
    footer()
    st.stop()

# ── 유통기한 분석 ──
expiry_data = []
for _, row in items_df.iterrows():
    exp = str(row.get("expiry_date", ""))
    opened = str(row.get("opened_date", ""))
    shelf = int(row.get("opened_shelf_days", 0))
    info = db.calc_expiry_status(exp, opened, shelf)
    expiry_data.append({
        "item_id": row["item_id"],
        "name": row["name"],
        "category": row["category"],
        "stock": int(row["stock"]),
        "expiry_date": exp,
        "d_day": info["d_day"],
        "color": info["color"],
        "label": info["label"],
        "alert": info["alert"],
    })

exp_df = pd.DataFrame(expiry_data)

# 분류 카운트
expired = len(exp_df[exp_df["color"] == "black"])
danger = len(exp_df[exp_df["color"] == "red"])
warning = len(exp_df[exp_df["color"] == "orange"])
safe = len(exp_df[exp_df["color"] == "green"])
low_stock = len(items_df[items_df["stock"] <= items_df["min_stock"]])

stat_badges([
    (str(total), "전체 상품"),
    (str(expired), "만료"),
    (str(danger), "긴급 (D-3)"),
    (str(warning), "주의 (D-7)"),
    (str(low_stock), "재고 부족"),
])

st.divider()

# ── 탭 구성 ──
tab_exp, tab_stock, tab_log = st.tabs([
    "유통기한 현황",
    "재고 현황",
    "최근 이력",
])

# ── 탭 1: 유통기한 ──
with tab_exp:
    # 만료/긴급 상품
    critical = exp_df[exp_df["color"].isin(["black", "red"])].sort_values("d_day")
    if not critical.empty:
        card_start(f"{icon('error', 20, '#dc2626')} 긴급 — 만료/임박 상품 ({len(critical)}건)")
        for _, r in critical.iterrows():
            color = "#991b1b" if r["color"] == "black" else "#dc2626"
            bg = "#fef2f2" if r["color"] == "black" else "#fff5f5"
            action = "즉시 폐기/할인 필요" if r["color"] == "black" else "빠른 출고 필요"
            st.markdown(f"""
            <div style="display:flex; align-items:center; gap:1rem; padding:0.6rem 1rem;
                        background:{bg}; border-left:4px solid {color}; border-radius:6px; margin-bottom:0.5rem;">
                <div style="min-width:60px; text-align:center;">
                    <span style="font-size:1.3rem; font-weight:700; color:{color};">{r['label']}</span>
                </div>
                <div style="flex:1;">
                    <span style="font-weight:600; color:#111;">{r['name']}</span>
                    <span style="color:#6b7280; font-size:0.8rem;"> ({r['item_id']})</span><br>
                    <span style="font-size:0.8rem; color:#6b7280;">유통기한: {r['expiry_date']} · 재고: {r['stock']}개 · {action}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        card_end()

    # 주의 상품
    warn = exp_df[exp_df["color"] == "orange"].sort_values("d_day")
    if not warn.empty:
        card_start(f"{icon('warning', 20, '#f59e0b')} 주의 — 7일 이내 ({len(warn)}건)")
        for _, r in warn.iterrows():
            st.markdown(f"""
            <div style="display:flex; align-items:center; gap:1rem; padding:0.5rem 1rem;
                        background:#fffbeb; border-left:4px solid #f59e0b; border-radius:6px; margin-bottom:0.4rem;">
                <div style="min-width:60px; text-align:center;">
                    <span style="font-size:1.1rem; font-weight:700; color:#92400e;">{r['label']}</span>
                </div>
                <div style="flex:1;">
                    <span style="font-weight:600;">{r['name']}</span>
                    <span style="color:#6b7280; font-size:0.8rem;"> · 유통기한: {r['expiry_date']} · 재고: {r['stock']}개</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        card_end()

    # 안전 상품
    ok = exp_df[exp_df["color"] == "green"].sort_values("d_day")
    if not ok.empty:
        with st.expander(f"정상 상품 ({len(ok)}건)", expanded=False):
            display = ok[["item_id", "name", "expiry_date", "label", "stock"]].copy()
            display.columns = ["고유번호", "상품명", "유통기한", "D-Day", "재고"]
            st.dataframe(display, use_container_width=True, height=300)

    # 유통기한 없는 상품
    no_exp = exp_df[exp_df["d_day"].isna()]
    if not no_exp.empty:
        st.caption(f"유통기한 미등록: {len(no_exp)}건")

# ── 탭 2: 재고 현황 ──
with tab_stock:
    # 재고 부족 목록
    low_items = items_df[items_df["stock"] <= items_df["min_stock"]].copy()
    if not low_items.empty:
        card_start(f"{icon('inventory', 20, '#3182f6')} 재고 부족 상품 ({len(low_items)}건)")
        for _, r in low_items.iterrows():
            pct = int(r["stock"] / max(r["min_stock"], 1) * 100)
            bar_color = "#ef4444" if r["stock"] == 0 else ("#f59e0b" if pct < 50 else "#3b82f6")
            order_text = f" · {icon('error', 14, '#ef4444')} 주문 필요" if r["stock"] == 0 else f" · {icon('warning', 14, '#f59e0b')} 부족"
            st.markdown(f"""
            <div style="padding:0.5rem 1rem; background:#f9fafb; border-radius:8px; margin-bottom:0.5rem;">
                <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                    <span style="font-weight:600;">{r['name']}</span>
                    <span style="font-size:0.85rem; color:#6b7280;">
                        {r['stock']}/{r['min_stock']}개 {order_text}
                    </span>
                </div>
                <div style="height:6px; background:#e5e7eb; border-radius:3px; overflow:hidden;">
                    <div style="height:100%; width:{min(pct, 100)}%; background:{bar_color}; border-radius:3px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        card_end()
    else:
        st.markdown(f"""
        <div class="toss-alert toss-alert-success">
            {icon("task_alt", 20, "#1a7f37")}
            <span>재고 부족 상품이 없습니다.</span>
        </div>
        """, unsafe_allow_html=True)

    # 카테고리별 재고
    if items_df["category"].any():
        card_start(f"{icon('monitoring', 20, '#3182f6')} 카테고리별 재고 현황")
        cat_summary = items_df.groupby("category").agg(
            상품수=("item_id", "count"),
            총재고=("stock", "sum"),
        ).reset_index()
        cat_summary.columns = ["카테고리", "상품 수", "총 재고"]
        st.dataframe(cat_summary, use_container_width=True)
        card_end()

    # 위치별 현황
    if items_df["location"].any():
        card_start(f"{icon('location_on', 20, '#3182f6')} 위치별 현황")
        loc_summary = items_df[items_df["location"] != ""].groupby("location").agg(
            상품수=("item_id", "count"),
            총재고=("stock", "sum"),
        ).reset_index()
        loc_summary.columns = ["위치", "상품 수", "총 재고"]
        st.dataframe(loc_summary, use_container_width=True)
        card_end()

# ── 탭 3: 최근 이력 ──
with tab_log:
    if logs_df.empty:
        st.markdown(f"""
        <div class="toss-alert toss-alert-info">
            {icon("info", 20, "#0969da")}
            <span>아직 처리 이력이 없습니다.</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        card_start(f"{icon('history', 20, '#3182f6')} 최근 이력 (전체 {len(logs_df)}건)")

        # 필터
        fc1, fc2 = st.columns(2)
        with fc1:
            actions = ["전체"] + sorted(logs_df["action"].unique().tolist())
            act_filter = st.selectbox("구분", actions, key="log_filter")
        with fc2:
            log_limit = st.selectbox("표시 건수", [20, 50, 100, "전체"], key="log_limit")

        display = logs_df.sort_values("timestamp", ascending=False)
        if act_filter != "전체":
            display = display[display["action"] == act_filter]
        if log_limit != "전체":
            display = display.head(int(log_limit))

        show_cols = display[["timestamp", "item_id", "action", "quantity", "worker", "note"]].copy()
        show_cols.columns = ["시각", "고유번호", "구분", "수량", "작업자", "비고"]
        st.dataframe(show_cols, use_container_width=True, height=400)
        card_end()

footer()
