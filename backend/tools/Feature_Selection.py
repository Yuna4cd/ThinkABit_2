"""
feature_selection.py
---------------------
Standalone tool for performing feature selection on a dataset.

Feature selection is the process of identifying which columns (features)
in a dataset are relevant, important, or redundant — helping users focus
their analysis on the columns that actually matter.

This file will be integrated into the main project later. For now it
operates directly on a pandas DataFrame.

WHAT THIS FILE DOES
-------------------
1. RELEVANCE SCORING
   Scores each column 0.0-1.0 based on how useful it is likely to be
   for analysis, considering:
     - Data type       : numeric columns score higher than pure text
     - Missing rate    : columns with many missing values score lower
     - Uniqueness      : ID-like columns (nearly all unique) score low
     - Variance        : near-constant columns score low

2. REDUNDANCY DETECTION
   Flags columns that are highly correlated with another column (>0.95
   correlation) — keeping one and marking the other as redundant.

3. RECOMMENDATIONS
   Marks each column as recommended to keep or remove, with a
   plain-English reason so the user understands the decision.

USAGE
-----
    import pandas as pd
    from feature_selection import select_features

    df = pd.read_csv("your_dataset.csv")
    result = select_features(df)

    print(result["recommended"])   # columns to keep
    print(result["to_remove"])     # columns to remove
    for col in result["columns"]:  # full ranked breakdown
        print(col)
"""

import pandas as pd


# ── Relevance levels ──────────────────────────────────────────────────────────
HIGH       = "high"
MEDIUM     = "medium"
LOW        = "low"
REDUNDANT  = "redundant"

# Correlation threshold above which a column is considered redundant
CORRELATION_THRESHOLD = 0.95


def select_features(
    dataframe: pd.DataFrame,
    selected_columns: list[str] | None = None,
    target_column: str | None = None,
) -> dict:
    """
    Assess all columns (or a chosen subset) and return a feature
    selection result.

    Parameters
    ----------
    dataframe        : The dataset to analyse as a pandas DataFrame.
    selected_columns : Optional list of column names to assess. When None
                       all columns are assessed.
    target_column    : Optional column the user wants to predict or analyse.
                       When provided, importance scores are calculated
                       relative to this column.

    Returns
    -------
    dict with keys:
        "total_columns"     : int   — total columns assessed
        "recommended_count" : int   — number of columns recommended to keep
        "columns"           : list  — full ranked breakdown, each entry is a dict:
                                        column_name, relevance, importance_score,
                                        missing_percent, is_recommended, reason
        "recommended"       : list[str] — column names to keep
        "to_remove"         : list[str] — column names to remove
        "warnings"          : list[str] — human-readable messages

    Raises
    ------
    ValueError — when selected_columns references columns not in the dataset.
    ValueError — when target_column is not found in the dataset.
    """
    # Validate selected columns
    if selected_columns:
        unknown = [c for c in selected_columns if c not in dataframe.columns]
        if unknown:
            raise ValueError(
                f"The following columns were not found in the dataset: {unknown}"
            )
        working_df = dataframe[selected_columns].copy()
    else:
        working_df = dataframe.copy()

    # Validate target column
    if target_column and target_column not in dataframe.columns:
        raise ValueError(
            f"Target column '{target_column}' not found in the dataset."
        )

    total_rows = len(working_df)
    assessments: list[dict] = []

    # Score every column
    for col in working_df.columns:
        series = working_df[col]
        missing_count   = int(series.isna().sum())
        missing_percent = round((missing_count / total_rows) * 100, 2) if total_rows > 0 else 0.0
        score, reason   = _score_column(series, col, missing_percent, target_column, working_df)
        relevance       = _score_to_relevance(score)

        assessments.append({
            "column_name":      col,
            "relevance":        relevance,
            "importance_score": round(score, 3),
            "missing_percent":  missing_percent,
            "is_recommended":   relevance in (HIGH, MEDIUM),
            "reason":           reason,
        })

    # Detect and flag redundant columns
    assessments = _flag_redundant_columns(assessments, working_df)

    # Sort by importance score descending
    assessments.sort(key=lambda a: a["importance_score"], reverse=True)

    recommended = [a["column_name"] for a in assessments if a["is_recommended"]]
    to_remove   = [a["column_name"] for a in assessments if not a["is_recommended"]]

    # Build warnings
    warnings: list[str] = []
    if to_remove:
        warnings.append(
            f"{len(to_remove)} column(s) are recommended for removal: {to_remove}."
        )
    if not recommended:
        warnings.append(
            "No columns were rated highly enough to recommend. "
            "Consider reviewing your dataset for quality issues."
        )

    return {
        "total_columns":     len(assessments),
        "recommended_count": len(recommended),
        "columns":           assessments,
        "recommended":       recommended,
        "to_remove":         to_remove,
        "warnings":          warnings,
    }


# ── Scoring helpers ───────────────────────────────────────────────────────────

def _score_column(
    series: pd.Series,
    col_name: str,
    missing_percent: float,
    target_column: str | None,
    dataframe: pd.DataFrame,
) -> tuple[float, str]:
    """
    Score a single column 0.0-1.0 and return a plain-English reason.

    TODO: When a target_column is provided, replace the heuristic score
    with a real correlation or mutual information score against the target:
        from sklearn.feature_selection import mutual_info_classif
    """
    score = 0.5  # base score
    reasons: list[str] = []

    # Penalise for high missing rate
    if missing_percent > 75:
        score -= 0.4
        reasons.append(f"{missing_percent}% of values are missing")
    elif missing_percent > 50:
        score -= 0.2
        reasons.append(f"{missing_percent}% of values are missing")
    elif missing_percent > 25:
        score -= 0.1
        reasons.append(f"{missing_percent}% of values are missing")

    non_null = series.dropna()

    if pd.api.types.is_numeric_dtype(series):
        score += 0.2
        # Near-constant columns add no information
        if len(non_null) > 1 and non_null.std() == 0:
            score -= 0.3
            reasons.append("column has no variance (all values are the same)")
        else:
            reasons.append("numeric column with analytical value")
    else:
        if len(non_null) > 0:
            unique_ratio = non_null.nunique() / len(non_null)
            if unique_ratio > 0.95:
                # Nearly all values unique — likely an ID column
                score -= 0.3
                reasons.append("nearly all values are unique (likely an ID column)")
            elif non_null.nunique() <= 20:
                # Low-cardinality categorical — good for grouping
                score += 0.1
                reasons.append("categorical column suitable for grouping")
            else:
                reasons.append("high-cardinality text column")

    score  = max(0.0, min(1.0, score))
    reason = "; ".join(reasons) if reasons else "standard column"
    return score, reason


def _score_to_relevance(score: float) -> str:
    if score >= 0.6:
        return HIGH
    if score >= 0.4:
        return MEDIUM
    return LOW


def _flag_redundant_columns(
    assessments: list[dict],
    dataframe: pd.DataFrame,
) -> list[dict]:
    """
    Detect pairs of numeric columns with correlation above
    CORRELATION_THRESHOLD and flag the lower-scoring one as redundant.
    """
    numeric_cols = dataframe.select_dtypes(include="number").columns.tolist()
    if len(numeric_cols) < 2:
        return assessments

    corr_matrix = dataframe[numeric_cols].corr().abs()
    flagged: set[str] = set()

    for i in range(len(numeric_cols)):
        for j in range(i + 1, len(numeric_cols)):
            col_a = numeric_cols[i]
            col_b = numeric_cols[j]
            if corr_matrix.loc[col_a, col_b] > CORRELATION_THRESHOLD:
                score_a = next((a["importance_score"] for a in assessments if a["column_name"] == col_a), 0)
                score_b = next((a["importance_score"] for a in assessments if a["column_name"] == col_b), 0)
                flagged.add(col_b if score_a >= score_b else col_a)

    updated: list[dict] = []
    for a in assessments:
        if a["column_name"] in flagged:
            updated.append({
                **a,
                "relevance":      REDUNDANT,
                "is_recommended": False,
                "reason":         a["reason"] + "; highly correlated with another column (redundant)",
            })
        else:
            updated.append(a)
    return updated


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    sample_df = pd.DataFrame({
        "order_id":     ["A001", "A002", "A003", "A004", "A005"],
        "first_name":   ["Alice", "Bob", "Carol", "Diana", "Eve"],
        "unit_price":   [10.0, 25.0, 15.0, 30.0, 20.0],
        "quantity":     [3, 2, 5, 1, 4],
        "revenue":      [30.0, 50.0, 75.0, 30.0, 80.0],
        "category":     ["A", "B", "A", "C", "B"],
        "constant_col": [1, 1, 1, 1, 1],
    })

    result = select_features(sample_df)

    print(f"Total columns  : {result['total_columns']}")
    print(f"Recommended    : {result['recommended']}")
    print(f"To remove      : {result['to_remove']}")
    print()
    for col in result["columns"]:
        print(
            f"  [{col['relevance']:<9}] {col['column_name']:<14} "
            f"score={col['importance_score']}  {col['reason']}"
        )
    print()
    for w in result["warnings"]:
        print(f"  WARNING: {w}")