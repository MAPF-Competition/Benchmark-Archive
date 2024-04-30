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


class BenchmarkConverter:
    """Class for benchmark converter
    Input the map, the scens (either scen-even or scen-random), the number of agents,
    and the number of tasks. The converter will start from the first row of the scen.
    """

    def __init__(self, input_arg) -> None:
        print("===== Initialize Benchmark Converter =====")

        self.start_loc:List[int] = []  # start locations
        self.tasks:List[int]  = []     # all the tasks

        # Load configuration file
        self.config: Dict = {}
        if input_arg.config is not None:  # Load the yaml file
            config_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), input_arg.config)
            with open(config_dir, mode="r", encoding="utf-8") as fin:
                self.config = yaml.load(fin, Loader=yaml.FullLoader)
        else:  #  Load the input arguments
            self.config["mapFile"]:str = input_arg.mapFile
            self.config["scenFile"]:List[str] = input_arg.scenFile
            self.config["teamSize"] = input_arg.teamSize
            if input_arg.agentFile is not None:
                self.config["agentFile"] = input_arg.agentFile
            if input_arg.taskFile is not None:
                self.config["taskFile"]  = input_arg.taskFile
            if input_arg.probFile is not None:
                self.config["probFile"] = input_arg.probFile
            if input_arg.taskNum is not None:
                self.config["taskNum"] = input_arg.taskNum
            if input_arg.revealNum is not None:
                self.config["revealNum"] = input_arg.revealNum

        assert self.config["teamSize"] is not None
        assert self.config["mapFile"] is not None
        assert self.config["scenFile"] is not None
        self.config["map_name"] = self.config["mapFile"].split("/")[-1].split(".")[0]
        self.config["scen_name"] = self.config["scenFile"][0].split("/")[-2].split("-")[-1]
        assert self.config["scen_name"] in ["even", "random"]

        # Set the default values in self.config
        if "taskNum" not in self.config.keys():
            self.config["taskNum"] = -1  # put all goal locations into the task
        if "revealNum"  not in self.config.keys():
            self.config["revealNum"] = 1
        if "ins_id" not in self.config.keys():
            self.config["ins_id"]:List[int] = [i+1 for i in range(25)]  # from 1 to 25
        if "agentFile" not in self.config.keys():
            self.config["agentFile"] = "./" + self.config["map_name"] + "_" +\
                self.config["scen_name"] + "_" + str(self.config["teamSize"]) + "_agents.txt"
        if "taskFile" not in self.config.keys():
            self.config["taskFile"] = "./" + self.config["map_name"] + "_" +\
                self.config["scen_name"] + "_" + str(self.config["teamSize"]) + "_tasks.txt"
        if "probFile" not in self.config.keys():
            self.config["probFile"] = "./" + self.config["map_name"] + "_" +\
                self.config["scen_name"] + "_" + str(self.config["teamSize"]) + "_problem.json"

        assert self.config["teamSize"] > 0
        assert self.config["taskNum"] > -2
        assert len(self.config["scenFile"]) > 0
        assert self.config["probFile"].split(".")[-1] == "json"


    def load_map_size(self):
        print("Get the size of map " + self.config["mapFile"])
        if not os.path.exists(self.config["mapFile"]):
            logging.error("\nNo map file is found!")
            sys.exit()

        with open(self.config["mapFile"], mode="r", encoding="utf-8") as fin:
            fin.readline()  # ignore "type"
            self.config["height"] = int(fin.readline().strip().split(' ')[1])
            self.config["width"]  = int(fin.readline().strip().split(' ')[1])


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
                    output_loc.append((cur_start, cur_goal))

        return output_loc


    def generate_txt(self):
        # assert self.config["teamSize"] == len(self.start_loc)
        with open(self.config["agentFile"], mode="w", encoding="utf-8") as fout:
            fout.write(str(len(self.start_loc)) + "\n")
            for _loc_ in self.start_loc:
                fout.write(str(_loc_) + "\n")

        with open(self.config["taskFile"], mode="w", encoding="utf-8") as fout:
            fout.write(str(len(self.tasks)) + "\n")
            for _loc_ in self.tasks:
                fout.write(str(_loc_) + "\n")

        problem_file = {
            "mapFile": self.config["mapFile"],
            "agentFile": self.config["agentFile"],
            "teamSize": self.config["teamSize"],
            "taskFile": self.config["taskFile"],
            "numTasksReveal": self.config["revealNum"],
            "taskAssignmentStrategy": "roundrobin"
        }
        with open(self.config["probFile"], mode="w", encoding="utf-8") as fout:
            json.dump(problem_file, fout, indent=4)


    def convert_to_tasks(self):
        all_locations:List[Tuple[int,int]] = self.load_locations()
        for sloc, gloc in all_locations:
            self.start_loc.append(sloc)
            self.tasks.append(gloc)


    # def convert_to_tasks(self):
    #     all_locations:List[Tuple[int,int]] = self.load_locations()
    #     num_all_locs = len(all_locations)
    #     agent_tasks:Dict[int,List[int]] = {}

    #     # Generate start locations and the initial tasks, one for each agent
    #     for aid in range(self.config["teamSize"]):
    #         cur_loc:Tuple[int,int] = all_locations.pop(0)
    #         self.start_loc[aid]:int = cur_loc[0]
    #         agent_tasks[aid] = [cur_loc[1]]
    #     assert len(all_locations) + self.config["teamSize"] == num_all_locs

    #     # Generate other tasks from all_locations
    #     ag_cnt = 0
    #     for (sloc, gloc) in all_locations:
    #         aid = ag_cnt % self.config["teamSize"]
    #         agent_tasks[aid].append(sloc)
    #         agent_tasks[aid].append(gloc)
    #         ag_cnt += 1

    #     # Collect the tasks in a round robin order
    #     has_task:List[bool] = [True for _ in range(self.config["teamSize"])]
    #     ag_cnt = 0
    #     while any(has_task):
    #         aid = ag_cnt % self.config["teamSize"]
    #         if agent_tasks[aid]:  # There is still elements in the list
    #             self.tasks.append(agent_tasks[aid].pop(0))
    #         else:
    #             has_task[aid] = False
    #         ag_cnt += 1

    # def verify(self):
    #     debug_tasks:List[int] = []
    #     with open(self.config["agentFile"], mode="r", encoding="utf-8") as fin:
    #         fin.readline()  # ignore the number of agents
    #         for _line_ in fin.readlines():
    #             debug_tasks.append(int(_line_.rstrip()))
    #     with open(self.config["taskFile"], mode="r", encoding="utf-8") as fin:
    #         fin.readline()  # ignore the number of tasks
    #         for _line_ in fin.readlines():
    #             debug_tasks.append(int(_line_.strip()))

    #     debug_start = []
    #     debug_goal  = []
    #     for _tid_, _task_ in enumerate(debug_tasks):
    #         if (_tid_ // self.config["teamSize"]) % 2 == 0:
    #             debug_start.append(_task_)
    #         else:
    #             debug_goal.append(_task_)

    #     for _scen_ in self.config["scenFile"]:
    #         with open(_scen_, mode="r", encoding="utf-8") as fin:
    #             fin.readline()
    #             for _line_ in fin.readlines():
    #                 _seg_ = _line_.split("\t")
    #                 _start_:int = int(_seg_[5]) * self.config["width"] + int(_seg_[4])
    #                 _goal_ :int = int(_seg_[7]) * self.config["width"] + int(_seg_[6])
    #                 _dbs_ = debug_start.pop(0)
    #                 _dbg_ = debug_goal.pop(0)
    #                 assert _start_ == _dbs_
    #                 assert _goal_  == _dbg_


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Take config.yaml as input!")
    parser.add_argument("--config", type=str, help="path to the configuration file", default=None)
    parser.add_argument("--map", dest="mapFile", type=str, help="path to the map file",
                        default="~/mapf_benchmark/mapf-map/random-32-32-20.map")
    parser.add_argument("--scen", dest="scenFile", type=str, help="path to all the scen files",
                        nargs="*", default="~/mapf_benchmark/scen-even/random-32-32-20-even-1.scen")
    parser.add_argument("--af", dest="agentFile", type=str, default=None, help="output agent file")
    parser.add_argument("--tf", dest="taskFile", type=str, default=None, help="output task file")
    parser.add_argument("--pf", dest="probFile", type=str, default=None, help="problem file")
    parser.add_argument("--ts", dest="teamSize", type=int, default=None, help="number of agents")
    parser.add_argument("--nt", dest="taskNum", type=str, default=None, help="number of tasks")
    parser.add_argument("--nr", dest="revealNum", type=int, default=None,
                        help="number of revealed tasks")
    args = parser.parse_args()

    benchmark_converter = BenchmarkConverter(input_arg=args)
    benchmark_converter.convert_to_tasks()
    benchmark_converter.generate_txt()
    # benchmark_converter.verify()
