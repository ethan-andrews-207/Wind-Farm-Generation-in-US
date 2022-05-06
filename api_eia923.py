
# %% Reading in data, setting up API request, and creating dataframe shells
import pandas as pd
import requests
import json

plant_full_api=pd.read_csv('plant_full_info.csv',dtype={'Plant Code':str})

plant_full_api=plant_full_api.drop(columns=['Unnamed: 0'])

plant_full_api_sample=plant_full_api.sample(10)

api='https://api.eia.gov/series/?'

key_value='IMdeDa31bq2kHNlVdniUHixr3dlJvMLNEYdptJj2'

frame=pd.DataFrame(columns=['period','Net Gen'])

generation=pd.DataFrame()

display(plant_full_api)

#%Runs recursive API call using plant codes, extracts generation data, appends to generation DF
for index,plant_code in plant_full_api['Plant Code'].iteritems(): 
    payload={'api_key':key_value,'series_id':'ELEC.PLANT.GEN.'+plant_code+'-ALL-ALL.M'}
    response=requests.get(api,payload)
    response_json=response.json()
    list=response_json['series']
    dict=list[0]
    list_of_lists=dict['data']
    df=pd.DataFrame(list_of_lists,columns=['period','Net Gen'])
    df['Plant Code']=plant_code
    generation=pd.concat([frame,df,generation])
    print(len(generation)) #For tracking progress of call, results in 138,000+ rows

generation[['period','Net Gen']]=generation[['period','Net Gen']].astype(int)

print(generation.describe())
#%%

generation.to_csv('gen_history.csv',index=False) 
# %%
