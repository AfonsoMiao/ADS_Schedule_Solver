from problems.problem_schedule import ScheduleProblem
from jmetal.algorithm.multiobjective import NSGAII
from jmetal.operator.mutation import PermutationSwapMutation
from jmetal.operator.crossover import PMXCrossover
from jmetal.util.comparator import MultiComparator
from jmetal.util.density_estimator import CrowdingDistance
""" from jmetal.util.ranking import FastNonDominatedRanking
from jmetal.operator import BinaryTournamentSelection """
from jmetal.util.solution import get_non_dominated_solutions
from jmetal.util.termination_criterion import StoppingByEvaluations

import time
from os import listdir
from os.path import isfile, join
import pandas as pd
import numpy as np

# Merge classes and solution generated by algorithm --> assign rooms to classes
def merge_solution(df_classes,df_rooms, solution):
    df = df_classes.copy()
    # Creates a column that has the code of the room --> assigning room for each class
    df['Room Code'] = solution
    # Merge classes_csv and rooms_csv to get room name
    df_final = df.merge(df_rooms, how="inner",left_on='Room Code', right_on='Code')
    # Selecting only useful columns
    interesting_columns = ['Unidade de execução', 'Início', 'Fim' ,'Dia' ,'Edifício', 'Nome sala', 'Número Horas', 'Inscritos no turno (no 1º semestre é baseado em estimativas)', 'Capacidade Normal', 'Code_x']
    return df_final[interesting_columns].rename(columns={"Code_x": "Code"})


# Merge weekly generated schedules --> final_schedule
def merge_files():
    mypath = "./solution_csv/"
    # Get name of files
    onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
    first_path = mypath + onlyfiles[0]
    df = pd.read_csv(first_path)
    onlyfiles.pop(0)
    # For loop to append weekly solutions
    for week_file in onlyfiles:
        df_read = pd.read_csv(mypath+week_file)
        df = df.append(df_read, ignore_index=True)
    # Refactor columns name and then merge.
    df_renamed = df.rename(columns={"Capacidade Normal": "Lotação", "Nome sala": "Sala da aula"})
    all_classes = pd.read_csv('./data/clean_timetable3.csv')
    all_columns = all_classes.columns
    df_final = all_classes.merge(df_renamed, how="inner",left_on='Code', right_on='Code').rename(columns={'Unidade de execução_x': 'Unidade de execução', 'Início_x': 'Início', 'Fim_x': 'Fim','Dia_x': 'Dia','Edifício': 'Edifício', 'Número Horas_x': 'Número Horas', 'Inscritos no turno (no 1º semestre é baseado em estimativas)_x': 'Inscritos no turno (no 1º semestre é baseado em estimativas)', 'Lotação_y': 'Lotação', 'Lotação_x': 'Lotação_Default', 'Sala da aula_y': 'Sala da aula'})
    oficial_columns = all_columns.tolist() + ['Lotação_Default']
    # Saving final solution
    df_final[oficial_columns].drop(['Número Horas', 'Semana', 'Ano', 'Code'], axis=1).to_csv("./final_schedule.csv", index=False, encoding="utf-8-sig")

# Function that chooses the best objective by priorities:
## 1) Fitness 3 --> classes at same time and room
## 2) Fitness 2 --> classes exceeded capacity of room
## 3) Fitness 1 --> number of rooms used
def choose_best_objective(objectives_matrix):
    objectives = pd.DataFrame(objectives_matrix, columns=['Fitness1', 'Fitness2', 'Fitness3'])
    fitness3_min_value = objectives['Fitness3'].min()
    fitness3_filtered = objectives[objectives['Fitness3'] == fitness3_min_value]
    fitness2_min_value = fitness3_filtered['Fitness2'].min()
    fitness2_filtered = fitness3_filtered[fitness3_filtered['Fitness2'] == fitness2_min_value]
    fitness1_min_value = fitness2_filtered['Fitness1'].min()
    fitness1_filtered = fitness2_filtered[fitness2_filtered['Fitness1'] == fitness1_min_value]
    return fitness1_filtered.values.tolist()[0] if len(fitness1_filtered) == 1 else fitness1_filtered.head(1).values.tolist()[0]

# Return the index of array that has the best solution
def return_best_solution_index(objectives_matrix, best_objective):
    np_best_objective = np.array(best_objective)
    for index in range(len(objectives_matrix)):
        np_objective = np.array(objectives_matrix[index])
        comparison = np_best_objective == np_objective
        equal_arrays = comparison.all()
        if equal_arrays:
            return index

def test_multi_files():
    all_classes = pd.read_csv('./data/clean_timetable3.csv')
    all_rooms = pd.read_csv('./data/clean_rooms.csv')
    # Selecting only important columns
    classes_columns = ['Code', 'Unidade de execução','Inscritos no turno (no 1º semestre é baseado em estimativas)', 'Número Horas', 'Semana', 'Ano', 'Início', 'Fim' ,'Dia']
    df_classes = all_classes[classes_columns]
    rooms_columns = ['Code','Capacidade Normal', 'Edifício', 'Nome sala']
    df_rooms = all_rooms[rooms_columns]
    

    weeks_array = df_classes['Semana'].unique()
    # Auxiliary variables
    runtime_array = np.array([])
    fitness_matrix = []
    for week in weeks_array:
        print('Running algorithm for week: ', week)
        df_class_week = df_classes[df_classes['Semana'] == week]#.sort_values(['Unidade de execução','Início'], ascending=True).reset_index(drop=True)
        df_class_week['Início2'] = pd.to_datetime(df_class_week['Início'], format='%d/%m/%Y %H:%M:%S')
        df_class_week = df_class_week.sort_values(['Unidade de execução','Início2'], ascending=True).reset_index(drop=True)
        problem = ScheduleProblem(df_class_week, df_rooms, 3, 0)
        max_evaluations = 10
        population_size = 30 #Number of solutions(schedules) to create
        start_time = time.time()
        algorithm = NSGAII(
            problem=problem,
            population_size=population_size,
            offspring_population_size=100,
                mutation=PermutationSwapMutation(1.0 / problem.number_of_variables),
                crossover=PMXCrossover(0.9),
                termination_criterion=StoppingByEvaluations(max_evaluations=max_evaluations)
        )
        algorithm.run()
        result = algorithm.get_result()
        front = get_non_dominated_solutions(result)
        solutions = [j_solution.variables for j_solution in front]
        objectives = [j_solution.objectives for j_solution in front]
        best_objective = choose_best_objective(objectives)
        solution_index = return_best_solution_index(objectives, best_objective)
        best_solution = solutions[solution_index]
        runtime = time.time() - start_time
        runtime_array = np.append(runtime_array, [runtime])
        fitness_matrix.append(np.append(best_objective, [str(week), str(runtime)]))
        print('Optimization ended')
        print('Number of solutions generated: ', len(front))
        print('Result: ', solutions)
        print('Objectives: ', objectives)
        print('Best objective: ', best_objective)
        print("--- %s seconds ---" % (runtime))
        path = 'week' + str(week)
        df_to_save = merge_solution(df_class_week, df_rooms, best_solution)
        df_to_save.to_csv('./solution_csv/' + path + '.csv', index=False, encoding="utf-8-sig")
        
        # Saves solution (room code) for each week
        #text_file = open("./solution_text/" + path + ".txt", "w")
        #text_file.write(str(best_solution))
        #text_file.close()

    #Save a file with total time of algorithm's runtime
    text_file = open("./total_time.txt", "w")
    string_total_time = "Runtime algorithm: " + str(runtime_array.sum())
    text_file.write(str(string_total_time))
    text_file.close()
    #Create fitness report
    df_fitness = pd.DataFrame(fitness_matrix, columns=['Fitness1', 'Fitness2', 'Fitness3', 'Week', 'Runtime'])
    df_fitness.to_csv('./fitness_report.csv', index=False, encoding="utf-8-sig")



test_multi_files()
merge_files()
