import sys
import pandas as pd
from plotnine import *
import scaling_dynamic_analysis as sda


if __name__ == "__main__":
    scale_name, max_scale = sda.read_metadata_from_json(sys.argv[1])
    all_data = sda.read_data_from_json(sys.argv[1])
    df = pd.DataFrame(all_data)

    # drop values that were not written to during the run
    df2 = df[df.value != -1]
    # reduce values grouped by scale and recorded value, i.e. across ranks for each scale
    df3 = df2.groupby(["scale", "value_id"]).max().reset_index()

    # fit a ridge regression to each unique value versus scale
    slopes = df3.groupby(["value_id"]).apply(sda.calc_ridge_trend).reset_index()
    # add slopes to the dataset and group by trend
    df3 = df3.merge(slopes, on="value_id", how="left")
    df3["slope_classification"] = df3.apply(sda.classify_trend, axis=1)

    # final plot of scale instructions vs scale; grouped by slope trend
    # useful options: scale_y_log10(); geom_hline(yintercept = (2**31 - 1))
    (ggplot(df3) + 
     aes(x="scale", y="value", group="value_id", color="factor(value_id)") + 
     theme(legend_position='none') + 
     geom_line() + 
     geom_point() + 
     facet_wrap("slope_classification")
    ).save("ridge_data_summary.pdf")

    # dump dataframe to csv
    df3.to_csv("ridge_data_summary.csv")
    
    
    print("\nExtrapolating now\n")

    # grab ridge models and plot extrapolated data
    extr = df3.groupby(["value_id"]).apply(sda.get_ridge_model).reset_index()
    extr["min_scale"] = 0
    extr["max_scale"] = max_scale

    extr["projected_scale"] = extr.apply(sda.get_linspace, axis=1)
    extr = extr.explode("projected_scale")
   
    extr["projected_value"] = extr.apply(sda.get_ridge_extrapolation, axis=1)
    # needs to be cast to a number for plotting; can't do earlier otherwise "reshape" complains
    extr["projected_scale"] = extr["projected_scale"].apply(pd.to_numeric)
    
    (ggplot(extr) + 
     aes(x="projected_scale", y="projected_value", group="value_id", color="factor(value_id)") + 
     theme(legend_position='none') + 
     geom_line() + 
     geom_point() +
     geom_hline(yintercept = (2**31 - 1))
    ).save("ridge_extrapolation.pdf")
