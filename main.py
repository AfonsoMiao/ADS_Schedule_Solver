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

# Filter rooms that don't have any hour assigned
# OUTPUT: Array that contains indices of rooms that has > 0 hours
def __get_rooms_indices(self, array_hours):
    return np.where(array_hours > 0.0)[0]

def merge_solution(df_classes,df_rooms, solution):
    df = df_classes.copy()
    df['Room Code'] = solution
    df_final = df.merge(df_rooms, how="inner",left_on='Room Code', right_on='Code')
    interesting_columns = ['Unidade de execução', 'Início', 'Fim' ,'Dia' ,'Edifício', 'Nome sala', 'Número Horas', 'Inscritos no turno (no 1º semestre é baseado em estimativas)', 'Capacidade Normal', 'Code_x']
    return df_final[interesting_columns].rename(columns={"Code_x": "Code"})

def merge_files():
    mypath = "./solution_csv/"
    onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]
    first_path = mypath + onlyfiles[0]
    df = pd.read_csv(first_path)
    onlyfiles.pop(0)
    for week_file in onlyfiles:
        df_read = pd.read_csv(mypath+week_file)
        df = df.append(df_read, ignore_index=True)
    df_renamed = df.rename(columns={"Capacidade Normal": "Lotação"})
    #print('Columns: ', df_final.columns)
    all_classes = pd.read_csv('./data/clean_timetable2.csv')
    df_final = all_classes.merge(df_renamed, how="inner",left_on='Code', right_on='Code')
    interesting_columns = ['Unidade de execução', 'Início', 'Fim' ,'Dia' ,'Edifício', 'Nome sala', 'Número Horas', 'Inscritos no turno (no 1º semestre é baseado em estimativas)', 'Lotação']
    df_final[interesting_columns].to_csv("./final_schedule.csv", index=False, encoding="utf-8-sig")

# Priorities:
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

def return_best_solution_index(objectives_matrix, best_objective):
    np_best_objective = np.array(best_objective)
    for index in range(len(objectives_matrix)):
        np_objective = np.array(objectives_matrix[index])
        comparison = np_best_objective == np_objective
        equal_arrays = comparison.all()
        if equal_arrays:
            return index

def test_multi_files():
    all_classes = pd.read_csv('./data/clean_timetable2.csv')
    all_rooms = pd.read_csv('./data/clean_rooms.csv')
    #initial_columns = all_classes.columns
    # Selecting only important columns
    classes_columns = ['Code', 'Unidade de execução','Inscritos no turno (no 1º semestre é baseado em estimativas)', 'Número Horas', 'Semana', 'Ano', 'Início', 'Fim' ,'Dia']
    df_classes = all_classes[classes_columns]
    #df_classes = all_classes
    rooms_columns = ['Code','Capacidade Normal', 'Edifício', 'Nome sala']
    df_rooms = all_rooms[rooms_columns]
    
    #Add auxiliary columns
    df_classes['Nivel capacidade'] = [int(round(x,-1)/10) for x in df_classes['Inscritos no turno (no 1º semestre é baseado em estimativas)']]
    df_rooms['Nivel capacidade'] = [int(round(x,-1)/10) for x in df_rooms['Capacidade Normal']]
    
    weeks_array = df_classes['Semana'].unique()
    runtime_array = np.array([])
    fitness_matrix = []
    for week in weeks_array:
        #week = weeks_array[index]
        print('Running algorithm for week: ', week)
        df_class_week = df_classes[df_classes['Semana'] == week].sort_values(['Unidade de execução','Início'], ascending=True).reset_index(drop=True)
        #df_class_week = df_classes[df_classes['Semana'] == week].reset_index(drop=True)
        problem = ScheduleProblem(df_class_week, df_rooms, 3, 0)
        max_evaluations = 7
        population_size = 20 #Number of solutions(schedules) to create
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
        fitness_matrix.append(np.append(objectives[0], [str(week), str(runtime)]))
        print('Optimization ended')
        print('Number of solutions generated: ', len(front))
        print('Result: ', solutions)
        print('Objectives: ', objectives)
        print('Best objective: ', best_objective)
        print("--- %s seconds ---" % (runtime))
        path = 'week' + str(week)
        df_to_save = merge_solution(df_class_week, df_rooms, best_solution)
        df_to_save.to_csv('./solution_csv/' + path + '.csv', index=False, encoding="utf-8-sig")
        
        #open text file
        text_file = open("./solution_text/" + path + ".txt", "w")
        #write string to file
        text_file.write(str(best_solution))
        #close file
        text_file.close()
        
    #open text file
    text_file = open("./total_time.txt", "w")
    string_total_time = "Total time running algorithm: " + str(runtime_array.sum())
    #write string to file
    text_file.write(str(string_total_time))
    #close file
    text_file.close()
    #Create fitness report
    df_fitness = pd.DataFrame(fitness_matrix, columns=['Fitness1', 'Fitness2', 'Fitness3', 'Week', 'Runtime'])
    df_fitness.to_csv('./fitness_report.csv', index=False, encoding="utf-8-sig")



def test_single_file():
    raw_classes = pd.read_csv('./data/week46.csv')
    raw_rooms = pd.read_csv('./data/clean_rooms.csv')
    #'Unidade de execução', 'Início', 'Fim' ,'Dia' ,'Edifício', 'Nome sala', 'Número Horas', 'Inscritos no turno (no 1º semestre é baseado em estimativas)', 'Capacidade Normal'
    # Extracting data for test purposes
    classes_columns = ['Code', 'Unidade de execução','Inscritos no turno (no 1º semestre é baseado em estimativas)', 'Número Horas', 'Semana', 'Ano', 'Code', 'Início', 'Fim' ,'Dia']
    df_classes = raw_classes[classes_columns]
    rooms_columns = ['Code','Capacidade Normal', 'Edifício', 'Nome sala']
    df_rooms = raw_rooms[rooms_columns]

    #Add auxiliary columns
    #df_classes['Index'] = np.arange(len(df_classes))
    #df_rooms['Index'] = np.arange(len(df_rooms))
    df_classes['Nivel capacidade'] = [int(round(x,-1)/10) for x in df_classes['Inscritos no turno (no 1º semestre é baseado em estimativas)']]
    df_rooms['Nivel capacidade'] = [int(round(x,-1)/10) for x in df_rooms['Capacidade Normal']]


    # User less rooms possible
    problem = ScheduleProblem(df_classes, df_rooms, 3, 0)

    max_evaluations = 5
    population_size = 100 #Number of solutions(schedules) to create

    start_time = time.time()

    algorithm = NSGAII(
        problem=problem,
        population_size=population_size,
        offspring_population_size=100,
            mutation=PermutationSwapMutation(1.0 / problem.number_of_variables),
            crossover=PMXCrossover(0.5),
            #selection=BinaryTournamentSelection(
            #    MultiComparator([FastNonDominatedRanking.get_comparator(),
            #                        CrowdingDistance.get_comparator()])),
            termination_criterion=StoppingByEvaluations(max_evaluations=max_evaluations)
    )

    algorithm.run()
    result = algorithm.get_result()
    front = get_non_dominated_solutions(result)
    solutions = [j_solution.variables for j_solution in front]
    objectives = [j_solution.objectives for j_solution in front]
    print('Optimization ended')
    print('Number of solutions generated: ', len(front))
    print('Result: ', solutions)
    print('Objectives: ', objectives)
    print("--- %s seconds ---" % (time.time() - start_time))

    df_to_save = merge_solution(df_classes, df_rooms, solutions[0])
    df_to_save.to_csv('./test.csv', index=False, encoding="utf-8-sig")

    #open text file
    text_file = open("./test_solution.txt", "w")
    #write string to file
    text_file.write(str(solutions[0]))
    #close file
    text_file.close()

test_multi_files()
merge_files()
