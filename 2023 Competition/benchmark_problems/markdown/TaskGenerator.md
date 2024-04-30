# Task Generation and Simulation

## Introduction
This document outlines the task generation and simulation process for a warehouse environment. The goal is to generate tasks for agents to perform, considering different kinds of tasks with specific probabilities. The simulation time is also considered, and an approach for handling "infinite" tasks is discussed.

## Task Generation Parameters
- `map`: The name of the map file representing the warehouse layout.
- Optional Parameters:
  - `n_tasks`: Number of tasks to generate (default: 10,000).
  - `task_type_rl`: Relative likelihood of selecting an 'E' (emitter/endpoint) or 'S' (service/storage) location (default: {E: 0.5, S: 0.5}).
  - `e_bucket_rl`: Relative likelihood of each 'E' bucket, divided into four buckets based on their location within the warehouse (default: {east: 0.25, south: 0.25, west: 0.25, north: 0.25}).
  - `s_bucket_rl`: Relative likelihood of each 'S' bucket, divided into 'k' buckets based on their minimum distance to any 'E' location (default: {b1: 1}).

## Version 1: Random Generation
In this version, all 'E' locations are put into one bucket, and all 'S' locations are put into another bucket. The relative likelihood of selecting an 'E' or an 'S' location is equal, resulting in the following distribution among the kinds of tasks that agents will be assigned:
- Probability of E->S or S->E tasks: 0.5
- Probability of E->E tasks: 0.25
- Probability of S->S tasks: 0.25

## Task Generation Process
1. Read the warehouse map from the provided file and record the 'E' and 'S' locations.
2. Determine the number of tasks to be generated based on the given `n_tasks` parameter.
3. Determine the task type ('E' or 'S') using the relative likelihood of 'E' and 'S'.
4. Determine the exact task location using the bucket settings and probabilities for each bucket. For the random version, there is only one bucket, and a location is randomly selected from that bucket.

## Version 2: Distribution on Average Distances
In this version, tasks are generated based on desired average distances between 'S' and 'E' locations. Each 'S' location is classified into buckets based on their average distance to 'E' locations. The probability of selecting a particular bucket is calculated, and tasks are generated accordingly.

### Task Generation Prep
1. Generate ranges for the average distances.
2. Given the number of buckets 'm', calculate the minimum `AVGDISTmin` and maximum `AVGDISTmax` average distances among all 'S' locations.
3. Divide the range [AVGDISTmin, AVGDISTmax] into 'm' ranges: {R0, R1, ..., Rm-1}.
4. Create 'm' buckets B={B0, B1, ..., Bm-1}, where each bucket can store multiple 'S' locations.
5. Create a list of portion numbers P={P0, P1, ..., Pm-1}, where P0 = 1 and Px = 1/2 * Px-1. These portion numbers determine the probability of selecting each bucket.

### Task Generation Process
1. Repeat the following procedure until the number of locations in the task file reaches the given number of tasks (`n_tasks`).
2. Generate a random number 'r' between 0 and 1.
3. If 'r' is less than 0.5, insert an 'E' location into the task file; otherwise, insert an 'S' location.
4. If 'r' indicates an 'S' location:
   a. Randomly select a bucket 'Bx' from B based on the probabilities in P.
   b. Randomly select an 'S' location 'Si' from Bx and insert it into the task file.

## Evaluation
The simulation time is set to 1 hour for each map, with 1 second per plan, resulting in 3600 timesteps. The task generation process will be evaluated based on the generated task distribution and adherence to specified probabilities.



