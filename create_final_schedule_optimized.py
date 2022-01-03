import pandas as pd
import numpy as np
import random
import math

def get_rooms(class_capacity_level, df_rooms):
    capacity_to_filter = class_capacity_level - 5
    rooms_filtered = df_rooms[(df_rooms['Capacidade Normal'] >= capacity_to_filter)].sort_values(by=['Capacidade Normal'], ascending=True)
    return rooms_filtered['Code'].reset_index(drop=True)

def choose_best_room_oficial(rooms_timetable, array_rooms, class_init, name_class, c_class, turn_class):
    solution = pd.DataFrame(columns=["Time", "Room Code"])
    n_classes = len(class_init)
    times_assign = class_init['Início'].values.tolist()
    aux_counter = 1
    for index in range(len(array_rooms)):
        room = array_rooms[index]
        timetable = rooms_timetable[room]
        intersection_time = np.intersect1d(timetable, times_assign, assume_unique=False, return_indices=False).tolist()
        if len(intersection_time) == 0:
            data = []
            for time in times_assign:
                data.append((time, room))
            aux_df = pd.DataFrame(data=data, columns=["Time", "Room Code"])
            solution = solution.append(aux_df, ignore_index=True)
            n_classes = n_classes - len(times_assign)
            if n_classes == 0:
                break
        elif len(intersection_time) != len(timetable): # Didn't intersect any time --> so is empty
            available_times = np.setdiff1d(times_assign, intersection_time, assume_unique=False).tolist()
            data = []
            for time in available_times:
                data.append((time, room))
            aux_df = pd.DataFrame(data=data, columns=["Time", "Room Code"])
            solution = solution.append(aux_df, ignore_index=True)
            n_classes = len(intersection_time)
            times_assign = intersection_time
            if n_classes == 0:
                times_assign = []
                break
        aux_counter +=1
    #Verify if still has classes that has no assigned room
    final_solution = class_init.merge(solution, how="inner", left_on="Início", right_on="Time")[['Code', 'Início' ,"Room Code"]]
    return final_solution

def update_timetable(df_solution, timetable): #selected_room variable--> input
    timetable_c = timetable.copy()
    list_rooms = df_solution['Room Code'].unique()
    for room_code in list_rooms:
        timetable_c[room_code] = timetable_c[room_code] + df_solution[df_solution['Room Code'] == room_code]['Início'].values.tolist()
    return timetable_c

def merge_solution(df_schedule, df_solution, df_rooms):
    df_sol_smp = df_solution.merge(df_rooms, how="inner", left_on="Room Code", right_on="Code")[['Code_x', 'Nome sala', 'Capacidade Normal']].rename(columns={"Code_x": "Class Code"})
    interesting_columns = df_schedule.columns.tolist() + ["Nome sala", "Capacidade Normal", "Lotação_Default"]
    interesting_columns.remove("Code")
    interesting_columns.remove("Sala da aula")
    interesting_columns.remove("Lotação")
    df_join = df_schedule.merge(df_sol_smp, how="inner", left_on="Code", right_on="Class Code").rename(columns={"Lotação": "Lotação_Default"})
    df_join[interesting_columns].rename(columns={"Nome sala": "Sala da aula", "Capacidade Normal": "Lotação"}).to_csv("./output/final_schedule2.csv", index=False, encoding="utf-8-sig")
    print('Saved new schedule')


schedule = pd.read_csv('./data/clean_timetable.csv')
rooms = pd.read_csv('./data/clean_rooms.csv')
print("There's %i type of classes" %(len(schedule['Unidade de execução'].unique())))
print("There's %i available rooms" % (rooms.shape[0]))
df_count_class = schedule[['Unidade de execução', 'Turma', 'Turno']].groupby(['Unidade de execução','Turma', 'Turno'], dropna=False)['Unidade de execução'] \
                             .count() \
                             .reset_index(name='count') \
                             .sort_values(['count'], ascending=False)
df_mean_class = schedule[['Unidade de execução', 'Inscritos no turno (no 1º semestre é baseado em estimativas)', 'Turma']].groupby(['Unidade de execução', 'Turma'], dropna=False)['Inscritos no turno (no 1º semestre é baseado em estimativas)'] \
                             .mean().round(0) \
                             .reset_index(name='mean')                             
rooms_timetable = [[]] * len(rooms)
df_solution = pd.DataFrame(columns=["Code", 'Início' ,"Room Code"])
counter = 0
for row in df_count_class.values:
    name_class = row[0]
    c_class = row[1]
    turn_class = row[2]
    class_timetable = schedule[(schedule['Unidade de execução'] == name_class) & (schedule['Turma'] == c_class) & (schedule['Turno'] == turn_class)][['Code', 'Início']] if isinstance(c_class, str) else schedule[(schedule['Unidade de execução'] == name_class) & (schedule['Turma'].isnull()) & (schedule['Turno'] == turn_class)][['Code', 'Início']]
    n_students = int(df_mean_class[(df_mean_class['Unidade de execução'] == name_class) & (df_mean_class['Turma'] == c_class)]['mean']) if isinstance(c_class, str) else int(df_mean_class[(df_mean_class['Unidade de execução'] == name_class) & (df_mean_class['Turma'].isnull())]['mean'])
    # Get list of rooms that can handle the n_students
    list_rooms = get_rooms(n_students, rooms)
    # Select the first room of the list
    selected_room = choose_best_room_oficial(rooms_timetable, list_rooms, class_timetable, name_class, c_class, turn_class)
    # Assign selected room for that class
    df_solution = df_solution.append(selected_room)
    rooms_timetable = update_timetable(selected_room, rooms_timetable)
    counter +=1
df_solution = df_solution.drop_duplicates()

merge_solution(schedule, df_solution, rooms)