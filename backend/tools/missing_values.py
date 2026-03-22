import pandas as pd

def is_missing_vals(dataset: pd.DataFrame) -> bool:
    """
    Checks to see if there are missing values in a dataset

    Args:
        dataset (DataFrame): dataset being checked for missing values

    Returns:
        bool: True if dataset contains missing values, otherwise False
    """
    missing = dataset.isna()
    return missing.any(axis=None)

def missing_val_rows(dataset: pd.DataFrame) -> pd.DataFrame:
    """
    Returns rows of dataset that contain missing values

    Args:
        dataset (DataFrame): dataset being checked for missing values

    Returns:
        DataFrame: Returns new dataset containing rows of missing values
    """
    missing = dataset.isna()
    return dataset[missing.any(axis=1)]

def missing_val_rows_indices(dataset: pd.DataFrame) -> list:
    """
    Returns indicies of rows from dataset that contain missing values

    Args:
        dataset (DataFrame): dataset being checked for missing values

    Returns:
        list[int]: Returns list of indices of rows containing missing values
    """
    missing = dataset.isna()
    return dataset[missing.any(axis=1)].index.to_list()

def remove_missing_rows(dataset: pd.DataFrame) -> pd.DataFrame:
    """
    Removes rows containing missing values

    Args:
        dataset (DataFrame): dataset being updated

    Returns:
        DataFrame: Returns DataFrame with missing value rows removed
    """
    return dataset.dropna()

def fill_mean(dataset: pd.DataFrame) -> pd.DataFrame:
    """
    Fills missing values with the mean of the column (numeric columns only)

    Args:
        dataset (DataFrame): dataset being updated

    Returns:
        DataFrame: Returns DataFrame with missing values as mean
    """
    means = dataset.mean(numeric_only=True)
    return dataset.fillna(means)

def fill_median(dataset: pd.DataFrame) -> pd.DataFrame:
    """
    Fills missing values with the median of the column (numeric columns only)

    Args:
        dataset (DataFrame): dataset being updated

    Returns:
        DataFrame: Returns DataFrame with missing values as median
    """
    medians = dataset.median(numeric_only=True)
    return dataset.fillna(medians)


def backfill(dataset: pd.DataFrame) -> pd.DataFrame:
    """
    Fills missing values with the value that comes after it columnwise

    Args:
        dataset (DataFrame): dataset being updated

    Returns:
        DataFrame: Returns DataFrame with missing values back filled
    """
    return dataset.bfill(axis=0)

def forwardfill(dataset: pd.DataFrame) -> pd.DataFrame:
    """
    Fills missing values with the value that comes before it columnwise

    Args:
        dataset (DataFrame): dataset being updated

    Returns:
        DataFrame: Returns DataFrame with missing values forward filled
    """
    return dataset.ffill(axis=0)

def bothfill(dataset: pd.DataFrame) -> pd.DataFrame:
    """
    Use both back fill and foward fill

    Args:
        dataset (DataFrame): dataset being updated

    Returns:
        DataFrame: Returns DataFrame with no missing values
    """
    return dataset.ffill(axis=0).bfill(axis=0)
