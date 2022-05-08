# Wind Power in the US: Generation vs. Capacity
Data and accompanying analysis on trends effecting power generation performance at the plant level

![alt text](https://media.giphy.com/media/rQdPpBsXTy7GU/giphy.gif)

The intention behind this repository is two-fold:
1. Provide scripts that do the gruntwork of accessing and tidying the plant-level data for wind farms in the US for those interested in exploring the relationships between a plant's characteristics & location with it's power generation performance, as measured by capacity factor* 

3. Generate visualizations and regressions results that attempt to identify significant relationships in the data in the form of a publicly-accessible, browser-based, interactive sets of charts, hosted by Datapane, as well as a simple table image of the regression results (see TL;DR below)



## TL;DR

*Datapane report with visualizations:* https://datapane.com/reports/aAMn0o3/wind-power-generation-report/

*Regression results (variables with significant relationships with capacity factor):*

![Regression Results](/regression_results.png)

Note: this is not a causal analysis, but lays the groundwork to pursue one



## Repository Contents and Instructions

This repository contains 3 externally-sourced input data files and 5 python scripts that produce 4 more intermediary datasets, as well as the analysis outlined above.

*Data*
1. '2___Plant_Y2020.xlsx'
 - This is the first of two files that come from the Energy Information Administration's Form 860, which is an annual survey completed by operators of power plants larger than 1 MW
 - It contains general plant-specific information, like location, NERC region, and voltage of the plant's interconnection to the grid
 - Form 860 can be accessed from the EIA's website: https://www.eia.gov/electricity/data/eia860/
2. '3_2_Wind_Y2020.xlsx'
- This the the second of two files from the Form 860
- This file contains information relevant to wind farms, like number of turbines, wind quality class, turbine height, as well as capacity information
3. 'wtk_site_metadata.csv'
- This file comes from the National Renewable Energy Laboratory's WIND Toolkit, which is provides a set of tools for wind developers to aid plant siting based on weather model data (among other purposes)
- The file used here provides summary statistics of the 120k simulation sites on which the larger toolkit is based, including average wind speed
- The file can be downloaded here: https://data.nrel.gov/submissions/54

*Scripts (to be run in the following order)*
1. 'plants.py'
- This script reads in the EIA Form 860 datasets listed above, trims them down to what we need, and merges them on their unique plant code, and outputs the plant characterisitcs to an intermediary csv file called 'plant_full_info.csv'
2. 'api_eia923.py'
- This script reads in the output file from the 'plants' script, and executes an API call to the EIA server to access the generation data from Form 923, which is another survey completed by plant operators and can be explored here: https://www.eia.gov/electricity/data/eia923/
- Iterating through each plant ID, the script compiles a pandas DataFrame with the monthly generation data from the 1215 wind plants (130k+ rows), and writes out the data to an intermediary output file called 'gen_history.csv')
3. 'generation.py'
- This script reads in the generation output file from the 'api_eia923' script, aggregates it to create a DataFrame with the annual generation for each plant in 2020, merges with the 'plant_full_info.csv' file from the first script, and writes out the the aggregated 2020 file ('plant_gen_2020.csv') as well as a monthly historical generation file ('plant_gen_history.csv')
4. 'geo_merge.py'
- This script merges the NREL wind site model data onto the plant information intermediary output file 'plant_full_info' from the 'plants' script. Using the geopandas sjoin_nearest method, the script joins each plant to its nearest model site. The script then writes out an intermediary output file called 'nearest_sim.csv'
5. 'analysis.py'
- This script is composed of three main parts: cleaning/prepping, modelling, and visualizing
- Cleaning/Prepping (lines 1:82): This section reads in three intermediary output files produced the above scripts- 'plant_gen_2020','plant_gen_history', and 'nearest_sim'. The model simulation data is merged onto the plant characteristics and generation DataFrames using the plant ID. I calculate capacity factor, which is the key outcome of interest in this analysis. Lastly, I create a sub-dataframe that isolates the plants that I will use in the regression by filtering out plants whose generation performance is skewed based on either data issues, being offline for a significant portion of the year, or having come online in 2020. I then split off a the Capacity Factor from the independent variables for modelling.
- Modelling (lines 84:97): This section contains the linear OLS modelling of the filtered dataset (n=1094) using the statsmodels module. The results are written out as a picture just containing the variables that have statistically significant relationship to capacity factor at 95% level. That picture is also pasted above.
- Visualizing (101:274): The remainder of the script contains the code that creates the charts that make up the Datapane report, including some aggregating for certain charts. The Altair module is used to create interactive visualizations, which is built on HTML. The code both saves a local HTML version of the report, but also uploads the report to Datapane's website, where it is publically accessible via the URL pasted above.

## Findings

I encourage viewers to explore the charts and regression results, as I thing there are many takeaways from this analysis. One thing that motivated this project was the question of whether developers have gotten better at siting wind plants over time as technology and data has helped reduce uncertainty. The regression results show there is a sigificant negative relationship between plant age and capacity factor, supporting that hypothesis. Also of interest, certain states have significantly lower capacity factors than average. This analysis doesn't go far enough to answer why that is, but it left me wondering how plant curtailment shows up in this data. Unfortunately, there is not much data on curtailment at the plant level, but I believe there may be way to estimate it by combining this data with wholesale power market data, assuming plants with high marginal energy costs are the ones that get curtailed.



*Capacity factor is a plants actual power generation expressed as a percentage of its maximum possible generation if it were to operate at full capacity over the given period of time. In this analysis, I focus on annual plant-level capacity factor for 2020.
