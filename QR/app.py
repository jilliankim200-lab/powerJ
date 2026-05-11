"""
칼퇴보장 QR 라벨기 — 홈
토스 모바일 스타일 · Material Icons
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
from utils.style import inject_css, hero, footer, stat_badges, icon
from utils import db

st.set_page_config(page_title="칼퇴보장 QR 라벨기", page_icon="📎", layout="wide")
inject_css()

# 사이드바 로고는 inject_css()에서 자동 주입

# ── 데이터 로드 ──
items_df = db.load_items()
logs_df = db.load_logs()
total_items = len(items_df)
total_stock = int(items_df["stock"].sum()) if total_items > 0 else 0

danger_count = 0
warning_count = 0
if total_items > 0 and "expiry_date" in items_df.columns:
    for _, row in items_df.iterrows():
        exp = row.get("expiry_date", "")
        opened = row.get("opened_date", "")
        shelf = int(row.get("opened_shelf_days", 0))
        if exp:
            info = db.calc_expiry_status(str(exp), str(opened), shelf)
            if info["color"] in ("black", "red"):
                danger_count += 1
            elif info["color"] == "orange":
                warning_count += 1

low_stock = len(items_df[items_df["stock"] <= items_df["min_stock"]]) if total_items > 0 else 0

# ══════════════════════════════════════════════════════════════════════
# 첫 방문자 가이드
# ══════════════════════════════════════════════════════════════════════
if total_items == 0:

    hero("엑셀만 올리면\nQR 라벨이 뚝딱!", "유통기한 D-Day 자동 표시 · 재고 관리 · 완전 무료")

    # ── 이런 분께 ──
    st.markdown(f"""
    <div class="toss-card">
        <div style="font-size:1.1rem; font-weight:800; color:#191f28; margin-bottom:0.75rem;">
            {icon("people", 22, "#3182f6")} 이런 분께 추천합니다
        </div>
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:0.5rem 2rem; font-size:0.92rem; line-height:1.8; color:#4e5968;">
            <div>{icon("check_circle", 18, "#3182f6")} QR 스티커를 <b>수작업</b>으로 붙이는 분</div>
            <div>{icon("check_circle", 18, "#3182f6")} 유통기한을 <b>엑셀/수기</b>로 관리하는 분</div>
            <div>{icon("check_circle", 18, "#3182f6")} 재고 파악하려고 <b>직접 세는</b> 분</div>
            <div>{icon("check_circle", 18, "#3182f6")} <b>유료 구독</b>이 부담되는 분</div>
            <div>{icon("check_circle", 18, "#3182f6")} 회사 데이터 <b>외부 전송이 불안</b>한 분</div>
            <div>{icon("check_circle", 18, "#3182f6")} <b>스마트폰 하나</b>로 해결하고 싶은 분</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── 3단계 사용법 ──
    st.markdown(f"""
    <div style="font-size:1.2rem; font-weight:800; color:#191f28; margin:2rem 0 1rem;">
        {icon("rocket_launch", 24, "#3182f6")} 3단계로 끝!
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:0.75rem;">
        <div class="toss-card" style="text-align:center;">
            <div style="width:48px; height:48px; border-radius:14px; background:#e8f4fd;
                        display:inline-flex; align-items:center; justify-content:center; margin-bottom:0.6rem;">
                {icon("upload_file", 28, "#3182f6", 600)}
            </div>
            <div style="font-size:1rem; font-weight:700; color:#191f28; margin-bottom:0.3rem;">데이터 준비</div>
            <div style="font-size:0.82rem; color:#8b95a1; line-height:1.5;">
                엑셀 업로드 또는<br>모바일에서 직접 입력<br>
                <span style="color:#3182f6; font-weight:600;">사진 찍으면 AI 자동 인식</span>
            </div>
        </div>
        <div class="toss-card" style="text-align:center;">
            <div style="width:48px; height:48px; border-radius:14px; background:#f3e8fd;
                        display:inline-flex; align-items:center; justify-content:center; margin-bottom:0.6rem;">
                {icon("print", 28, "#8b5cf6", 600)}
            </div>
            <div style="font-size:1rem; font-weight:700; color:#191f28; margin-bottom:0.3rem;">라벨 PDF 출력</div>
            <div style="font-size:0.82rem; color:#8b95a1; line-height:1.5;">
                폼텍 규격 PDF 즉시 생성<br>
                <span style="color:#d1242f; font-weight:600;">유통기한 임박 빨간 강조</span><br>
                프린터로 바로 인쇄
            </div>
        </div>
        <div class="toss-card" style="text-align:center;">
            <div style="width:48px; height:48px; border-radius:14px; background:#e6f9ed;
                        display:inline-flex; align-items:center; justify-content:center; margin-bottom:0.6rem;">
                {icon("qr_code_scanner", 28, "#1a7f37", 600)}
            </div>
            <div style="font-size:1rem; font-weight:700; color:#191f28; margin-bottom:0.3rem;">스캔하고 관리</div>
            <div style="font-size:0.82rem; color:#8b95a1; line-height:1.5;">
                QR 스캔 → 원터치 처리<br>
                <span style="color:#1a7f37; font-weight:600;">입고 / 출고 / 점검 / 개봉</span><br>
                대시보드에서 한눈에
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── 특장점 ──
    st.markdown(f"""
    <div style="font-size:1.2rem; font-weight:800; color:#191f28; margin:2rem 0 1rem;">
        {icon("auto_awesome", 24, "#3182f6")} 다른 도구와 뭐가 다른가요?
    </div>
    """, unsafe_allow_html=True)

    features = [
        ("paid", "#3182f6", "#e8f4fd", "완전 무료 & 무제한", "로그인 없이 1,000장도 무료. 광고·유료 전환 없음."),
        ("event_busy", "#d1242f", "#fff0f0", "유통기한 D-Day 자동 표시", "임박 상품은 라벨에 빨간 경고 띠 자동 표시. 시중 도구에 없는 기능."),
        ("shield_lock", "#1b64da", "#e8f4fd", "데이터 보안 (No Server)", "엑셀 데이터는 서버에 저장되지 않음. 브라우저에서 즉시 처리."),
        ("qr_code_scanner", "#1a7f37", "#e6f9ed", "QR 스캔 → 즉시 재고 관리", "라벨을 붙인 후 스캔하면 입고/출고/점검을 원터치로 처리."),
        ("photo_camera", "#9a6700", "#fff8e1", "사진 → 유통기한 자동 인식", "상품 뒷면 촬영 시 AI(EasyOCR)가 날짜를 자동으로 읽어냄."),
        ("straighten", "#6e5494", "#f3e8fd", "폼텍 규격 정밀 지원", "24칸·21칸·40칸·65칸 폼텍 실측값 4종 규격 지원."),
    ]

    for ic, color, bg, title, desc in features:
        st.markdown(f"""
        <div class="toss-card" style="display:flex; align-items:flex-start; gap:1rem;">
            <div style="min-width:44px; height:44px; border-radius:12px; background:{bg};
                        display:flex; align-items:center; justify-content:center;">
                {icon(ic, 24, color, 600)}
            </div>
            <div>
                <div style="font-size:1rem; font-weight:700; color:#191f28;">{title}</div>
                <div style="font-size:0.88rem; color:#8b95a1; margin-top:2px; line-height:1.5;">{desc}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── 메뉴 안내 ──
    st.markdown(f"""
    <div style="font-size:1.2rem; font-weight:800; color:#191f28; margin:2rem 0 1rem;">
        {icon("menu_book", 24, "#3182f6")} 메뉴 안내
    </div>
    """, unsafe_allow_html=True)

    menus = [
        ("label", "#3182f6", "라벨 생성", "엑셀 업로드 → 열 매칭 → QR 라벨 PDF 생성. 유통기한 열 선택 시 D-Day 자동 표시.", "/🏷️_라벨_생성"),
        ("smartphone", "#8b5cf6", "모바일 입력", "엑셀 없이 직접 입력, 사진 OCR 인식, 귀찮음 제로 대량 생성.", "/📱_모바일_입력"),
        ("inventory_2", "#1a7f37", "재고 관리", "상품 등록/수정/삭제, 입출고 처리, 위치·안전재고 관리.", "/📦_재고_관리"),
        ("qr_code_scanner", "#e65100", "QR 스캔", "스마트폰 스캔 → 상품 정보 즉시 표시 → 원터치 입고/출고/점검.", "/📱_QR_스캔"),
        ("monitoring", "#0969da", "대시보드", "유통기한 D-Day, 재고 부족 현황, 카테고리별 통계, 입출고 이력.", "/📊_대시보드"),
        ("gavel", "#8b95a1", "이용약관", "개인정보 처리방침, 면책 조항, 오픈소스 라이선스.", "/⚖️_이용약관"),
    ]

    for ic, color, title, desc, link in menus:
        st.markdown(f"""
        <a href="{link}" target="_self" style="text-decoration:none; display:block;">
        <div class="toss-card" style="display:flex; align-items:center; gap:1rem; cursor:pointer;">
            <div style="min-width:40px; height:40px; border-radius:10px; background:#f2f4f6;
                        display:flex; align-items:center; justify-content:center;">
                {icon(ic, 22, color, 500)}
            </div>
            <div style="flex:1;">
                <div style="font-size:0.95rem; font-weight:700; color:#191f28;">{title}</div>
                <div style="font-size:0.82rem; color:#8b95a1; line-height:1.4;">{desc}</div>
            </div>
            {icon("chevron_right", 20, "#d1d6db")}
        </div>
        </a>
        """, unsafe_allow_html=True)

    # ── 시작 CTA ──
    st.markdown(f"""
    <div style="text-align:center; margin:2rem 0;">
        <div style="display:inline-flex; align-items:center; gap:8px;
                    background:#3182f6; color:white; padding:1rem 2.5rem;
                    border-radius:16px; font-size:1.1rem; font-weight:700;">
            {icon("arrow_back", 22, "white", 600)} 사이드바에서 라벨 생성을 눌러 시작하세요
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── FAQ ──
    st.markdown(f"""
    <div style="font-size:1.2rem; font-weight:800; color:#191f28; margin:2rem 0 1rem;">
        {icon("help", 24, "#3182f6")} 자주 묻는 질문
    </div>
    """, unsafe_allow_html=True)

    with st.expander("정말 무료인가요? 유료로 바뀌지 않나요?"):
        st.markdown("**네, 완전히 무료입니다.** 로그인도 필요 없고 사용량 제한도 없습니다. 모든 기능이 오픈소스 라이브러리로 만들어져 유지 비용이 0원이므로 유료 전환 계획이 없습니다.")

    with st.expander("회사 데이터를 올려도 안전한가요?"):
        st.markdown("**안전합니다.** 업로드한 엑셀 데이터는 서버에 저장되지 않습니다. 브라우저 세션 내에서만 처리되며, 탭을 닫으면 즉시 삭제됩니다. 외부 전송, 로그 기록, 쿠키 추적 일절 없습니다.")

    with st.expander("엑셀 파일이 없어도 쓸 수 있나요?"):
        st.markdown("**네!** 📱 모바일 입력 페이지에서 직접 입력하거나, 상품명+수량만 넣으면 고유번호가 자동 생성됩니다. 상품 뒷면을 사진 찍으면 AI가 유통기한을 자동 인식합니다.")

    with st.expander("어떤 라벨지를 사야 하나요?"):
        st.markdown("""
        다이소, 쿠팡 등에서 **폼텍 라벨지**를 구매하세요:

        | 모델 | 칸수 | 용도 |
        |------|------|------|
        | **LQ-3105** (추천) | 24칸 (3×8) | 일반 상품 라벨 |
        | LQ-3107 | 21칸 (3×7) | 큰 글씨 라벨 |
        | LQ-3112 | 40칸 (4×10) | 소형 분류용 |
        | LQ-3100 | 65칸 (5×13) | 미니 라벨 |
        """)

    with st.expander("QR을 스캔하면 뭐가 되나요?"):
        st.markdown("라벨 생성 시 **'QR에 관리 URL 포함'**을 체크하면, 스캔 시 해당 상품의 관리 페이지가 열립니다. 거기서 **입고 +1, 출고 -1, 개봉 기록, 점검 완료**를 원터치로 처리할 수 있습니다.")

    with st.expander("모바일에서도 쓸 수 있나요?"):
        st.markdown("**네.** 스마트폰 브라우저에서 그대로 접속하면 됩니다. 📱 모바일 입력 페이지는 큰 버튼과 입력 필드로 최적화되어 있습니다.")

# ══════════════════════════════════════════════════════════════════════
# 기존 사용자 (등록 상품 있을 때)
# ══════════════════════════════════════════════════════════════════════
else:
    hero("칼퇴보장 QR 라벨기", "QR 라벨 생성 · 재고 관리 · 유통기한 추적 · 입출고 이력")

    stat_badges([
        (str(total_items), "등록 상품"),
        (str(total_stock), "총 재고"),
        (str(len(logs_df)), "처리 이력"),
        (str(danger_count), "긴급 알림"),
    ])

    st.divider()

    # 빠른 메뉴
    st.markdown(f"""
    <div style="font-size:1.1rem; font-weight:800; color:#191f28; margin-bottom:0.75rem;">
        {icon("widgets", 22, "#3182f6")} 빠른 시작
    </div>
    """, unsafe_allow_html=True)

    quick_menus = [
        ("label", "#3182f6", "#e8f4fd", "라벨 생성", "엑셀 → QR → PDF"),
        ("inventory_2", "#1a7f37", "#e6f9ed", "재고 관리", "입출고 · 위치 · 재고"),
        ("qr_code_scanner", "#e65100", "#fff3e0", "QR 스캔", "스캔 즉시 조회/처리"),
        ("monitoring", "#0969da", "#e8f4fd", "대시보드", "유통기한 · 알림 · 통계"),
    ]

    cols = st.columns(4)
    for i, (ic, color, bg, title, desc) in enumerate(quick_menus):
        with cols[i]:
            st.markdown(f"""
            <div class="toss-card" style="text-align:center; min-height:130px;">
                <div style="width:44px; height:44px; border-radius:12px; background:{bg};
                            display:inline-flex; align-items:center; justify-content:center; margin-bottom:0.5rem;">
                    {icon(ic, 24, color, 600)}
                </div>
                <div style="font-size:0.95rem; font-weight:700; color:#191f28;">{title}</div>
                <div style="font-size:0.78rem; color:#8b95a1; margin-top:2px;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="toss-alert toss-alert-info">
        {icon("arrow_back", 20, "#0969da")} <span>왼쪽 사이드바에서 메뉴를 선택하세요.</span>
    </div>
    """, unsafe_allow_html=True)

    # 긴급 알림
    if danger_count > 0 or warning_count > 0 or low_stock > 0:
        st.markdown(f"""
        <div style="font-size:1.1rem; font-weight:800; color:#191f28; margin:1.5rem 0 0.75rem;">
            {icon("notifications_active", 22, "#d1242f")} 알림
        </div>
        """, unsafe_allow_html=True)

        if danger_count > 0:
            st.markdown(f"""
            <div class="toss-alert toss-alert-danger">
                {icon("error", 20, "#d1242f")}
                <span>유통기한 만료/임박 상품 <b>{danger_count}건</b> — 대시보드에서 확인하세요.</span>
            </div>
            """, unsafe_allow_html=True)
        if warning_count > 0:
            st.markdown(f"""
            <div class="toss-alert toss-alert-warning">
                {icon("warning", 20, "#9a6700")}
                <span>유통기한 7일 이내 상품 <b>{warning_count}건</b></span>
            </div>
            """, unsafe_allow_html=True)
        if low_stock > 0:
            st.markdown(f"""
            <div class="toss-alert toss-alert-warning">
                {icon("inventory", 20, "#9a6700")}
                <span>재고 부족 상품 <b>{low_stock}건</b> — 주문이 필요합니다.</span>
            </div>
            """, unsafe_allow_html=True)

footer()
