# Benchmark Problem Generators

This repo contains Python scripts to generate benchmark problem files used in the  [2023 LoRR competition](https://www.leagueofrobotrunners.org/).
This readme gives a simple introduction. For detailed usage instructions and examples, please refer to the [Tutorial](./markdown/Tutorial.md).

## Installation and Requirements

Requirements:
- Python 3.10 or higher
- easydict
  
To get started with the scripts, you need to install the easydict package. You can install it using pip:
```shell
pip install easydict
```

## Benchmark Generator

The script `benchmark_generator.py` is used to create new problem instances. At a minimum, the program requires as input a map file, the sizes of agent teams, and the description of the task set. In the simplest usage, only the size of the task set is required and individual errands are randomly generated. We show this usage below:

```shell
python ./script/benchmark_generator.py  --mapFile  ./script/sortation_large.map  --problemName randomTest --taskNum 5 --teamSizes 100 200 300 --benchmark_folder ./test
```

It is also possible to create problem instances using pre-generated task sets, which are specialised for certain types of maps (e.g. warehouse, see below). We show this usage below:
```shell
python ./script/benchmark_generator.py  --mapFile ./script/sortation_large.map  --problemName warehouseTest --taskFile ./script/sortation_large.tasks --teamSizes 100 200 300 --benchmark_folder ./test
```

## Warehouse Map Generator

The script `warehouse_map_generator.py` is used to create warehouse maps. We distinguish two types of warehouses: sortation and fulfilment. In the example below,
we show how to generate a sortation map. The parameters of the map are given in a pre-specified configuration file (they can also be specified as command line arguments):

```shell
python ./script/warehouse_map_generator.py --config ./sortation_medium.yaml
```
or with command line arguments:

```shell
python ./script/warehouse_map_generator.py --mapWidth 200 --mapHeight 140 --output "sortation_medium.map" --stationConfig "sortation_emitter.txt" --storageSize 1 1 --stationDistance 1
```

## Warehouse Task Generator

The script `warehouse_task_generator.py` is used to generate customised task sets for warehouse maps. The task sets are generated according to a specific distribution.
In the example below, we show how to generate a task set where tasks are categorised into 5 buckets according to the distances between distinguished types of locations on the warehouse map (emitter points and service points):

```shell
 python ./script/warehouse_task_generator.py --mapFile ./script/sortation_small.map --taskNum 100 --taskFile ./tasks.tasks --m_buckets 5
```
