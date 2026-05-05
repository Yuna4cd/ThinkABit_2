from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import pandas as pd
import numpy as np
from scipy.stats import chi2

router = APIRouter()

# ── Request models ────────────────────────────────────────────────────────────

class IQRRequest(BaseModel):
    data: list[dict]
    column: str
    multiplier: float = 1.5

class MahalanobisRequest(BaseModel):
    data: list[dict]
    alpha: float = 0.01
    
class SummaryRequest(BaseModel):
    data: list[dict]

# ── IQR endpoint ──────────────────────────────────────────────────────────────

@router.post("/analyze/iqr")
def iqr_outliers(body: IQRRequest):
    df = pd.DataFrame(body.data)
    s = df[body.column]

    q1 = float(s.quantile(0.25))
    q3 = float(s.quantile(0.75))
    iqr = q3 - q1
    lower = q1 - body.multiplier * iqr
    upper = q3 + body.multiplier * iqr

    mask = (s < lower) | (s > upper)

    return {
        "column": body.column,
        "q1": q1,
        "q3": q3,
        "iqr": iqr,
        "lower_bound": lower,
        "upper_bound": upper,
        "n_outliers": int(mask.sum()),
        "outlier_indices": df[mask].index.tolist(),
    }

# ── Mahalanobis endpoint ──────────────────────────────────────────────────────

@router.post("/analyze/mahalanobis")
def mahalanobis_outliers(body: MahalanobisRequest):
    df = pd.DataFrame(body.data)
    numeric_df = df.select_dtypes(include=[np.number]).dropna()

    if numeric_df.shape[1] < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 numeric columns for Mahalanobis distance.")

    X = numeric_df.values
    n, k = X.shape

    if n <= k:
        raise HTTPException(status_code=400, detail="Number of rows must be greater than number of columns.")

    mean = np.mean(X, axis=0)
    cov = np.cov(X, rowvar=False)

    try:
        inv_cov = np.linalg.inv(cov)
    except np.linalg.LinAlgError:
        raise HTTPException(status_code=400, detail="Covariance matrix is singular.")

    centered = X - mean
    d_squared = np.sum((centered @ inv_cov) * centered, axis=1)
    distances = np.sqrt(d_squared).tolist()

    threshold = float(np.sqrt(chi2.ppf(1 - body.alpha, df=k)))
    is_outlier = [d > threshold for d in distances]

    return {
        "distances": distances,
        "threshold": threshold,
        "n_outliers": sum(is_outlier),
        "outlier_indices": [i for i, v in enumerate(is_outlier) if v],
    }

@router.post("/analyze/summary")
def summary_stats(body: SummaryRequest):
    df = pd.DataFrame(body.data)
    numeric_df = df.select_dtypes(include=[np.number])

    result = {}
    for col in numeric_df.columns:
        s = numeric_df[col].dropna()
        result[col] = {
            "count": int(s.count()),
            "missing": int(df[col].isna().sum()),
            "mean": round(float(s.mean()), 2),
            "median": round(float(s.median()), 2),
            "std": round(float(s.std()), 2),
            "min": round(float(s.min()), 2),
            "max": round(float(s.max()), 2),
            "q1": round(float(s.quantile(0.25)), 2),
            "q3": round(float(s.quantile(0.75)), 2),
            "skewness": round(float(s.skew()), 2),
        }

    return {"summary": result}

@router.post("/analyze/correlation")
def correlation(body: SummaryRequest):
    df = pd.DataFrame(body.data)
    numeric_df = df.select_dtypes(include=[np.number]).dropna()

    if numeric_df.shape[1] < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 numeric columns for correlation.")

    corr_matrix = numeric_df.corr().round(2)
    columns = corr_matrix.columns.tolist()

    result = []
    for col in columns:
        for other_col in columns:
            result.append({
                "col1": col,
                "col2": other_col,
                "correlation": float(corr_matrix[col][other_col]),
            })

    return {
        "columns": columns,
        "matrix": result,
    }