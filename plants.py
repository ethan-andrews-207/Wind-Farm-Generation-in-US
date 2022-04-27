#%% WIND GEN 
from operator import index
from pydoc import describe
from numpy import disp, std
import pandas as pd

pd.set_option('display.max_columns', None)

wind_specific=pd.read_excel('3_2_Wind_Y2020.xlsx',skiprows=[0],sheet_name='Operable')

wind_specific.info()

display(wind_specific)

convert_type={'Utility ID':str,'Plant Code':str,'Sector':str,'Wind Quality Class':str}

wind_specific=wind_specific.astype(convert_type)

wind_specific["day"]=1

wind_specific['Start of Operation']=wind_specific['Operating Year'].astype(str)+"-"+wind_specific['Operating Month'].astype(str)+"-"+wind_specific['day'].astype(str)

wind_specific['Start of Operation']=pd.to_datetime(wind_specific['Start of Operation'])

wind_specific.drop(columns=['Operating Year','Operating Month','day','Sector','Prime Mover'],inplace=True)

wind_specific['season capacity diff']=wind_specific['Summer Capacity (MW)']-wind_specific['Winter Capacity (MW)']

wind_specific['season capacity diff'].describe()

wind_specific.drop(columns=['Summer Capacity (MW)','Winter Capacity (MW)','season capacity diff'],inplace=True)


#%% GENERATOR TO PLANT AGG

wind_plants=wind_specific.groupby('Plant Code')

wind_plants=wind_plants.agg({'Utility ID':'first','Utility Name':'first','Plant Name':'first','State':'first','County':'first','Status':'first'
                            ,'Technology':'first','Sector Name':'first','Nameplate Capacity (MW)':sum,'Number of Turbines':sum,'Predominant Turbine Manufacturer':pd.Series.mode,
                            'Predominant Turbine Model Number':pd.Series.mode,'Design Wind Speed (mph)':'median','Wind Quality Class':pd.Series.mode,'Turbine Hub Height (Feet)':'median',
                            'Start of Operation':min})

wind_plants.reset_index(inplace=True)
wind_plants=wind_plants.rename(columns={'index':'Plant Code'})




# %% PLANT BASICS
plant_basics=pd.read_excel('2___Plant_Y2020.xlsx',skiprows=[0],sheet_name='Plant')

plant_basics.info()

plant_basics=plant_basics[['Plant Code','Latitude','Longitude','NERC Region','Balancing Authority Code','Balancing Authority Name','Grid Voltage (kV)']]

plant_basics[['Grid Voltage (kV)','Latitude','Longitude']]=plant_basics[['Grid Voltage (kV)','Latitude','Longitude']].apply(pd.to_numeric,errors='coerce')

plant_basics['Plant Code']=plant_basics['Plant Code'].astype(str)





# %% MERGE PLANT BASIC INFO WITH WIND SPECIFIC DATA, WRITE OUT COMPLETE PLANT DATA
plant_full=wind_plants.merge(plant_basics,how='inner',on='Plant Code',validate='1:1')

plant_full.to_csv('plant_full_info.csv')

display(plant_full)





#%% V1. GENERATION HISTORY FROM API

gen_history=pd.read_csv('gen_history.csv',dtype={'Plant Code':str,'period':str,'Net Gen':int})

gen_history['year']=gen_history['period'].str.slice(0,4)
gen_history['month']=gen_history['period'].str.slice(4,)

gen_history['day']=1

gen_history['gen period']=gen_history['year'].astype(str)+"-"+gen_history['month'].astype(str)+"-"+gen_history['day'].astype(str)

gen_history['gen period']=pd.to_datetime(gen_history['gen period'])

gen_history=gen_history.drop(columns=['month','day','period'])

gen_2020=gen_history.query("year=='2020'")

gen_2020=gen_2020.groupby('Plant Code')

gen_2020=gen_2020['Net Gen'].agg([sum,std])

gen_2020=gen_2020.rename(columns={'sum':'Annual Net Gen','std':'Monthly Gen Std Dev'})

display(gen_history)
display(gen_2020)


#%% MERGE PLANT WITH GEN DATA

plant_history=plant_full.merge(gen_history,on='Plant Code',validate='1:m')

plant_2020=plant_full.merge(gen_2020,on='Plant Code',validate='1:1')


#%% Writing out data for other scripts

plant_history.to_csv('plant_gen_history.csv',index=False)

plant_2020.to_csv('plant_gen_2020.csv',index=False)










#################################OLD
#%% V2. 2020 GENERATION
generation=pd.read_excel('EIA_923_2020.xlsx',skiprows=5,sheet_name='Page 1 Generation and Fuel Data')

display(generation)

generation['Plant Id']=generation['Plant Id'].astype(str)

generation.set_index('Plant Id',inplace=True)

generation=generation.loc[:,generation.columns.str.startswith('Net')]

generation=generation.apply(pd.to_numeric,errors='coerce')

display(generation)

generation=generation.reset_index()

gen_plant=generation.groupby('Plant Id',as_index=False)

gen_plant=gen_plant.agg({'Netgen\nJanuary':sum,'Netgen\nFebruary':sum,'Netgen\nMarch':sum,'Netgen\nApril':sum,'Netgen\nMay':sum,'Netgen\nJune':sum,
                        'Netgen\nJuly':sum,'Netgen\nAugust':sum,'Netgen\nSeptember':sum,'Netgen\nOctober':sum,'Netgen\nNovember':sum,'Netgen\nDecember':sum,
                        'Net Generation\n(Megawatthours)':sum})

gen_plant['Summer Avg Gen']=(gen_plant['Netgen\nJune']+gen_plant['Netgen\nJuly']+gen_plant['Netgen\nAugust'])

gen_plant['Winter Avg Gen']=(gen_plant['Netgen\nDecember']+gen_plant['Netgen\nJanuary']+gen_plant['Netgen\nFebruary'])

gen_plant['Seasonality Ratio']=gen_plant['Summer Avg Gen']/gen_plant['Winter Avg Gen']

gen_plant=gen_plant.rename(columns={'Net Generation\n(Megawatthours)':'Annual Net Gen'})

gen_annual=gen_plant[['Plant Id','Annual Net Gen','Seasonality Ratio']]

display(gen_annual)



#%% CREATE MONTHLY 2020 GENERATION DATAFRAME
gen_plant_tidy=gen_plant.drop(columns=['Annual Net Gen','Summer Avg Gen','Winter Avg Gen','Seasonality Ratio'])

gen_month=pd.melt(gen_plant_tidy,id_vars='Plant Id',var_name='Month',value_name='Net Generation')

gen_month['Month']=gen_month['Month'].str.replace('Netgen\n','')

gen_month['Year']=2020
gen_month['Day']=1

month_map={'January':1,'February':2,'March':3,'April':4,'May':5,'June':6,'July':7,'August':8,'September':9,'October':10,'November':11,'December':12}
gen_month['Month']=gen_month['Month'].map(month_map)

gen_month['Date']=gen_month['Year'].astype(str)+"-"+gen_month['Month'].astype(str)+"-"+gen_month['Day'].astype(str)

gen_month['Date']=pd.to_datetime(gen_month['Date'])

gen_month=gen_month[['Plant Id','Date','Net Generation']]

display(gen_month)

plant_annual=plant_full.merge(gen_annual,left_on='Plant Code',right_on='Plant Id',validate='1:1')

plant_annual=plant_annual.drop(columns=['Plant Id']) 

plant_month=plant_full.merge(gen_month,left_on='Plant Code',right_on='Plant Id',validate='1:m')

plant_month=plant_month.drop(columns=['Plant Id']) 