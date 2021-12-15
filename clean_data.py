import pandas as pd
import numpy as np

data_path = "./data/"

df_classes = pd.read_csv(data_path + "timetable.csv", header=0, sep=";", encoding="utf-8-sig")
df_rooms = pd.read_csv(data_path + "rooms.csv", header=0, sep=";", encoding="utf-8-sig")
print(df_classes.columns)

print('UC sem datas: ', len(df_classes[df_classes['Dia'].isnull()])) 
df_classes = df_classes[df_classes['Dia'].notnull()]
df_classes['Início'] = (df_classes['Dia'] + " " + df_classes['Início']).astype(str)
df_classes['Fim'] = (df_classes['Dia'] + " " + df_classes['Fim']).astype(str)
df_classes['Número Horas'] = (pd.to_datetime(df_classes['Fim']) - pd.to_datetime(df_classes['Início'])) /np.timedelta64(1,'h')
df_classes['Semana'] = (pd.to_datetime(df_classes['Dia'], format='%d/%m/%Y')).dt.strftime('%U').astype(int)
df_classes['Ano'] = (pd.to_datetime(df_classes['Dia'], format='%d/%m/%Y')).dt.strftime('%Y').astype(int)
df_classes['Code'] = np.arange(len(df_classes))
df_classes.to_csv('./data/clean_timetable.csv', index=False, encoding="utf-8-sig")

#Ignore rooms which has normal capacity of 1
df_rooms2 = df_rooms[df_rooms['Capacidade Normal'] != 1]
df_rooms2['Code'] = np.arange(len(df_rooms2))
df_rooms2.to_csv('./data/clean_rooms.csv', index=False, encoding="utf-8-sig")