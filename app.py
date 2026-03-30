import os
import json
import numpy as np
from flask import Flask, request, jsonify, render_template
import pandas as pd


def to_native(obj):
    """numpy/pandas 타입을 Python 네이티브 타입으로 변환"""
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, dict):
        return {k: to_native(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_native(v) for v in obj]
    if pd.isna(obj):
        return None
    return obj

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify(error="파일을 선택해주세요."), 400

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in (".xlsx", ".xls", ".csv"):
        return jsonify(error="엑셀(.xlsx, .xls) 또는 CSV 파일만 지원합니다."), 400

    filepath = os.path.join(UPLOAD_DIR, file.filename)
    file.save(filepath)

    try:
        if ext == ".csv":
            df = pd.read_csv(filepath)
        else:
            df = pd.read_excel(filepath, engine="openpyxl")
    except Exception as e:
        return jsonify(error=f"파일 읽기 실패: {e}"), 400

    # 기본 정보
    summary = {
        "filename": file.filename,
        "rows": len(df),
        "columns": list(df.columns),
    }

    # 숫자형 / 문자형 컬럼 분리
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    text_cols = df.select_dtypes(exclude="number").columns.tolist()

    # 숫자형 컬럼 통계
    stats = {}
    for col in numeric_cols:
        stats[col] = {
            "합계": round(df[col].sum(), 2),
            "평균": round(df[col].mean(), 2),
            "최대": round(df[col].max(), 2),
            "최소": round(df[col].min(), 2),
        }

    # 차트 데이터 자동 생성
    charts = []

    # 1) 첫 번째 텍스트 컬럼 × 각 숫자 컬럼 → 막대 차트
    if text_cols and numeric_cols:
        label_col = text_cols[0]
        labels = df[label_col].astype(str).tolist()

        # 라벨이 너무 많으면 상위 20개만
        if len(labels) > 20:
            df_top = df.head(20)
            labels = df_top[label_col].astype(str).tolist()
        else:
            df_top = df

        for ncol in numeric_cols[:5]:  # 최대 5개 차트
            charts.append({
                "title": f"{label_col} 별 {ncol}",
                "type": "bar",
                "labels": labels,
                "datasets": [{
                    "label": ncol,
                    "data": df_top[ncol].fillna(0).round(2).tolist(),
                }],
            })

    # 2) 텍스트 컬럼의 값 분포 → 파이 차트
    for tcol in text_cols[:2]:
        counts = df[tcol].value_counts().head(10)
        charts.append({
            "title": f"{tcol} 분포",
            "type": "pie",
            "labels": counts.index.astype(str).tolist(),
            "datasets": [{
                "label": tcol,
                "data": counts.values.tolist(),
            }],
        })

    # 3) 숫자 컬럼끼리 추세 → 라인 차트 (행 인덱스 기준)
    if len(numeric_cols) >= 2:
        line_labels = list(range(1, min(len(df) + 1, 51)))  # 최대 50행
        datasets = []
        for ncol in numeric_cols[:4]:
            datasets.append({
                "label": ncol,
                "data": df[ncol].head(50).fillna(0).round(2).tolist(),
            })
        charts.append({
            "title": "숫자 컬럼 추세",
            "type": "line",
            "labels": line_labels,
            "datasets": datasets,
        })

    # 테이블 미리보기 (상위 30행)
    preview = df.head(30).fillna("").to_dict(orient="records")

    result = to_native({
        "summary": summary,
        "stats": stats,
        "charts": charts,
        "preview": preview,
        "numeric_cols": numeric_cols,
        "text_cols": text_cols,
    })

    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
