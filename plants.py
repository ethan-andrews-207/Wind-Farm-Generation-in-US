#%% Reading in and cleaning up wind-specific plant characteristics data 
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


#%% Aggregating from generator level to plant level

wind_plants=wind_specific.groupby('Plant Code')

wind_plants=wind_plants.agg({'Utility ID':'first','Utility Name':'first','Plant Name':'first','State':'first','County':'first','Status':'first'
                            ,'Technology':'first','Sector Name':'first','Nameplate Capacity (MW)':sum,'Number of Turbines':sum,'Predominant Turbine Manufacturer':pd.Series.mode,
                            'Predominant Turbine Model Number':pd.Series.mode,'Design Wind Speed (mph)':'median','Wind Quality Class':pd.Series.mode,'Turbine Hub Height (Feet)':'median',
                            'Start of Operation':min})

wind_plants.reset_index(inplace=True)
wind_plants=wind_plants.rename(columns={'index':'Plant Code'})




# %% Reading and trimming general plant information 
plant_basics=pd.read_excel('2___Plant_Y2020.xlsx',skiprows=[0],sheet_name='Plant')

plant_basics.info()

plant_basics=plant_basics[['Plant Code','Latitude','Longitude','NERC Region','Balancing Authority Code','Balancing Authority Name','Grid Voltage (kV)']]

plant_basics[['Grid Voltage (kV)','Latitude','Longitude']]=plant_basics[['Grid Voltage (kV)','Latitude','Longitude']].apply(pd.to_numeric,errors='coerce')

plant_basics['Plant Code']=plant_basics['Plant Code'].astype(str)





# %% Merging general and wind-specific characeristics of plants, then writing out to be used in API script to get generation data
plant_full=wind_plants.merge(plant_basics,how='inner',on='Plant Code',validate='1:1')

plant_full.to_csv('plant_full_info.csv')

display(plant_full)
