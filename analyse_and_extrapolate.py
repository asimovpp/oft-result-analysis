import sys
import pandas as pd
from plotnine import *
import scaling_dynamic_analysis as sda
from mizani.formatters import scientific_format

INT_LIMIT = 2**31 - 1

if __name__ == "__main__":
    scale_name, max_scale, instrumentation_file = sda.read_metadata_from_json(sys.argv[1])
    if instrumentation_file != "":
        value_id_info = sda.parse_value_ids(instrumentation_file)

    all_data = sda.read_data_from_json(sys.argv[1])
    df = pd.DataFrame(all_data)

    # drop values that were not written to during the run
    df2 = df[df.value != -1]
    # reduce values grouped by scale and recorded value, i.e. across ranks for each scale
    df3 = df2.groupby(["scale", "value_id"]).max().reset_index()

    # fit a polynomial (of degree 1) to each unique value versus scale; return only the slope of the line
    slopes = df3.groupby(["value_id"]).apply(sda.calc_linear_fit_slope).reset_index()
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
     facet_wrap("slope_classification") +
     scale_y_continuous(labels=scientific_format(digits=2))
    ).save("data_summary.pdf")

    # dump dataframe to csv
    df3.to_csv("data_summary.csv")
   
    
    print("\nExtrapolating now\n")

    # select one of the below
    #model_fitting_method = sda.get_ridge_model
    #model_fitting_method = sda.get_kernel_ridge_model
    #model_fitting_method = sda.get_svr_model
    #model_fitting_method = sda.get_best_poly_model
    model_fitting_method = sda.get_best_func_model

    extr = df3
    #extr = df3[df3.slope_classification == "positive"] # only extrapolate curves with a positive slope on average.
    extr = extr.groupby(["value_id"]).apply(model_fitting_method).reset_index()
    extr = extr.merge(df3[["value_id", "slope_classification"]], on="value_id", how="left")

    extr["min_scale"] = 1
    extr["max_scale"] = max_scale
    extr["projected_scale"] = extr.apply(sda.get_linspace, axis=1)
    extr = extr.explode("projected_scale")
    
    extr["projected_value"] = extr.apply(sda.get_extrapolation, axis=1)
    # needs to be cast to a number for plotting; can't do earlier otherwise "reshape" complains
    extr["projected_scale"] = extr["projected_scale"].apply(pd.to_numeric)
   
    # plot measured data (points) and model+extrapolation (line)
    projection_plot=(ggplot() + 
     geom_line(aes(x="projected_scale", y="projected_value", 
               group="value_id", color="factor(value_id)"), data=extr) + 
     geom_point(aes(x="scale", y="value", group="value_id", color="factor(value_id)"), data=df3) + 
     theme(legend_position='none', axis_text_x=element_text(rotation=90)) + 
     facet_wrap("slope_classification") +
     scale_y_continuous(labels=scientific_format(digits=2)) +
     scale_x_continuous(labels=scientific_format(digits=2))
    )


    print("\nChecking for potential overflows..")
    
    overshot = extr[extr.projected_value > INT_LIMIT]
    overshot_ids = overshot.value_id.drop_duplicates()
    if len(overshot_ids) == 0:
        print("Did not find any overflowing values!\n")
    else:
        print("Found the following potentially overflowing values:")
        value_info = pd.DataFrame(value_id_info)
        if len(value_info.value_id.drop_duplicates()) < len(df3.value_id.drop_duplicates()):
            print("ERROR. There are more value IDs than descriptions. Exiting.")
            exit(1)
        overshot_value_info = value_info[value_info.value_id.isin(overshot_ids)]
        print(overshot_value_info)
        projection_plot += geom_hline(yintercept = INT_LIMIT)
    projection_plot.save("value_projections.pdf")
