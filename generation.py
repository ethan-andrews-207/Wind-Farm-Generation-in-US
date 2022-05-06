#%%
import pandas as pd
from numpy import disp, std

#%%  Read in generation data generated from API script

gen_history=pd.read_csv('gen_history.csv',dtype={'Plant Code':str,'period':str,'Net Gen':int})

gen_history['year']=gen_history['period'].str.slice(0,4)
gen_history['month']=gen_history['period'].str.slice(4,)

gen_history['day']=1

gen_history['gen period']=gen_history['year'].astype(str)+"-"+gen_history['month'].astype(str)+"-"+gen_history['day'].astype(str)

gen_history['gen period']=pd.to_datetime(gen_history['gen period'])

gen_history=gen_history.drop(columns=['month','day','period'])

#%%Trim and aggregate to annual generation for 2020
gen_2020=gen_history.query("year=='2020'")

gen_2020=gen_2020.groupby('Plant Code')

gen_2020=gen_2020['Net Gen'].agg([sum,std])

gen_2020=gen_2020.rename(columns={'sum':'Annual Net Gen','std':'Monthly Gen Std Dev'})

display(gen_history)
display(gen_2020)


#%% Merge generation data with plant characteristics

plant_full=pd.read_csv('plant_full_info.csv',dtype={'Plant Code':str})

plant_history=plant_full.merge(gen_history,on='Plant Code',validate='1:m')

plant_2020=plant_full.merge(gen_2020,on='Plant Code',validate='1:1')


#%% Writing out datasets to be used in analysis script

plant_history.to_csv('plant_gen_history.csv',index=False)

plant_2020.to_csv('plant_gen_2020.csv',index=False)

# %%
