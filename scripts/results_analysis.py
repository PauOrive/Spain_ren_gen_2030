"""
Results Analysis Script for Spain 2030 Renewable Generation Study


Analisis que se van a hacer (basicamente los mismos graficos del thesis):
- Summary statistics tables for each scenario
- Distribution plots (renewable share, prices)
- Hourly and monthly profiles for emissions and prices
- Generation vs capacity mix analysis
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings

warnings.filterwarnings('ignore')

# Optimization for single-column figures
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
DATA_DIR = PROJECT_ROOT / "output" / "detailed_results"
OUTPUT_DIR = PROJECT_ROOT / "output" / "analysis"

# Create output directory if it doesn't exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

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

# ============================================================================
# HELPER FUNCTIONS FOR COLUMN DETECTION
# ============================================================================

def find_column(df, keywords):
    """
    Helper function to find a column by keywords.
    Looks for a column containing all specified keywords (case-insensitive).
    """
    keywords = [kw.lower() for kw in keywords] if isinstance(keywords, list) else [keywords.lower()]
    for col in df.columns:
        col_lower = col.lower()
        if all(kw in col_lower for kw in keywords):
            return col
    return None


# ============================================================================
# SUMMARY STATISTICS
# ============================================================================

def calculate_main_statistics(all_data):
    """
    Calculate main statistics per scenario for the results table.
    
    Replicates Table 1 from the paper with key performance measures.
    """
    summary_stats = []
    
    for scenario_name in SCENARIOS:
        data = all_data.get(scenario_name, {})
        
        if not data or 'main_results' not in data:
            print(f"Warning: No main_results data for {scenario_name}")
            continue
        
        df = data['main_results']
        stats = {'Scenario': scenario_name}
        
        # Renewable Share - use share column if available (decimal 0-1), convert to %
        share_ren_col = find_column(df, ['share', 'renewable']) or find_column(df, ['renewable', 'share'])
        if share_ren_col:
            ren_share = df[share_ren_col] * 100
        else:
            # Calculate from nominal values
            ren_col = find_column(df, ['renewable', 'generation']) or find_column(df, ['renewable', 'gen'])
            total_col = find_column(df, ['total', 'generation']) or find_column(df, ['total', 'gen'])
            if ren_col and total_col:
                ren_share = (df[ren_col] / df[total_col]) * 100
            else:
                ren_share = pd.Series([np.nan] * len(df))
        
        stats['Renewable Share (%)'] = ren_share.mean()
        stats['Ren. Share Std Dev (%)'] = ren_share.std()
        stats['Ren. Share 5th Pct (%)'] = ren_share.quantile(0.05)
        stats['Ren. Share 95th Pct (%)'] = ren_share.quantile(0.95)
        stats['Prob. Target (%)'] = (ren_share >= 81).sum() / len(df) * 100
        
        # Emissions - convert from tonnes to MtCO2
        emis_col = find_column(df, ['direct', 'emissions']) or find_column(df, ['emissions'])
        if emis_col:
            stats['Avg. Emissions (MtCO2)'] = (df[emis_col] / 1e6).mean()
        else:
            stats['Avg. Emissions (MtCO2)'] = np.nan
        
        # Price
        price_col = find_column(df, ['avg', 'price']) or find_column(df, ['price'])
        stats['Avg. Price (€/MWh)'] = df[price_col].mean() if price_col else np.nan
        
        # Solar Curtailment (%) - direct column search for curt_solar_pv
        if 'curt_solar_pv' in df.columns:
            solar_curt_vals = df['curt_solar_pv']
            # Check if values are in decimal format (0-1)
            if solar_curt_vals.max() <= 1.0:
                stats['Solar Curtailment (%)'] = solar_curt_vals.mean() * 100
            else:
                stats['Solar Curtailment (%)'] = solar_curt_vals.mean()
        else:
            stats['Solar Curtailment (%)'] = np.nan
        
        # Wind Curtailment (%) - direct column search for curt_wind
        if 'curt_wind' in df.columns:
            wind_curt_vals = df['curt_wind']
            # Check if values are in decimal format (0-1)
            if wind_curt_vals.max() <= 1.0:
                stats['Wind Curtailment (%)'] = wind_curt_vals.mean() * 100
            else:
                stats['Wind Curtailment (%)'] = wind_curt_vals.mean()
        else:
            stats['Wind Curtailment (%)'] = np.nan
        
        # LOE (Loss of Load Events) - lole_hours
        if 'lole_hours' in df.columns:
            stats['LOE Hours'] = df['lole_hours'].mean()
        else:
            stats['LOE Hours'] = np.nan
        
        # EENS (Energy Not Supplied) - total_ens in MWh, convert to GWh
        if 'total_ens' in df.columns:
            stats['EENS (GWh)'] = (df['total_ens'] / 1000).mean()
        else:
            stats['EENS (GWh)'] = np.nan
        
        # Demand
        demand_col = find_column(df, ['total', 'demand']) or find_column(df, ['demand'])
        if demand_col:
            # Convert from MWh to TWh (divide by 1e6)
            stats['Demand (TWh)'] = (df[demand_col] / 1e6).mean()
        else:
            stats['Demand (TWh)'] = np.nan
        
        # Consumer Surplus - convert from euros to billions (€B)
        consumer_col = find_column(df, ['consumer', 'surplus'])
        if consumer_col:
            stats['Consumer Surplus (€B)'] = (df[consumer_col] / 1e9).mean()
        else:
            stats['Consumer Surplus (€B)'] = np.nan
        
        summary_stats.append(stats)
    
    summary_df = pd.DataFrame(summary_stats)
    
    # Save to CSV
    output_file = OUTPUT_DIR / "01_main_statistics.csv"
    summary_df.to_csv(output_file, index=False)
    print(f"\n[OK] Main statistics saved to {output_file}")
    print(summary_df.to_string())
    
    return summary_df


def generate_main_results_table(all_data):
    """
    Generate Table 3: "Main Results by Scenario" for LaTeX replication.
    
    Creates the table with these metrics (all as percentages of generation):
    - Renewable gen. (%)
    - Low carbon gen. (%)
    - CC gas gen. (%)
    - Battery out (%)
    - Emissions (MtCO2)
    - Price (€/MWh)
    """
    table_data = []
    
    for scenario_name in SCENARIOS:
        data = all_data.get(scenario_name, {})
        
        if not data or 'main_results' not in data:
            continue
        
        df = data['main_results']
        row = {'Scenario': scenario_name.capitalize()}
        
        # Get total generation for percentage calculations
        total_gen_col = find_column(df, ['total', 'generation']) or find_column(df, ['total', 'gen'])
        total_gen = df[total_gen_col].mean() if total_gen_col else 1.0
        
        # Option 1: Use share columns if available (already in decimal format)
        share_ren_col = find_column(df, ['share', 'renewable']) or find_column(df, ['renewable', 'share'])
        if share_ren_col:
            # Column is in decimal (0-1), convert to percentage
            row['Renewable gen. (%)'] = df[share_ren_col].mean() * 100
        else:
            # Calculate from nominal values
            ren_col = find_column(df, ['renewable', 'generation']) or find_column(df, ['renewable', 'gen'])
            if ren_col:
                row['Renewable gen. (%)'] = (df[ren_col].mean() / total_gen) * 100
            else:
                row['Renewable gen. (%)'] = np.nan
        
        # Low carbon generation (%) - renewable + nuclear as percentage
        share_low_carbon_col = find_column(df, ['share', 'low', 'carbon']) or find_column(df, ['low', 'carbon', 'share'])
        if share_low_carbon_col:
            row['Low carbon gen. (%)'] = df[share_low_carbon_col].mean() * 100
        else:
            # Calculate: renewable + nuclear
            ren_col = find_column(df, ['renewable', 'generation']) or find_column(df, ['renewable', 'gen'])
            nuc_col = find_column(df, ['nuclear', 'generation']) or find_column(df, ['nuclear', 'gen'])
            if ren_col and nuc_col:
                low_carbon = df[ren_col].mean() + df[nuc_col].mean()
                row['Low carbon gen. (%)'] = (low_carbon / total_gen) * 100
            else:
                row['Low carbon gen. (%)'] = np.nan
        
        # CC gas generation (%) - Combined Cycle gas as percentage of total generation
        # Combined Cycle (CC) uses combined_cycle_gen, not gas_turbine_gen
        if 'combined_cycle_gen' in df.columns:
            row['CC gas gen. (%)'] = (df['combined_cycle_gen'].mean() / total_gen) * 100
        else:
            row['CC gas gen. (%)'] = np.nan
        
        # Battery output (%) - as percentage of total generation
        batt_col = find_column(df, ['battery', 'output']) or find_column(df, ['battery', 'out'])
        if batt_col:
            row['Battery out (%)'] = (df[batt_col].mean() / total_gen) * 100
        else:
            row['Battery out (%)'] = np.nan
        
        # Emissions (MtCO2) - convert from tonnes to MtCO2
        emis_col = find_column(df, ['direct', 'emissions']) or find_column(df, ['emissions'])
        if emis_col:
            # Assuming the value is in tonnes, convert to MtCO2
            row['Emissions (MtCO2)'] = df[emis_col].mean() / 1e6
        else:
            row['Emissions (MtCO2)'] = np.nan
        
        # Price (€/MWh)
        price_col = find_column(df, ['avg', 'price']) or find_column(df, ['price'])
        if price_col:
            row['Price (€/MWh)'] = df[price_col].mean()
        else:
            row['Price (€/MWh)'] = np.nan
        
        table_data.append(row)
    
    main_results_df = pd.DataFrame(table_data)
    
    # Save as CSV
    csv_output = OUTPUT_DIR / "02_main_results_table.csv"
    main_results_df.to_csv(csv_output, index=False)
    print(f"\n[OK] Main Results Table saved to {csv_output}")
    print("\nMain Results by Scenario:")
    print("="*80)
    print(main_results_df.to_string(index=False))
    
    # Generate LaTeX format
    latex_output = OUTPUT_DIR / "02_main_results_table.tex"
    latex_content = generate_latex_table(main_results_df)
    
    with open(latex_output, 'w', encoding='utf-8') as f:
        f.write(latex_content)
    print(f"\n[OK] LaTeX Table saved to {latex_output}")
    
    return main_results_df


def generate_latex_table(df):
    """
    Generate LaTeX table code from DataFrame.
    Matches the style from the paper.
    """
    scenarios = df['Scenario'].tolist()
    scenario_abbr = {
        'Baseline': 'Base.',
        'Nuclear': 'Nucl.',
        'Optimistic': 'Opt.',
        'Climate change': 'Clim.',
        'No batteries': 'No Batt.'
    }
    
    latex = r"""\begin{center}
    \vspace{-0.25cm}
    \captionsetup{type=table}
    \caption{Main Results by Scenario}
    \label{tab:main_results}
    \small 
    \begin{tabular}{lcccc}
        \toprule
        \textbf{Variable} & """
    
    # Header with scenario abbreviations
    for scenario in scenarios:
        abbr = scenario_abbr.get(scenario, scenario[:6])
        latex += f"\n        \\textbf{{{abbr}}} & " if scenario != scenarios[-1] else f"\n        \\textbf{{{abbr}}} \\\\\n"
    
    latex += "        \\midrule\n"
    
    # Data rows
    metrics = [col for col in df.columns if col != 'Scenario']
    for metric in metrics:
        latex += f"        {metric} & "
        values = []
        for idx, scenario in enumerate(scenarios):
            val = df[df['Scenario'] == scenario][metric].values[0]
            if pd.isna(val):
                values.append("-")
            else:
                # Format based on metric type
                if 'Emissions' in metric:
                    values.append(f"{val:.1f}")
                elif 'Price' in metric:
                    values.append(f"{val:.1f}")
                else:
                    values.append(f"{val:.1f}")
            
            if idx < len(scenarios) - 1:
                latex += values[-1] + " & "
            else:
                latex += values[-1] + " \\\\\n"
    
    latex += r"""        \bottomrule
    \end{tabular}
    \vspace{-0.25cm}
    \caption*{\footnotesize \textit{Note:} Figures represent averages across 10,000 Monte Carlo simulations per scenario. Low carbon includes renewable sources plus nuclear generation.}
\end{center}"""
    
    return latex


def print_scenario_details(all_data):
    """Print detailed statistics for each scenario."""
    print("\n" + "="*80)
    print("DETAILED SCENARIO STATISTICS")
    print("="*80)
    
    for scenario_name in SCENARIOS:
        data = all_data.get(scenario_name, {})
        if not data or 'main_results' not in data:
            continue
        
        df = data['main_results']
        print(f"\n{scenario_name.upper()}")
        print("-" * 40)
        print(df.describe())


# ============================================================================
# DISTRIBUTION ANALYSIS
# ============================================================================

def analyze_renewable_share_distributions(all_data):
    """
    Analyze and plot the distribution of renewable share across scenarios.
    Replicates Figure 1 from the paper.
    """
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    axes = axes.flatten()
    
    for idx, scenario_name in enumerate(SCENARIOS):
        data = all_data.get(scenario_name, {})
        if not data or 'main_results' not in data:
            continue
        
        df = data['main_results']
        
        # Try to find renewable share column (should be in decimal format 0-1)
        share_col = find_column(df, ['share', 'renewable']) or find_column(df, ['renewable', 'share'])
        
        if share_col:
            # Column is already in decimal (0-1), convert to percentage
            ren_share = df[share_col] * 100
        else:
            # Try calculating from nominal values
            ren_col = find_column(df, ['renewable', 'generation']) or find_column(df, ['renewable', 'gen'])
            total_col = find_column(df, ['total', 'generation']) or find_column(df, ['total', 'gen'])
            
            if ren_col and total_col:
                ren_share = (df[ren_col] / df[total_col]) * 100
            else:
                print(f"Warning: No renewable share column found in {scenario_name}")
                continue
        
        ax = axes[idx]
        ax.hist(ren_share, bins=50, color=COLORS.get(scenario_name, '#1f77b4'), 
                alpha=0.7, edgecolor='black')
        ax.axvline(ren_share.mean(), color='red', linestyle='--', linewidth=2, 
                   label=f'Mean: {ren_share.mean():.1f}%')
        ax.axvline(81, color='green', linestyle='--', linewidth=2, 
                   label='Target: 81%')
        ax.set_xlabel('Renewable Share (%)')
        ax.set_ylabel('Frequency')
        ax.set_title(f'{scenario_name.capitalize()}')
        ax.legend()
        ax.grid(alpha=0.3)
    
    # Remove extra subplot
    fig.delaxes(axes[-1])
    
    plt.suptitle('Distribution of Renewable Share Across Scenarios', 
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    output_file = OUTPUT_DIR / "03_renewable_share_distributions.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"[OK] Renewable share distributions saved to {output_file}")
    plt.close()

    # Individual plots
    for scenario_name in SCENARIOS:
        data = all_data.get(scenario_name, {})
        if not data or 'main_results' not in data:
            continue
        df = data['main_results']
        share_col = find_column(df, ['share', 'renewable']) or find_column(df, ['renewable', 'share'])
        if share_col:
            ren_share = df[share_col] * 100
        else:
            ren_col = find_column(df, ['renewable', 'generation']) or find_column(df, ['renewable', 'gen'])
            total_col = find_column(df, ['total', 'generation']) or find_column(df, ['total', 'gen'])
            if ren_col and total_col:
                ren_share = (df[ren_col] / df[total_col]) * 100
            else:
                continue
        
        plt.figure(figsize=(5.5, 4.5))
        plt.hist(ren_share, bins=50, color=COLORS.get(scenario_name, '#1f77b4'), alpha=0.7, edgecolor='black')
        plt.axvline(ren_share.mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {ren_share.mean():.1f}%')
        plt.axvline(81, color='green', linestyle='--', linewidth=2, label='Target: 81%')
        plt.xlabel('Renewable Share (%)')
        plt.ylabel('Frequency')
        plt.title(f'{scenario_name.capitalize()}')
        plt.legend()
        plt.grid(alpha=0.3)
        plt.tight_layout()
        ind_output = OUTPUT_DIR / f"03_renewable_share_{scenario_name.replace(' ', '_')}.png"
        plt.savefig(ind_output, dpi=300, bbox_inches='tight')
        plt.close()


def analyze_price_distributions(all_data):
    """
    Analyze and plot the distribution of average prices across scenarios.
    Replicates Figure 3 from the paper.
    """
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    axes = axes.flatten()
    
    for idx, scenario_name in enumerate(SCENARIOS):
        data = all_data.get(scenario_name, {})
        if not data or 'main_results' not in data:
            continue
        
        df = data['main_results']
        price_col = find_column(df, ['avg', 'price']) or find_column(df, ['price'])
        
        if not price_col:
            print(f"Warning: No price column found in {scenario_name}")
            continue
        
        prices = df[price_col]
        
        ax = axes[idx]
        ax.hist(prices, bins=50, color=COLORS.get(scenario_name, '#1f77b4'), 
                alpha=0.7, edgecolor='black')
        ax.axvline(prices.mean(), color='red', linestyle='--', linewidth=2, 
                   label=f'Mean: €{prices.mean():.1f}/MWh')
        ax.set_xlabel('Average Price (€/MWh)')
        ax.set_ylabel('Frequency')
        ax.set_title(f'{scenario_name.capitalize()}')
        ax.legend()
        ax.grid(alpha=0.3)
    
    # Remove extra subplot
    fig.delaxes(axes[-1])
    
    plt.suptitle('Distribution of Average Prices Across Scenarios', 
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    output_file = OUTPUT_DIR / "04_price_distributions.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"[OK] Price distributions saved to {output_file}")
    plt.close()

    # Individual plots
    for scenario_name in SCENARIOS:
        data = all_data.get(scenario_name, {})
        if not data or 'main_results' not in data:
            continue
        df = data['main_results']
        price_col = find_column(df, ['avg', 'price']) or find_column(df, ['price'])
        if not price_col:
            continue
        prices = df[price_col]
        
        plt.figure(figsize=(5.5, 4.5))
        plt.hist(prices, bins=50, color=COLORS.get(scenario_name, '#1f77b4'), alpha=0.7, edgecolor='black')
        plt.axvline(prices.mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: €{prices.mean():.1f}/MWh')
        plt.xlabel('Average Price (€/MWh)')
        plt.ylabel('Frequency')
        plt.title(f'{scenario_name.capitalize()}')
        plt.legend()
        plt.grid(alpha=0.3)
        plt.tight_layout()
        ind_output = OUTPUT_DIR / f"04_price_distributions_{scenario_name.replace(' ', '_')}.png"
        plt.savefig(ind_output, dpi=300, bbox_inches='tight')
        plt.close()


# ============================================================================
# HOURLY PROFILE ANALYSIS
# ============================================================================

def analyze_hourly_profiles(all_data):
    """
    Analyze hourly emissions and prices by hour of day.
    Replicates Figure from paper showing hourly patterns.
    """
    fig1, ax_price = plt.subplots(figsize=(5.5, 4.5))
    fig2, ax_emissions = plt.subplots(figsize=(5.5, 4.5))
    
    # Prepare data for hourly analysis
    for scenario_name in SCENARIOS:
        data = all_data.get(scenario_name, {})
        if not data or 'hourly_profiles' not in data:
            continue
        
        df = data['hourly_profiles']
        
        # Group by hour and calculate statistics
        if 'hour' in df.columns:
            hourly_stats = df.groupby('hour').agg({
                'price': ['mean', 'std'],
                'emissions': ['mean', 'std']
            })
        else:
            # If no hour column, assume data is ordered hourly for a year
            # Create hour column (0-23 repeating)
            df['hour'] = (df.index % 8760) % 24
            hourly_stats = df.groupby('hour').agg({
                'price': ['mean', 'std'] if 'price' in df.columns else [],
                'emissions': ['mean', 'std'] if 'emissions' in df.columns else []
            })
        
        hours = hourly_stats.index
        
        # Plot prices
        if 'price' in hourly_stats.columns:
            prices = hourly_stats['price']['mean']
            ax_price.plot(hours, prices, label=scenario_name.capitalize(), 
                   color=COLORS.get(scenario_name, '#1f77b4'), linewidth=2)
        
        # Plot emissions
        if 'emissions' in hourly_stats.columns:
            emissions = hourly_stats['emissions']['mean']
            ax_emissions.plot(hours, emissions, label=scenario_name.capitalize(), 
                   color=COLORS.get(scenario_name, '#1f77b4'), linewidth=2)
    
    ax_price.set_xlabel('Hour of Day')
    ax_price.set_ylabel('Average Price (€/MWh)')
    ax_price.set_title('Hourly Price Profile')
    ax_price.legend()
    ax_price.grid(alpha=0.3)
    ax_price.set_xticks(range(0, 24, 2))
    fig1.tight_layout()
    output_file1 = OUTPUT_DIR / "05_hourly_profiles_price.png"
    fig1.savefig(output_file1, dpi=300, bbox_inches='tight')
    plt.close(fig1)
    
    ax_emissions.set_xlabel('Hour of Day')
    ax_emissions.set_ylabel('Average Emissions (tCO2/MWh)')
    ax_emissions.set_title('Hourly Emissions Profile')
    ax_emissions.legend()
    ax_emissions.grid(alpha=0.3)
    ax_emissions.set_xticks(range(0, 24, 2))
    fig2.tight_layout()
    output_file2 = OUTPUT_DIR / "05_hourly_profiles_emissions.png"
    fig2.savefig(output_file2, dpi=300, bbox_inches='tight')
    plt.close(fig2)
    print(f"[OK] Hourly profiles saved to {OUTPUT_DIR}")

# ============================================================================
# MONTHLY PROFILE ANALYSIS
# ============================================================================

def analyze_monthly_profiles(all_data):
    """
    Analyze monthly emissions and prices by month.
    Replicates monthly emissions figure from paper.
    """
    fig1, ax_price = plt.subplots(figsize=(5.5, 4.5))
    fig2, ax_emissions = plt.subplots(figsize=(5.5, 4.5))
    
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    # Prepare data for monthly analysis
    for scenario_name in SCENARIOS:
        data = all_data.get(scenario_name, {})
        if not data or 'monthly_profiles' not in data:
            continue
        
        df = data['monthly_profiles']
        
        # Group by month and calculate mean
        if 'month' in df.columns:
            monthly_stats = df.groupby('month').mean()
        else:
            # If no month column, assume first 12 rows are months
            if len(df) >= 12:
                monthly_stats = df.iloc[:12].reset_index(drop=True)
                monthly_stats.index = range(1, 13)
            else:
                continue
        
        months_idx = monthly_stats.index if 'month' in df.columns else range(1, len(monthly_stats) + 1)
        
        # Plot prices
        if 'price' in monthly_stats.columns or 'avg_price' in monthly_stats.columns:
            price_col = 'price' if 'price' in monthly_stats.columns else 'avg_price'
            prices = monthly_stats[price_col]
            ax_price.plot(months_idx, prices, label=scenario_name.capitalize(), 
                   color=COLORS.get(scenario_name, '#1f77b4'), linewidth=2, marker='o')
        
        # Plot emissions
        if 'emissions' in monthly_stats.columns or 'avg_emissions' in monthly_stats.columns:
            emissions_col = 'emissions' if 'emissions' in monthly_stats.columns else 'avg_emissions'
            emissions = monthly_stats[emissions_col]
            ax_emissions.plot(months_idx, emissions, label=scenario_name.capitalize(), 
                   color=COLORS.get(scenario_name, '#1f77b4'), linewidth=2, marker='o')
    
    ax_price.set_xlabel('Month')
    ax_price.set_ylabel('Average Price (€/MWh)')
    ax_price.set_title('Monthly Price Profile')
    ax_price.set_xticks(range(1, 13))
    ax_price.set_xticklabels(months, rotation=45)
    ax_price.legend()
    ax_price.grid(alpha=0.3)
    fig1.tight_layout()
    output_file1 = OUTPUT_DIR / "06_monthly_profiles_price.png"
    fig1.savefig(output_file1, dpi=300, bbox_inches='tight')
    plt.close(fig1)
    
    ax_emissions.set_xlabel('Month')
    ax_emissions.set_ylabel('Average Emissions (tCO2/MWh)')
    ax_emissions.set_title('Monthly Emissions Profile')
    ax_emissions.set_xticks(range(1, 13))
    ax_emissions.set_xticklabels(months, rotation=45)
    ax_emissions.legend()
    ax_emissions.grid(alpha=0.3)
    fig2.tight_layout()
    output_file2 = OUTPUT_DIR / "06_monthly_profiles_emissions.png"
    fig2.savefig(output_file2, dpi=300, bbox_inches='tight')
    plt.close(fig2)
    print(f"[OK] Monthly profiles saved to {OUTPUT_DIR}")

# ============================================================================
# INPUTS AND CAPACITY ANALYSIS
# ============================================================================

def analyze_inputs_and_capacity(all_data):
    """
    Analyze realized inputs (capacities and other parameters) by scenario.
    """
    summary_inputs = []
    
    for scenario_name in SCENARIOS:
        data = all_data.get(scenario_name, {})
        if not data or 'inputs_realized' not in data:
            continue
        
        df = data['inputs_realized']
        
        # Get mean values for key inputs
        input_summary = {'Scenario': scenario_name}
        
        # Try to capture common column names for capacities
        capacity_cols = [col for col in df.columns if 'capacity' in col.lower() 
                        or 'cap_' in col.lower()]
        
        for col in capacity_cols:
            if col in df.columns:
                input_summary[col] = df[col].mean()
        
        summary_inputs.append(input_summary)
    
    if summary_inputs:
        inputs_df = pd.DataFrame(summary_inputs)
        output_file = OUTPUT_DIR / "07_capacity_inputs.csv"
        inputs_df.to_csv(output_file, index=False)
        print(f"\n[OK] Capacity inputs saved to {output_file}")
        print(inputs_df.to_string())
    
    return summary_inputs if summary_inputs else None


def analyze_generation_vs_capacity_mix(all_data):
    """
    Analyze and plot generation mix and capacity mix by scenario.
    Creates two stacked bar charts: one for generation (GWh) and one for capacity (GW).
    Includes percentage labels for technologies >= 3% of total.
    """
    tech_colors = {
        # Renewables (bottom)
        'Wind': '#5F9EA0',
        'Solar PV': '#FFA500',
        'Solar Thermal': '#FFD700',
        'Conventional Hydro': '#4169E1',
        'Run-of-River Hydro': '#87CEEB',
        'Other Renewable': '#32CD32',
        'Renewable Waste': '#90EE90',
        # Non-Renewables (top)
        'Coal': '#8B4513',
        'Combined Cycle': '#E74C3C',
        'Gas Turbine': '#FF6B6B',
        'Vapor Turbine': '#CD5C5C',
        'Diesel': '#A0522D',
        'Cogeneration': '#DC143C',
        'Non-Renewable Waste': '#FF8C00',
        'Nuclear': '#FFD700',
        # Storage
        'Battery': '#9370DB',
        'Pumped Hydro': '#4682B4',
    }
    
    fig1, ax1 = plt.subplots(figsize=(6, 5))
    fig2, ax2 = plt.subplots(figsize=(6, 5))
    
    # Mapping of display names to column names
    generation_mappings = {
        # Renewables (bottom)
        'Wind': 'wind_gen',
        'Solar PV': 'solar_pv_gen',
        'Solar Thermal': 'solar_thermal_gen',
        'Conventional Hydro': 'conventional_hydro_gen',
        'Run-of-River Hydro': 'run_of_river_hydro_gen',
        'Other Renewable': 'other_renewable_gen',
        'Renewable Waste': 'renewable_waste_gen',
        # Non-Renewables (top)
        'Coal': 'coal_gen',
        'Combined Cycle': 'combined_cycle_gen',
        'Gas Turbine': 'gas_turbine_gen',
        'Vapor Turbine': 'vapor_turbine_gen',
        'Diesel': 'diesel_gen',
        'Cogeneration': 'cogeneration_gen',
        'Non-Renewable Waste': 'non_renewable_waste_gen',
        'Nuclear': 'nuclear_gen',
    }
    
    capacity_mappings = {
        # Renewables (bottom)
        'Wind': 'wind_cap_gw',
        'Solar PV': 'solar_pv_cap_gw',
        'Solar Thermal': 'solar_thermal_cap_gw',
        'Conventional Hydro': 'conventional_hydro_cap_gw',
        'Run-of-River Hydro': 'run_of_river_hydro_cap_gw',
        'Other Renewable': 'other_renewable_cap_gw',
        'Renewable Waste': 'renewable_waste_cap_gw',
        # Non-Renewables (top)
        'Coal': 'coal_cap_gw',
        'Combined Cycle': 'combined_cycle_cap_gw',
        'Gas Turbine': 'gas_turbine_cap_gw',
        'Vapor Turbine': 'vapor_turbine_cap_gw',
        'Diesel': 'diesel_cap_gw',
        'Cogeneration': 'cogeneration_cap_gw',
        'Non-Renewable Waste': 'nonrenewable_waste_cap_gw',
        'Nuclear': 'nuclear_cap_gw',
    }
    
    # Collect generation and capacity data
    generation_by_tech = {scenario: {} for scenario in SCENARIOS}
    capacity_by_tech = {scenario: {} for scenario in SCENARIOS}
    total_generation = {scenario: 0 for scenario in SCENARIOS}
    total_capacity = {scenario: 0 for scenario in SCENARIOS}
    
    for scenario_name in SCENARIOS:
        data = all_data.get(scenario_name, {})
        
        # Get generation data
        if data and 'main_results' in data:
            main_df = data['main_results']
            
            for tech, col in generation_mappings.items():
                if col in main_df.columns:
                    value = main_df[col].mean() / 1000  # Convert MWh to GWh
                    generation_by_tech[scenario_name][tech] = value
                    total_generation[scenario_name] += value
                else:
                    generation_by_tech[scenario_name][tech] = 0
        
        # Get capacity data
        if data and 'inputs_realized' in data:
            inputs_df = data['inputs_realized']
            
            for tech, col in capacity_mappings.items():
                if col in inputs_df.columns:
                    value = inputs_df[col].mean()  # Already in GW
                    capacity_by_tech[scenario_name][tech] = value
                    total_capacity[scenario_name] += value
                else:
                    capacity_by_tech[scenario_name][tech] = 0
    
    # Prepare technology order
    renewable_order = ['Wind', 'Solar PV', 'Solar Thermal', 'Conventional Hydro', 'Run-of-River Hydro', 'Other Renewable', 'Renewable Waste']
    non_renewable_order = ['Coal', 'Combined Cycle', 'Gas Turbine', 'Vapor Turbine', 'Diesel', 'Cogeneration', 'Non-Renewable Waste', 'Nuclear']
    all_techs = renewable_order + non_renewable_order
    
    x_pos = np.arange(len(SCENARIOS))
    width = 0.5
    
    # ===== PLOT 1: GENERATION MIX WITH PERCENTAGES =====
    bottom = np.zeros(len(SCENARIOS))
    
    for tech in all_techs:
        values = [generation_by_tech[s].get(tech, 0) for s in SCENARIOS]
        
        # Skip if all values are 0
        if sum(values) == 0:
            continue
        
        bars = ax1.bar(x_pos, values, width, label=tech, bottom=bottom, 
                       color=tech_colors.get(tech, '#CCCCCC'), alpha=0.85, 
                       edgecolor='white', linewidth=0.5)
        
        # Add percentage labels on bars (only if >= 3%)
        for i, (bar, val) in enumerate(zip(bars, values)):
            if total_generation[SCENARIOS[i]] > 0:
                pct = (val / total_generation[SCENARIOS[i]]) * 100
                if pct >= 3:  # Only show if >= 3%
                    height = bar.get_height()
                    ax1.text(bar.get_x() + bar.get_width()/2., bottom[i] + height/2.,
                            f'{pct:.1f}%', ha='center', va='center', fontsize=7, 
                            fontweight='bold', color='white')
        
        bottom += values
    
    ax1.set_ylabel('Total Generation (GWh)', fontsize=11, fontweight='bold')
    ax1.set_xlabel('Scenario', fontsize=11, fontweight='bold')
    ax1.set_title('Electricity Generation Mix', fontsize=12, fontweight='bold', pad=10)
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels([s.capitalize() for s in SCENARIOS], fontsize=10)
    ax1.grid(axis='y', alpha=0.3)
    
    # ===== PLOT 2: CAPACITY MIX =====
    bottom = np.zeros(len(SCENARIOS))
    
    for tech in all_techs:
        values = [capacity_by_tech[s].get(tech, 0) for s in SCENARIOS]
        
        # Skip if all values are 0
        if sum(values) == 0:
            continue
        
        bars = ax2.bar(x_pos, values, width, label=tech, bottom=bottom, 
                       color=tech_colors.get(tech, '#CCCCCC'), alpha=0.85, 
                       edgecolor='white', linewidth=0.5)
        
        # Add percentage labels on bars (only if >= 3%)
        for i, (bar, val) in enumerate(zip(bars, values)):
            if total_capacity[SCENARIOS[i]] > 0:
                pct = (val / total_capacity[SCENARIOS[i]]) * 100
                if pct >= 3:  # Only show if >= 3%
                    height = bar.get_height()
                    ax2.text(bar.get_x() + bar.get_width()/2., bottom[i] + height/2.,
                            f'{pct:.1f}%', ha='center', va='center', fontsize=7, 
                            fontweight='bold', color='white')
        
        bottom += values
    
    ax2.set_ylabel('Total Installed Capacity (GW)', fontsize=11, fontweight='bold')
    ax2.set_xlabel('Scenario', fontsize=11, fontweight='bold')
    ax2.set_title('Installed Capacity Mix', fontsize=12, fontweight='bold', pad=10)
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels([s.capitalize() for s in SCENARIOS], fontsize=10)
    ax2.grid(axis='y', alpha=0.3)
    
    # Create legend outside plot 1
    handles1, labels1 = ax1.get_legend_handles_labels()
    fig1.legend(handles1, labels1, loc='center', bbox_to_anchor=(0.5, -0.05), 
               ncol=4, fontsize=8, framealpha=0.95, title='Technology', 
               title_fontsize=9)
    fig1.subplots_adjust(bottom=0.25)
    output_file1 = OUTPUT_DIR / "08_generation_mix.png"
    fig1.savefig(output_file1, dpi=300, bbox_inches='tight')
    plt.close(fig1)
    
    # Create legend outside plot 2
    handles2, labels2 = ax2.get_legend_handles_labels()
    fig2.legend(handles2, labels2, loc='center', bbox_to_anchor=(0.5, -0.05), 
               ncol=4, fontsize=8, framealpha=0.95, title='Technology', 
               title_fontsize=9)
    fig2.subplots_adjust(bottom=0.25)
    output_file2 = OUTPUT_DIR / "08_capacity_mix.png"
    fig2.savefig(output_file2, dpi=300, bbox_inches='tight')
    plt.close(fig2)
    print(f"[OK] Generation and capacity mix saved to {OUTPUT_DIR}")


# ============================================================================
# CORRELATION AND REGRESSION ANALYSIS
# ============================================================================

def analyze_capacity_correlations(all_data):
    """
    Analyze correlations between capacity variables and renewable share.
    Useful for understanding what drives renewable penetration.
    """
    for scenario_name in SCENARIOS:
        data = all_data.get(scenario_name, {})
        if not data:
            continue
        
        # Merge main results with inputs if both exist
        if 'main_results' in data and 'inputs_realized' in data:
            main_df = data['main_results']
            inputs_df = data['inputs_realized']
            
            # Ensure same number of rows
            if len(main_df) == len(inputs_df):
                merged_df = pd.concat([main_df, inputs_df], axis=1)
                
                # Find renewable share and capacity columns
                ren_cols = [col for col in merged_df.columns if 'renewable' in col.lower() or 'ren_share' in col.lower()]
                cap_cols = [col for col in merged_df.columns if 'capacity' in col.lower() or 'cap_' in col.lower()]
                
                if ren_cols and cap_cols:
                    ren_col = ren_cols[0]
                    
                    # Calculate correlations
                    correlations = {}
                    for cap_col in cap_cols:
                        if merged_df[cap_col].dtype in [np.float64, np.int64]:
                            corr = merged_df[ren_col].corr(merged_df[cap_col])
                            correlations[cap_col] = corr
                    
                    if correlations:
                        print(f"\n{scenario_name.upper()} - Capacity Correlations with Renewable Share:")
                        print("-" * 60)
                        sorted_corr = sorted(correlations.items(), key=lambda x: abs(x[1]), reverse=True)
                        for cap, corr in sorted_corr[:10]:
                            print(f"  {cap}: {corr:+.3f}")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main execution function."""
    print("\n" + "="*80)
    print("SPAIN 2030 RENEWABLE GENERATION - RESULTS ANALYSIS")
    print("="*80)
    
    # Check if data directory exists
    if not DATA_DIR.exists():
        print(f"\n[ERROR] Data directory not found: {DATA_DIR}")
        print("Please ensure the detailed_results folder exists in output/")
        return
    
    print(f"\nData directory: {DATA_DIR}")
    print(f"Output directory: {OUTPUT_DIR}")
    
    # Load all scenario data
    print("\n" + "-"*80)
    print("LOADING DATA")
    print("-"*80)
    all_data = load_all_scenarios()
    
    # Check if any data was loaded
    loaded_scenarios = [s for s in SCENARIOS if s in all_data and all_data[s]]
    if not loaded_scenarios:
        print("\n[ERROR] No data loaded. Please check the data directory structure.")
        return
    
    print(f"\n[OK] Successfully loaded data for: {', '.join(loaded_scenarios)}")
    
    # Generate analyses
    print("\n" + "-"*80)
    print("GENERATING ANALYSES")
    print("-"*80)
    
    # 1. Summary statistics
    print("\n1. Calculating main statistics...")
    calculate_main_statistics(all_data)
    
    # 1b. Main Results Table (Paper Table 3)
    print("\n1b. Generating Main Results Table...")
    generate_main_results_table(all_data)
    
    # 2. Print detailed statistics
    print("\n2. Printing detailed scenario statistics...")
    print_scenario_details(all_data)
    
    # 3. Distribution analysis
    print("\n3. Analyzing renewable share distributions...")
    analyze_renewable_share_distributions(all_data)
    
    print("\n4. Analyzing price distributions...")
    analyze_price_distributions(all_data)
    
    # 4. Hourly analysis
    print("\n5. Analyzing hourly profiles...")
    analyze_hourly_profiles(all_data)
    
    # 5. Monthly analysis
    print("\n6. Analyzing monthly profiles...")
    analyze_monthly_profiles(all_data)
    
    # 6. Capacity analysis
    print("\n7. Analyzing capacity inputs...")
    analyze_inputs_and_capacity(all_data)
    
    # 6b. Generation vs Capacity mix
    print("\n7b. Analyzing generation and capacity mix...")
    analyze_generation_vs_capacity_mix(all_data)
    
    # 7. Correlation analysis
    print("\n8. Analyzing capacity correlations...")
    analyze_capacity_correlations(all_data)
    
    print("\n" + "="*80)
    print("[OK] ANALYSIS COMPLETE")
    print("="*80)
    print(f"\nResults saved to: {OUTPUT_DIR}")
    print("\nGenerated files:")
    print("  - 01_main_statistics.csv")
    print("  - 02_main_results_table.csv (Main Results by Scenario)")
    print("  - 02_main_results_table.tex (LaTeX format)")
    print("  - 03_renewable_share_distributions.png")
    print("  - 04_price_distributions.png")
    print("  - 05_hourly_profiles.png")
    print("  - 06_monthly_profiles.png")
    print("  - 07_capacity_inputs.csv")
    print("  - 08_generation_mix.png (Generation & Capacity mix)")


if __name__ == "__main__":
    main()
