# diagnostics

# hemos visto que todas las unfeasibilities suceden con baseline_year = 2024 y start_day entre 8 y 14.

# load the required libraries
using DataFrames
using CSV
using Statistics
using Distributions
using KernelDensity
using StatsBase
using Printf

# ===== Monte Carlo Set up =====

# define project location
project_root = dirname(@__DIR__)

# load the function that models the electricity market and the other auxiliary functions
include(joinpath(project_root, "scripts", "model_electricity_market.jl"))
include(joinpath(project_root, "scripts", "auxiliary_functions.jl"))

# load the fixed datasets
historical_data        = CSV.read(joinpath(project_root, "data", "historical_data.csv"), DataFrame)
technology_data        = CSV.read(joinpath(project_root, "data", "technology_data.csv"), DataFrame)
projection_deltas_data = CSV.read(joinpath(project_root, "data", "projection_deltas_data.csv"), DataFrame)

# Aisla exactamente la ventana problemática
problematic_window = filter(row ->
    row.year == 2024 &&
    row.day >= 8 &&
    row.day <= 14,
    historical_data
)

# Compara con una ventana que funciona bien, e.g. 2023 día 8-14
good_window = filter(row ->
    row.year == 2023 &&
    row.day >= 8 &&
    row.day <= 14,
    historical_data
)

# Mira las columnas clave
select(problematic_window, [:day, :residential_demand_gwh, :solar_pv_cap_gw, :wind_cap_gw, :conventional_hydro_cap_gw])
select(good_window, [:day, :residential_demand_gwh, :solar_pv_cap_gw, :wind_cap_gw, :conventional_hydro_cap_gw])