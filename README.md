# Spain_ren_gen_2030

This is the repository for the working paper: "A stochastic policy assessment of Spain’s 81% renewable electricity target for 2030", by Cristobal Blanco and Pau Orive. 

## Abstract 

This study provides a probabilistic assessment of Spain’s 2030 renewable electricity target, as outlined in the 2024 update of the National Integrated Energy and Climate Plan (PNIEC). Using a partial-equilibrium social planner model and 10,000 Monte Carlo simulations per scenario, we evaluate system performance under five strategic configurations: Baseline, Nuclear, Optimistic, Climate Change, and No Batteries.

Our results reveal a significant implementation gap: the Baseline scenario yields an expected renewable share of 73.75%, meeting the official 81% target in only 9.06% of iterations. Even under the most favorable configuration — the Optimistic scenario, combining accelerated renewable and battery deployment with enhanced demand flexibility — the compliance probability reaches only 14.51%. We further identify a Nuclear Paradox: retaining the 7.1 GW nuclear fleet yields the lowest wholesale price (61.51 €/MWh) and minimum emissions (3.81 MtCO22), yet makes the 81% target structurally unachievable, reducing the expected renewable share to 70.07% and the compliance probability to exactly zero. Climate change compounds these risks, reducing compliance probability to 3.80% through coincident reductions in hydropower availability and cooling-driven demand growth.

Across all five scenarios, Loss of Load Expectation and Expected Energy Not Served remain at zero, driven by extensive combined cycle gas retention. Spain’s transition risk has therefore shifted from physical grid security to policy and investment coordination: whether the capacity deployment trajectory required to meet the 81% target will materialize within the available timeframe.

## Highlights

-   Spain’s 81% renewable electricity target for 2030 is unlikely under current policy.
-   Compliance depends almost exclusively on capacity deployment, not market conditions.
-   Nuclear retention minimises prices and emissions but makes the renewable target unachievable.
-   Climate change significantly reduces the probability of meeting the 2030 target

## Methdology summary

We build a partial-equilibrium power system simulation model in which a social planner maximises social welfare by choosing the optimal hourly electricity dispatch subject to market clearing, capacity, and ramping constraints, inspired in Reguant "The Efficiency and Sectoral Distributional Implications of Large-Scale Renewable Policies", *Journal of the Association of Environmental and Resource Economics*, 2019, 6:S1, S129-S168. Under perfect competition, this formulation replicates the economic merit order. Demand is disaggregated into residential, commercial, and industrial sectors, each modelled via a linear demand curve calibrated using baseline demand, observed reference prices, and sector-specific short-run price elasticities.

The model covers up to 15 generation technologies following the PNIEC taxonomy, including coal, combined cycle gas (CCGT), nuclear, solar PV, wind, conventional and run-of-river hydro, and utility-scale batteries and pumped hydro storage. VRE generation is capped by hourly meteorological availability profiles derived from historical climate data. Hydropower is subject to dynamic hourly bounds and weekly volume constraints. Storage technologies are modelled with explicit charging and discharging decisions, round-trip efficiency, and state-of-charge constraints. Interconnections with France, Portugal, and Morocco are fixed exogenously.

### Data Projections and Delta Calibration

Rather than constructing synthetic 2030 profiles, the model scales historical hourly data (2020–2024) using variable-specific adjustment factors (deltas) derived from independent 2030 projections sourced from the PNIEC, Aurora Energy Research, the IEA World Energy Outlook, and BloombergNEF, among others. Each delta is computed relative to a historical baseline year and applied multiplicatively to the corresponding variable.

Since the purpose of the paper is to analyze the electricity system in 2030, we have gathered data on projections of installed capacity, electricity demand and commodity prices to that target year. To handle the uncertainty on what will be the specific realization, we run 10,000 Monte Carlo simulations on 4 different scenarios, keeping track of the average renewable share in each iteration as well as other outcomes such as the total emissions, battery inflos and outflows, etcetera.

### Monte Carlo Procedure

The model is solved 10,000 times per scenario. In each iteration, a baseline year is drawn at random from 2020–2024, and a single 7-day window is extracted from each month of that year, yielding a 2,016-hour dataset. This design balances computational cost with meteorological robustness, ensuring adequate coverage of tail events including prolonged low-renewable periods.

For each volatile variable — electricity demand, installed capacity by technology, fuel costs, and EU ETS prices — a delta is sampled at runtime from a distribution fitted to the available point estimates. Policy-driven phase-outs receive a deterministic delta. Variables with few or tightly concentrated projections are sampled from a normal distribution; variables with more dispersed estimates use Kernel Density Estimation with inverse transform sampling. Draws are clamped to prevent extreme outliers, with an additional non-negativity constraint on capacity parameters.

### Scenarios

Five scenarios are evaluated:

-   Baseline: planned coal and nuclear phase-outs proceed; standard capacity growth and demand elasticity.
-   Nuclear: nuclear fleet retained at full capacity; renewable deployment reduced by 25% and battery deployment by 50% to capture the crowding-out effect on private investment.
-   Optimistic: renewable deployment upsized by 25%, battery deployment by 50%, and demand price elasticity doubled to reflect enhanced demand response.
-   Climate Change: hydro generation reduced by 20%; sectoral demand adjusted via a monthly scaling vector to reflect higher summer cooling loads and lower winter heating demand.
-   No Batteries_ battery deployment halted entirely, to isolate and quantify the systemic value of utility-scale storage.

## How to navigate the repository

The repository follows standard practices: it contains three folders (data, scrpits and outputs) containing all the ingredients needed to replicate the paper.
Each folder contains its own README.md file with specific guidelines to navigate each folder. 

### Instructions to replicate the paper

In order to replicate our work you just have to:

1. Clone or download this repository
2. Install julia and the required dependencies (also R and python if you also want to run other scripts)
3. Get a Gurobi optimization license (note that the one available in the free trial version is not powerful enough)
4. From the project root directory, run the script `04_monte_carlo_simulations.jl` 
5. Once run, get the results with `05_results_analysis.py` 

We encourage researchers to play with the numbers defining the scenarios or even include new scenarios. Scenarios are defined in the same `04_monte_carlo_simulations.jl` script, though for advanced manipulation you might need to dive into `02_auxiliary_functions.jl` and `03_model_electricity_market.jl`.

Also, we think the project could benefit from economies of scale as the same methodology can be used for other case studies tailoring the model to the country or region of interest (in fact, Reguant's paper from which the model is inspired was tailored to California). 

## Limitations of the study

Our methodology does not incorporate competition among producers and the transmission grid is not modeled. In addition, there were not so many projections available for some variables for 2030. Last but not least, the model is relatively rigid to how the market conditions were in the last years, so dramatic changes such as massive deployment of rooftop solar, virtual power plants, demand response mechanisms and other features are not incorporated. 

Any other constructive criticism would be very appreciated by the authors. 



## Versions

The first version of the project was the Master Thesis I conducted at Barcelona School of Economics alongside Cristobal Blanco and Tomás Butelman. 
Cristobal and Pau continued working in the second version, polishing scripts, validating data collection, updating parts of the analysis, diving deeper into the policy implications and ultimately adapting all the content to journal format, which in practice implied rewriting the whole paper. 