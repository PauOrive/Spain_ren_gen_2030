# Scripts

This folder contains the scripts needed to replicate the paper. The scripts defining the model and to run the Monte Carlo simulations are written in Julia, since we think is the most suited for this kind of optimization models. Data extraction, processing and analysis of results is done in R & Python. 

They are organized as follows:

## 1. Script to get the historical calibration data

These are non essential to replicate the paper as we provide the complete datasets, but show where the data was sourced from.

Note that both the [ESIOS](https://api.esios.ree.es/) and [ENTSO-E](https://transparencyplatform.zendesk.com/hc/en-us/articles/12845911031188-How-to-get-security-token) API request a valid personal token, which you can ask in the hyperlinks to each source.

-   `00_get_historical_data..py`: does everything in one go. It downloads hourly generation, demand, spot prices, interconnection flows and installed capacities from ESIOS, fetches disaggregated hydro data from ENTSO-E, pulls fuel and carbon costs from MIBGAS and Yahoo Finance (with local Excel fallbacks for ETS and uranium), applies a three-step missing data imputation, and saves the final dataset to `data/historical_data.csv`. It is the only script you need to run to regenerate the main dataset from scratch.

## 2. Scripts to run the Monte Carlo Simulations

-   `02_auxiliary_functions.jl`: containa auxiliary functions to run the Monte Carlo loop.
-   `03_model_electricity_market.jl`: defines the mathematical optimization model used to simulate the Spanish electricity market.
-   `04_monte_carlo_simulations.jl`: runs the Monte Carlo Simulations for each scenario and saves the results into the `output/detailed_results` folder as .csv files. We have not included the full results in this repository since they are too heavy. Instead, we have added a sample_results with the results of the first 100 iteration of each scenario. 

These core scripts of the project work with the following datasets in the `data/` folder:

-   historical_data.csv
-   technology_data.csv
-   projection_deltas_data.csv
-   technical_params.csv

Forking this repository you can play adjusting the model and/or scenario-specific assumptions to test how the model responds to other assumptions.

Note that you will need a [Gurobi license](https://www.gurobi.com/academia/academic-program-and-licenses/) to run the model (free for students!). 
If you do, we would love to get your feedback!

## 3. Scrips to create the graphs and other outputs

-   `01_summary_statistics.R` creates summary statistics tables and graphs of the historical data (2020-2024), saved in `output/historical_summary_stats`
-   `05_results_analysis.py` creates the summary tables and graphs for the main results, saved in `output/results_analysis`

