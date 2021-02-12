import re, os, json
import pandas as pd
import numpy as np

from sklearn.linear_model import Ridge

from sklearn.svm import SVR
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import RobustScaler
from sklearn.multioutput import MultiOutputRegressor


def _parse_line(line, rx_dict):
    for key, rx in rx_dict.items():
        match = rx.search(line)
        if match:
            return key, match
    return None, None


def parse_data_file(filename):
    rx_dict = {"data_line": re.compile(r"Rank (-?\d+); Value (\d+) maxed at (-?\d+)")}
    data = []
    with open(filename, "r") as f:
        for line in f:
            key, m = _parse_line(line, rx_dict)
            if m:
                rank = int(m.group(1))
                val_id = int(m.group(2))
                val = int(m.group(3))
                datum = {"rank": rank, "value_id": val_id, "value": val, "filename": filename}
                data.append(datum)
    return data


def parse_value_ids(filename):
    #ID 12 given to ├  %2255 = add nsw i32 %2239, %2254, !dbg !292 on Line 887 in file kabpar.f90
    rx_dict = {"id_line": re.compile(r"ID (\d+) given to ├  (%.*) on Line (\d+) in file (.*)")}
    data = []
    with open(filename, "r") as f:
        for line in f:
            key, m = _parse_line(line, rx_dict)
            if m:
                val_id = int(m.group(1))
                instr = m.group(2)
                line = int(m.group(3))
                file = m.group(4)
                datum = {"value_id": val_id, "instr": instr, "line": line, "file": file}
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
        data = parse_data_file(dirname + "/" + filename)
        for d in data:
            d["scale"] = scale
        all_data = all_data + data 
    return all_data


def read_metadata_from_json(json_filename):
    dirname=os.path.dirname(json_filename)    
    with open(json_filename) as f:
        contents = json.load(f)
        scale_name = contents["scale_name"] if "scale_name" in contents else "scale"
        max_scale  = contents["max_scale"] if "max_scale" in contents else -1
        instrumentation_file = dirname + "/" +contents["instrumentation_file"] if "instrumentation_file" in contents else ""

    return scale_name, max_scale, instrumentation_file


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


def get_svr_model(group):
    regr = make_pipeline(RobustScaler(), SVR(kernel="rbf", tol=1e-5, C=1000, degree=2, epsilon=1e-8))
    regr.fit(group.scale.to_numpy().reshape(-1, 1), group.value)
    # have to wrap the model in [] because it is a pipleine and DataFrame thinks it's being given 2 things
    return pd.Series([regr], index=["ridge_model"])


def get_linspace(row):
    return np.linspace(start=row.min_scale, stop=row.max_scale, num=10, dtype="int")

def get_ridge_extrapolation(row):
    #X = np.linspace(start=row.min_scale, stop=row.max_scale, num=100).reshape(-1,1)
    X = row.projected_scale.reshape(-1,1)
    return row.ridge_model.predict(X)[0]
