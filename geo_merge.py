#%% Reading in plant data and wind simulation site data from NREL
import pandas as pd
import geopandas as gpd

plant_geo=pd.read_csv('plant_full_info.csv',dtype={'Plant Code':str})
wind_geo=pd.read_csv('wtk_site_metadata.csv',dtype={'site_id':str})

plant_geo=plant_geo[['Plant Code','Latitude','Longitude','State']]
wind_geo=wind_geo[['site_id','longitude','latitude','capacity_factor','wind_speed']]

#Converting dataframes to geodataframes using coordinates as geometry
plant_points = gpd.GeoDataFrame(
    plant_geo, geometry=gpd.points_from_xy(plant_geo.Longitude, plant_geo.Latitude),crs="EPSG:5070")

wind_points = gpd.GeoDataFrame(
    wind_geo, geometry=gpd.points_from_xy(wind_geo.longitude, wind_geo.latitude),crs="EPSG:5070")

#Joining each plant to its nearest simulation site and computing distance between pounts
nearest=gpd.sjoin_nearest(plant_points,wind_points,how='inner',distance_col='Distance')


#Some descriptive stats of distance column- units are degrees in projected coordinate space
print(nearest['Distance'].describe())

#Example row; distance between plant and sim site ~500 feet
Mars_hill=nearest['Plant Code']=='56448'
nearest_Mars=nearest[Mars_hill]
print(nearest_Mars)

#Mean distances between plants and nearest sim sites by states; Alaska and Hawaii are very large because sim sites are only in contiguous US
state=nearest.groupby('State')
mean_dist=state['Distance'].mean()
print(nearest['geometry'])

#Writing out dataset to be used in analysis script
nearest[['Plant Code','geometry','Distance','capacity_factor','wind_speed']].to_csv('nearest_sim.csv',index=False)
# %%