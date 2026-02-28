import pandas as pd


def iqr_outliers_one_column(
    df: pd.DataFrame,
    column: str,
    *,
    multiplier: float = 1.5,
    include_bounds: bool = True,
):
    """
    IQR outlier detection for ONE numeric column.

    Rule:
      Q1 = 25th percentile
      Q3 = 75th percentile
      IQR = Q3 - Q1
      lower = Q1 - multiplier * IQR
      upper = Q3 + multiplier * IQR
      outlier if value < lower or value > upper
      (if include_bounds=False, uses <= and >= instead)

    Returns:
      dict with Q1, Q3, IQR, bounds, count, and outlier rows.

    Assumes:
      - df is already cleaned (no missing in that column, numeric)
    """

    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in DataFrame.")

    s = df[column]

    if not pd.api.types.is_numeric_dtype(s):
        raise ValueError(f"Column '{column}' must be numeric for IQR outlier detection.")

    if s.isna().any():
        raise ValueError(
            f"Column '{column}' contains missing values. Clean/impute before running IQR."
        )

    if len(s) < 4:
        raise ValueError("Too few rows to compute quartiles reliably (need at least 4).")

    if multiplier <= 0:
        raise ValueError("multiplier must be > 0.")

    # Quartiles + IQR
    q1 = float(s.quantile(0.25, interpolation="linear"))
    q3 = float(s.quantile(0.75, interpolation="linear"))
    iqr = q3 - q1

    # If all values are identical, IQR == 0 => bounds collapse; then no outliers unless include_bounds=False.
    lower = q1 - multiplier * iqr
    upper = q3 + multiplier * iqr

    if include_bounds:
        mask = (s < lower) | (s > upper)
        rule = f"value < {lower} OR value > {upper}"
    else:
        mask = (s <= lower) | (s >= upper)
        rule = f"value <= {lower} OR value >= {upper}"

    outliers = df.loc[mask].copy()

    return {
        "column": column,
        "multiplier": float(multiplier),
        "q1": q1,
        "q3": q3,
        "iqr": float(iqr),
        "lower_bound": float(lower),
        "upper_bound": float(upper),
        "n_outliers": int(mask.sum()),
        "outliers": outliers,
        "rule": rule,
    }