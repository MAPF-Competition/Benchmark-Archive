# Generating Warehouse

## Introduction
This document outlines the process of generating warehouse maps used in the competition. The goal is to generate a map file given the usser-specified configurations.

Aside fomr the free space that robots can traverse, the warehouse map contains four components: the pickup stations, the storage blocks, the emitters, and the pillars.
In general, the layout of the warehouse map is a rectangule, with one pillar on each corner, pickup stations (with emitters) on four sides, and a rectangluar storage area in the center with storage blocks and corridors.

## Input Parameters
We use a `yaml` file to include all the parameters needed for generating a warehouse map, which contains:
- `mapW`: The width of the warehouse map
- `mapH`: The height of the warehouse map
- `mapName`: The output name of the warehouse map, which will be strored under the same directory as the `warehouse_generator.py`.
- `stationName`: The file name of the pickup station layout, see the following description.
- `stationNum`: The number of pickup stations in the warehouse map.
- `storageSize`: The size of the storage blocks in the format of `[width, height]`.
- `emitterW`: The distance between two consequtive emitters
- `corridorW`: The distance between two storage blocks.
- `pillarW`: The width of the pillar (the bird-view of a pillar is a square).
- `operW`: The distance between the pickup station and the storage area.

Please refer to our `warehouse_config.yaml` as an example.

## Layout for the Pickup Stations
We provide customized pickup station layout for the users. The layout file contains the width and the height of the pickup station, followed by the layout that should be of the same size as the provided width and height. The symbol used for the layout are as follows:
- `.`: free space (grid)
- `@`: blocked space (obstacle)
- `E`: emitter (the exact location for robots to pickup or drop their stuffs)

The layout in the file is based on the pickup station shown on the west (i.e., the left-hand side) of the warehouse map. Please refer to out `station.txt` as an example.

## Run the Program
Simply put all the files under the same directory and run the command
```
python warehouse_generator.py --config ./warehouse_config.yaml
```
