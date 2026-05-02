# this script generates the main result tables and grahs from the MC simulations

library(tidyverse)
options(scipen = 999)

# set wd with relative route if possible
setwd("/Users/pauorive23/Desktop/paper/")

prueba <- "old/prueba3"

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

quantile(main_results$solve_time)


# 1.2. Mean results table ----
mean_share_ren_gen <- main_results |> 
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
            curt_wind     = round(mean(curt_wind), 3)
            ) |> 
  pivot_longer(
    cols = -scenario,
    names_to = "variable",
    values_to = "value"
  ) |>
  pivot_wider(
    names_from = scenario
  )


# 1.3. Expected "evolution" of generation ----
# would be nice to make a comparison of the share of each of the main sources contributing to generation
# try to load directly files from data/summary_stats

grouped_generation_year_in <- read_csv("...") 

evolution_generation_shares <- grouped_generation_year_in |> 
  filter(year %in% c(2020, 2024))

# 2030 projection depends on the specific scenario







