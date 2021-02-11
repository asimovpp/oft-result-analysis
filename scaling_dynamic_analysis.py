import re
import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge


rx_dict = {"data_line": re.compile(r"Rank (-?\d+); Value (\d+) maxed at (-?\d+)")}


def _parse_line(line, rx_dict):
    for key, rx in rx_dict.items():
        match = rx.search(line)
        if match:
            return key, match

    return None, None


def parse_file(filename):
    data = []

    with open(filename, "r") as f:
        for line in f:
            #print(line)
            key, m = _parse_line(line, rx_dict)
            if m:
                rank = int(m.group(1))
                val_id = int(m.group(2))
                val = int(m.group(3))
                datum = {"rank": rank, "value_id": val_id, "value": val, "filename": filename}
                data.append(datum)
    
    world_size = max([datum["rank"] for datum in data]) + 1
    for datum in data:
        datum["world_size"] = world_size

    return data


def almost_zero(group):
    tolerance = 1e-10
    if (group["trend_slope"].abs() < tolerance).any():
        if (group["value"] == group["value"][0]).all(): 
            group["trend_slope"] = 0
    
    return group["trend_slope"]


def calc_trend(group):
    fitted = np.polyfit(group.world_size, group.value, deg=2)
    print(fitted)
    slope = fitted[0]
    tolerance = 1e-10
    if np.abs(slope) < tolerance:
        slope = 0.0
    return pd.Series(slope, index=["trend_slope"])


def calc_ridge(group):
    clf = Ridge(alpha=1.0)
    clf.fit(X, y)

    fitted = np.polyfit(group.world_size, group.value, deg=2)
    print(fitted)
    slope = fitted[0]
    tolerance = 1e-10
    if np.abs(slope) < tolerance:
        slope = 0.0
    return pd.Series(slope, index=["trend_slope"])


def classify_trend(row):
    slope_column_name = "trend_slope"
    if(row[slope_column_name] == 0.0):
        return "flat"
    elif(row[slope_column_name] > 0.0):
        return "positive"
    if(row[slope_column_name] < 0.0):
        return "negative"

