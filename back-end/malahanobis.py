import numpy as np
import pandas as pd
from scipy.stats import chi2

def mahalanobis_outliers(df: pd.DataFrame, alpha: float = 0.01):
    """
    Compute Mahalanobis distance for each row and flag outliers.

    Assumes:
    - df contains only numeric features
    - No missing values
    - Data has already been cleaned
    """

    # Convert to numpy
    X = df.values
    n, k = X.shape

    if k < 2:
        raise ValueError("Mahalanobis distance requires at least 2 features.")

    if n <= k:
        raise ValueError("Number of rows must be greater than number of features.")

    # Step 1: Compute mean
    mean = np.mean(X, axis=0)

    # Step 2: Compute covariance matrix
    cov = np.cov(X, rowvar=False)

    # Step 3: Invert covariance
    try:
        inv_cov = np.linalg.inv(cov)
    except np.linalg.LinAlgError:
        raise ValueError("Covariance matrix is singular and cannot be inverted.")

    # Step 4: Compute Mahalanobis distance
    centered = X - mean
    left = centered @ inv_cov
    d_squared = np.sum(left * centered, axis=1)
    distances = np.sqrt(d_squared)

    # Step 5: Chi-square threshold
    threshold = np.sqrt(chi2.ppf(1 - alpha, df=k))

    # Step 6: Flag outliers
    is_outlier = distances > threshold
    outliers = df[is_outlier]

    return {
        "distances": distances,
        "threshold": threshold,
        "n_outliers": int(np.sum(is_outlier)),
        "outliers": outliers
    }