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
        scale_name = json.load(f)["scale_name"]
    return scale_name


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

    print(clf.coef_)
    slope = clf.coef_[0]
    return pd.Series(slope, index=["trend_slope"])



