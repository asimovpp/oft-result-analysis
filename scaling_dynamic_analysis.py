import re, os, json
import pandas as pd
import numpy as np

from sklearn.linear_model import Ridge
from sklearn.kernel_ridge import KernelRidge

from sklearn.svm import SVR
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import RobustScaler
from sklearn.multioutput import MultiOutputRegressor

from numpy.polynomial import Polynomial

from scipy.optimize import curve_fit

from functools import partial

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
    #clf = Ridge(alpha=1.0)
    clf = KernelRidge(alpha=1.0, kernel="rbf", gamma=1e-3)
    clf.fit(group.scale.to_numpy().reshape(-1, 1), group.value)
    #return clf
    return pd.Series(clf, index=["ridge_model"])


def get_svr_model(group):
    #regr = make_pipeline(StandardScaler(), SVR(kernel="rbf", C=1000, epsilon=10, gamma=10000))
    regr = make_pipeline(StandardScaler(), SVR(kernel="rbf", C=1e11, gamma=1e0))
    svr = regr.fit(group.scale.to_numpy().reshape(-1, 1), group.value)
    #scaler = StandardScaler()
    #scaler.fit(group.scale.to_numpy().reshape(-1, 1))
    #print(group.value)
    #print(scaler.transform(group.value.to_numpy().reshape(-1, 1)))
    # have to wrap the model in [] because it is a pipleine and DataFrame thinks it's being given 2 things
    return pd.Series([regr], index=["ridge_model"])


def get_linspace(row):
    return np.linspace(start=row.min_scale, stop=row.max_scale, num=10, dtype="int")

def get_ridge_extrapolation(row):
    #X = np.linspace(start=row.min_scale, stop=row.max_scale, num=100).reshape(-1,1)
    X = row.projected_scale.reshape(-1,1)
    return row.ridge_model.predict(X)[0]


def compare_instrumentation_info(filename1, filename2):
    info1 = parse_value_ids(filename1)
    info2 = parse_value_ids(filename2)
    df1 = pd.DataFrame(info1) 
    df2 = pd.DataFrame(info2) 

    if len(df1) != len(df2):
        print("Inputs have a different number of instrumented instructions")
        return 1

    print(df1.compare(df2))

    #return df1, df2
    

def check_fit(model, xs, observed):
    ys = [model(x) for x in xs]
    num = np.sqrt( sum([(y-o)**2 for y,o in zip(ys,observed)])  / len(ys))
    return num
    #denum = max(ys) - min(ys)
    # if num is 0, it's a perfect fit.
    # In that case, denum might be 0 if the model is a constant
    # so just return a perfect fit score
    #if num == 0:
    #    return 1
    # but for a degree 0 poly, denum is still 0 but num can be nonzero...
    #return 1 - num/denum

#WIP
# find best polynomial fit to points
# could ask the user to specify max degree
# Possible limitation: decaying functions will go negative in extrapolation
def get_best_poly_fit(group):
    max_degree = 3
    fitted = Polynomial.fit(group.scale, group.value, deg=max_degree)
    score = check_fit(fitted, group.scale, group.value)
    min_score = score 
    best_fitted = fitted
    for degree in reversed(range(0, max_degree)):
        fitted = Polynomial.fit(group.scale, group.value, deg=degree)
        score = check_fit(fitted, group.scale, group.value)
        if score <= min_score:
            min_score = score
            best_fitted = fitted
        #print(score, fitted, list(group.scale), list(group.value))
        #print(score, fitted)

    return pd.Series([best_fitted], index=["poly_model"])

def get_poly_extrapolation(row):
    return row.poly_model(row.projected_scale)


models = [
        lambda x, a, b    : a * x + b,
        lambda x, a, b, c : a * x**b + c,
        lambda x, a, b, c : a / x**b + c
         ]
        #lambda x, a, b, c : a * x**2 + b * x + c
        #lambda x, a, b : b * np.log(x) + np.log(a)
        #{ lambda x, a, b    : a * x**(1/2) + b, 
        #{ lambda x, a, b    : a / x**(2) + b,
        #{ lambda x, a, b    : a / x + b, 

# modify partial from functools ( https://docs.python.org/3/library/functools.html ).
# puts the passed args at the end, not the beginning
def my_partial(func, *args, **keywords):
    def newfunc(*fargs, **fkeywords):
        newkeywords = {**keywords, **fkeywords}
        return func(*fargs, *args, **newkeywords)
    newfunc.func = func
    newfunc.args = args
    newfunc.keywords = keywords
    return newfunc

def get_best_func_fit(group):
    min_score = None
    best_fitted = None
    print()
    print(list(group.scale))
    print(list(group.value))
    for i,model in enumerate(models):
        try:
            coefs, _ = curve_fit(model, group.scale, group.value)
        except RuntimeError as err:
            print(">>>caugt", err)
            continue 
        fitted = my_partial(model, *coefs)
        score = check_fit(fitted, group.scale, group.value)
        # in cases where all group.value entries are equal, any of the models can be fit 
        # by setting everything except the constant to near 0. To get around this: have the linear
        # model first in the queue and look for strictly smaller scores in other models.
        if min_score == None or score < min_score:
            print("  found a better model", score, min_score)
            min_score = score
            best_fitted = fitted
        #print(score, fitted, list(group.scale), list(group.value))
        print(score, coefs)
    

    return pd.Series(best_fitted, index=["func_model"])

def get_func_extrapolation(row):
    return row.func_model(row.projected_scale)






