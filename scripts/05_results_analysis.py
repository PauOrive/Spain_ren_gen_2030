"""
Results Analysis Script for Spain 2030 Renewable Generation Study

Analysis conducted:
- Summary statistics tables for each scenario
- Distribution plots (renewable share, prices)
- Hourly and monthly profiles for emissions and prices
- Generation vs capacity mix analysis
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import warnings

warnings.filterwarnings('ignore')

# Setting for single-column figures
plt.rcParams.update({
    'font.size': 11,
    'axes.labelsize': 12,
    'axes.titlesize': 13,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10
})

# ============================================================================
# CONFIGURATION AND PATHS
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR     = PROJECT_ROOT / "output" / "detailed_results"
OUTPUT_DIR   = PROJECT_ROOT / "output" / "results_analysis"
GRAPHS_DIR   = OUTPUT_DIR / "graphs"
TABLES_DIR   = OUTPUT_DIR / "tables"

# Create output directories if they don't exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
GRAPHS_DIR.mkdir(parents=True, exist_ok=True)
TABLES_DIR.mkdir(parents=True, exist_ok=True)

# Define scenarios
SCENARIOS = ["baseline", "nuclear", "optimistic", "climate change", "no batteries"]

# Color palette for scenarios
COLORS = {
    "baseline": "#1f77b4",
    "nuclear": "#ff7f0e",
    "optimistic": "#2ca02c",
    "climate change": "#d62728",
    "no batteries": "#9467bd"
}

# ============================================================================
# DATA LOADING FUNCTIONS
# ============================================================================

def load_scenario_data(scenario_name):
    """
    Load all data files for a given scenario.
    
    Returns: dict with DataFrames for main_results, hourly_profiles, 
             monthly_profiles, delta_draws, inputs_realized
    """
    data = {}
    
    # Map scenario names to file prefixes
    file_prefix = scenario_name
    
    try:
        # Load main results
        main_results_file = DATA_DIR / f"{file_prefix}_main_results.csv"
        if main_results_file.exists():
            data['main_results'] = pd.read_csv(main_results_file)
        
        # Load hourly profiles
        hourly_file = DATA_DIR / f"{file_prefix}_hourly_profiles.csv"
        if hourly_file.exists():
            data['hourly_profiles'] = pd.read_csv(hourly_file)
        
        # Load monthly profiles
        monthly_file = DATA_DIR / f"{file_prefix}_monthly_profiles.csv"
        if monthly_file.exists():
            data['monthly_profiles'] = pd.read_csv(monthly_file)
        
        # Load delta draws (uncertainty parameters)
        delta_file = DATA_DIR / f"{file_prefix}_delta_draws.csv"
        if delta_file.exists():
            data['delta_draws'] = pd.read_csv(delta_file)
        
        # Load realized inputs
        inputs_file = DATA_DIR / f"{file_prefix}_inputs_realized.csv"
        if inputs_file.exists():
            data['inputs_realized'] = pd.read_csv(inputs_file)
        
        print(f"[OK] Loaded data for {scenario_name}")
        return data
    
    except Exception as e:
        print(f"[ERROR] Error loading data for {scenario_name}: {e}")
        return {}


def load_all_scenarios():
    """Load data for all scenarios."""
    all_data = {}
    for scenario in SCENARIOS:
        all_data[scenario] = load_scenario_data(scenario)
    return all_data

# ============================================================================
# SUMMARY STATISTICS
# ============================================================================

def calculate_main_statistics(all_data):
    """
    Summary statistics table per scenario.
    Units from Julia model:
    - Shares: decimal (0-1) → converted to %
    - Demand: GWh → converted to TWh (/ 1e3)
    - Welfare columns: euros → converted to €B (/ 1e9)
    - Emissions: already in MtCO2
    - Everything else: as-is
    """
    rows = []

    for scenario_name in SCENARIOS:
        data = all_data.get(scenario_name, {})
        if not data or 'main_results' not in data:
            print(f"Warning: No main_results data for {scenario_name}")
            continue

        df = data['main_results']
        ren_share = df['share_renewable_gen'] * 100  

        row = {
            'Scenario':                scenario_name,
            # Renewable share
            'Ren. Share Mean (%)':     round(ren_share.mean(), 2),
            'Ren. Share Std Dev (%)':  round(ren_share.std(), 2),
            'Ren. Share 5th Pct (%)':  round(ren_share.quantile(0.05), 2),
            'Ren. Share 95th Pct (%)': round(ren_share.quantile(0.95), 2),
            'Prob. Target 81% (%)':    round((ren_share >= 81).mean() * 100, 2),
            # Generation shares
            'Low Carbon Share (%)':    round(df['share_low_carbon_gen'].mean() * 100, 2),
            'Min Non-Ren Share (%)':   round(df['share_min_non_ren'].mean() * 100, 2),
            # Storage
            'Battery Out (GWh)':       round(df['battery_out'].mean(), 2),
            'Pumped Hydro Out (GWh)':  round(df['pumped_hydro_out'].mean(), 2),
            'Storage Share (%)':       round((df['storage_out'] / df['total_generation']).mean() * 100, 2),
            # Market
            'Avg. Price (€/MWh)':      round(df['avg_price'].mean(), 2),
            'Demand (TWh)':            round((df['total_demand'] / 1e3).mean(), 2),
            # Welfare
            'Consumer Surplus (€B)':   round((df['consumer_surplus'] / 1e9).mean(), 2),
            'Producer Surplus (€B)':   round((df['producer_surplus'] / 1e9).mean(), 2),
            'Total Cost (€B)':         round((df['total_cost'] / 1e9).mean(), 2),
            'Net Welfare (€B)':        round((df['net_welfare'] / 1e9).mean(), 2),
            # Environmental
            'Emissions (MtCO2)':       round((df['direct_emissions'] / 1e6).mean(), 2),
            'Solar Curtailment (%)':   round(df['curt_solar_pv'].mean() * 100, 2),
            'Wind Curtailment (%)':    round(df['curt_wind'].mean() * 100, 2),
            # Reliability
            'LOLE Hours':              round(df['lole_hours'].mean(), 2),
            'EENS (GWh)':              round(df['total_ens'].mean(), 2),
        }
        rows.append(row)

    summary_df = pd.DataFrame(rows)

    output_file = TABLES_DIR / "01_main_statistics.csv"
    summary_df.to_csv(output_file, index=False)
    print(f"\n[OK] Main statistics saved to {output_file}")
    print(summary_df.to_string())

    return summary_df


def generate_latex_rows(all_data):
    """
    Generates a .tex file with all result rows ready to paste into any LaTeX table.
    No \\midrule separators — add them manually as needed.
    Covers all metrics computed in calculate_main_statistics.
    """
    rows = []

    for scenario_name in SCENARIOS:
        data = all_data.get(scenario_name, {})
        if not data or 'main_results' not in data:
            print(f"Warning: No main_results data for {scenario_name}")
            continue

        df = data['main_results']
        ren_share = df['share_renewable_gen'] * 100

        row = {
            'Ren. Share Mean (\\%)':     round(ren_share.mean(), 2),
            'Ren. Share Std Dev (\\%)':  round(ren_share.std(), 2),
            'Ren. Share 5th Pct (\\%)':  round(ren_share.quantile(0.05), 2),
            'Ren. Share 95th Pct (\\%)': round(ren_share.quantile(0.95), 2),
            'Compliance Prob. $\\ge 81\\%$ (\\%)': round((ren_share >= 81).mean() * 100, 2),
            'Low Carbon Share (\\%)':    round(df['share_low_carbon_gen'].mean() * 100, 2),
            'Min Non-Ren Share (\\%)':   round(df['share_min_non_ren'].mean() * 100, 2),
            'CC Gas Gen. (\\%)':         round((df['combined_cycle_gen'] / df['total_generation']).mean() * 100, 2),
            'Battery Out (GWh)':         round(df['battery_out'].mean(), 2),
            'Pumped Hydro Out (GWh)':    round(df['pumped_hydro_out'].mean(), 2),
            'Storage Share (\\%)':       round((df['storage_out'] / df['total_generation']).mean() * 100, 2),
            'Avg. Price (\\euro/MWh)':   round(df['avg_price'].mean(), 2),
            'Demand (TWh)':              round((df['total_demand'] / 1e3).mean(), 2),
            'Consumer Surplus (\\euro B)': round((df['consumer_surplus'] / 1e9).mean(), 2),
            'Producer Surplus (\\euro B)': round((df['producer_surplus'] / 1e9).mean(), 2),
            'Total Cost (\\euro B)':       round((df['total_cost'] / 1e9).mean(), 2),
            'Net Welfare (\\euro B)':      round((df['net_welfare'] / 1e9).mean(), 2),
            'Emissions (MtCO$_2$)':      round(df['direct_emissions'].mean(), 2),
            'Solar Curtailment (\\%)':   round(df['curt_solar_pv'].mean() * 100, 2),
            'Wind Curtailment (\\%)':    round(df['curt_wind'].mean() * 100, 2),
            'LOLE (hours)':              round(df['lole_hours'].mean(), 2),
            'EENS (GWh)':                round(df['total_ens'].mean(), 2),
        }
        rows.append(row)

    # Build LaTeX lines
    metrics   = list(rows[0].keys())
    scenarios = [r['Scenario'] for r in rows] if 'Scenario' in rows[0] else SCENARIOS

    lines = []
    for metric in metrics:
        values = ' & '.join(
            '-' if pd.isna(row.get(metric)) else f'{row.get(metric, 0):.2f}'
            for row in rows
        )
        lines.append(f'        {metric} & {values} \\\\')

    output = '\n'.join(lines)

    latex_output = TABLES_DIR / "01_all_results_rows.tex"
    with open(latex_output, 'w', encoding='utf-8') as f:
        f.write(output)
    print(f"[OK] All LaTeX result rows saved to {latex_output}")

    return output


# ============================================================================
# DISTRIBUTION ANALYSIS
# ============================================================================

def analyze_renewable_share_distributions(all_data):
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    axes = axes.flatten()

    # Compute global x range across all scenarios
    all_shares = []
    for scenario_name in SCENARIOS:
        data = all_data.get(scenario_name, {})
        if data and 'main_results' in data:
            all_shares.append(data['main_results']['share_renewable_gen'] * 100)
    
    xlim = None
    if all_shares:
        combined = pd.concat(all_shares)
        x_min, x_max = combined.min(), combined.max()
        margin = (x_max - x_min) * 0.05
        xlim = (x_min - margin, x_max + margin)

    for idx, scenario_name in enumerate(SCENARIOS):
        data = all_data.get(scenario_name, {})
        if not data or 'main_results' not in data:
            continue

        df = data['main_results']
        ren_share = df['share_renewable_gen'] * 100

        def _plot(ax):
            ax.hist(ren_share, bins=50, color=COLORS.get(scenario_name, '#1f77b4'),
                    alpha=0.7, edgecolor='black')
            ax.axvline(ren_share.mean(), color='red', linestyle='--', linewidth=2,
                       label=f'Mean: {ren_share.mean():.1f}%')
            ax.axvline(81, color='green', linestyle='--', linewidth=2, label='Target: 81%')
            if xlim:
                ax.set_xlim(xlim)
            ax.set_xlabel('Renewable Share (%)')
            ax.set_ylabel('Frequency')
            ax.set_title(scenario_name.capitalize())
            ax.legend()
            ax.grid(alpha=0.3)

        _plot(axes[idx])

        fig_ind, ax_ind = plt.subplots(figsize=(5.5, 4.5))
        _plot(ax_ind)
        fig_ind.tight_layout()
        fig_ind.savefig(GRAPHS_DIR / f"03_renewable_share_{scenario_name.replace(' ', '_')}.png",
                        dpi=300, bbox_inches='tight')
        plt.close(fig_ind)

    fig.delaxes(axes[-1])
    plt.tight_layout()
    fig.savefig(GRAPHS_DIR / "03_renewable_share_distributions.png", dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"[OK] Renewable share distributions saved to {OUTPUT_DIR}")

HISTORICAL_AVG_PRICE = 93.07  # €/MWh, Spain historical average 2020-2024

def analyze_price_distributions(all_data):
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    axes = axes.flatten()

    # Compute global x range across all scenarios
    all_prices = []
    for scenario_name in SCENARIOS:
        data = all_data.get(scenario_name, {})
        if data and 'main_results' in data:
            all_prices.append(data['main_results']['avg_price'])

    xlim = None
    if all_prices:
        combined = pd.concat(all_prices)
        x_min, x_max = combined.min(), combined.max()
        margin = (x_max - x_min) * 0.05
        xlim = (x_min - margin, x_max + margin)

    for idx, scenario_name in enumerate(SCENARIOS):
        data = all_data.get(scenario_name, {})
        if not data or 'main_results' not in data:
            continue

        df = data['main_results']
        prices = df['avg_price']

        def _plot(ax):
            ax.hist(prices, bins=50, color=COLORS.get(scenario_name, '#1f77b4'),
                    alpha=0.7, edgecolor='black')
            ax.axvline(prices.mean(), color='red', linestyle='--', linewidth=2,
                       label=f'Mean: €{prices.mean():.1f}/MWh')
            ax.axvline(HISTORICAL_AVG_PRICE, color='orange', linestyle=':', linewidth=2,
                       label=f'Historical avg. (2020–24): €{HISTORICAL_AVG_PRICE}/MWh')
            if xlim:
                ax.set_xlim(xlim)
            ax.set_xlabel('Average Price (€/MWh)')
            ax.set_ylabel('Frequency')
            ax.set_title(scenario_name.capitalize())
            ax.legend()
            ax.grid(alpha=0.3)

        _plot(axes[idx])

        fig_ind, ax_ind = plt.subplots(figsize=(5.5, 4.5))
        _plot(ax_ind)
        fig_ind.tight_layout()
        fig_ind.savefig(GRAPHS_DIR / f"04_price_distributions_{scenario_name.replace(' ', '_')}.png",
                        dpi=300, bbox_inches='tight')
        plt.close(fig_ind)

    fig.delaxes(axes[-1])
    plt.tight_layout()
    fig.savefig(GRAPHS_DIR / "04_price_distributions.png", dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"[OK] Price distributions saved to {OUTPUT_DIR}")


# ============================================================================
# HOURLY PROFILE ANALYSIS
# ============================================================================

def analyze_hourly_profiles(all_data):
    """
    Hourly price and emissions profiles by scenario.
    """
    fig1, ax_price     = plt.subplots(figsize=(5.5, 4.5))
    fig2, ax_emissions = plt.subplots(figsize=(5.5, 4.5))

    for scenario_name in SCENARIOS:
        data = all_data.get(scenario_name, {})
        if not data or 'hourly_profiles' not in data:
            continue

        df = data['hourly_profiles']

        if 'hour' not in df.columns:
            df['hour'] = (df.index % 8760) % 24

        hourly = df.groupby('hour')[['price', 'emissions']].mean()

        ax_price.plot(hourly.index, hourly['price'],
                      label=scenario_name.capitalize(),
                      color=COLORS.get(scenario_name, '#1f77b4'),
                      linewidth=2, marker='o', markersize=4)

        ax_emissions.plot(hourly.index, hourly['emissions'],
                          label=scenario_name.capitalize(),
                          color=COLORS.get(scenario_name, '#1f77b4'),
                          linewidth=2, marker='o', markersize=4)

    ax_price.set_xlabel('Hour of Day')
    ax_price.set_ylabel('Average Price (€/MWh)')
    ax_price.set_title('Hourly Price Profile')
    ax_price.set_xticks(range(0, 24, 2))
    ax_price.legend()
    ax_price.grid(alpha=0.3)
    fig1.tight_layout()
    fig1.savefig(GRAPHS_DIR / '05_hourly_profiles_price.png', dpi=300, bbox_inches='tight')
    plt.close(fig1)

    ax_emissions.set_xlabel('Hour of Day')
    ax_emissions.set_ylabel('Average Emissions (tCO2/MWh)')
    ax_emissions.set_title('Hourly Emissions Profile')
    ax_emissions.set_xticks(range(0, 24, 2))
    ax_emissions.legend()
    ax_emissions.grid(alpha=0.3)
    fig2.tight_layout()
    fig2.savefig(GRAPHS_DIR / '05_hourly_profiles_emissions.png', dpi=300, bbox_inches='tight')
    plt.close(fig2)

    # CSV export: hourly price per scenario (one row per hour, one col per scenario)
    price_rows = []
    for scenario_name in SCENARIOS:
        data = all_data.get(scenario_name, {})
        if not data or 'hourly_profiles' not in data:
            continue
        df = data['hourly_profiles'].copy()
        if 'hour' not in df.columns:
            df['hour'] = (df.index % 8760) % 24
        s = df.groupby('hour')['price'].mean()
        s.name = scenario_name
        price_rows.append(s)
    if price_rows:
        df_out = pd.concat(price_rows, axis=1)
        df_out.index.name = 'hour'
        df_out.to_csv(TABLES_DIR / '05_hourly_profiles_price.csv')
    print(f"[OK] Hourly profiles saved to {OUTPUT_DIR}")

# ============================================================================
# MONTHLY PROFILE ANALYSIS
# ============================================================================

def analyze_monthly_profiles(all_data):
    """
    Monthly price and emissions profiles by scenario.
    """
    fig1, ax_price     = plt.subplots(figsize=(5.5, 4.5))
    fig2, ax_emissions = plt.subplots(figsize=(5.5, 4.5))

    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    for scenario_name in SCENARIOS:
        data = all_data.get(scenario_name, {})
        if not data or 'monthly_profiles' not in data:
            continue

        df = data['monthly_profiles']

        if 'month' in df.columns:
            monthly = df.groupby('month')[['price', 'emissions']].mean()
        else:
            monthly = df.iloc[:12].reset_index(drop=True)
            monthly.index = range(1, 13)

        ax_price.plot(monthly.index, monthly['price'],
                      label=scenario_name.capitalize(),
                      color=COLORS.get(scenario_name, '#1f77b4'),
                      linewidth=2, marker='o', markersize=4)

        ax_emissions.plot(monthly.index, monthly['emissions'],
                          label=scenario_name.capitalize(),
                          color=COLORS.get(scenario_name, '#1f77b4'),
                          linewidth=2, marker='o', markersize=4)

    ax_price.set_xlabel('Month')
    ax_price.set_ylabel('Average Price (€/MWh)')
    ax_price.set_title('Monthly Price Profile')
    ax_price.set_xticks(range(1, 13))
    ax_price.set_xticklabels(months, rotation=45)
    ax_price.legend()
    ax_price.grid(alpha=0.3)
    fig1.tight_layout()
    fig1.savefig(GRAPHS_DIR / '06_monthly_profiles_price.png', dpi=300, bbox_inches='tight')
    plt.close(fig1)

    ax_emissions.set_xlabel('Month')
    ax_emissions.set_ylabel('Average Emissions (tCO2/MWh)')
    ax_emissions.set_title('Monthly Emissions Profile')
    ax_emissions.set_xticks(range(1, 13))
    ax_emissions.set_xticklabels(months, rotation=45)
    ax_emissions.legend()
    ax_emissions.grid(alpha=0.3)
    fig2.tight_layout()
    fig2.savefig(GRAPHS_DIR / '06_monthly_profiles_emissions.png', dpi=300, bbox_inches='tight')
    plt.close(fig2)

    # CSV export: monthly price per scenario (one row per month, one col per scenario)
    price_rows = []
    for scenario_name in SCENARIOS:
        data = all_data.get(scenario_name, {})
        if not data or 'monthly_profiles' not in data:
            continue
        df = data['monthly_profiles']
        s = df.groupby('month')['price'].mean() if 'month' in df.columns \
            else pd.Series(df['price'].iloc[:12].values, index=range(1, 13))
        s.name = scenario_name
        price_rows.append(s)
    if price_rows:
        df_out = pd.concat(price_rows, axis=1)
        df_out.index = ['Jan','Feb','Mar','Apr','May','Jun',
                        'Jul','Aug','Sep','Oct','Nov','Dec']
        df_out.index.name = 'month'
        df_out.to_csv(TABLES_DIR / '06_monthly_profiles_price.csv')
    print(f"[OK] Monthly profiles saved to {OUTPUT_DIR}")


# ============================================================================
# COMBINED PROFILE FIGURES (grouped by price / by emissions)
# ============================================================================

def analyze_combined_profiles(all_data):
    """
    Two combined figures:
      - Price combined:     hourly price (top) + monthly price (bottom)
      - Emissions combined: hourly emissions (top) + monthly emissions (bottom)
    """
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    fig_price, (ax_hp, ax_mp) = plt.subplots(2, 1, figsize=(5.5, 8))
    fig_emis,  (ax_he, ax_me) = plt.subplots(2, 1, figsize=(5.5, 8))

    for scenario_name in SCENARIOS:
        data  = all_data.get(scenario_name, {})
        color = COLORS.get(scenario_name, '#1f77b4')
        kw    = dict(label=scenario_name.capitalize(), color=color,
                     linewidth=2, marker='o', markersize=4)

        # Hourly rows
        if data and 'hourly_profiles' in data:
            df = data['hourly_profiles'].copy()
            if 'hour' not in df.columns:
                df['hour'] = (df.index % 8760) % 24
            hourly = df.groupby('hour')[['price', 'emissions']].mean()
            ax_hp.plot(hourly.index, hourly['price'],     **kw)
            ax_he.plot(hourly.index, hourly['emissions'], **kw)

        # Monthly rows
        if data and 'monthly_profiles' in data:
            df = data['monthly_profiles']
            if 'month' in df.columns:
                monthly = df.groupby('month')[['price', 'emissions']].mean()
            else:
                monthly = df.iloc[:12].reset_index(drop=True)
                monthly.index = range(1, 13)
            ax_mp.plot(monthly.index, monthly['price'],     **kw)
            ax_me.plot(monthly.index, monthly['emissions'], **kw)

    # Price combined formatting
    ax_hp.set_xlabel('Hour of Day', fontsize=12)
    ax_hp.set_ylabel('Average Price (€/MWh)', fontsize=12)
    ax_hp.set_title('Hourly Price Profile', fontsize=13)
    ax_hp.set_xticks(range(0, 24, 2))
    ax_hp.tick_params(labelsize=10)
    ax_hp.legend(fontsize=10)
    ax_hp.grid(alpha=0.3)

    ax_mp.set_xlabel('Month', fontsize=12)
    ax_mp.set_ylabel('Average Price (€/MWh)', fontsize=12)
    ax_mp.set_title('Monthly Price Profile', fontsize=13)
    ax_mp.set_xticks(range(1, 13))
    ax_mp.set_xticklabels(months, rotation=45)
    ax_mp.tick_params(labelsize=10)
    ax_mp.legend(fontsize=10)
    ax_mp.grid(alpha=0.3)

    fig_price.tight_layout()
    fig_price.savefig(GRAPHS_DIR / '05_06_price_profiles_combined.png', dpi=300, bbox_inches='tight')
    plt.close(fig_price)

    # Emissions combined formatting
    ax_he.set_xlabel('Hour of Day', fontsize=12)
    ax_he.set_ylabel('Average Emissions (tCO2/MWh)', fontsize=12)
    ax_he.set_title('Hourly Emissions Profile', fontsize=13)
    ax_he.set_xticks(range(0, 24, 2))
    ax_he.tick_params(labelsize=10)
    ax_he.legend(fontsize=10)
    ax_he.grid(alpha=0.3)

    ax_me.set_xlabel('Month', fontsize=12)
    ax_me.set_ylabel('Average Emissions (tCO2/MWh)', fontsize=12)
    ax_me.set_title('Monthly Emissions Profile', fontsize=13)
    ax_me.set_xticks(range(1, 13))
    ax_me.set_xticklabels(months, rotation=45)
    ax_me.tick_params(labelsize=10)
    ax_me.legend(fontsize=10)
    ax_me.grid(alpha=0.3)

    fig_emis.tight_layout()
    fig_emis.savefig(GRAPHS_DIR / '05_06_emissions_profiles_combined.png', dpi=300, bbox_inches='tight')
    plt.close(fig_emis)
    print(f"[OK] Combined price and emissions profiles saved to {OUTPUT_DIR}")


# ============================================================================
# GENERATION MIX PROFILES (HOURLY & MONTHLY — ALL SCENARIOS)
# ============================================================================

GEN_COLS = {
    'Solar PV':            ('solar_pv',  '#FFA500'),
    'Wind':                ('wind',      '#5F9EA0'),
    'Conventional Hydro':  ('conv_hydro','#4169E1'),
    'Combined Cycle':      ('ccgt',      '#E74C3C'),
    'Cogeneration':        ('cogen',     '#DC143C'),
    'Nuclear':             ('nuclear',   '#FFD700'),
    'Battery':             ('batt_out',  '#9370DB'),
    'Pumped Hydro':        ('ph_out',    '#4682B4'),
    'Other Renewable':     (None,        '#32CD32'),
    'Other Non-Renewable': (None,        '#FF8C00'),
}

def _build_generation_hourly(df):
    """Return mean-by-hour DataFrame with residual Other columns."""
    if 'hour' not in df.columns:
        df = df.copy()
        df['hour'] = (df.index % 8760) % 24
    hourly = df.groupby('hour')[['solar_pv', 'wind', 'conv_hydro', 'ccgt',
                                  'cogen', 'nuclear', 'batt_out', 'ph_out',
                                  'ren_gen', 'non_ren_gen']].mean()
    hourly['Other Renewable']     = (hourly['ren_gen']
                                     - hourly['solar_pv']
                                     - hourly['wind']
                                     - hourly['conv_hydro']).clip(lower=0)
    hourly['Other Non-Renewable'] = (hourly['non_ren_gen']
                                     - hourly['ccgt']
                                     - hourly['nuclear']
                                     - hourly['cogen']).clip(lower=0)
    return hourly

def _build_generation_monthly(df):
    """Return mean-by-month DataFrame with residual Other columns.
    Expects a monthly_profiles DataFrame which already has a 'month' column.
    """
    if 'month' not in df.columns:
        raise ValueError("monthly_profiles must contain a 'month' column")
    monthly = df.groupby('month')[['solar_pv', 'wind', 'conv_hydro', 'ccgt',
                                    'cogen', 'nuclear', 'batt_out', 'ph_out',
                                    'ren_gen', 'non_ren_gen']].mean()
    monthly['Other Renewable']     = (monthly['ren_gen']
                                      - monthly['solar_pv']
                                      - monthly['wind']
                                      - monthly['conv_hydro']).clip(lower=0)
    monthly['Other Non-Renewable'] = (monthly['non_ren_gen']
                                      - monthly['ccgt']
                                      - monthly['nuclear']
                                      - monthly['cogen']).clip(lower=0)
    return monthly

def _plot_generation_mix_grid(all_data, build_fn, xlabel, xticks_fn, filename,
                               data_key='hourly_profiles', xticklabels=None):
    """
    2×3 grid of stacked area charts (one per scenario, 6th cell = shared legend).
    build_fn: callable(df) → aggregated DataFrame
    xticks_fn: callable(ax) to set xticks
    """
    fig, axes = plt.subplots(2, 3, figsize=(16, 9))
    axes = axes.flatten()

    for idx, scenario_name in enumerate(SCENARIOS):
        ax = axes[idx]
        data = all_data.get(scenario_name, {})
        if not data or data_key not in data:
            ax.set_visible(False)
            continue

        agg = build_fn(data[data_key].copy())

        stack_data, stack_labels, stack_colors = [], [], []
        for tech, (col, color) in GEN_COLS.items():
            series = agg[tech] if col is None else agg[col]
            stack_data.append(series.values)
            stack_labels.append(tech)
            stack_colors.append(color)

        ax.stackplot(agg.index, stack_data, labels=stack_labels,
                     colors=stack_colors, alpha=0.85)
        ax.set_title(scenario_name.capitalize())
        ax.set_xlabel(xlabel)
        ax.set_ylabel('Mean Generation (GWh)')
        xticks_fn(ax)
        ax.grid(alpha=0.3)

    # 6th cell: shared legend
    ax_leg = axes[5]
    ax_leg.set_visible(False)
    handles = [plt.Rectangle((0, 0), 1, 1, color=c, alpha=0.85)
               for _, (_, c) in GEN_COLS.items()]
    labels  = list(GEN_COLS.keys())
    fig.legend(handles, labels, loc='lower right',
               bbox_to_anchor=(0.98, 0.05), ncol=2, fontsize=9,
               framealpha=0.95, title='Technology', title_fontsize=10)

    fig.tight_layout()
    fig.savefig(GRAPHS_DIR / filename, dpi=300, bbox_inches='tight')
    plt.close(fig)


def analyze_hourly_generation_mix(all_data):
    """Hourly generation mix stacked area — 2×3 grid, one panel per scenario."""
    _plot_generation_mix_grid(
        all_data,
        build_fn   = _build_generation_hourly,
        xlabel     = 'Hour of Day',
        xticks_fn  = lambda ax: ax.set_xticks(range(0, 24, 4)),
        filename   = '07_hourly_generation_mix.png',
    )
    print(f"[OK] Hourly generation mix saved to {OUTPUT_DIR}")


def analyze_monthly_generation_mix(all_data):
    """Monthly generation mix stacked area — 2×3 grid, one panel per scenario."""
    MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    def set_month_ticks(ax):
        ax.set_xticks(range(1, 13))
        ax.set_xticklabels(MONTHS, rotation=45, fontsize=8)

    _plot_generation_mix_grid(
        all_data,
        build_fn   = _build_generation_monthly,
        xlabel     = 'Month',
        xticks_fn  = set_month_ticks,
        filename   = '10_monthly_generation_mix.png',
        data_key   = 'monthly_profiles',
    )

    # CSV export
    rows = []
    for scenario_name in SCENARIOS:
        data = all_data.get(scenario_name, {})
        if not data or 'monthly_profiles' not in data:
            continue
        agg = _build_generation_monthly(data['monthly_profiles'].copy())
        for month_idx in agg.index:
            row = {'scenario': scenario_name, 'month': MONTHS[month_idx - 1]}
            for tech, (col, _) in GEN_COLS.items():
                row[tech] = agg.loc[month_idx, tech if col is None else col]
            rows.append(row)

    if rows:
        df_out = pd.DataFrame(rows).set_index(['scenario', 'month'])
        df_out.to_csv(TABLES_DIR / '10_monthly_generation_mix.csv')
    print(f"[OK] Monthly generation mix saved to {OUTPUT_DIR}")


def analyze_hourly_storage(all_data):
    """
    Hourly storage charge/discharge profiles for all scenarios.
    Charge shown as negative, discharge as positive.
    Saves two separate figures: one for batteries, one for pumped hydro.
    """
    fig_batt, ax_batt = plt.subplots(figsize=(7, 5))
    fig_ph,   ax_ph   = plt.subplots(figsize=(7, 5))

    for scenario_name in SCENARIOS:
        data = all_data.get(scenario_name, {})
        if not data or 'hourly_profiles' not in data:
            continue

        df = data['hourly_profiles'].copy()
        if 'hour' not in df.columns:
            df['hour'] = (df.index % 8760) % 24

        hourly = df.groupby('hour')[
            ['batt_in', 'batt_out', 'ph_in', 'ph_out']
        ].mean()

        color = COLORS.get(scenario_name, '#1f77b4')
        label = scenario_name.capitalize()

        # Battery
        ax_batt.plot(hourly.index,  hourly['batt_out'],
                     color=color, linewidth=2, marker='o', markersize=4, label=f'{label} (out)')
        ax_batt.plot(hourly.index, -hourly['batt_in'],
                     color=color, linewidth=2, marker='o', markersize=4,
                     linestyle='--', alpha=0.6, label=f'{label} (charge)')

        # Pumped hydro
        ax_ph.plot(hourly.index,  hourly['ph_out'],
                   color=color, linewidth=2, marker='o', markersize=4, label=f'{label} (out)')
        ax_ph.plot(hourly.index, -hourly['ph_in'],
                   color=color, linewidth=2, marker='o', markersize=4,
                   linestyle='--', alpha=0.6, label=f'{label} (pumping)')

    for ax, ylabel in [
        (ax_batt, 'Mean GWh (+ discharge / − charge)'),
        (ax_ph,   'Mean GWh (+ generation / − pumping)'),
    ]:
        ax.axhline(0, color='black', linewidth=0.8, linestyle='-')
        ax.set_xlabel('Hour of Day')
        ax.set_ylabel(ylabel)
        ax.set_xticks(range(0, 24, 2))
        ax.legend(fontsize=7, ncol=2)
        ax.grid(alpha=0.3)

    fig_batt.tight_layout()
    fig_batt.savefig(GRAPHS_DIR / '08_hourly_storage_battery.png', dpi=300, bbox_inches='tight')
    plt.close(fig_batt)

    fig_ph.tight_layout()
    fig_ph.savefig(GRAPHS_DIR / '08_hourly_storage_pumped_hydro.png', dpi=300, bbox_inches='tight')
    plt.close(fig_ph)

    # CSV export: one row per hour, columns = scenario_batt_out, scenario_batt_in, scenario_ph_out, scenario_ph_in
    storage_rows = []
    for scenario_name in SCENARIOS:
        data = all_data.get(scenario_name, {})
        if not data or 'hourly_profiles' not in data:
            continue
        df = data['hourly_profiles'].copy()
        if 'hour' not in df.columns:
            df['hour'] = (df.index % 8760) % 24
        hourly = df.groupby('hour')[['batt_in', 'batt_out', 'ph_in', 'ph_out']].mean()
        hourly.columns = [f'{scenario_name}_{c}' for c in hourly.columns]
        storage_rows.append(hourly)
    if storage_rows:
        pd.concat(storage_rows, axis=1).to_csv(TABLES_DIR / '08_hourly_storage_profiles.csv')
    print(f"[OK] Hourly storage profiles saved to {OUTPUT_DIR}")


def analyze_renewable_share_profiles(all_data):
    """
    Renewable share profiles: hourly (top) and monthly (bottom), all scenarios.
    """
    MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    fig, axes = plt.subplots(2, 1, figsize=(5.5, 8))

    for scenario_name in SCENARIOS:
        data    = all_data.get(scenario_name, {})
        color   = COLORS.get(scenario_name, '#1f77b4')
        label   = scenario_name.capitalize()
        kwargs  = dict(color=color, linewidth=2, marker='o', markersize=4, label=label)

        # Hourly
        if data and 'hourly_profiles' in data:
            df = data['hourly_profiles'].copy()
            if 'hour' not in df.columns:
                df['hour'] = (df.index % 8760) % 24
            hourly = df.groupby('hour')['ren_share'].mean() * 100
            axes[0].plot(hourly.index, hourly.values, **kwargs)

        # Monthly
        if data and 'monthly_profiles' in data:
            df = data['monthly_profiles']
            if 'month' in df.columns:
                monthly = df.groupby('month')['ren_share'].mean() * 100
            else:
                monthly = df['ren_share'].iloc[:12].reset_index(drop=True) * 100
                monthly.index = range(1, 13)
            axes[1].plot(monthly.index, monthly.values, **kwargs)

    axes[0].set_xlabel('Hour of Day', fontsize=12)
    axes[0].set_ylabel('Renewable Share (%)', fontsize=12)
    axes[0].set_title('Hourly Renewable Share', fontsize=13)
    axes[0].set_xticks(range(0, 24, 2))
    axes[0].tick_params(labelsize=10)
    axes[0].legend(fontsize=10)
    axes[0].grid(alpha=0.3)

    axes[1].set_xlabel('Month', fontsize=12)
    axes[1].set_ylabel('Renewable Share (%)', fontsize=12)
    axes[1].set_title('Monthly Renewable Share', fontsize=13)
    axes[1].set_xticks(range(1, 13))
    axes[1].set_xticklabels(MONTHS, rotation=45)
    axes[1].tick_params(labelsize=10)
    axes[1].legend(fontsize=10)
    axes[1].grid(alpha=0.3)

    fig.tight_layout()
    fig.savefig(GRAPHS_DIR / '09_renewable_share_profiles.png', dpi=300, bbox_inches='tight')
    plt.close(fig)

    # CSV export: hourly and monthly renewable share (%) per scenario
    hourly_rows, monthly_rows = [], []
    for scenario_name in SCENARIOS:
        data = all_data.get(scenario_name, {})
        if data and 'hourly_profiles' in data:
            df = data['hourly_profiles'].copy()
            if 'hour' not in df.columns:
                df['hour'] = (df.index % 8760) % 24
            s = df.groupby('hour')['ren_share'].mean() * 100
            s.name = scenario_name
            hourly_rows.append(s)
        if data and 'monthly_profiles' in data:
            df = data['monthly_profiles']
            if 'month' in df.columns:
                s = df.groupby('month')['ren_share'].mean() * 100
            else:
                s = df['ren_share'].iloc[:12].reset_index(drop=True) * 100
                s.index = range(1, 13)
            s.name = scenario_name
            monthly_rows.append(s)
    if hourly_rows:
        df_h = pd.concat(hourly_rows, axis=1)
        df_h.index.name = 'hour'
        df_h.to_csv(TABLES_DIR / '09_renewable_share_hourly.csv')
    if monthly_rows:
        df_m = pd.concat(monthly_rows, axis=1)
        df_m.index.name = 'month'
        df_m.to_csv(TABLES_DIR / '09_renewable_share_monthly.csv')
    print(f"[OK] Renewable share profiles saved to {OUTPUT_DIR}")

# ============================================================================
# INPUTS AND CAPACITY ANALYSIS
# ============================================================================

def analyze_inputs_and_capacity(all_data):
    """Summarize mean realized capacity inputs by scenario."""
    rows = []

    for scenario_name in SCENARIOS:
        data = all_data.get(scenario_name, {})
        if not data or 'inputs_realized' not in data:
            continue

        df = data['inputs_realized']
        cap_cols = [col for col in df.columns if 'cap_' in col.lower()]
        row = {'Scenario': scenario_name} | {col: round(df[col].mean(), 2) for col in cap_cols}
        rows.append(row)

    if rows:
        inputs_df = pd.DataFrame(rows)
        output_file = TABLES_DIR / "07_capacity_inputs.csv"
        inputs_df.to_csv(output_file, index=False)
        print(f"\n[OK] Capacity inputs saved to {output_file}")
        print(inputs_df.to_string())
        return inputs_df

    return None


# Technology definitions — shared between generation and capacity plots
TECH_COLORS = {
    'Wind':                '#5F9EA0',
    'Solar PV':            '#FFA500',
    'Solar Thermal':       '#FFD700',
    'Conventional Hydro':  '#4169E1',
    'Run-of-River Hydro':  '#87CEEB',
    'Other Renewable':     '#32CD32',
    'Renewable Waste':     '#90EE90',
    'Coal':                '#8B4513',
    'Combined Cycle':      '#E74C3C',
    'Gas Turbine':         '#FF6B6B',
    'Vapor Turbine':       '#CD5C5C',
    'Diesel':              '#A0522D',
    'Cogeneration':        '#DC143C',
    'Non-Renewable Waste': '#FF8C00',
    'Nuclear':             '#FFD700',
    'Battery':             '#9370DB',
    'Pumped Hydro':        '#4682B4',
}

TECH_ORDER = [
    'Wind', 'Solar PV', 'Solar Thermal', 'Conventional Hydro', 'Run-of-River Hydro',
    'Other Renewable', 'Renewable Waste',
    'Coal', 'Combined Cycle', 'Gas Turbine', 'Vapor Turbine',
    'Diesel', 'Cogeneration', 'Non-Renewable Waste', 'Nuclear',
]

GENERATION_COLS = {
    'Wind':                'wind_gen',
    'Solar PV':            'solar_pv_gen',
    'Solar Thermal':       'solar_thermal_gen',
    'Conventional Hydro':  'conventional_hydro_gen',
    'Run-of-River Hydro':  'run_of_river_hydro_gen',
    'Other Renewable':     'other_renewable_gen',
    'Renewable Waste':     'renewable_waste_gen',
    'Coal':                'coal_gen',
    'Combined Cycle':      'combined_cycle_gen',
    'Gas Turbine':         'gas_turbine_gen',
    'Vapor Turbine':       'vapor_turbine_gen',
    'Diesel':              'diesel_gen',
    'Cogeneration':        'cogeneration_gen',
    'Non-Renewable Waste': 'non_renewable_waste_gen',
    'Nuclear':             'nuclear_gen',
}

CAPACITY_COLS = {
    'Wind':                'wind_cap_gw',
    'Solar PV':            'solar_pv_cap_gw',
    'Solar Thermal':       'solar_thermal_cap_gw',
    'Conventional Hydro':  'conventional_hydro_cap_gw',
    'Run-of-River Hydro':  'run_of_river_hydro_cap_gw',
    'Other Renewable':     'other_renewable_cap_gw',
    'Renewable Waste':     'renewable_waste_cap_gw',
    'Coal':                'coal_cap_gw',
    'Combined Cycle':      'combined_cycle_cap_gw',
    'Gas Turbine':         'gas_turbine_cap_gw',
    'Vapor Turbine':       'vapor_turbine_cap_gw',
    'Diesel':              'diesel_cap_gw',
    'Cogeneration':        'cogeneration_cap_gw',
    'Non-Renewable Waste': 'nonrenewable_waste_cap_gw',
    'Nuclear':             'nuclear_cap_gw',
}


def _plot_stacked_bars(ax, data_by_tech, totals, ylabel, title):
    """Generic stacked bar chart with percentage labels for technologies >= 3%."""
    x_pos  = np.arange(len(SCENARIOS))
    bottom = np.zeros(len(SCENARIOS))

    for tech in TECH_ORDER:
        values = [data_by_tech[s].get(tech, 0) for s in SCENARIOS]
        if sum(values) == 0:
            continue

        bars = ax.bar(x_pos, values, 0.5, label=tech, bottom=bottom,
                      color=TECH_COLORS.get(tech, '#CCCCCC'), alpha=0.85,
                      edgecolor='white', linewidth=0.5)

        for i, (bar, val) in enumerate(zip(bars, values)):
            if totals[SCENARIOS[i]] > 0:
                pct = val / totals[SCENARIOS[i]] * 100
                if pct >= 3:
                    ax.text(bar.get_x() + bar.get_width() / 2., bottom[i] + bar.get_height() / 2.,
                            f'{pct:.1f}%', ha='center', va='center',
                            fontsize=7, fontweight='bold', color='white')
        bottom += values

    ax.set_ylabel(ylabel, fontsize=11, fontweight='bold')
    ax.set_xlabel('Scenario', fontsize=11, fontweight='bold')
    ax.set_title(title, fontsize=12, fontweight='bold', pad=10)
    ax.set_xticks(x_pos)
    ax.set_xticklabels([s.capitalize() for s in SCENARIOS], fontsize=10)
    ax.grid(axis='y', alpha=0.3)


def analyze_generation_vs_capacity_mix(all_data):
    """
    Stacked bar charts for generation mix (GWh) and capacity mix (GW) by scenario.
    """
    # Collect data
    gen_by_tech = {s: {} for s in SCENARIOS}
    cap_by_tech = {s: {} for s in SCENARIOS}
    total_gen   = {s: 0  for s in SCENARIOS}
    total_cap   = {s: 0  for s in SCENARIOS}

    for scenario_name in SCENARIOS:
        data = all_data.get(scenario_name, {})

        if data and 'main_results' in data:
            df = data['main_results']
            for tech, col in GENERATION_COLS.items():
                val = df[col].mean() if col in df.columns else 0
                gen_by_tech[scenario_name][tech] = val
                total_gen[scenario_name] += val

        if data and 'inputs_realized' in data:
            df = data['inputs_realized']
            for tech, col in CAPACITY_COLS.items():
                val = df[col].mean() if col in df.columns else 0
                cap_by_tech[scenario_name][tech] = val
                total_cap[scenario_name] += val

    # Generation plot
    fig1, ax1 = plt.subplots(figsize=(6, 5))
    _plot_stacked_bars(ax1, gen_by_tech, total_gen,
                       ylabel='Total Generation (GWh)',
                       title='Electricity Generation Mix')
    handles, labels = ax1.get_legend_handles_labels()
    fig1.legend(handles, labels, loc='center', bbox_to_anchor=(0.5, -0.05),
                ncol=4, fontsize=8, framealpha=0.95, title='Technology', title_fontsize=9)
    fig1.subplots_adjust(bottom=0.25)
    fig1.savefig(GRAPHS_DIR / "08_generation_mix.png", dpi=300, bbox_inches='tight')
    plt.close(fig1)

    # Capacity plot
    fig2, ax2 = plt.subplots(figsize=(6, 5))
    _plot_stacked_bars(ax2, cap_by_tech, total_cap,
                       ylabel='Total Installed Capacity (GW)',
                       title='Installed Capacity Mix')
    handles, labels = ax2.get_legend_handles_labels()
    fig2.legend(handles, labels, loc='center', bbox_to_anchor=(0.5, -0.05),
                ncol=4, fontsize=8, framealpha=0.95, title='Technology', title_fontsize=9)
    fig2.subplots_adjust(bottom=0.25)
    fig2.savefig(GRAPHS_DIR / "08_capacity_mix.png", dpi=300, bbox_inches='tight')
    plt.close(fig2)
    print(f"[OK] Generation and capacity mix saved to {OUTPUT_DIR}")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    print("\n" + "="*80)
    print("SPAIN 2030 RENEWABLE GENERATION - RESULTS ANALYSIS")
    print("="*80)

    if not DATA_DIR.exists():
        print(f"\n[ERROR] Data directory not found: {DATA_DIR}")
        return

    print(f"\nData:   {DATA_DIR}")
    print(f"Output: {OUTPUT_DIR}")

    # Load data
    all_data = load_all_scenarios()
    loaded = [s for s in SCENARIOS if s in all_data and all_data[s]]
    if not loaded:
        print("\n[ERROR] No data loaded. Please check the data directory structure.")
        return
    print(f"\n[OK] Loaded: {', '.join(loaded)}")

    # Analyses
    print("\n" + "-"*80)

    # --- Summary tables ---
    calculate_main_statistics(all_data)
    generate_latex_rows(all_data)
    analyze_renewable_share_distributions(all_data)
    analyze_price_distributions(all_data)
    analyze_inputs_and_capacity(all_data)
    analyze_generation_vs_capacity_mix(all_data)

    # --- Hourly profiles ---
    analyze_hourly_profiles(all_data)
    analyze_hourly_generation_mix(all_data)
    analyze_hourly_storage(all_data)

    # --- Monthly profiles ---
    analyze_monthly_profiles(all_data)
    analyze_monthly_generation_mix(all_data)

    # --- Combined hourly + monthly ---
    analyze_renewable_share_profiles(all_data)
    analyze_combined_profiles(all_data)

    print("\n" + "="*80)
    print("[OK] ANALYSIS COMPLETE")
    print(f"Results saved to: {OUTPUT_DIR}")
    print("="*80)

if __name__ == "__main__":
    main()