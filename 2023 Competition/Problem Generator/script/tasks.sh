#!/bin/bash

for i in {0..25};
do
python3.10 task_generator.py --map ~/Codes/research/traffic-mapf/benchmark-lifelong/maps/sortation_small.map --n_tasks 50000 --output ~/Codes/research/traffic-mapf/benchmark-lifelong/tasks/sortation_small_$i.task
done
