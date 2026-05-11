"""
CSV 기반 무료 데이터베이스 모듈
- items.csv: 상품 마스터 (고유번호, 이름, 유통기한, 위치, 재고 등)
- logs.csv:  입출고/점검 이력 로그
"""

import os
from datetime import datetime, date
from typing import Optional

import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

ITEMS_FILE = os.path.join(DATA_DIR, "items.csv")
LOGS_FILE = os.path.join(DATA_DIR, "logs.csv")

ITEMS_COLUMNS = [
    "item_id",        # 고유번호 (QR에 들어가는 값)
    "name",           # 상품명
    "category",       # 카테고리
    "expiry_date",    # 유통기한 (YYYY-MM-DD)
    "opened_date",    # 개봉일 (YYYY-MM-DD, 없으면 빈값)
    "opened_shelf_days",  # 개봉 후 사용 가능 일수
    "stock",          # 현재 재고 수량
    "min_stock",      # 최소 안전재고
    "location",       # 위치 (예: A구역 3번선반)
    "status",         # 상태: 정상 / 주의 / 위험 / 폐기
    "memo",           # 메모
    "created_at",     # 등록일시
    "updated_at",     # 수정일시
]

LOGS_COLUMNS = [
    "log_id",
    "item_id",
    "action",         # 입고 / 출고 / 점검 / 개봉 / 폐기 / 수정
    "quantity",       # 수량 변동 (+/-)
    "worker",         # 작업자
    "note",           # 비고
    "timestamp",
]


def _ensure_files():
    """CSV 파일이 없으면 빈 파일 생성."""
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(ITEMS_FILE):
        pd.DataFrame(columns=ITEMS_COLUMNS).to_csv(ITEMS_FILE, index=False)
    if not os.path.exists(LOGS_FILE):
        pd.DataFrame(columns=LOGS_COLUMNS).to_csv(LOGS_FILE, index=False)


def load_items() -> pd.DataFrame:
    """전체 상품 목록 로드."""
    _ensure_files()
    df = pd.read_csv(ITEMS_FILE, dtype=str).fillna("")
    if "stock" in df.columns:
        df["stock"] = pd.to_numeric(df["stock"], errors="coerce").fillna(0).astype(int)
    if "min_stock" in df.columns:
        df["min_stock"] = pd.to_numeric(df["min_stock"], errors="coerce").fillna(0).astype(int)
    if "opened_shelf_days" in df.columns:
        df["opened_shelf_days"] = pd.to_numeric(df["opened_shelf_days"], errors="coerce").fillna(0).astype(int)
    return df


def save_items(df: pd.DataFrame):
    """전체 상품 목록 저장."""
    _ensure_files()
    df.to_csv(ITEMS_FILE, index=False)


def load_logs() -> pd.DataFrame:
    """이력 로그 전체 로드."""
    _ensure_files()
    return pd.read_csv(LOGS_FILE, dtype=str).fillna("")


def save_logs(df: pd.DataFrame):
    """이력 로그 저장."""
    _ensure_files()
    df.to_csv(LOGS_FILE, index=False)


def get_item(item_id: str) -> Optional[pd.Series]:
    """고유번호로 상품 1건 조회."""
    df = load_items()
    matches = df[df["item_id"] == item_id]
    if matches.empty:
        return None
    return matches.iloc[0]


def upsert_item(item: dict):
    """상품 등록 또는 수정 (item_id 기준)."""
    df = load_items()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    item.setdefault("created_at", now)
    item["updated_at"] = now

    mask = df["item_id"] == item["item_id"]
    if mask.any():
        for k, v in item.items():
            if k in df.columns and k != "created_at":
                df.loc[mask, k] = v
    else:
        new_row = {c: item.get(c, "") for c in ITEMS_COLUMNS}
        new_row["created_at"] = now
        new_row["updated_at"] = now
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    save_items(df)


def delete_item(item_id: str):
    """상품 삭제."""
    df = load_items()
    df = df[df["item_id"] != item_id]
    save_items(df)


def add_log(item_id: str, action: str, quantity: int = 0, worker: str = "", note: str = ""):
    """이력 로그 1건 추가."""
    df = load_logs()
    log_id = f"LOG-{datetime.now().strftime('%Y%m%d%H%M%S')}-{len(df)+1}"
    new_log = {
        "log_id": log_id,
        "item_id": item_id,
        "action": action,
        "quantity": str(quantity),
        "worker": worker,
        "note": note,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    df = pd.concat([df, pd.DataFrame([new_log])], ignore_index=True)
    save_logs(df)


def adjust_stock(item_id: str, delta: int, action: str, worker: str = "", note: str = ""):
    """재고 수량 변경 + 로그 기록."""
    df = load_items()
    mask = df["item_id"] == item_id
    if not mask.any():
        return False

    current = int(df.loc[mask, "stock"].values[0])
    new_stock = max(0, current + delta)
    df.loc[mask, "stock"] = new_stock
    df.loc[mask, "updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 상태 자동 갱신
    min_stock = int(df.loc[mask, "min_stock"].values[0])
    if new_stock == 0:
        df.loc[mask, "status"] = "위험"
    elif new_stock <= min_stock:
        df.loc[mask, "status"] = "주의"
    else:
        df.loc[mask, "status"] = "정상"

    save_items(df)
    add_log(item_id, action, delta, worker, note)
    return True


def calc_expiry_status(expiry_str: str, opened_str: str = "", shelf_days: int = 0) -> dict:
    """유통기한/개봉일 기반 상태 계산."""
    today = date.today()
    result = {"d_day": None, "opened_d_day": None, "color": "green", "label": "정상", "alert": ""}

    # 유통기한 D-Day
    if expiry_str:
        try:
            exp = datetime.strptime(expiry_str, "%Y-%m-%d").date()
            d = (exp - today).days
            result["d_day"] = d
            if d < 0:
                result.update(color="black", label="만료", alert=f"유통기한 {-d}일 경과!")
            elif d <= 3:
                result.update(color="red", label=f"D-{d}", alert=f"유통기한 {d}일 남음!")
            elif d <= 7:
                result.update(color="orange", label=f"D-{d}", alert=f"유통기한 {d}일 남음")
            else:
                result.update(color="green", label=f"D-{d}")
        except ValueError:
            pass

    # 개봉 후 사용기한
    if opened_str and shelf_days > 0:
        try:
            opened = datetime.strptime(opened_str, "%Y-%m-%d").date()
            used_days = (today - opened).days
            remain = shelf_days - used_days
            result["opened_d_day"] = remain
            if remain < 0:
                result.update(color="black", label="개봉 만료", alert=f"개봉 후 {-remain}일 초과!")
            elif remain <= 2:
                if result["color"] not in ("black",):
                    result.update(color="red", label=f"개봉 D-{remain}", alert=f"개봉 후 {remain}일 남음!")
        except ValueError:
            pass

    return result


def get_fifo_warning(item_id: str) -> str:
    """선입선출 경고: 같은 카테고리에서 먼저 들어온 상품이 있으면 알림."""
    df = load_items()
    item = df[df["item_id"] == item_id]
    if item.empty:
        return ""

    cat = item.iloc[0]["category"]
    created = item.iloc[0]["created_at"]
    if not cat or not created:
        return ""

    same_cat = df[(df["category"] == cat) & (df["item_id"] != item_id) & (df["stock"] > 0)]
    if same_cat.empty:
        return ""

    older = same_cat[same_cat["created_at"] < created]
    if older.empty:
        return ""

    return f"같은 카테고리({cat})에 먼저 입고된 상품이 {len(older)}개 있습니다. 선입선출을 권장합니다!"


def bulk_import_items(df_upload: pd.DataFrame, id_col: str, name_col: str, expiry_col: str = "", category_col: str = ""):
    """엑셀 업로드 데이터를 일괄 등록."""
    for _, row in df_upload.iterrows():
        item = {
            "item_id": str(row[id_col]),
            "name": str(row[name_col]),
            "category": str(row[category_col]) if category_col else "",
            "expiry_date": str(row[expiry_col]) if expiry_col else "",
            "stock": 1,
            "min_stock": 5,
            "status": "정상",
            "location": "",
            "memo": "",
        }
        upsert_item(item)
