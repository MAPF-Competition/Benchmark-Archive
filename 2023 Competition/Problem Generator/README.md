# Benchmark Problem Generators

This repo contains Python scripts to generate benchmark problem files used in the  [2023 LoRR competition](https://www.leagueofrobotrunners.org/).

## Generators Overview
### 1. Random Benchmark Generator: Generates random problems
```shell
python3 ./script/benchmark_generator.py  --mapFile  /random.domain/maps/random-32-32-20.map  --problemName randomTest --taskNum 5 --team_sizes 100 200 300 --benchmark_folder ./test --isWarehouse False
```

### 2. Generate Benchmarks for Warehouse Maps

#### 2.1 Warehouse Map Generator: Generates warehouse layouts.
**Example Usage：**
```shell
python ./script/warehouse_map_generator.py --config ./scripts/sortation_config.yaml
```

#### 2.2. Warehouse Task Generator: Generates task files based on the map.
**Example Usage：**
```shell
 python3 ./script/warehouse_task_generator.py --mapFile ./2023-main/warehouse.domain/maps/warehouse_large.map  --taskNum 100 --taskFile ./tasks.tasks --m_buckets 5
```
#### 2.3. Benchmark Generator using the task files.
**Example Usage：**
```shell
python3 ./script/benchmark_generator.py  --mapFile ./2023-main/warehouse.domain/maps/warehouse_large.map  --problemName warehouseTest --taskFile ./tasks.tasks  --team_sizes 100 200 300 --benchmark_folder ./test
```
For detailed usage instructions and examples, please refer to the [Tutorial](./markdown/Tutorial.md).

## Tutorial
For step-by-step instructions and detailed usage examples of each generator script, please refer to the [Tutorial](./markdown/Tutorial.md).
