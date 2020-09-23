import sys
import re
import pandas as pd
import numpy as np
from plotnine import *

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
    slope = np.polyfit(group.world_size, group.value, deg=1)[0]
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


all_data = []
for filename in sys.argv[1:]:
    all_data = all_data + parse_file(filename)

df = pd.DataFrame(all_data)
df2 = df[df.value != -1]
#find max values in table grouped by world_size and value_id, i.e. max across ranks
df3 = df2.groupby(["world_size", "value_id"]).max().reset_index()

#(ggplot(df3) + aes(x="world_size", y="value", color="factor(value_id)") + geom_line() + geom_point())


#df3["group"] = df3.apply(func=lambda x: x["value_id"] // 5, axis=1)
#(ggplot(df3) + aes(x="world_size", y="value", color="factor(value_id)") + geom_line() + geom_point() + facet_wrap("group"))

slopes = df3.groupby(["value_id"]).apply(calc_trend).reset_index()
#slopes = df3.groupby(["value_id"]).apply(func=lambda x: pd.Series(np.polyfit(x.world_size, x.value, deg=1)[0], index=["trend_slope"])).reset_index()
df3 = df3.merge(slopes, on="value_id", how="left")

#df3["trend_slope"] = df3.groupby(["value_id"]).apply(almost_zero)

df3["slope_classification"] = df3.apply(classify_trend, axis=1)

(ggplot(df3) + aes(x="world_size", y="value", color="factor(value_id)") + geom_line() + geom_point() + scale_y_log10() + facet_wrap("slope_classification")).save("data_summary.pdf")

df3.to_csv("data_summary.csv")

