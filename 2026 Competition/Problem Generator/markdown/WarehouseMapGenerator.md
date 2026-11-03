# Generating Warehouse Map

## Introduction
This document outlines the process of generating warehouse maps used in the competition. The goal is to generate a map file given the usser-specified configurations.

Aside from the free space that robots can traverse, the warehouse map contains four components: the pickup stations, the storage blocks, the emitters, and the pillars.
In general, the layout of the warehouse map is a rectangle, with one pillar on each corner, pickup stations (with emitters) on four sides, and a rectangular storage area in the center with storage blocks and corridors.

## Input Parameters
Either use command line arguments or a `yaml` file to include all the parameters needed for generating a warehouse map, which contains:
- `--mapWidth MAP_WIDTH`: (Required if --config is not provided) Width of the warehouse.
- `--mapHeight MAP_HEIGHT`: (Required if --config is not provided) Height of the warehouse.
- `--output MAP_NAME`: (Required if --config is not provided) Name of the generated warehouse map.
- `--stationConfig`: (Required if --config is not provided) The file name of the pickup station layout, see the following description.
- `--stationNumber STATION_NUM`: (Required if --config is not provided) Number of pickup stations to be added in the warehouse.
- `--stationDistance (default 2)`: distance between two consecutive emitters
- `--corridorWidth (default 1)`:  distance between two storage blocks
- `--pillarWidth (default 4)`: width of the pillar
- `--operWidth (default 5)`: distance between the pickup station and the sotrage area
- `--storageSize (default [3,2])`: (width, height) of the storage

All the paths should be relative to the directory where `warehouse_map_generator.py` is located.

Please refer to our `fulfillment_config.yaml` as an example.

## Layout for the Pickup Stations
We provide customized pickup station layout for the users. The layout file contains the width and the height of the pickup station, followed by the layout that should be of the same size as the provided width and height. The symbols used for the layout are as follows:
- `.`: free space (traversable)
- `@`: blocked space (obstacle)
- `E`: emitter point (traversable)
- `S`: service point (traversable)

Emitter points and service points are potential tasks(errands) locations.
The layout in the file is based on the pickup station shown on the west (i.e., the left-hand side) of the warehouse map. Please refer to the `picking_station.txt` as an example.

## Run the Program
Simply put all the files under the same directory and run the command
```
python ./script/warehouse_map_generator.py --config ./fulfillment_config.yaml
```
