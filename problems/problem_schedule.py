from jmetal.core.problem import PermutationProblem
from jmetal.core.solution import PermutationSolution
import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class ScheduleProblem(PermutationProblem):

    def __init__(self, df_classes: pd.DataFrame = None, df_rooms: pd.DataFrame = None,number_objetives: int = None, number_constraints: int = None):
        super(ScheduleProblem, self).__init__()
        number_classes = len(df_classes)
        number_rooms = len(df_rooms)
        print('Number of classes: ', number_classes)
        print('Number of rooms available: ', number_rooms)
    
        self.df_classes = df_classes
        self.df_rooms = df_rooms
        self.number_rooms = number_rooms
        self.number_of_variables = number_classes
        self.number_of_objectives = number_objetives
        self.number_of_constraints = number_constraints
        self.obj_directions = [self.MINIMIZE, self.MINIMIZE, self.MINIMIZE]


    def evaluate(self, solution: PermutationSolution) -> PermutationSolution:

        schedule = solution.variables # schedule --> [room1, room2, room3]
        df_solution = self.__merge_solution(schedule)

        fitness_number_rooms = len(df_solution['Nome sala'].unique()) #Number of rooms occupied
        fitness_exceeded_capacity = self.__check_exceeded_capacity(df_solution) #Sum of exceeded capacity
        fitness_same_room_time = self.__check_class_same_time(df_solution) #Sum of classes that are at same time and room

        
        solution.objectives[0] = fitness_number_rooms
        solution.objectives[1] = fitness_exceeded_capacity
        solution.objectives[2] = fitness_same_room_time

        return solution

    def __check_class_same_time(self, df_solution):
        df = df_solution.value_counts(subset=['Nome sala', 'Início'], sort=False)
        filtered_array = df.values[df.values > 1]
        return len(filtered_array)

    def __check_exceeded_capacity(self, df_solution):
        df_exceeded = df_solution[df_solution['Inscritos no turno (no 1º semestre é baseado em estimativas)'] > df_solution['Capacidade Normal']]
        fitness = 0
        if len(df_exceeded) != 0:
            for index in range(len(df_exceeded)):
                class_capacity = int(df_exceeded.iloc[index]['Inscritos no turno (no 1º semestre é baseado em estimativas)'])
                room_capacity = int(df_exceeded.iloc[index]['Capacidade Normal'])
                diff_capacity = class_capacity - room_capacity
                if diff_capacity >= 5:
                    fitness += 1
        return fitness
    
    def __merge_solution(self, solution):
        df = self.df_classes.copy()
        df['Room Code'] = solution
        df_final = df.merge(self.df_rooms, how="inner",left_on='Room Code', right_on='Code')
        interesting_columns = ['Unidade de execução', 'Início', 'Fim' ,'Dia' ,'Edifício', 'Nome sala', 'Número Horas', 'Inscritos no turno (no 1º semestre é baseado em estimativas)', 'Capacidade Normal']
        return df_final[interesting_columns]

    
    def __get_rooms(self, class_capacity_level):
        level_rooms = self.df_rooms['Nivel capacidade'].unique()
        min_capacity = level_rooms[level_rooms<=class_capacity_level].max() if len(level_rooms[level_rooms<=class_capacity_level]) != 0 else class_capacity_level
        rooms_filtered = self.df_rooms[(self.df_rooms['Nivel capacidade'] >= min_capacity)]
        return rooms_filtered['Code'].reset_index(drop=True)

    # Stills needs to be better
    # Only choose a room with higher capacity if rooms that can handle the capacity are full
    def __choose_best_room(self, rooms_timetable, array_rooms, class_init):
        available_rooms = []
        for index in range(len(array_rooms)):
            room = array_rooms[index]
            timetable = rooms_timetable[room]
            if class_init not in timetable:
                available_rooms.append(index)
        filtered_rooms = np.take(array_rooms, available_rooms).reset_index(drop=True) if len(available_rooms) != 0 else array_rooms
        #print(filtered_rooms.tolist())
        #print(available_rooms)
        #print("\n")
        #Simple filtered_rooms
        #filtered_rooms_simple = available_rooms if len(available_rooms) != 0 else array_rooms
        random_index = random.randint(0, len(filtered_rooms)-1)
        #non_error_response = filtered_rooms[random_index]
        #simple_error = filtered_rooms_simple[random_index]
        #print('Oficial: ', filtered_rooms)
        #print('Simpler: ', filtered_rooms_simple)
        #print("\n")
        #Implementation for new solution
        #boolean_rooms = self.df_rooms.Code.isin(filtered_rooms)
        #df_final = self.df_rooms[boolean_rooms].sort_values(['Nivel capacidade']).reset_index(drop=True)
        return filtered_rooms[random_index] #df_final.head(random_index)['Code'][0] if len(df_final) > 1 else df_final.head(1)['Code'][0]

            
    def create_solution(self) -> PermutationSolution:
        new_solution = PermutationSolution(number_of_variables=self.number_of_variables,
                                           number_of_objectives=self.number_of_objectives)
        rooms_timetable = []
        schedule = [None] * len(self.df_classes)

        for _ in range(len(self.df_rooms)):
            rooms_timetable.append([])

        max_index = self.number_of_variables - 1 #NEW solution
        add_next_class = False #NEW solution
        for index in range(len(self.df_classes)):
            #Implementation for new solution
            if add_next_class == True:
                add_next_class = False
                continue
            class_capacity_level = int(self.df_classes.loc[index, 'Nivel capacidade'])
            class_uc = str(self.df_classes.loc[index, 'Unidade de execução']) #NEW solution
            class_init = str(self.df_classes.loc[index, 'Início'])
            class_final = str(self.df_classes.loc[index, 'Fim'])
            class_final_date_obj = datetime.strptime(class_final, '%d/%m/%Y %H:%M:%S')
            #Return array of available rooms for that capacity
            array_rooms = self.__get_rooms(class_capacity_level) #Get's room for that capacity
            #print('Class capacity: ', class_capacity_level)
            best_room = self.__choose_best_room(rooms_timetable, array_rooms, class_init)
            #Function that chooses the best room via input array rooms 
            schedule[index] = best_room
            rooms_timetable[best_room].append(class_init)
            #NEW solution --> it's getting fitness3 > 0
            if (index+1) <= max_index: #Can't surpass the maximum index
                next_index = index+1
                next_class_uc = str(self.df_classes.loc[next_index, 'Unidade de execução'])
                next_class_init = str(self.df_classes.loc[next_index, 'Início'])
                next_class_init_obj = datetime.strptime(next_class_init, '%d/%m/%Y %H:%M:%S')
                previous_class_endtime_plusm = class_final_date_obj + timedelta(minutes=30)
                previous_class_endtime_plush = class_final_date_obj + timedelta(hours=1)
                add_next_class = True if (class_uc == next_class_uc) and ((class_final_date_obj == next_class_init_obj) or (previous_class_endtime_plusm == next_class_init_obj) or (previous_class_endtime_plush == next_class_init_obj)) else False
                if add_next_class:
                    if next_class_init not in rooms_timetable[best_room]:
                        schedule[next_index] = best_room
                        rooms_timetable[best_room].append(next_class_init)
                    else:
                        add_next_class = False
        new_solution.variables = schedule
        return new_solution
        



    def get_name(self) -> str:
        return 'ScheduleProblem'