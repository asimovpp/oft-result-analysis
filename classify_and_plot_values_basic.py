import sys
import pandas as pd
from plotnine import *
import scaling_dynamic_analysis as sda


if __name__ == "__main__":
    all_data = sda.read_data_from_json(sys.argv[1])
    df = pd.DataFrame(all_data)

    # drop values that were not written to during the run
    df2 = df[df.value != -1]
    # reduce values grouped by scale and recorded value, i.e. across ranks for each scale
    df3 = df2.groupby(["scale", "value_id"]).max().reset_index()

    # simply plot all values against scale
    #(ggplot(df3) + aes(x="scale", y="value", color="factor(value_id)") + geom_line() + geom_point()).save("value_vs_scale.pdf")

    # fit a polynomial (of degree 1) to each unique value versus scale; return only the slope of the line
    slopes = df3.groupby(["value_id"]).apply(sda.calc_linear_fit_slope).reset_index()
    # add slopes to the dataset and group by trend
    df3 = df3.merge(slopes, on="value_id", how="left")
    df3["slope_classification"] = df3.apply(sda.classify_trend, axis=1)

    # final plot of scale instructions vs scale; grouped by slope trend
    # useful options: scale_y_log10(); geom_hline(yintercept = (2**31 - 1))
    (ggplot(df3) + aes(x="scale", y="value", color="factor(value_id)") + theme(legend_position='none') + geom_line() + scale_y_log10() + geom_point() + facet_wrap("slope_classification")).save("data_summary.pdf")

    # dump dataframe to csv
    df3.to_csv("data_summary.csv")
