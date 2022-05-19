# About
This tool is intended to analyse the dynamic output from a series of small scale runs of applications instrumented using OFT: https://git.ecdf.ed.ac.uk/jzarins/llvm_hpc_static_analysis

This involves running the instrumented application at a few small scales (e.g. using 4, 8, 16, 32 MPI ranks or a few small problem sizes). The results can be passed to the present tool to parse the output of OFT runs and classify the trends as "falling", "static" or "growing". 
Furthermore, a polynomial trend line is fit to each value and extrapolated to predict the scale at which the value would overflow.

# Use
See the `example_data` directory for an example of how to prepare data for analysis.

`oft_instrumentation.txt` is the output from the static analysis part of OFT. This is required in order to link Value IDs to specific instructions.
The `outN.txt` files are outputs from a series of runs of an OFT instrumented application.

`description.json` describes the experiment.
"inputs" is a list of "scale" and "file" tuples, where "scale" is some notion of the scale of the application or problem at which the OFT instrumented application was run and "file" is the corresponding OFT output file for that run.
"scale_name" is a human-readable description of what scale refers to.
"max_scale" is the value of scale to which trends will be extrapolated to.
"instrumentation_file" is the name of the file which contains the output from the static analysis part of OFT.

The analysis can be performed by running:
```bash
python3 analyse_and_extrapolate.py example_data/description.json
```

If extrapolation shows potential overflows, the results will be presented in the console:
```
Checking for potential overflows..
Found the following potentially overflowing values:
    value_id                                        instr  line         file
    4          4  %2732 = mul nsw i32 %2712, %2731, !dbg !186   563  kabmain.f90
```

The input data will be visualised and summarised in `data_summary.pdf` (one colored line per value) and `data_summary.csv`.
Extrapolation will be visualised in `value_projections.pdf`. This shows the fitted lines in color and the 32-bit integer limit as a black horizontal line.
