#!/bin/sh
docker build -t schedule_solver ../
docker run --name "schedule_solver_container" -d schedule_solver