# Generating Benchmark Problems

## Introduction
This document outlines the process of generating benchmark problems using existing map and task files along with specified input parameters. The goal is to create multiple benchmark problem files, each with a different number of agents, following a specified task assignment strategy.

## Input Parameters
- `existing_map_file`: The name of the existing map file representing the warehouse layout.
- `existing_task_file`: The name of the existing task file containing generated tasks for the warehouse environment.
- `num_agents`: A list of integers representing the number of agents (team size) for which benchmark problems should be generated (e.g., [100, 200, 300, ...]).
- `target_folder`: The directory where the resulting problem files will be placed.
- `problem_name`: The prefix name of the resulting problem files.
- `numTasksReveal`: The number of tasks revealed to agents at the beginning of the simulation (default: 1).
- `minEPT`: The minimum number of errands per task (default:1)
- `maxEPT`: The maximum number of errands per task (default:3)
<!-- - `taskAssignmentStrategy`: The task assignment strategy to be used (default: round-robin). -->

## Output Files Structure
The following files will be generated in the specified `target_folder`:

### Benchmark Problem Files
- `[Problem Name]_100.json`: Benchmark problem file with 100 agents.
- `[Problem Name]_200.json`: Benchmark problem file with 200 agents.
- `[Problem Name]_300.json`: Benchmark problem file with 300 agents.
- ...

### Agents Files
- `[Problem Name]_team_100.agents`: File containing information about agents for the problem with 100 agents.
- `[Problem Name]_team_200.agents`: File containing information about agents for the problem with 200 agents.
- `[Problem Name]_team_300.agents`: File containing information about agents for the problem with 300 agents.
- ...

### Maps File
- A copy of the existing map file will be included in the output folder.

### Tasks File
- A copy of the existing task file will be included in the output folder.

## Input JSON Format
Refer to the [Input/Output Format](https://github.com/MAPF-Competition/Start-Kit/blob/main/Input_Output_Format.md) specification in the benchmark problems git repository for examples and specifications of the input JSON file.

## Task Generation Process
The benchmark problem generation process involves creating separate problem files for each specified number of agents. The task assignment strategy, such as round-robin, will be applied to distribute the tasks among the agents.



