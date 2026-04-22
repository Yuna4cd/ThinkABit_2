"""
feature_engineering.py
------------------------
Standalone tool for performing feature engineering on a dataset.

Feature engineering is the process of creating new columns from existing
ones or transforming existing columns into a more useful form — helping
users get more value out of their data before analysis or visualization.

This file will be integrated into the main project later. For now it
operates directly on a pandas DataFrame.

WHAT THIS FILE DOES
-------------------
1. COMBINING COLUMNS
   Creates a new column by combining two existing columns:
     - concatenate : joins two text columns  e.g. "Alice" + "Smith" → "Alice Smith"
     - add         : adds two numeric columns        price + tax → total
     - subtract    : subtracts one from another      total - discount → final
     - multiply    : multiplies two numeric columns  quantity × price → revenue
     - divide      : divides one column by another   revenue ÷ quantity → avg_price

2. TRANSFORMING COLUMNS
   Modifies an existing column into a more useful form:
     - normalize   : scales values to 0-1 range (min-max scaling)
     - standardize : scales to mean=0, std=1 (z-score)
     - encode      : converts category labels to numeric codes
     - log         : applies natural log to reduce skew
     - bin         : groups values into equal-width buckets

USAGE
-----
    import pandas as pd
    from feature_engineering import combine_columns, transform_column, engineer_features

    df = pd.read_csv("your_dataset.csv")

    # Combine two columns
    df, result = combine_columns(df, "first_name", "last_name",
                                 strategy="concatenate", new_column_name="full_name")

    # Transform a column
    df, result = transform_column(df, "unit_price", strategy="normalize",
                                  new_column_name="unit_price_norm")

    # Or apply multiple operations at once
    operations = {
        "combine": [
            {"column_a": "first_name", "column_b": "last_name",
             "strategy": "concatenate", "new_column_name": "full_name"},
            {"column_a": "unit_price", "column_b": "quantity",
             "strategy": "multiply", "new_column_name": "total_price"},
        ],
        "transform": [
            {"column_name": "unit_price", "strategy": "normalize",
             "new_column_name": "unit_price_norm"},
            {"column_name": "category", "strategy": "encode",
             "new_column_name": "category_encoded"},
        ],
    }
    df, result = engineer_features(df, operations)
    print(result["operations_applied"])
    print(result["new_columns"])
"""

import math
import pandas as pd


# ── Supported strategies ──────────────────────────────────────────────────────
COMBINE_STRATEGIES   = {"concatenate", "add", "subtract", "multiply", "divide"}
TRANSFORM_STRATEGIES = {"normalize", "standardize", "encode", "log", "bin"}


def combine_columns(
    dataframe: pd.DataFrame,
    column_a: str,
    column_b: str,
    strategy: str,
    new_column_name: str,
) -> tuple[pd.DataFrame, dict]:
    """
    Create a new column by combining two existing columns.

    Parameters
    ----------
    dataframe       : The dataset as a pandas DataFrame.
    column_a        : Name of the first source column.
    column_b        : Name of the second source column.
    strategy        : How to combine them. One of:
                      "concatenate", "add", "subtract", "multiply", "divide"
    new_column_name : Name for the new column.

    Returns
    -------
    tuple[pd.DataFrame, dict]
        - Updated DataFrame with the new column added.
        - Result dict with keys: success (bool), column (str),
          description (str), warning (str or None).

    Raises
    ------
    ValueError — when an unsupported strategy is given.
    """
    if strategy not in COMBINE_STRATEGIES:
        raise ValueError(
            f"Unsupported combine strategy '{strategy}'. "
            f"Must be one of: {sorted(COMBINE_STRATEGIES)}"
        )

    # Validate both columns exist
    for col in (column_a, column_b):
        if col not in dataframe.columns:
            return dataframe, {
                "success":     False,
                "column":      new_column_name,
                "description": None,
                "warning":     f"Combine skipped: column '{col}' not found in dataset.",
            }

    df = dataframe.copy()
    a, b = df[column_a], df[column_b]

    try:
        if strategy == "concatenate":
            df[new_column_name] = a.astype(str) + " " + b.astype(str)
            description = f"Joined '{column_a}' and '{column_b}' as text into '{new_column_name}'."

        elif strategy == "add":
            df[new_column_name] = pd.to_numeric(a, errors="coerce") + pd.to_numeric(b, errors="coerce")
            description = f"Added '{column_a}' + '{column_b}' into '{new_column_name}'."

        elif strategy == "subtract":
            df[new_column_name] = pd.to_numeric(a, errors="coerce") - pd.to_numeric(b, errors="coerce")
            description = f"Subtracted '{column_b}' from '{column_a}' into '{new_column_name}'."

        elif strategy == "multiply":
            df[new_column_name] = pd.to_numeric(a, errors="coerce") * pd.to_numeric(b, errors="coerce")
            description = f"Multiplied '{column_a}' × '{column_b}' into '{new_column_name}'."

        elif strategy == "divide":
            num_b = pd.to_numeric(b, errors="coerce").replace(0, float("nan"))
            df[new_column_name] = pd.to_numeric(a, errors="coerce") / num_b
            description = f"Divided '{column_a}' ÷ '{column_b}' into '{new_column_name}' (zero → null)."

    except Exception as exc:
        return dataframe, {
            "success":     False,
            "column":      new_column_name,
            "description": None,
            "warning":     f"Combine '{new_column_name}' failed: {str(exc)[:100]}.",
        }

    return df, {
        "success":     True,
        "column":      new_column_name,
        "description": description,
        "warning":     None,
    }


def transform_column(
    dataframe: pd.DataFrame,
    column_name: str,
    strategy: str,
    new_column_name: str | None = None,
    num_bins: int = 5,
) -> tuple[pd.DataFrame, dict]:
    """
    Transform an existing column and store the result in a new column
    (or overwrite the original if new_column_name is None).

    Parameters
    ----------
    dataframe       : The dataset as a pandas DataFrame.
    column_name     : Name of the column to transform.
    strategy        : How to transform it. One of:
                      "normalize", "standardize", "encode", "log", "bin"
    new_column_name : Name for the result column. When None the original
                      column is overwritten.
    num_bins        : Number of bins for "bin" strategy. Default 5.

    Returns
    -------
    tuple[pd.DataFrame, dict]
        - Updated DataFrame with the transformed column.
        - Result dict with keys: success (bool), column (str),
          description (str or None), warning (str or None).

    Raises
    ------
    ValueError — when an unsupported strategy is given.
    """
    if strategy not in TRANSFORM_STRATEGIES:
        raise ValueError(
            f"Unsupported transform strategy '{strategy}'. "
            f"Must be one of: {sorted(TRANSFORM_STRATEGIES)}"
        )

    result_col = new_column_name if new_column_name else column_name

    if column_name not in dataframe.columns:
        return dataframe, {
            "success":     False,
            "column":      result_col,
            "description": None,
            "warning":     f"Transform skipped: column '{column_name}' not found in dataset.",
        }

    df     = dataframe.copy()
    series = df[column_name]

    try:
        if strategy == "normalize":
            numeric        = pd.to_numeric(series, errors="coerce")
            col_min, col_max = numeric.min(), numeric.max()
            if col_max == col_min:
                return dataframe, {
                    "success": False, "column": result_col, "description": None,
                    "warning": f"Normalize skipped for '{column_name}': all values are the same.",
                }
            df[result_col] = (numeric - col_min) / (col_max - col_min)
            description    = f"Scaled '{column_name}' to 0-1 range into '{result_col}'."

        elif strategy == "standardize":
            numeric        = pd.to_numeric(series, errors="coerce")
            mean, std      = numeric.mean(), numeric.std()
            if std == 0:
                return dataframe, {
                    "success": False, "column": result_col, "description": None,
                    "warning": f"Standardize skipped for '{column_name}': standard deviation is zero.",
                }
            df[result_col] = (numeric - mean) / std
            description    = f"Standardized '{column_name}' to mean=0, std=1 into '{result_col}'."

        elif strategy == "encode":
            categories     = series.astype(str).unique()
            mapping        = {cat: idx for idx, cat in enumerate(sorted(categories))}
            df[result_col] = series.astype(str).map(mapping)
            description    = (
                f"Encoded categories in '{column_name}' as numbers into '{result_col}'. "
                f"Mapping: {mapping}"
            )

        elif strategy == "log":
            numeric = pd.to_numeric(series, errors="coerce")
            if (numeric <= 0).any():
                return dataframe, {
                    "success": False, "column": result_col, "description": None,
                    "warning": (
                        f"Log transform skipped for '{column_name}': "
                        f"column contains zero or negative values."
                    ),
                }
            df[result_col] = numeric.apply(math.log)
            description    = f"Applied natural log to '{column_name}' into '{result_col}'."

        elif strategy == "bin":
            numeric        = pd.to_numeric(series, errors="coerce")
            df[result_col] = pd.cut(numeric, bins=num_bins, labels=False)
            description    = f"Grouped '{column_name}' into {num_bins} equal-width bins into '{result_col}'."

    except Exception as exc:
        return dataframe, {
            "success":     False,
            "column":      result_col,
            "description": None,
            "warning":     f"Transform '{strategy}' failed for '{column_name}': {str(exc)[:100]}.",
        }

    return df, {
        "success":     True,
        "column":      result_col,
        "description": description,
        "warning":     None,
    }


def engineer_features(
    dataframe: pd.DataFrame,
    operations: dict,
) -> tuple[pd.DataFrame, dict]:
    """
    Apply multiple combine and/or transform operations in one call.

    Parameters
    ----------
    dataframe  : The dataset as a pandas DataFrame.
    operations : Dict with optional keys:
                   "combine"   : list of combine operation dicts, each with:
                                   column_a, column_b, strategy, new_column_name
                   "transform" : list of transform operation dicts, each with:
                                   column_name, strategy,
                                   new_column_name (optional),
                                   num_bins (optional, default 5)

    Returns
    -------
    tuple[pd.DataFrame, dict]
        - Updated DataFrame with all successful operations applied.
        - Summary dict with keys:
            operations_applied  : int
            new_columns         : list[str]  — brand new columns created
            transformed_columns : list[str]  — existing columns modified
            operations          : list[dict] — log of every operation
            warnings            : list[str]  — skipped operations

    Raises
    ------
    ValueError — when no operations are provided.
    """
    combine_ops   = operations.get("combine",   [])
    transform_ops = operations.get("transform", [])

    if not combine_ops and not transform_ops:
        raise ValueError("At least one combine or transform operation must be provided.")

    df                   = dataframe.copy()
    applied:      list[dict] = []
    new_columns:  list[str]  = []
    transformed:  list[str]  = []
    warnings:     list[str]  = []

    # Apply combine operations first
    for op in combine_ops:
        df, result = combine_columns(
            df,
            column_a        = op["column_a"],
            column_b        = op["column_b"],
            strategy        = op["strategy"],
            new_column_name = op["new_column_name"],
        )
        if result["success"]:
            new_columns.append(result["column"])
            applied.append({"type": "combine", "column": result["column"], "description": result["description"]})
        else:
            warnings.append(result["warning"])

    # Apply transform operations
    for op in transform_ops:
        df, result = transform_column(
            df,
            column_name     = op["column_name"],
            strategy        = op["strategy"],
            new_column_name = op.get("new_column_name"),
            num_bins        = op.get("num_bins", 5),
        )
        if result["success"]:
            if op.get("new_column_name"):
                new_columns.append(result["column"])
            else:
                transformed.append(result["column"])
            applied.append({"type": "transform", "column": result["column"], "description": result["description"]})
        else:
            warnings.append(result["warning"])

    return df, {
        "operations_applied":   len(applied),
        "new_columns":          new_columns,
        "transformed_columns":  transformed,
        "operations":           applied,
        "warnings":             warnings,
    }


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    sample_df = pd.DataFrame({
        "order_id":   ["A001", "A002", "A003", "A004", "A005"],
        "first_name": ["Alice", "Bob", "Carol", "Diana", "Eve"],
        "last_name":  ["Smith", "Jones", "White", "Brown", "Davis"],
        "unit_price": [10.0, 25.0, 15.0, 30.0, 20.0],
        "quantity":   [3, 2, 5, 1, 4],
        "category":   ["A", "B", "A", "C", "B"],
    })

    updated_df, result = engineer_features(sample_df, {
        "combine": [
            {"column_a": "first_name", "column_b": "last_name",
             "strategy": "concatenate", "new_column_name": "full_name"},
            {"column_a": "unit_price", "column_b": "quantity",
             "strategy": "multiply",    "new_column_name": "total_price"},
        ],
        "transform": [
            {"column_name": "unit_price", "strategy": "normalize",
             "new_column_name": "unit_price_norm"},
            {"column_name": "category",   "strategy": "encode",
             "new_column_name": "category_encoded"},
        ],
    })

    print(f"Operations applied  : {result['operations_applied']}")
    print(f"New columns         : {result['new_columns']}")
    print(f"Transformed columns : {result['transformed_columns']}")
    print()
    for op in result["operations"]:
        print(f"  [{op['type']:<9}] {op['description']}")
    print()
    print(updated_df[["full_name", "total_price", "unit_price_norm", "category_encoded"]].to_string())