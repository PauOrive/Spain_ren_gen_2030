# this script produces some graphs to obtain descriptive statistics

library(tidyverse)

setwd("/Users/pauorive23/Desktop/GitHub/Spain_ren_gen_2030/data")

# load data and add some grouped columns
historical_data_in <- read_csv("historical_data.csv")

historical_data <- historical_data_in |>  
  mutate(total_demand_gwh = residential_demand_gwh + commercial_demand_gwh + industrial_demand_gwh,
        renewable_generation_gwh = conventional_hydro_gen_gwh + run_of_river_hydro_gen_gwh + pumped_hydro_gen_gwh + solar_pv_gen_gwh + solar_thermal_gen_gwh + wind_gen_gwh + other_renewable_gen_gwh + renewable_waste_gen_gwh,
        nonrenewable_generation_gwh = coal_gen_gwh + combined_cycle_gen_gwh + gas_turbine_gen_gwh + vapor_turbine_gen_gwh + cogeneration_gen_gwh + diesel_gen_gwh + nonrenewable_waste_gen_gwh + nuclear_gen_gwh,
        total_generation_gwh = renewable_generation_gwh + nonrenewable_generation_gwh,
        total_imports_gwh = imports_France_gwh + imports_Portugal_gwh + imports_Morocco_gwh,
        total_exports_gwh = exports_France_gwh + exports_Portugal_gwh + exports_Morocco_gwh
  )


# TABLES ----

## ===== Summary tables by year of all variables =====
summary_per_year <- historical_data |>
  group_by(year) |>
  summarise(
    across(.cols = where(is.numeric) & -c(month, day, hour), 
           .fns = mean, 
           .names = "mean_{.col}"),
    
    across(.cols = c(total_demand_gwh, residential_demand_gwh, commercial_demand_gwh,
                     industrial_demand_gwh, total_generation_gwh, total_imports_gwh, total_exports_gwh,
                     renewable_generation_gwh, nonrenewable_generation_gwh, 
                     imports_France_gwh, imports_Portugal_gwh, imports_Morocco_gwh,
                     exports_France_gwh, exports_Portugal_gwh, exports_Morocco_gwh,
                     pumped_hydro_consumption_gwh),
           .fns = sum, 
           .names = "total_{.col}"),
    
    across(.cols = c(renewable_generation_gwh, nonrenewable_generation_gwh, coal_gen_gwh,
                     combined_cycle_gen_gwh, gas_turbine_gen_gwh, vapor_turbine_gen_gwh,
                     cogeneration_gen_gwh, diesel_gen_gwh, nonrenewable_waste_gen_gwh,
                     nuclear_gen_gwh, conventional_hydro_gen_gwh, run_of_river_hydro_gen_gwh, pumped_hydro_gen_gwh, pumped_hydro_consumption_gwh,
                     solar_pv_gen_gwh, solar_thermal_gen_gwh,
                     wind_gen_gwh, other_renewable_gen_gwh, renewable_waste_gen_gwh,
                     imports_France_gwh, imports_Portugal_gwh, imports_Morocco_gwh),
           .fns = ~ sum(.) / sum(total_generation_gwh), 
           .names = "share_{.col}")
  )


## ===== Summary tables by month of all variables =====
summary_per_year_month <- historical_data |>
  group_by(year, month) |>
  summarise(
    across(.cols = where(is.numeric) & !day & !hour, 
           .fns = mean, 
           .names = "mean_{.col}"),
    
    across(.cols = c(total_demand_gwh, residential_demand_gwh, commercial_demand_gwh,
                     industrial_demand_gwh, total_generation_gwh, total_imports_gwh, total_exports_gwh,
                     renewable_generation_gwh, nonrenewable_generation_gwh, 
                     imports_France_gwh, imports_Portugal_gwh, imports_Morocco_gwh,
                     exports_France_gwh, exports_Portugal_gwh, exports_Morocco_gwh),
           .fns = sum, 
           .names = "total_{.col}"),
    
    across(.cols = c(renewable_generation_gwh, nonrenewable_generation_gwh, coal_gen_gwh,
                     combined_cycle_gen_gwh, gas_turbine_gen_gwh, vapor_turbine_gen_gwh,
                     cogeneration_gen_gwh, diesel_gen_gwh, nonrenewable_waste_gen_gwh,
                     nuclear_gen_gwh, conventional_hydro_gen_gwh, run_of_river_hydro_gen_gwh, pumped_hydro_gen_gwh,
                     solar_pv_gen_gwh, solar_thermal_gen_gwh,
                     wind_gen_gwh, other_renewable_gen_gwh, renewable_waste_gen_gwh,
                     imports_France_gwh, imports_Portugal_gwh, imports_Morocco_gwh),
           .fns = ~ sum(.) / sum(total_generation_gwh), 
           .names = "share_{.col}")
  )



## ===== Generation shares (grouped) ===== 
grouped_generation_year <- historical_data |> 
  select(time_long, year, contains("gen_"), total_generation_gwh) |>
  rename(`Combined cycle`     = combined_cycle_gen_gwh,         
         `Cogeneration`       = cogeneration_gen_gwh,
         `Nuclear`            = nuclear_gen_gwh,
         `Conventional hydro` = conventional_hydro_gen_gwh,
         `Pumped hydro`       = pumped_hydro_gen_gwh,
         `Batteries`          = batteries_gen_gwh,  # though pre-2025 is basically 0
         `Solar PV`           = solar_pv_gen_gwh,
         `Wind`               = wind_gen_gwh) |> 
  mutate(`Other non renewable` = coal_gen_gwh 
         + gas_turbine_gen_gwh 
         + vapor_turbine_gen_gwh 
         + diesel_gen_gwh 
         + nonrenewable_waste_gen_gwh,
         `Other renewable` = run_of_river_hydro_gen_gwh 
         + solar_thermal_gen_gwh 
         + other_renewable_gen_gwh 
         + renewable_waste_gen_gwh,
         `Total` = total_generation_gwh,
         .keep = "unused"
  ) |> 
  group_by(year) |> 
  summarize(across(.cols = where(is.numeric), 
                   .fns = sum), 
            .groups = "drop") |> 
  mutate(across(.cols = where(is.numeric) & -all_of("year"),
                .fns = ~ . / `Total`))




## ===== Historical emissions =====
# just takes into account direct emissions, hence lower emissions rate than usually reported is to be expected
emission_rates <- read_csv("technology_data.csv", show_col_types = FALSE) 

# print direct emission rates
emission_rates$direct_e_tco2_gwh[emission_rates$direct_e_tco2_gwh > 0]

emissions_per_year <- historical_data |> 
  group_by(year) |> 
  summarize(total_emissions_tco2 = sum(
    coal_gen_gwh               * 820,
    combined_cycle_gen_gwh     * 360,
    gas_turbine_gen_gwh        * 650,
    vapor_turbine_gen_gwh      * 700,
    cogeneration_gen_gwh       * 490,
    diesel_gen_gwh             * 820,
    nonrenewable_waste_gen_gwh * 230
  ),
  total_generation_gwh = sum(total_generation_gwh),
  .groups = "drop") |> 
  mutate(emissions_intensity_tco2_gwh = total_emissions_tco2 / total_generation_gwh / 1e3)





# GRAPHS ----

## ===== Graph 1: Historical generation by month ===== 

tech_colors <- c(
  "Combined cycle"       = "#f7a6a6",  
  "Cogeneration"         = "firebrick",  
  "Nuclear"              = "maroon",  
  "Other non renewable"  = "#B08D57",  
  "Conventional hydro"   = "navy",
  "Run of river hydro"   = "steelblue",  
  "Pumped hydro"         = "lightsteelblue",  
  "Solar PV"             = "#F4C430",  
  "Wind"                 = "seagreen",  
  "Batteries"            = "peru",  
  "Other renewable"      = "darkslategray",
  "Total"                = "white"  
)

# compute grouped monthly averages
grouped_generation <- historical_data |> 
  select(time_long, year, month, contains("gen_"), total_generation_gwh) |>
  rename(`Combined cycle`     = combined_cycle_gen_gwh,         
         `Cogeneration`       = cogeneration_gen_gwh,
         `Nuclear`            = nuclear_gen_gwh,
         `Conventional hydro` = conventional_hydro_gen_gwh,
         `Pumped hydro`       = pumped_hydro_gen_gwh,
         `Batteries`          = batteries_gen_gwh,  # though pre-2025 is basically 0
         `Solar PV`           = solar_pv_gen_gwh,
         `Wind`               = wind_gen_gwh) |> 
  mutate(`Other non renewable` = coal_gen_gwh 
                                + gas_turbine_gen_gwh 
                                + vapor_turbine_gen_gwh 
                                + diesel_gen_gwh 
                                + nonrenewable_waste_gen_gwh,
         `Other renewable` = run_of_river_hydro_gen_gwh 
                            + solar_thermal_gen_gwh 
                            + other_renewable_gen_gwh 
                            + renewable_waste_gen_gwh,
         `Total` = total_generation_gwh,
         .keep = "unused"
         ) |> 
  group_by(year, month) |> 
  summarize(across(where(is.numeric), sum), 
            .groups = "drop") |> 
  mutate(date = ymd(paste(year, month, "01")), .before = year) |> 
  select(-year, -month)
  
# pivot to long format
generation_long <- grouped_generation |> 
  pivot_longer(
    cols = -date,
    names_to = "technology", 
    values_to = "generation"
    ) |> 
  mutate(technology = factor(technology, levels = names(tech_colors))) |> 
  filter(technology != "Total")

# construct the graph
p1 <- ggplot(generation_long, aes(x = date, y = generation, fill = technology)) +
  geom_area(position = "stack", alpha = 0.9) +
  scale_fill_manual(values = tech_colors) +
  scale_x_date(
    breaks = seq(min(generation_long$date), max(generation_long$date), by = "6 months"),
    date_labels = "%Y-%m",
    expand = c(0, 0)
  ) +
  geom_vline(
    xintercept = seq(min(generation_long$date), max(generation_long$date), by = "6 months"),
    color = "gray80", linewidth = 0.2
  ) +
  labs(
    y = "Monthly generation (TWh)",
    fill = "Technology"
  ) +
  theme_minimal() +
  theme(
    axis.title.x = element_blank(),
    axis.title.y = element_text(color = "gray10", face = "bold", size = 14),
    axis.text = element_text(color = "gray10", face = "bold", size = 12),
    axis.text.y = element_text(size = 14),
    axis.ticks.x = element_blank(),
    legend.title = element_blank(),
    legend.text = element_text(size = 14),
    legend.position = "bottom",
    panel.grid.major.x = element_blank(),
    panel.grid.minor = element_blank(),
    plot.margin = margin(10, 20, 10, 10)
  )

p1


## ===== Graph 2: Historical capacity by month ===== 

# compute grouped monthly averages
grouped_capacity <- historical_data |> 
  select(time_long, year, month, contains("cap_")) |>
  rename(`Combined cycle`     = combined_cycle_cap_gw,         
         `Cogeneration`       = cogeneration_cap_gw,
         `Nuclear`            = nuclear_cap_gw,
         `Conventional hydro` = conventional_hydro_cap_gw,
         `Pumped hydro`       = pumped_hydro_turb_cap_gw,
         `Batteries`          = batteries_cap_gw,  # though pre-2025 is basically 0
         `Solar PV`           = solar_pv_cap_gw,
         `Wind`               = wind_cap_gw) |> 
  mutate(`Other non renewable` = coal_cap_gw 
         + gas_turbine_cap_gw 
         + vapor_turbine_cap_gw 
         + diesel_cap_gw 
         + nonrenewable_waste_cap_gw,
         `Other renewable` = run_of_river_hydro_cap_gw 
         + solar_thermal_cap_gw 
         + other_renewable_cap_gw 
         + renewable_waste_cap_gw,
         .keep = "unused"
  ) |> 
  group_by(year, month) |> 
  summarize(across(where(is.numeric), 
                   mean), 
            .groups = "drop") |> 
  mutate(date = ymd(paste(year, month, "01")), .before = year) |> 
  select(-year, -month) |> 
  mutate(`Total`= `Combined cycle` + `Cogeneration` + `Nuclear` + `Conventional hydro` 
                  + `Pumped hydro` + `Batteries` + `Solar PV` + `Wind` 
                    + `Other non renewable` + `Other renewable`)

# pivot to long format
capacity_long <- grouped_capacity |> 
  pivot_longer(
    cols = -date,
    names_to = "technology", 
    values_to = "capacity"
  ) |> 
  mutate(technology = factor(technology, levels = names(tech_colors))) |> 
  filter(technology != "Total")

# construct the graph
p2 <- ggplot(capacity_long, aes(x = date, y = capacity, fill = technology)) +
  geom_area(position = "stack", alpha = 0.9) +
  scale_fill_manual(values = tech_colors) +
  scale_x_date(
    breaks = seq(min(capacity_long$date), max(capacity_long$date), by = "6 months"),
    date_labels = "%Y-%m",
    expand = c(0, 0)
  ) +
  geom_vline(
    xintercept = seq(min(capacity_long$date), max(capacity_long$date), by = "6 months"),
    color = "gray80", linewidth = 0.2
  ) +
  labs(
    y = "Installed capacity (GWh)",
    fill = "Technology"
  ) +
  theme_minimal() +
  theme(
    axis.title.x = element_blank(),
    axis.title.y = element_text(color = "gray10", face = "bold", size = 14),
    axis.text = element_text(color = "gray10", face = "bold", size = 12),
    axis.text.y = element_text(size = 14),
    axis.ticks.x = element_blank(),
    legend.title = element_blank(),
    legend.text = element_text(size = 14),
    legend.position = "right",
    panel.grid.major.x = element_blank(),
    panel.grid.minor = element_blank(),
    plot.margin = margin(10, 20, 10, 10)
  )

p2


## ===== Graph 3: Sectoral demand profiles ===== 

# Define colors
demand_colors <- c("Residential" = "steelblue",
                   "Commercial" = "peru", 
                   "Industrial" = "maroon",
                   "Total" = "seagreen")

### G3.1 Historical evolution of total demand ----





### G3.2 Hourly demand profile ----

# Define function to compute hourly/monthly profiles
compute_profiles <- function(data, group_var) {
  data |> 
    group_by({{ group_var }}) |> 
    summarize(
      res_dem = mean(residential_demand_gwh), 
      com_dem = mean(commercial_demand_gwh),  
      ind_dem = mean(industrial_demand_gwh),  
      total_dem = mean(residential_demand_gwh + commercial_demand_gwh + industrial_demand_gwh), 
      # Calculate standard errors and confidence intervals
      res_se = sd(residential_demand_gwh) / sqrt(n()), 
      com_se = sd(commercial_demand_gwh) / sqrt(n()),
      ind_se = sd(industrial_demand_gwh) / sqrt(n()),
      total_se = sd(residential_demand_gwh + commercial_demand_gwh + industrial_demand_gwh) / sqrt(n()), 
      # 95% confidence intervals
      res_ci_lower = res_dem - 1.96 * res_se,
      res_ci_upper = res_dem + 1.96 * res_se,
      com_ci_lower = com_dem - 1.96 * com_se,
      com_ci_upper = com_dem + 1.96 * com_se,
      ind_ci_lower = ind_dem - 1.96 * ind_se,
      ind_ci_upper = ind_dem + 1.96 * ind_se,
      total_ci_lower = total_dem - 1.96 * total_se,
      total_ci_upper = total_dem + 1.96 * total_se
    )
}

hourly_demand <- compute_profiles(historical_data, hour) 
  

# Create the hourly plot 
p3.2 <- ggplot(hourly_demand, aes(x = hour)) +
  # Add confidence interval ribbons
  geom_ribbon(aes(ymin = res_ci_lower, ymax = res_ci_upper), 
              fill = "steelblue", alpha = 0.2) +
  geom_ribbon(aes(ymin = com_ci_lower, ymax = com_ci_upper), 
              fill = "peru", alpha = 0.2) +
  geom_ribbon(aes(ymin = ind_ci_lower, ymax = ind_ci_upper), 
              fill = "maroon", alpha = 0.2) +
  geom_ribbon(aes(ymin = total_ci_lower, ymax = total_ci_upper), 
              fill = "seagreen", alpha = 0.2) +
  # Add lines
  geom_line(aes(y = res_dem, color = "Residential"), size = 1.2) +
  geom_line(aes(y = com_dem, color = "Commercial"), size = 1.2) +
  geom_line(aes(y = ind_dem, color = "Industrial"), size = 1.2) +
  geom_line(aes(y = total_dem, color = "Total"), size = 1.5) +
  # Apply colors and labels
  scale_color_manual(values = demand_colors) +
  scale_x_continuous(breaks = seq(0, 23, 2)) +
  scale_y_continuous(breaks = seq(0, 35, 5)) +
  labs(y = "Average hourly demand (GWh)") +
  # Apply theme
  theme_minimal() +
  theme(
    axis.title.x = element_blank(),
    axis.title.y = element_text(face = "bold", size = 16),
    axis.text = element_text(color = "gray10", face = "bold", size = 12),
    axis.text.y = element_text(size = 14),
    axis.ticks.x = element_blank(),
    legend.position = "bottom", 
    legend.title = element_blank(),
    panel.grid.major.x = element_line(color = "gray90", size = 0.2),
    panel.grid.minor = element_blank(),
    panel.border = element_rect(color = "gray75", fill = NA, size = 0.5),
    plot.margin = margin(20, 30, 20, 20)
  )

p3.2


### G3.3 Monthly demand profile ----

# Calculate monthly demand with confidence intervals
monthly_demand <- compute_profiles(historical_data, month)

# Create the monthly plot 
p3.3 <- ggplot(monthly_demand, aes(x = month)) +
  # Add confidence interval ribbons
  geom_ribbon(aes(ymin = res_ci_lower, ymax = res_ci_upper), 
              fill = "steelblue", alpha = 0.2) +
  geom_ribbon(aes(ymin = com_ci_lower, ymax = com_ci_upper), 
              fill = "peru", alpha = 0.2) +
  geom_ribbon(aes(ymin = ind_ci_lower, ymax = ind_ci_upper), 
              fill = "maroon", alpha = 0.2) +
  geom_ribbon(aes(ymin = total_ci_lower, ymax = total_ci_upper), 
              fill = "seagreen", alpha = 0.2) +
  # Add lines
  geom_line(aes(y = res_dem, color = "Residential"), size = 1.2) +
  geom_line(aes(y = com_dem, color = "Commercial"), size = 1.2) +
  geom_line(aes(y = ind_dem, color = "Industrial"), size = 1.2) +
  geom_line(aes(y = total_dem, color = "Total"), size = 1.5) +
  # Apply colors and labels
  scale_color_manual(values = demand_colors) +
  scale_y_continuous(breaks = seq(0, 35, 5)) +
  scale_x_continuous(breaks = 1:12, 
                     labels = c("Jan", "Feb", "Mar", "Apr", "May", "Jun",
                                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")) +
  labs(y = "Average monthly demand (GWh)") +
  # Apply theme
  theme_minimal() +
  theme(
    axis.title.x = element_blank(),
    axis.title.y = element_text(face = "bold", size = 16),
    axis.text = element_text(color = "gray10", face = "bold", size = 12),
    axis.text.y = element_text(size = 14),
    axis.ticks.x = element_blank(),
    legend.title = element_blank(),
    legend.text = element_text(size = 14),
    legend.position = "bottom",  
    panel.grid.major.x = element_line(color = "gray90", size = 0.2),
    panel.grid.minor = element_blank(),
    panel.border = element_rect(color = "gray75", fill = NA, size = 0.5),
    plot.margin = margin(20, 30, 20, 20)
  )

p3.3


## ===== Solar and wind capacity factors ===== 

solar_wind_cap_factors <- historical_data |> 
  select(year, month, day, hour, solar_pv_cap_factor, wind_cap_factor)

hourly_summary <- solar_wind_cap_factors |>
  group_by(hour) |>
  summarise(
    solar_mean = mean(solar_pv_cap_factor, na.rm = TRUE),
    solar_low  = quantile(solar_pv_cap_factor, 0.025, na.rm = TRUE),
    solar_high = quantile(solar_pv_cap_factor, 0.975, na.rm = TRUE),
    wind_mean  = mean(wind_cap_factor, na.rm = TRUE),
    wind_low   = quantile(wind_cap_factor, 0.025, na.rm = TRUE),
    wind_high  = quantile(wind_cap_factor, 0.975, na.rm = TRUE)
  )

# Plot for solar
ggplot(hourly_summary, aes(x = hour)) +
  geom_ribbon(aes(ymin = solar_low, ymax = solar_high), fill = "gold", alpha = 0.3) +
  geom_line(aes(y = solar_mean), color = "orange", size = 1) +
  labs(title = "Hourly Solar PV Capacity Factor with 95% CI",
       x = "Hour of Day", y = "Solar Capacity Factor") +
  theme_minimal()

# Plot for wind
ggplot(hourly_summary, aes(x = hour)) +
  geom_ribbon(aes(ymin = wind_low, ymax = wind_high), fill = "skyblue", alpha = 0.3) +
  geom_line(aes(y = wind_mean), color = "blue", size = 1) +
  labs(title = "Hourly Wind Capacity Factor with 95% CI",
       x = "Hour of Day", y = "Wind Capacity Factor") +
  theme_minimal()



