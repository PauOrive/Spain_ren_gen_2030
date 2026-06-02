# this script produces some graphs to obtain descriptive statistics

library(tidyverse)
library(patchwork)
library(zoo)

setwd("/Users/pauorive23/Desktop/GitHub/Spain_ren_gen_2030")

# load data and add some grouped columns
historical_data_in <- read_csv("data/historical_data.csv")

# define output paths
output_tables <- "output/historical_summary_stats/tables"
output_graphs <- "output/historical_summary_stats/graphs"


historical_data <- historical_data_in |>  
  mutate(total_demand_gwh = residential_demand_gwh + commercial_demand_gwh + industrial_demand_gwh,
        renewable_generation_gwh = conventional_hydro_gen_gwh + run_of_river_hydro_gen_gwh + solar_pv_gen_gwh + solar_thermal_gen_gwh + wind_gen_gwh + other_renewable_gen_gwh + renewable_waste_gen_gwh,
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

write_csv(summary_per_year, file.path(output_tables, "summary_per_year.csv"))


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

write_csv(summary_per_year_month, file.path(output_tables, "summary_per_year_month.csv"))


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

write_csv(grouped_generation_year, file.path(output_tables, "grouped_generation_year.csv"))


## ===== Historical emissions =====
# just takes into account direct emissions, hence lower emissions rate than usually reported is to be expected
emission_rates <- read_csv("data/technology_data.csv", show_col_types = FALSE) 

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


write_csv(emissions_per_year, file.path(output_tables, "emissions_per_year.csv"))



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

ggsave(file.path(output_graphs, "01_historical_generation.png"), bg = "white")


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

ggsave(file.path(output_graphs, "02_historical_capacity.png"), bg = "white")


# Put one graph on top of the other
gp1p2 <- (p2 / p1) +
  plot_layout(guides = "collect") &
  theme(
    legend.position = "bottom",
    legend.title = element_blank(),
    legend.text = element_text(size = 10)
  )

gp1p2

ggsave(file.path(output_graphs, "12_historical_gen_cap.png"),
       gp1p2,
       bg = "white",
       width = 8,
       height = 10
       )



## ===== Graph 3: Evolution of mean renewable share historically ===== 

# Create monthly date
renewable_share <- summary_per_year_month |>
  select(year, month, renewable_share = share_renewable_generation_gwh) |> 
  mutate(
    date = ymd(paste(year, month, "01"))
  )

# Identify significant peaks and troughs
renewable_share_labels <- renewable_share |>
  mutate(
    roll_max = rollapply(
      renewable_share,
      width = 7,
      FUN = max,
      fill = NA,
      align = "center"
    ),
    roll_min = rollapply(
      renewable_share,
      width = 7,
      FUN = min,
      fill = NA,
      align = "center"
    ),
    is_global_peak = renewable_share == roll_max,
    is_global_trough = renewable_share == roll_min,
    lag_3 = lag(renewable_share, 3),
    lead_3 = lead(renewable_share, 3),
    peak_significant =
      is_global_peak &
      renewable_share > pmax(lag_3, lead_3, na.rm = TRUE) + 0.02,
    trough_significant =
      is_global_trough &
      renewable_share < pmin(lag_3, lead_3, na.rm = TRUE) - 0.02
  )

peak_trough_points <- renewable_share_labels |>
  filter(peak_significant | trough_significant)

peak_labels <- renewable_share_labels |>
  filter(peak_significant)

trough_labels <- renewable_share_labels |>
  filter(trough_significant)

last_obs <- renewable_share |>
  slice_tail(n = 1)

# Plot
p3 <- ggplot(renewable_share, aes(x = date, y = renewable_share)) +
  
  # Main series
  geom_line(
    color = "black",
    linewidth = 1.2
  ) +
  
  # Linear trend
  geom_smooth(
    method = "lm",
    se = FALSE,
    color = "darkred",
    linetype = "dashed",
    alpha = 0.7
  ) +
  
  # Vertical lines every 6 months
  geom_vline(
    xintercept = seq(
      min(renewable_share$date),
      max(renewable_share$date),
      by = "6 months"
    ),
    color = "gray80",
    linewidth = 0.2
  ) +
  
  # Highlight peaks and troughs
  geom_point(
    data = peak_trough_points,
    color = "black",
    fill = "white",
    shape = 21,
    size = 2,
    stroke = 1.2
  ) +
  
  # Highlight latest observation
  geom_point(
    data = last_obs,
    color = "black",
    fill = "white",
    shape = 21,
    size = 2,
    stroke = 1.2
  ) +
  
  # Peak labels
  geom_text(
    data = peak_labels,
    aes(label = round(100 * renewable_share, 1)),
    vjust = -0.8,
    fontface = "bold",
    size = 3,
    color = "black"
  ) +
  
  # Trough labels
  geom_text(
    data = trough_labels,
    aes(label = round(100 * renewable_share, 1)),
    vjust = 1.3,
    fontface = "bold",
    size = 3,
    color = "black"
  ) +
  
  # Last observation label
  geom_text(
    data = last_obs,
    aes(label = round(100 * renewable_share, 1)),
    vjust = 1.3,
    fontface = "bold",
    size = 3,
    color = "black"
  ) +
  
  scale_x_date(
    date_breaks = "6 months",
    date_labels = "%y-%m",
    expand = c(0.02, 0.02)
  ) +
  
  scale_y_continuous(
    labels = scales::number_format(
      scale = 100,
      accuracy = 1
    ),
    breaks = seq(0, 1, by = 0.05)
  ) +
  
  labs(
    y = "Renewable share (%)",
    x = NULL
  ) +
  
  theme_minimal() +
  
  theme(
    axis.title.y = element_text(
      face = "bold",
      size = 13
    ),
    axis.text = element_text(
      color = "gray10",
      face = "bold",
      size = 10
    ),
    axis.text.y = element_text(size = 11),
    axis.ticks.x = element_blank(),
    panel.grid.major.x = element_blank(),
    panel.grid.minor = element_blank(),
    panel.border = element_rect(
      color = "gray75",
      fill = NA,
      linewidth = 0.5
    ),
    plot.margin = margin(
      20, 30, 20, 20
    )
  )

p3

ggsave(file.path(output_graphs, "03_historical_ren_share.png"),
       p3,
       bg = "white",
       width = 5
)


## ===== Graph 4: Sectoral demand profiles ===== 

# Define colors
demand_colors <- c("Residential" = "steelblue",
                   "Commercial" = "peru", 
                   "Industrial" = "maroon",
                   "Total" = "seagreen")

### G4.1 Historical evolution of total demand ----

demand_by_year_sector <- historical_data |> 
  select(year, residential_demand_gwh, commercial_demand_gwh, industrial_demand_gwh) |> 
  group_by(year) |> 
  summarize(total_res_demand = sum(residential_demand_gwh),
            total_com_demand = sum(commercial_demand_gwh),
            total_ind_demand = sum(industrial_demand_gwh)) |> 
  mutate(total_res_demand = total_res_demand / 1e3,
         total_com_demand = total_com_demand / 1e3,
         total_ind_demand = total_ind_demand / 1e3) |> 
  mutate(total_demand = total_res_demand + total_com_demand + total_ind_demand)

historical_demand <- tibble(
  year = c(2015, 2016, 2017, 2018, 2019),
  total_res_demand = NA,
  total_com_demand = NA,
  total_ind_demand = NA,
  total_demand = c(262.81, 264.67, 267.87, 268.89, 264.66)
)

projection_demand <- tibble(
  year = rep(2030, 9),
  total_res_demand = NA,
  total_com_demand = NA,
  total_ind_demand = NA,
  total_demand = c(344, 274, 295, 330, 311.70, 351.06, 286.5, 280, 294)
)

df_demand_complete <- rbind(historical_demand, demand_by_year_sector, projection_demand)

# Prepare data for plotting
# 1. Data for 2015-2019 (total demand only)
df_2015_2019 <- df_demand_complete |> 
  filter(year >= 2015 & year <= 2019) |>
  mutate(group = "historical_total")

# 2. Data for 2020-2024 (stacked sectorial)
df_2020_2024 <- df_demand_complete |> 
  filter(year >= 2020 & year <= 2024) |>
  pivot_longer(cols = c(total_res_demand, total_com_demand, total_ind_demand),
               names_to = "sector", values_to = "demand") |>
  mutate(sector = case_when(
    sector == "total_res_demand" ~ "Residential",
    sector == "total_com_demand" ~ "Commercial", 
    sector == "total_ind_demand" ~ "Industrial"
  ))

# 3. Data for 2030 (ordered by ascending total_demand)
df_2030 <- df_demand_complete |> 
  filter(year == 2030) |>
  arrange(total_demand) |>
  mutate(
    scenario = paste0("S", 1:9),  # Create scenario labels
    color_group = ifelse(total_demand < 300, "below_300", "above_300"),
    # Position columns with reduced gap (2025-2029 for 9 scenarios)
    year_dodged = seq(2025, 2029, length.out = 9)
  )

# Data for trend line (2015-2024)
df_trend <- df_demand_complete |> 
  filter(year >= 2015 & year <= 2024) |>
  select(year, total_demand)

# Create the plot
# Prepare data for plotting
# 1. Data for 2015-2019 (total demand only)
df_2015_2019 <- df_demand_complete |> 
  filter(year >= 2015 & year <= 2019) |>
  mutate(group = "historical_total")

# 2. Data for 2020-2024 (stacked sectorial)
df_2020_2024 <- df_demand_complete |> 
  filter(year >= 2020 & year <= 2024) |>
  pivot_longer(cols = c(total_res_demand, total_com_demand, total_ind_demand),
               names_to = "sector", values_to = "demand") |>
  mutate(sector = case_when(
    sector == "total_res_demand" ~ "Residential",
    sector == "total_com_demand" ~ "Commercial", 
    sector == "total_ind_demand" ~ "Industrial"
  ))

df_2020_2024 <- df_2020_2024 |> 
  mutate(demand_share = demand/total_demand)

# 3. Data for 2030 (ordered by ascending total_demand)
df_2030 <- df_demand_complete |> 
  filter(year == 2030) |>
  arrange(total_demand) |>
  mutate(
    scenario = paste0("S", 1:9),  # Create scenario labels
    color_group = ifelse(total_demand < 300, "Accepted projections", "Rejected projections"),
    # Position columns with more space after 2024 (2026-2030 for 9 scenarios)
    year_dodged = seq(2026, 2030, length.out = 9)
  )

# Data for trend line (2015-2024)
df_trend <- df_demand_complete |> 
  filter(year >= 2015 & year <= 2024) |>
  select(year, total_demand)

# Create the plot
p4.1 <- ggplot() +
  # 1. Total demand columns for 2015-2019
  geom_col(data = df_2015_2019, 
           aes(x = year, y = total_demand), 
           fill = "lightblue", width = 0.7, alpha = 0.8) +
  
  # 2. Stacked columns for 2020-2024
  geom_col(data = df_2020_2024, 
           aes(x = year, y = demand, fill = sector), 
           width = 0.7, alpha = 0.8) +
  
  # 4. Columns for 2030 scenarios (ordered and larger width)
  geom_col(data = df_2030, 
           aes(x = year_dodged, y = total_demand, fill = color_group), 
           width = 0.6, alpha = 0.8) +
  
  # 5. Trend line for 2020-2024 extended from 2015 to 2030
  geom_smooth(data = df_demand_complete |> filter(year >= 2020 & year <= 2024), 
              aes(x = year, y = total_demand, linetype = "2020-2024 trend"), 
              method = "lm", se = FALSE, fullrange = TRUE,
              color = "darkblue", size = 1.2) +
  
  # Custom colors
  scale_fill_manual(values = c(
    "Residential" = "steelblue",
    "Commercial" = "peru", 
    "Industrial" = "maroon",
    "Accepted projections" = "seagreen",
    "Rejected projections" = "darkred"
  )) +
  
  scale_linetype_manual(name = "", values = c("2020-2024 trend" = "dashed")) +
  
  # Customize x-axis with more space between 2024 and 2026
  scale_x_continuous(
    breaks = c(2015:2024, 2028),
    labels = c(2015:2024, "2030"),
    limits = c(2014.5, 2030.5)
  ) +
  
  # Labels and theme
  labs(
    x = NULL,
    y = "Demand (TWh)",
    fill = "Category"
  ) +
  
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
    panel.grid.major.x = element_blank(),
    panel.grid.minor = element_blank(),
    panel.border = element_rect(color = "gray75", fill = NA, size = 0.5),
    plot.margin = margin(20, 30, 20, 20)
  ) +
  
  # Add numbers on top of columns
  # For 2015-2019 (1 decimal)
  geom_text(data = df_2015_2019, 
            aes(x = year, y = total_demand + 5, label = round(total_demand, 1)),
            vjust = -0.8, hjust = 0.5, color = "black", size = 4.5, fontface = "bold") +
  
  # For 2020-2024 stacked columns (1 decimal, show total)
  geom_text(data = df_demand_complete|> filter(year >= 2020 & year <= 2024), 
            aes(x = year, y = total_demand + 5, label = round(total_demand, 1)),
            vjust = -0.8, hjust = 0.5, color = "black", size = 4.5, fontface = "bold") +
  
  # For 2030 scenarios (0 decimals)
  geom_text(data = df_2030, 
            aes(x = year_dodged, y = total_demand + 5, label = round(total_demand, 0)),
            vjust = -0.8, hjust = 0.5, color = "black", size = 4.5, fontface = "bold")

# Display the plot
p4.1

ggsave(file.path(output_graphs, "41_evolution_demand.png"),
       p4.1,
       bg = "white"
)



### G4.2 Hourly demand profile ----

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
p4.2 <- ggplot(hourly_demand, aes(x = hour)) +
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

p4.2

ggsave(file.path(output_graphs, "42_historical_hourly_demand.png"),
       p4.2,
       bg = "white"
)


### G4.3 Monthly demand profile ----

# Calculate monthly demand with confidence intervals
monthly_demand <- compute_profiles(historical_data, month)

# Create the monthly plot 
p4.3 <- ggplot(monthly_demand, aes(x = month)) +
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

p4.3

ggsave(file.path(output_graphs, "43_historical_hourly_demand.png"),
       p4.3,
       bg = "white"
)

## ===== Graph 5. Solar and wind capacity factors ===== 

solar_wind_cap_factors <- historical_data |> 
  select(year, month, day, hour, solar_pv_cap_factor, wind_cap_factor)

# Transform data to long format for box plots
hourly_long_boxplot <- solar_wind_cap_factors |>
  pivot_longer(
    cols = c(solar_pv_cap_factor, wind_cap_factor),
    names_to = "type",
    values_to = "capacity_factor"
  ) |>
  mutate(
    type = case_when(
      type == "solar_pv_cap_factor" ~ "Solar PV",
      type == "wind_cap_factor" ~ "Wind",
      TRUE ~ type
    ),
    hour = factor(hour)  
  )

monthly_long_boxplot <- solar_wind_cap_factors %>%
  pivot_longer(
    cols = c(solar_pv_cap_factor, wind_cap_factor),
    names_to = "type",
    values_to = "capacity_factor"
  ) %>%
  mutate(
    type = case_when(
      type == "solar_pv_cap_factor" ~ "Solar PV",
      type == "wind_cap_factor" ~ "Wind",
      TRUE ~ type
    ),
    month = factor(month, levels = 1:12, labels = month.abb)  # Convert month to factor with month names
  )


### G5.1 Hourly capacity factor profiles ----

# Solar PV box plot
solar_hourly_boxplot <- hourly_long_boxplot |>
  filter(type == "Solar PV") |>
  ggplot(aes(x = hour, y = capacity_factor * 100)) +
  geom_boxplot(fill = "#F4C430", alpha = 0.8, outlier.shape = NA) +
  labs(y = "Solar PV Capacity Factor (%)") +
  theme_minimal() +
  theme(
    axis.title.x = element_blank(),
    axis.title.y = element_text(face = "bold", size = 16),
    axis.text = element_text(color = "gray10", face = "bold", size = 12),
    axis.text.y = element_text(size = 14),
    axis.ticks.x = element_blank(),
    legend.position = "none",
    panel.grid.major.x = element_line(color = "gray90", size = 0.2),
    panel.grid.minor = element_blank(),
    panel.border = element_rect(color = "gray75", fill = NA, size = 0.5),
    plot.margin = margin(20, 30, 20, 20)
  )

# Wind box plot
wind_hourly_boxplot <- hourly_long_boxplot |>
  filter(type == "Wind") |>
  ggplot(aes(x = hour, y = capacity_factor * 100)) +
  geom_boxplot(fill = "seagreen", alpha = 0.8, outlier.shape = NA) +
  labs(y = "Wind Capacity Factor (%)") +
  theme_minimal() +
  theme(
    axis.title.x = element_blank(),
    axis.title.y = element_text(face = "bold", size = 16),
    axis.text = element_text(color = "gray10", face = "bold", size = 12),
    axis.text.y = element_text(size = 14),
    axis.ticks.x = element_blank(),
    legend.position = "none",
    panel.grid.major.x = element_line(color = "gray90", size = 0.2),
    panel.grid.minor = element_blank(),
    panel.border = element_rect(color = "gray75", fill = NA, size = 0.5),
    plot.margin = margin(20, 30, 20, 20)
  )


p5.1 <- solar_hourly_boxplot + wind_hourly_boxplot

p5.1

ggsave(file.path(output_graphs, "51_hourly_solar_wind_cap_factors.png"),
       p5.1,
       bg = "white"
)


### G5.2 Hourly capacity factor profiles ----

# Solar PV monthly box plot
solar_monthly_boxplot <- monthly_long_boxplot %>%
  filter(type == "Solar PV") %>%
  ggplot(aes(x = month, y = capacity_factor * 100)) +
  geom_boxplot(fill = "#F4C430", alpha = 0.8, outlier.shape = NA) +
  labs(y = "Solar PV Capacity Factor (%)") +
  theme_minimal() +
  theme(
    axis.title.x = element_blank(),
    axis.title.y = element_text(face = "bold", size = 16),
    axis.text = element_text(color = "gray10", face = "bold", size = 12),
    axis.text.y = element_text(size = 14),
    axis.ticks.x = element_blank(),
    legend.position = "none",
    panel.grid.major.x = element_line(color = "gray90", size = 0.2),
    panel.grid.minor = element_blank(),
    panel.border = element_rect(color = "gray75", fill = NA, size = 0.5),
    plot.margin = margin(20, 30, 20, 20)
  )

# Wind monthly box plot
wind_monthly_boxplot <- monthly_long_boxplot %>%
  filter(type == "Wind") %>%
  ggplot(aes(x = month, y = capacity_factor * 100)) +
  geom_boxplot(fill = "seagreen", alpha = 0.8, outlier.shape = NA) +
  labs(y = "Wind Capacity Factor (%)") +
  theme_minimal() +
  theme(
    axis.title.x = element_blank(),
    axis.title.y = element_text(face = "bold", size = 16),
    axis.text = element_text(color = "gray10", face = "bold", size = 12),
    axis.text.y = element_text(size = 14),
    axis.ticks.x = element_blank(),
    legend.position = "none",
    panel.grid.major.x = element_line(color = "gray90", size = 0.2),
    panel.grid.minor = element_blank(),
    panel.border = element_rect(color = "gray75", fill = NA, size = 0.5),
    plot.margin = margin(20, 30, 20, 20)
  )

p5.2 <- solar_monthly_boxplot + wind_monthly_boxplot

p5.2

ggsave(file.path(output_graphs, "52_monthly_solar_wind_cap_factors.png"),
       p5.2,
       bg = "white"
)

