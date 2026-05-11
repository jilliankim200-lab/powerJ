"""토스(Toss) 모바일 스타일 디자인 시스템 + Material Icons"""

import streamlit as st

# Google Material Symbols 아이콘 헬퍼
def icon(name: str, size: int = 24, color: str = "inherit", weight: int = 400) -> str:
    """Google Material Symbols 아이콘 HTML 반환."""
    return (
        f'<span class="material-symbols-rounded" '
        f'style="font-size:{size}px; color:{color}; font-variation-settings: '
        f"'wght' {weight}; vertical-align:middle;\">{name}</span>"
    )


COMMON_CSS = """
<style>
/* ── 폰트 & Material Icons ── */
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;600;700;800&display=swap');
/* Material Icons - link 태그로 로드하여 충돌 방지 */

html, body, [class*="st-"] {
    font-family: 'Noto Sans KR', -apple-system, sans-serif !important;
    -webkit-font-smoothing: antialiased;
}

.material-symbols-rounded {
    font-family: 'Material Symbols Rounded';
    font-weight: normal;
    font-style: normal;
    display: inline-block;
    line-height: 1;
    text-transform: none;
    letter-spacing: normal;
    word-wrap: normal;
    white-space: nowrap;
    direction: ltr;
    font-variation-settings: 'FILL' 1, 'wght' 400, 'GRAD' 0, 'opsz' 24;
}

/* ── 레이아웃 ── */
.block-container {
    max-width: 720px !important;
    padding: 2rem 1.5rem 4rem !important;
}

/* ── 사이드바 ── */
[data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid #f2f4f6;
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    font-size: 0.95rem;
}

/* 사이드바 "keyboard_double" 깨진 아이콘 텍스트 숨김 */
[data-testid="stSidebarCollapsedControl"] {
    visibility: hidden;
    height: 0;
    overflow: hidden;
}
[data-testid="stSidebarHeader"] {
    visibility: hidden;
    height: 0;
    min-height: 0 !important;
    padding: 0 !important;
    overflow: hidden;
}

/* 사이드바 "app" 홈 링크 숨기고 커스텀 대체 */
[data-testid="stSidebarNav"] li:first-child {
    display: none;
}

/* 사이드바 상단에 로고 영역 고정 */
[data-testid="stSidebar"]::before {
    content: '';
    display: block;
}
/* 로고를 네비 위에 배치: position fixed */
.sidebar-logo {
    padding: 1.25rem 1rem 0.75rem;
    border-bottom: 1px solid #f2f4f6;
    margin-bottom: 0.5rem;
}

/* ── 토스 히어로 ── */
.toss-hero {
    text-align: left;
    padding: 2rem 0 1.5rem;
}
.toss-hero h1 {
    font-size: 1.75rem;
    font-weight: 800;
    color: #191f28;
    margin: 0 0 0.4rem;
    letter-spacing: -0.5px;
    line-height: 1.35;
}
.toss-hero p {
    font-size: 0.95rem;
    color: #8b95a1;
    margin: 0;
    font-weight: 400;
}

/* ── 토스 카드 ── */
.toss-card {
    background: #ffffff;
    border: 1px solid #f2f4f6;
    border-radius: 16px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 0.75rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    transition: box-shadow 0.2s;
}
.toss-card:hover {
    box-shadow: 0 4px 16px rgba(0,0,0,0.08);
}
.toss-card-title {
    font-size: 0.8rem;
    font-weight: 600;
    color: #8b95a1;
    letter-spacing: 0.3px;
    margin-bottom: 0.75rem;
}

/* ── 통계 (토스 스타일) ── */
.toss-stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
    gap: 0.5rem;
    margin: 1rem 0;
}
.toss-stat {
    text-align: center;
    padding: 1rem 0.5rem;
    background: #f9fafb;
    border-radius: 14px;
}
.toss-stat .num {
    font-size: 1.75rem;
    font-weight: 800;
    color: #191f28;
    letter-spacing: -1px;
}
.toss-stat .label {
    font-size: 0.75rem;
    color: #8b95a1;
    margin-top: 4px;
    font-weight: 500;
}

/* ── 상태 뱃지 ── */
.badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 3px 10px;
    border-radius: 8px;
    font-size: 0.78rem;
    font-weight: 600;
}
.badge-green  { background: #e8f5e9; color: #2e7d32; }
.badge-yellow { background: #fff8e1; color: #f57f17; }
.badge-orange { background: #fff3e0; color: #e65100; }
.badge-red    { background: #ffebee; color: #c62828; }
.badge-black  { background: #f5f5f5; color: #424242; }

/* ── 알림 (토스 스타일) ── */
.toss-alert {
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
    padding: 1rem 1.25rem;
    border-radius: 14px;
    margin: 0.5rem 0;
    font-size: 0.9rem;
    line-height: 1.6;
}
.toss-alert-info    { background: #e8f4fd; color: #0969da; }
.toss-alert-warning { background: #fff8e1; color: #9a6700; }
.toss-alert-danger  { background: #fff0f0; color: #d1242f; }
.toss-alert-success { background: #e6f9ed; color: #1a7f37; }

/* ── 입력 필드 (크게) ── */
.stTextInput input,
.stNumberInput input,
.stDateInput input,
.stSelectbox [data-baseweb="select"] {
    font-size: 1.05rem !important;
    padding: 0.75rem 1rem !important;
    border-radius: 12px !important;
    border: 1.5px solid #e5e8eb !important;
    background: #f9fafb !important;
}
.stTextInput input:focus,
.stNumberInput input:focus {
    border-color: #3182f6 !important;
    box-shadow: 0 0 0 3px rgba(49,130,246,0.12) !important;
    background: #fff !important;
}
.stTextInput label,
.stNumberInput label,
.stSelectbox label,
.stDateInput label,
.stCheckbox label,
.stRadio label {
    font-size: 0.9rem !important;
    font-weight: 600 !important;
    color: #4e5968 !important;
}

/* ── 버튼 (토스 블루) ── */
.stButton > button[kind="primary"],
.stDownloadButton > button {
    width: 100%;
    background: #3182f6 !important;
    color: white !important;
    border: none !important;
    padding: 0.85rem 1.5rem !important;
    border-radius: 14px !important;
    font-size: 1.05rem !important;
    font-weight: 700 !important;
    transition: background 0.15s !important;
}
.stButton > button[kind="primary"]:hover,
.stDownloadButton > button:hover {
    background: #1b64da !important;
}
.stButton > button[kind="secondary"] {
    width: 100%;
    background: #f2f4f6 !important;
    color: #4e5968 !important;
    border: none !important;
    padding: 0.8rem 1.5rem !important;
    border-radius: 14px !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
}

/* ── 파일 업로더 ── */
[data-testid="stFileUploader"] {
    border: 2px dashed #d1d6db;
    border-radius: 16px;
    padding: 1rem;
    background: #fafbfc;
}
/*
 * Streamlit 위젯 내부 폰트 복원
 * Material Symbols Rounded 폰트가 Streamlit 내부 텍스트
 * (upload, arrow_right 등)를 아이콘으로 렌더링하는 것을 방지
 */
[data-testid="stFileUploader"] *,
[data-testid="stExpander"] summary *,
[data-testid="stExpander"] summary,
.streamlit-expanderHeader *,
.streamlit-expanderHeader,
[data-testid="stSidebar"] nav *,
[data-testid="stSidebarNav"] *,
button, select, input, textarea,
[data-baseweb] * {
    font-family: 'Noto Sans KR', -apple-system, sans-serif !important;
}
/* material-symbols-rounded 클래스만 아이콘 폰트 사용 */
.material-symbols-rounded {
    font-family: 'Material Symbols Rounded' !important;
}

/* ── 탭 (토스 스타일) ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    background: #f2f4f6;
    border-radius: 12px;
    padding: 3px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 10px;
    font-weight: 600;
    font-size: 0.9rem;
    padding: 0.6rem 1rem;
    color: #8b95a1;
}
.stTabs [aria-selected="true"] {
    background: #ffffff !important;
    color: #191f28 !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}
.stTabs [data-baseweb="tab-highlight"] {
    display: none;
}

/* ── 구분선 ── */
hr {
    border: none;
    border-top: 1px solid #f2f4f6;
    margin: 1.5rem 0;
}

/* ── 테이블 ── */
.stDataFrame {
    border-radius: 14px !important;
    overflow: hidden;
}

/* ── 푸터 ── */
.toss-footer {
    text-align: center;
    padding: 2rem 1rem;
    margin-top: 3rem;
    font-size: 0.78rem;
    color: #b0b8c1;
    line-height: 1.7;
    border-top: 1px solid #f2f4f6;
}

/* ── 유틸리티 ── */
.text-muted { color: #8b95a1; }
.text-primary { color: #3182f6; }
.text-danger { color: #d1242f; }
.text-success { color: #1a7f37; }
.text-warning { color: #9a6700; }
.fw-800 { font-weight: 800; }
.fw-700 { font-weight: 700; }
.fw-600 { font-weight: 600; }
.fs-sm { font-size: 0.85rem; }
.fs-xs { font-size: 0.78rem; }

/* 보안 배너 */
.security-banner {
    display: flex; align-items: center; gap: 0.75rem;
    background: #e6f9ed; border-radius: 14px;
    padding: 1rem 1.25rem; margin: 1rem 0;
    font-size: 0.88rem; color: #1a7f37;
}
</style>
"""


def inject_css():
    """공통 CSS + Material Icons + 사이드바 로고 주입."""
    # Material Icons를 link 태그로 로드
    st.markdown(
        '<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:'
        'opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" rel="stylesheet">',
        unsafe_allow_html=True,
    )
    st.markdown(COMMON_CSS, unsafe_allow_html=True)

    # 사이드바 최상단 로고 + 홈 버튼 (모든 페이지 공통)
    st.sidebar.markdown(f"""
    <div class="sidebar-logo">
        <div style="font-size:1.1rem; font-weight:800; color:#191f28; display:flex; align-items:center; gap:8px;">
            {icon("qr_code_2", 28, "#3182f6", 700)} 칼퇴보장 QR 라벨기
        </div>
        <div style="font-size:0.75rem; color:#8b95a1; margin-top:4px;">무료 · 무제한 · 데이터 저장 안 함</div>
    </div>
    <a href="/" target="_self" style="display:flex; align-items:center; gap:8px;
        padding:0.6rem 0.75rem; border-radius:10px; background:#f2f4f6;
        text-decoration:none; color:#191f28; font-weight:600; font-size:0.9rem;
        margin:0 1rem 0.5rem;">
        {icon("home", 20, "#3182f6", 600)} 홈
    </a>
    """, unsafe_allow_html=True)


def hero(title: str, subtitle: str):
    """토스 스타일 좌측 정렬 헤더."""
    st.markdown(f"""
    <div class="toss-hero">
        <h1>{title}</h1>
        <p>{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)


def card_start(title: str = ""):
    title_html = f'<div class="toss-card-title">{title}</div>' if title else ""
    st.markdown(f'<div class="toss-card">{title_html}', unsafe_allow_html=True)


def card_end():
    st.markdown('</div>', unsafe_allow_html=True)


def stat_badges(items: list[tuple[str, str]]):
    """[(값, 라벨), ...] → 토스 스타일 통계."""
    badges = "".join(
        f'<div class="toss-stat"><div class="num">{val}</div><div class="label">{label}</div></div>'
        for val, label in items
    )
    st.markdown(f'<div class="toss-stats">{badges}</div>', unsafe_allow_html=True)


def status_badge(status: str) -> str:
    """상태 문자열 → 색상 뱃지 HTML."""
    color_map = {"정상": "green", "주의": "yellow", "위험": "red", "만료": "black", "폐기": "black"}
    c = color_map.get(status, "green")
    return f'<span class="badge badge-{c}">{status}</span>'


def footer():
    st.markdown(f"""
    <div class="toss-footer">
        {icon("lock", 14, "#b0b8c1")} 데이터 서버 저장 안 함 · 세션 종료 시 즉시 삭제<br>
        본 도구는 무료로 제공되며 출력 결과물에 대한 최종 책임은 사용자에게 있습니다.<br>
        <span style="font-size:0.7rem;">사이드바 ⚖️ 이용약관에서 개인정보 처리방침, 면책 조항, 오픈소스 라이선스를 확인하세요.</span>
    </div>
    """, unsafe_allow_html=True)
