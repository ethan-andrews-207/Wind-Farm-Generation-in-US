
# %%Importing modules used in analysis
from statistics import mode
from unicodedata import name
import numpy as np
from numpy import sort
import pandas as pd
import matplotlib.pyplot as plt
import altair as alt
from sqlalchemy import values
import datapane as dp
dp.login(token='fe7f5674e813c8a7739d1b5171c3c01e6299bf6f')#For uploading visualizations to DataPane's website
import datetime as dt
import statsmodels.api as sm
import dataframe_image as dfi


pd.set_option("display.precision", 2)

#Reading in plant-level data that contains characteristics and generation; there is a 2020 annual dataset and a historical dataset containing monthly generation
plant_2020=pd.read_csv('plant_gen_2020.csv',dtype={'Plant Code':str})
plant_history=pd.read_csv('plant_gen_history.csv',dtype={'Plant Code':str})

#%%Joining wind speed/NREL simulation data onto plants
nearest=pd.read_csv('nearest_sim.csv',dtype={'Plant Code':str})

plant_2020=plant_2020.merge(nearest,on='Plant Code',validate='1:1')
plant_history=plant_history.merge(nearest,on='Plant Code',validate='m:1')

#%%Cleaning up dataframes
plant_2020.drop(columns='Unnamed: 0',inplace=True)
plant_history.drop(columns='Unnamed: 0',inplace=True)

plant_2020=plant_2020.rename(columns={'Annual Net Gen':'2020 Net Generation (MWh)','capacity_factor':'Simulated Capacity Factor','wind_speed':'Average Local Wind Speed'})

plant_2020['Start of Operation']=pd.to_datetime(plant_2020['Start of Operation'],yearfirst=True)

plant_history['gen period']=pd.to_datetime(plant_history['gen period'],yearfirst=True)

plant_history=plant_history.rename(columns={'gen period':'Generation Period'})

#%% Compting capacity factor 
plant_2020['Annual Capacity Factor']=plant_2020['2020 Net Generation (MWh)']/(plant_2020['Nameplate Capacity (MW)']*8760)
plant_2020['Gen per Turbine']=plant_2020['2020 Net Generation (MWh)']/plant_2020['Number of Turbines']

plant_2020['Annual Capacity Factor']=np.where(plant_2020['Annual Capacity Factor']>1,np.nan,plant_2020['Annual Capacity Factor'])

plant_2020=plant_2020.sort_values(by=['State'])

plant_history['Monthly Capacity Factor']=plant_history['Net Gen']/(plant_history['Nameplate Capacity (MW)']*730)

plant_2020['Year Built']=plant_2020['Start of Operation'].dt.year

plant_2020['Wind Quality Class']=plant_2020['Wind Quality Class'].astype(str)


#Creating sub-dataframe that filters out plants with very low and high capacity factors (data quality councerns), 
#those that were designated as out of operation, and those that came online in 2020
#This is for estimating the statistical relationships between characterisitcs of plants and generation performance

no_outliers=(plant_2020['Annual Capacity Factor']<.7)& (plant_2020['Annual Capacity Factor']>.05) & (plant_2020['Status']=='OP') & (plant_2020['Year Built']<2020)

plant_2020_trim=plant_2020[no_outliers]

#%%Creating dataframe for linear OLS model with target column and fixed effects
keep_cols=['Plant Code','State','Sector Name','Nameplate Capacity (MW)','Number of Turbines','Predominant Turbine Manufacturer','Design Wind Speed (mph)','Wind Quality Class','Turbine Hub Height (Feet)'
            ,'Year Built','NERC Region','Balancing Authority Code','Grid Voltage (kV)','Simulated Capacity Factor','Average Local Wind Speed','Annual Capacity Factor']

plant_2020_model=plant_2020_trim[keep_cols]

dums=pd.get_dummies(plant_2020_model,columns=['State','Sector Name','Predominant Turbine Manufacturer','NERC Region','Balancing Authority Code','Wind Quality Class'],drop_first=True)

X=dums.drop(columns='Annual Capacity Factor')
X=X.set_index('Plant Code')
Y=dums[['Annual Capacity Factor','Plant Code']]
Y=Y.set_index('Plant Code')

X_statmodel=sm.add_constant(X)

mask=X_statmodel.columns.str.contains('NERC.*')|X_statmodel.columns.str.contains('Balancing.*')

X_statmodel=X_statmodel.loc[:,~mask]

#%%Running OLS Model, printing results, and saving as picture

model=sm.OLS(Y,X_statmodel).fit(cov_type='HC1')

model_summary=model.summary()

results_as_html=model_summary.tables[1].as_html()
coefs=pd.read_html(results_as_html, header=0, index_col=0)[0]

coefs=coefs.rename(columns={'P>|z|':'P_value'})

coefs_sig=coefs.query("P_value<=.05")

coefs_sig.dfi.export('regression_results.png')

# %% Grouping plants by state for monthly generation

plant_20_22_month=plant_history.query("year>=2020")
plant_20_22_month_state=plant_20_22_month.groupby('State',as_index=False)
plant_20_22_month_state=plant_20_22_month_state.agg({'Nameplate Capacity (MW)':sum,
                                                    'Number of Turbines':sum,
                                                    'Plant Code':'nunique',
                                                    'wind_speed':'median',
                                                    'Net Gen':sum,
                                                    'NERC Region':mode})
plant_20_22_month_state['Annual Capacity Factor']=plant_20_22_month_state['Net Gen']/(plant_20_22_month_state['Nameplate Capacity (MW)']*8760)

plant_20_22_month_state=plant_20_22_month_state.rename(columns={'NERC Region':'Predominant NERC Region','Plant Code':'Number of Plants'})


# %% Creating charts in Altair and uploading to Datapane


#Scatter plot of plants by generation and capacity, with bar chart of states by net gen which acts as filter when clicked
click = alt.selection_multi(fields=['State'])

alt_chart_plant = alt.Chart(plant_2020).mark_circle(size=60).encode(
    x='Nameplate Capacity (MW)',
    y='2020 Net Generation (MWh):Q',
    color='NERC Region',
    size='Number of Turbines',
    tooltip=['Plant Name:N','Utility Name:N','State','2020 Net Generation (MWh):Q','Number of Turbines','Predominant Turbine Manufacturer']
    ).properties(title='Plants by Generation and Capacity',
    width=1000,
    height=600
    ).transform_filter(click)

alt_chart_state = alt.Chart(plant_20_22_month_state).mark_bar().encode(
    x='Net Gen',
    y=alt.Y('State',sort='-x'),
    color=alt.condition(click,alt.value('steelblue'),alt.value('lightgray'))
    ).properties(title='States by Wind Generation',
    width=1000,
    height=600
    ).add_selection(click)

state_plant_chart=alt.vconcat(alt_chart_plant,alt_chart_state,data=plant_2020)


#Chart of plants by year built and turbine manufacturer
top10manuf = plant_2020['Predominant Turbine Manufacturer'].value_counts()[:5].index


plant_2020['Turbine Manufacturer']=plant_2020.loc[~plant_2020['Predominant Turbine Manufacturer'].isin(top10manuf),'Predominant Turbine Manufacturer'] = 'Other'


plants_by_manuf = alt.Chart(plant_2020).mark_bar().encode(
    alt.X('Start of Operation:T',timeUnit='year'),
    alt.Y('count(Plant Code)'),
    color='Predominant Turbine Manufacturer'
    ).properties(title='Number of Plants Built per Year and Turbine Manufacturer',
    width=1000,
    height=600
    )

#Capacity factor by plant age scatter plot with OLS line
cap_by_year=alt.Chart(plant_2020_trim).mark_circle().encode(
    alt.X('Start of Operation:T',timeUnit='year'),
    alt.Y('Annual Capacity Factor'),
    size='Nameplate Capacity (MW)',
    tooltip=['Plant Name:N','Utility Name:N','State','2020 Net Generation (MWh):Q','Number of Turbines','Predominant Turbine Manufacturer']
    ).properties(title='Plants by Age and 2020 Capacity Factor*',
    width=1000,
    height=600
    )

cap_by_year_line=alt.layer(
            cap_by_year,
            cap_by_year.transform_regression(on='Start of Operation',regression= 'Annual Capacity Factor').mark_line(
            )
)

#Capacity factor by NERC region jittered scatterplot
cap_by_nerc=alt.Chart(plant_2020).mark_circle(
    opacity=.8,
    stroke='black',
    strokeWidth=1
).encode(
    alt.X('Annual Capacity Factor'),
    alt.Y('NERC Region'),
    alt.Size('Nameplate Capacity (MW)',
    scale=alt.Scale(range=[1,800])),
    alt.Color('NERC Region',legend=None)
).properties(title='Capacity Factor by NERC Region',
width=1000,
height=600
)


#Historical generation chart for NY farms
plant_history_ny=plant_history.query("State=='NY'")

alt.data_transformers.disable_max_rows()

input_dropdown = alt.binding_select(options=plant_history_ny['Plant Name'].unique(), name='Plant Name')
selection = alt.selection_single(fields=['Plant Name'], bind=input_dropdown,name='Plant Name')

gen_by_year_plant=alt.Chart(plant_history_ny).mark_line().encode(
    alt.X('Generation Period',timeUnit='yearmonth'),
    alt.Y('Net Gen:Q')
    ).properties(title='Net Generation by New York Wind Farms',
    width=1000,
    height=600
    ).add_selection(
        selection
    ).transform_filter(
        selection
    )

#State by capacity factor bar chart
alt_chart_state_cap= alt.Chart(plant_2020).mark_bar().encode(
    x='median(Annual Capacity Factor)',
    y=alt.Y('State',sort='-x'),
    color='sum(2020 Net Generation (MWh))'
    ).properties(title='States by Capacity Factor',
    width=1000,
    height=600
    )

# Saving local report as html file
wind_report=dp.Report(
    dp.Page(
        title='Overview',
        blocks=[state_plant_chart]
    ),
    dp.Page(
        title='Plants by Age and 2020 Capacity Factor*',
        blocks=[cap_by_year_line
        ,"*Only includes plants in operation with capacity factor between .05 and .7 that came online before 2020\n\n"]
    ),
    dp.Page(
        title='Plants by Manufacturer',
        blocks=[plants_by_manuf]
    ),
    dp.Page(title='Capacity Factor by NERC Region',
            blocks=[cap_by_nerc]
    ),
    dp.Page(title='Net Generation by New York Wind Farms',
            blocks=[gen_by_year_plant]
    ),
        dp.Page(title='States by Median Capacity Factor',
            blocks=[alt_chart_state_cap]
    ),            
    ).save(path='plant_gen_report.html',formatting=dp.ReportFormatting(width=dp.ReportWidth.FULL))


#Uploading report to datapane site
dp.Report(
    dp.Page(
        title='Overview',
        blocks=[state_plant_chart]
    ),
    dp.Page(
        title='Plants by Age and 2020 Capacity Factor*',
        blocks=[cap_by_year_line
        ,"*Only includes plants in operation with capacity factor between .05 and .7 that came online before 2020\n\n"]
    ),
    dp.Page(
        title='Plants by Manufacturer',
        blocks=[plants_by_manuf]
    ),
    dp.Page(title='Capacity Factor by NERC Region',
            blocks=[cap_by_nerc]
    ),
    dp.Page(title='Net Generation by New York Wind Farms',
            blocks=[gen_by_year_plant]
    ), 
            dp.Page(title='States by Median Capacity Factor',
            blocks=[alt_chart_state_cap]
    ),         
    ).upload(name='Wind Power Generation Report')

# %%
