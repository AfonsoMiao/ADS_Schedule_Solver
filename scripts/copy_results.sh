#!/bin/sh
container_id=$(docker ps -aqf "name=schedule_solver")
docker cp $container_id:/code/output/final_schedule.csv ../output/
docker cp $container_id:/code/output/final_schedule_optimized.csv ../output/
docker cp $container_id:/code/output/fitness_report.csv ../output/
docker cp $container_id:/code/output/total_time.txt ../output/
docker cp $container_id:/code/output/total_time_optimized.txt ../output/