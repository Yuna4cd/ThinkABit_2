import statsmodels.api as sm
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import numpy as np
import pandas as pd

def linear_regression(dataset: pd.DataFrame, y: str) -> tuple[float, float, float]:
    """
    Applies linear regression to the dataset and returns performance metrics

    Args:
        dataset (DataFrame): dataset being used
        y (str): Target column name

    Returns:
        tuple: standard deviation of the test data, rmse, and r^2 value
    """
    target = dataset[y]

    #ensuring only numeric columns and splitting training and testing data
    numeric = dataset.select_dtypes(include='number')
    X = numeric.drop(y, axis=1)
    X_train, X_test, y_train, y_test = train_test_split(X, target, test_size=0.2)

    #using a standard scaler to account for columns with different units
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    #train and predict using linear regression
    model = sm.OLS(y_train, X_train_scaled).fit()
    y_pred = model.predict(X_test_scaled)

    #calculating performance metrics
    std = np.std(y_test)
    rmse = mean_squared_error(y_test, y_pred) ** 1/2
    r2 = r2_score(y_test, y_pred)
    

    return std, rmse, r2
