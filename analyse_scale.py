import sys
import pandas as pd
from plotnine import *
import scaling_dynamic_analysis as sda


if __name__ == "__main__":
    #all_data = sda.read_data_from_files(sys.argv[1:])
    all_data = sda.read_data_from_json(sys.argv[1])


    df = pd.DataFrame(all_data)
    df2 = df[df.value != -1]
    #find max values in table grouped by world_size and value_id, i.e. max across ranks
    #df3 = df2.groupby(["world_size", "value_id"]).max().reset_index()
    df3 = df2.groupby(["scale", "value_id"]).max().reset_index()

    #(ggplot(df3) + aes(x="world_size", y="value", color="factor(value_id)") + geom_line() + geom_point())


    #df3["group"] = df3.apply(func=lambda x: x["value_id"] // 5, axis=1)
    #(ggplot(df3) + aes(x="world_size", y="value", color="factor(value_id)") + geom_line() + geom_point() + facet_wrap("group"))

    slopes = df3.groupby(["value_id"]).apply(sda.calc_poly_trend).reset_index()
    #slopes = df3.groupby(["value_id"]).apply(func=lambda x: pd.Series(np.polyfit(x.world_size, x.value, deg=1)[0], index=["trend_slope"])).reset_index()
    df3 = df3.merge(slopes, on="value_id", how="left")

    #df3["trend_slope"] = df3.groupby(["value_id"]).apply(almost_zero)

    df3["slope_classification"] = df3.apply(sda.classify_trend, axis=1)

    #(ggplot(df3) + aes(x="world_size", y="value", color="factor(value_id)") + theme(legend_position='none') + geom_line() + geom_point() + scale_y_log10() + facet_wrap("slope_classification")).save("data_summary.pdf")
    (ggplot(df3) + aes(x="scale", y="value", color="factor(value_id)") + theme(legend_position='none') + geom_line() + geom_point() + facet_wrap("slope_classification") + geom_hline(yintercept = (2**31 - 1))).save("data_summary.pdf")

    df3.to_csv("data_summary.csv")
