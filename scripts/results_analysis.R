# this script generates the main result tables and grahs from the MC simulations

library(tidyverse)
library(janitor)

options(scipen = 999)

# set wd with relative route if possible
setwd("/Users/pauorive23/Desktop/paper/")

# prueba <- "p1_5by_7dwindow_nodia15"
prueba <- "p2_5by_7dwindow"

# 1. Analysis of main Results ---- 

# 1.1. infeasibilities ----
# in theory, since now we have the load_shedding variable there should be no infeasible iteration

files <- list.files(prueba,
                    pattern = "main_results.*\\.csv$",
                    full.names = TRUE)

main_results <- map(files, function(f) {
  scenario <- str_remove(basename(f), "_?main_results\\.csv$")  
  read_csv(f, show_col_types = FALSE) |> 
    mutate(scenario = scenario, .before = iteration)
}) %>%
  bind_rows()

# unfeasibles per scenario
unfeasibilities <- main_results |> 
  filter(mip_gap == -1) |> 
  group_by(scenario) |> 
  count()

# infeasibilities by date
check_unfeasibilities <- main_results |> 
  filter(mip_gap == -1) |> 
  group_by(baseline_year, day_start) |> 
  count()

solve_time <- quantile(main_results$solve_time)

# 1.2. Mean results table ----
summary_results <- main_results |> 
  filter(mip_gap != -1) |> 
  group_by(scenario) |> 
  summarize(ren_gen_share = round(mean(share_renewable_gen), 3),
            low_c_share   = round(mean(share_low_carbon_gen), 3),
            min_non_ren_c = round(mean(share_min_non_ren), 3),
            price         = round(mean(avg_price), 3),
            demand        = round(mean(total_demand), 3),
            welfare_M     = round(mean(net_welfare) / 1e6, 3),
            batt_out      = round(mean(battery_out), 3),
            ph_out        = round(mean(pumped_hydro_out), 3),
            storage_share = round(mean(storage_out / total_generation), 3),
            emissions_Mt  = round(mean(direct_emissions / 1e6), 3),
            curt_solar_pv = round(mean(curt_solar_pv), 3),
            curt_wind     = round(mean(curt_wind), 3),
            lole_hours    = round(mean(lole_hours), 3),
            total_ens     = round(mean(total_ens), 3)
            ) |> 
  pivot_longer(
    cols = -scenario,
    names_to = "variable",
    values_to = "value"
  ) |>
  pivot_wider(
    names_from = scenario
  )


check_share_ren_gen <- main_results |> 
  filter(mip_gap != -1) |> 
  group_by(scenario, baseline_year) |> 
  summarize(ren_gen_share = round(mean(share_renewable_gen), 3),
            .groups = "drop")


# 1.3. Expected "evolution" of generation ----
# would be nice to make a comparison of the share of each of the main sources contributing to generation
# try to load directly files from data/summary_stats







rm(list=ls())

means  <- read_csv("mean_hist_vars_to_scale.csv")
deltas <- read_csv2("projection_deltas_out.csv") 

years <- c(2020, 2021, 2022, 2023, 2024)
demand_vars <- c("residential_demand_gwh", "commercial_demand_gwh", "industrial_demand_gwh")

# Pivota means a formato largo
means_long <- means |>
  pivot_longer(cols = -variable, names_to = "year", values_to = "hist_mean") |>
  mutate(year = as.integer(year),
         variable = str_remove(variable, "^mean_"))

# Calcula la demanda total histórica por año (suma de las 3 sectoriales)
total_demand_hist <- means_long |>
  filter(variable %in% demand_vars) |>
  group_by(year) |>
  summarise(hist_mean = sum(hist_mean), .groups = "drop") |>
  mutate(variable = "total_national_demand_gwh")

means_long_full <- bind_rows(means_long, total_demand_hist)

# Calcula deltas por año base
deltas_by_year <- deltas |>
  select(variable, value_estimate, weight) |>
  mutate(value_estimate = as.numeric(value_estimate),
         weight = as.numeric(weight)) |>
  drop_na(value_estimate) |>
  cross_join(tibble(year = years)) |>
  left_join(means_long_full, by = c("variable", "year")) |>
  drop_na(hist_mean) |>
  mutate(delta = value_estimate / hist_mean - 1) |>
  # Expande total_national_demand a las 3 demandas sectoriales
  mutate(variable = if_else(
    variable == "total_national_demand_gwh",
    list(demand_vars),
    list(variable)
  )) |>
  unnest(variable) |>
  select(year, variable, delta, weight)

# Comprueba resultados
deltas_by_year |>
  group_by(variable, year) |>
  summarise(mean = mean(delta), min = min(delta), max = max(delta), n = n(), .groups = "drop") |>
  print(n = 100)

write_csv(deltas_by_year, "projection_deltas_by_year.csv")




