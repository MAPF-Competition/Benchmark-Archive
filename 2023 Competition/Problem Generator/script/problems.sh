#!/bin/bash

for i in {0..24};
do
python3.7 benchmark_generator.py --map ~/Codes/research/traffic-mapf/benchmark-lifelong/maps/$1.map --task_file ~/Codes/research/traffic-mapf/benchmark-lifelong/tasks/${1}_$i.tasks --problemName ${1}_$i --team_sizes `seq ${2} ${3} ${4}` --benchmark_folder ~/Codes/research/traffic-mapf/benchmark-lifelong/ --tasks_reveal 1 --taskAssignmentStrategy roundrobin
done
