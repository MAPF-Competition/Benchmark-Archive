# -*- coding: UTF-8 -*-
"""Benchmark converter
Convert the MAPF instances in MAPF benchmark suite to task files
"""

import os
import sys
import logging
import argparse
from typing import List, Tuple, Dict
import json
import yaml
import random


class BenchmarkConverter:
    """Class for benchmark converter
    Input the map, the scens (either scen-even or scen-random), the number of agents,
    and the number of tasks. The converter will start from the first row of the scen.
    """

    def __init__(self, input_arg) -> None:
        print("===== Initialize Benchmark Converter =====")

        self.tasks:List[int]  = []     # all the tasks
        self.all_locs = []

        # Load configuration file
        self.config: Dict = {}

        self.config["scenFile"]:List[str] = input_arg.scenFile
        self.config["taskFile"]  = input_arg.taskFile
        self.config["mapFile"] = input_arg.mapFile
        assert self.config["mapFile"] is not None
        assert self.config["scenFile"] is not None
        self.config["map_name"] = self.config["mapFile"].split("/")[-1].split(".")[0]
        self.config["scen_name"] = self.config["scenFile"][0].split("/")[-2].split("-")[-1]




    def load_map_size(self):
        print("Get the size of map " + self.config["mapFile"])
        if not os.path.exists(self.config["mapFile"]):
            logging.error("\nNo map file is found!")
            sys.exit()

        with open(self.config["mapFile"], mode="r", encoding="utf-8") as fin:
            fin.readline()  # ignore "type"
            self.config["height"] = int(fin.readline().strip().split(' ')[1])
            self.config["width"]  = int(fin.readline().strip().split(' ')[1])
            fin.readline()


    def load_locations(self) -> List[Tuple[int,int]]:
        self.load_map_size()  # Add map width and height to self.config
        assert "height" in self.config.keys() and self.config["height"] > 0
        assert "width"  in self.config.keys() and self.config["width"] > 0

        output_loc:List[Tuple[int,int]] = []
        for _scen_ in self.config["scenFile"]:
            if not os.path.exists(_scen_):
                logging.error("\nNo scen path is found!")
                sys.exit()

            with open(_scen_, mode="r", encoding="utf-8") as fin:
                head:str = fin.readline().rstrip("\n").split(" ")[0]  # ignore the first line
                assert head == "version"  # we only process files from the MAPF suite
                for line in fin.readlines():
                    line_seg = line.split("\t")
                    cur_start:int = int(line_seg[5]) * self.config["width"] + int(line_seg[4])
                    cur_goal:int  = int(line_seg[7]) * self.config["width"] + int(line_seg[6])
                    if (cur_start == 3960 or cur_goal == 3960):
                        print("here:",_scen_)
                    output_loc.append((cur_start, cur_goal))

        return output_loc


    def generate_txt(self, num_tasks, num_files):
        for i in range(num_files):
            with open(self.config["taskFile"] + str(i) + ".task", mode="w", encoding="utf-8") as fout:
                fout.write(str(num_tasks) + "\n")
                tasks = random.choices(self.all_locs, k=num_tasks)
                # tasks = random.sample(self.all_locs, k=num_tasks)
                for j in tasks:
                    fout.write(str(j) + "\n")
        


    def convert_to_tasks(self):
        all_locations:List[Tuple[int,int]] = self.load_locations()
        for sloc, gloc in all_locations:
            self.all_locs.append(sloc)
            self.all_locs.append(gloc)




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Take config.yaml as input!")
    parser.add_argument("--map", dest="mapFile", type=str, help="path to the map file",
                        default="~/mapf_benchmark/mapf-map/random-32-32-20.map")
    parser.add_argument("--scen", dest="scenFile", type=str, help="path to all the scen files",
                        nargs="*", default="~/mapf_benchmark/scen-even/random-32-32-20-even-1.scen")
    parser.add_argument("--tf", dest="taskFile", type=str, default=None, help="output task file")
    parser.add_argument("--nt", dest="numTasks", type=int, default=1000, help="number of tasks")

    parser.add_argument("--nf", dest="numFiles", type=int, default=1, help="number of files")

    args = parser.parse_args()

    benchmark_converter = BenchmarkConverter(input_arg=args)
    benchmark_converter.convert_to_tasks()
    benchmark_converter.generate_txt(args.numTasks, args.numFiles)
    # benchmark_converter.verify()
