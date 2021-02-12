import re, os, json
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
    return data


def read_data_from_json(json_filename):
    all_data = []
    dirname=os.path.dirname(json_filename)    
    with open(json_filename) as f:
        inputs = json.load(f)["inputs"]

    for ip in inputs:
        scale = ip["scale"]
        filename = ip["file"]
        data = parse_file(dirname + "/" + filename)
        for d in data:
            d["scale"] = scale
        all_data = all_data + data 
    return all_data


def read_metadata_from_json(json_filename):
    with open(json_filename) as f:
        contents = json.load(f)
        scale_name = contents["scale_name"] if "scale_name" in contents else "scale"
        max_scale  = contents["max_scale"] if "max_scale" in contents else -1

    return scale_name, max_scale


def calc_poly_trend(group):
    fitted = np.polyfit(group.scale, group.value, deg=1)
    #print(fitted)
    slope = fitted[0]
    return pd.Series(slope, index=["trend_slope"])


def classify_trend(row):
    slope_column_name = "trend_slope"
    slope = row[slope_column_name]
    tolerance = 1e-10
    if(np.abs(slope) < tolerance): # treat very small slopes as flat
        return "flat"
    elif(slope > 0.0):
        return "positive"
    if(slope < 0.0):
        return "negative"


#WIP
def calc_ridge_trend(group):
    clf = Ridge(alpha=1.0)
    clf.fit(group.scale.to_numpy().reshape(-1, 1), group.value)
    slope = clf.coef_[0]
    return pd.Series(slope, index=["trend_slope"])


#WIP
def get_ridge_model(group):
    clf = Ridge(alpha=1.0)
    clf.fit(group.scale.to_numpy().reshape(-1, 1), group.value)
    #return clf
    return pd.Series(clf, index=["ridge_model"])


def get_linspace(row):
    return np.linspace(start=row.min_scale, stop=row.max_scale, num=50, dtype="int")

def get_ridge_extrapolation(row):
    #X = np.linspace(start=row.min_scale, stop=row.max_scale, num=100).reshape(-1,1)
    X = row.projected_scale.reshape(-1,1)
    return row.ridge_model.predict(X)[0]
## user defines max scale
## we fit ridge or svr to the data
## then we take a space (linear or exponential) between largest measured scale and max scale
## then use the fitted model to predict values for each intermediate point
## plot the extrapolation! Or print the last one that doesn't overflow and the first one that does.
