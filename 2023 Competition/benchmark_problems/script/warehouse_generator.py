# -*- coding: UTF-8 -*-
"""Warehouse Generator
Generate warehouse with pickup stations and storages (shelves)
"""

import os
import argparse
from typing import Dict
import copy
import yaml


class WarehouseGenerator:
    """Class for the warehouse generator
    Inputs: width, height, number of pickup stations
    """
    def __init__(self, input_arg) -> None:
        print("===== Initialize warehouse generator =====")

        # Load configuration file
        self.config: Dict = {}
        if input_arg.config is not None:  # Load the yaml file
            config_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), input_arg.config)
            with open(config_dir, mode="r", encoding="utf-8") as fin:
                self.config = yaml.load(fin, Loader=yaml.FullLoader)
        else:  #  Load the input arguments
            self.config["mapW"] = input_arg.mapW
            self.config["mapH"] = input_arg.mapH
            self.config["mapName"] = input_arg.mapName
            self.config["stationNum"] = input_arg.stationNum

        assert self.config["mapW"] is not None
        assert self.config["mapH"] is not None
        assert self.config["mapName"] is not None
        assert self.config["stationNum"] is not None

        # Initialize an empty warehouse
        self.warehouse = []
        for _ in range(self.config["mapH"]):
            tmp_list = ["." for _ in range(self.config["mapW"])]
            self.warehouse.append(tmp_list)
        self.max_raw = self.config["mapH"] - 1
        self.max_col = self.config["mapW"] - 1


        # Initialize the pillars
        for i in range(self.config["pillarW"]):
            for j in range(self.config["pillarW"]):
                self.warehouse[i][j] = "@"
                self.warehouse[self.max_raw-i][j] = "@"
                self.warehouse[i][self.max_col-j] = "@"
                self.warehouse[self.max_raw-i][self.max_col-j] = "@"

        # Initialize the station
        self.station = []
        self.cur_path = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(self.cur_path, self.config["stationName"]),
                  mode="r", encoding="utf-8") as fin:
            self.config["stationH"] = int(fin.readline().strip().split(" ")[1])
            self.config["stationW"] = int(fin.readline().strip().split(" ")[1])
            for _line_ in fin.readlines():
                self.station.append(list(_line_.strip()))
            assert len(self.station) == self.config["stationH"]
            assert len(self.station[0]) == self.config["stationW"]

        #copy for record as block padding guide map
        self.warehouse_record = copy.deepcopy(self.warehouse)
        self.map_row_end = self.config["mapH"] - self.config["pillarW"]
        self.map_column_end = self.config["mapW"] - self.config["pillarW"]

        # Simplified version
        self.has_station = {"E": False, "S": False, "W": False, "N": False}


    def print_map(self):
        for i in range(self.config["mapH"]):
            print("".join(self.warehouse[i]))
        print("-------------------------------------------")


    def load_stations(self):
        sta_cnt = 0  # Station counter

        # Start from the west side
        cur_raw = self.config["pillarW"] + 1
        # if sta_cnt < self.config["stationNum"]:  #add paddings for the start
        #     for i in range(1,self.config["operW"]+1):
        #         if cur_raw-i >=0:
        #             for j in range(STATION_SIZE[1]+self.config["operW"]):
        #                 if self.warehouse_record[cur_raw-i][j] != '@':
        #                     self.warehouse_record[cur_raw-i][j] = 'P'

        adding = False
        while (cur_raw + self.config["stationH"] + self.config["pillarW"]) < self.config["mapH"] \
            and sta_cnt < self.config["stationNum"]:
            adding = True
            # #add block record 'B' for station
            # for i in range(STATION_SIZE[1] + self.config["emitterW"]*2):
            #     for j in range(STATION_SIZE[0]):
            #         self.warehouse_record[cur_raw+i][j] = 'B'
            #     for k in range(self.config["operW"]):
            #         self.warehouse_record[cur_raw+i][STATION_SIZE[0]+k] = 'P'

            # Create a block for station and the emitters
            # self.warehouse[cur_raw][1] = "E"
            # for i in range(STATION_SIZE[1]):  # station width
            #     for j in range(STATION_SIZE[0]):  # station height
            #         self.warehouse[cur_raw+1+i][j] = "@"
            # if STATION_SIZE[0] > 0 and STATION_SIZE[1] > 0:  # Add another emiter
            #     self.warehouse[cur_raw+1+STATION_SIZE[1]][1] = "E"
            for _w_ in range(self.config["stationW"]):
                for _h_ in range(self.config["stationH"]):
                    self.warehouse[cur_raw+ _h_][_w_] = self.station[_h_][_w_]
            sta_cnt += 1
            self.has_station["W"] = True
            cur_raw += (self.config["emitterW"] + self.config["stationH"])

        # if adding:  #add paddings for the end
        #     for i in range(self.config["operW"]):
        #         if cur_raw+i < self.config["mapH"]:
        #             for j in range(STATION_SIZE[1]+self.config["operW"]):
        #                 if self.warehouse_record[cur_raw+i][j] != '@':
        #                     self.warehouse_record[cur_raw+i][j] = 'P'

        # Move to the south side
        cur_col = self.config["pillarW"] + 1
        # if sta_cnt < self.config["stationNum"]:  #add paddings for the start
        #     for i in range(1,STATION_SIZE[1]+self.config["operW"]+1):
        #         for j in range(1,self.config["operW"]+1):
        #             if cur_col-j>=0:
        #                 if self.warehouse_record[self.config["mapH"]-i][cur_col-j] != '@':
        #                     self.warehouse_record[self.config["mapH"]-i][cur_col-j]  = 'P'

        adding = False
        while (cur_col + self.config["stationH"] + self.config["pillarW"]) < self.config["mapW"] \
            and sta_cnt < self.config["stationNum"]:
            adding = True
            # #add block record 'B' for station
            # for i in range(STATION_SIZE[1] + self.config["emitterW"]*2):
            #     for j in range(STATION_SIZE[0]):
            #         self.warehouse_record[self.config["mapH"]-j-1][cur_col+i] = 'B'
            #     for k in range(self.config["operW"]):
            #         self.warehouse_record[self.config["mapH"]-k-STATION_SIZE[0]-1][cur_col+i] = 'P'

            # Create a block for station and the emitters
            # self.warehouse[self.max_raw-1][cur_col] = "E"
            # for i in range(STATION_SIZE[1]):  # station width
            #     for j in range(STATION_SIZE[0]):  # station height
            #         self.warehouse[self.max_raw-j][cur_col+1+self.config["emitterW"]+i] = "@"
            # if STATION_SIZE[0] > 0 and STATION_SIZE[1] > 0:  # Add another emitter
            #     self.warehouse[self.max_raw-1][cur_col+1+self.config["emitterW"]+STATION_SIZE[1]] = "E"
            for _w_ in range(self.config["stationW"]):
                for _h_ in range(self.config["stationH"]):
                    self.warehouse[self.max_raw-_w_][cur_col+_h_] = self.station[_h_][_w_]
            sta_cnt += 1
            self.has_station["S"] = True
            cur_col += (self.config["emitterW"] + self.config["stationH"])

        # if adding:  #add paddings for the end
        #     for i in range(self.config["operW"]):
        #         if cur_col+i < self.config["mapW"]:
        #             for j in range(STATION_SIZE[1]+self.config["operW"]):
        #                 if self.warehouse_record[self.config["mapH"]-j-1][cur_col+i] != '@':
        #                     self.warehouse_record[self.config["mapH"]-j-1][cur_col+i] = 'P'

        # Move to the east side
        cur_raw = self.max_raw - self.config["pillarW"] - 1
        # if sta_cnt < self.config["stationNum"]:  #add paddings for the start
        #     for i in range(1,STATION_SIZE[1]+self.config["operW"]+1):
        #         for j in range(1,self.config["operW"]+1):
        #             if cur_raw+j < self.config["mapH"]:
        #                 if self.warehouse_record[cur_raw+j][self.config["mapW"]-i] != '@':
        #                     self.warehouse_record[cur_raw+j][self.config["mapW"]-i]  = 'P'

        adding = False
        while (cur_raw - self.config["stationH"] - self.config["pillarW"]) >= 0 \
            and sta_cnt < self.config["stationNum"]:
            adding = True
            # #add block record 'B' for station
            # for i in range(STATION_SIZE[1] + self.config["emitterW"]*2):
            #     for j in range(STATION_SIZE[0]):
            #         self.warehouse_record[cur_raw-i][self.config["mapW"]-j-1] = 'B'
            #     for k in range(self.config["operW"]):
            #         self.warehouse_record[cur_raw-i][self.config["mapW"]-k-STATION_SIZE[0]-1] = 'P'

            # Create a block for station and the emitters
            # self.warehouse[cur_raw][self.max_col-1] = "E"
            # for i in range(STATION_SIZE[1]):  # station width
            #     for j in range(STATION_SIZE[0]):  # station height
            #         self.warehouse[cur_raw-1-self.config["emitterW"]-i][self.max_col-j] = "@"
            # if STATION_SIZE[0] > 0 and STATION_SIZE[1] > 0:  # Add another emitter
            #     self.warehouse[cur_raw-1-self.config["emitterW"]-STATION_SIZE[1]][self.max_col-1] = "E"
            for _w_ in range(self.config["stationW"]):
                for _h_ in range(self.config["stationH"]):
                    self.warehouse[cur_raw - _h_][self.max_col-_w_] = self.station[_h_][_w_]
            sta_cnt += 1
            self.has_station["E"] = True
            cur_raw -= (self.config["emitterW"] + self.config["stationH"])

        # if adding:  #add paddings for the end
        #     for i in range(self.config["operW"]):
        #         if cur_raw-i >= 0:
        #             for j in range(STATION_SIZE[1]+self.config["operW"]):
        #                 if self.warehouse_record[cur_raw-i][self.config["mapW"]-j-1] != '@':
        #                     self.warehouse_record[cur_raw-i][self.config["mapW"]-j-1] = 'P'

        # Move to the north side
        cur_col = self.max_col - self.config["pillarW"] - 1
        # if sta_cnt < self.config["stationNum"]:  #add paddings for the start
        #     for i in range(1,self.config["operW"]+1):
        #         for j in range(STATION_SIZE[1]+self.config["operW"]):
        #             if self.warehouse_record[j][self.config["mapW"]-i] != '@':
        #                 self.warehouse_record[j][self.config["mapW"]-i] = 'P'

        adding = False
        while (cur_col - self.config["stationH"] - self.config["pillarW"]) >= 0 \
            and sta_cnt < self.config["stationNum"]:
            adding = True
            # #add block record 'B' for station
            # for i in range(STATION_SIZE[1] + self.config["emitterW"]*2):
            #     for j in range(STATION_SIZE[0]):
            #         self.warehouse_record[j][cur_col-i-1] = 'B'
            #     for k in range(self.config["operW"]):
            #         self.warehouse_record[STATION_SIZE[1]+k][cur_col-i-1] = 'P'

            # Create a block for station and the emitters
            # self.warehouse[1][cur_col] = "E"
            # for i in range(STATION_SIZE[1]):  # station width
            #     for j in range(STATION_SIZE[0]):  # station height
            #         self.warehouse[j][cur_col-1-self.config["emitterW"]-i] = "@"
            # if STATION_SIZE[0] > 0 and STATION_SIZE[1] > 0:  # Add another emitter
            #     self.warehouse[1][cur_col-1-self.config["emitterW"]-STATION_SIZE[1]] = "E"
            for _w_ in range(self.config["stationW"]):
                for _h_ in range(self.config["stationH"]):
                    self.warehouse[_w_][cur_col-_h_] = self.station[_h_][_w_]
            sta_cnt += 1
            self.has_station["N"] = True
            cur_col -= (self.config["emitterW"] + self.config["stationH"])

        # if adding:  #add paddings for the end
        #     for i in range(self.config["operW"]):
        #         if cur_col-i >= 0:
        #             for j in range(STATION_SIZE[1]+self.config["operW"]):
        #                 if self.warehouse_record[j][cur_col-i] != '@':
        #                     self.warehouse_record[j][cur_col-i] = 'P'


    def load_storages(self):
        start_raw = self.config["stationW"] + self.config["operW"] \
            if self.has_station["N"] else self.config["pillarW"]
        start_col = self.config["stationW"] + self.config["operW"] \
            if self.has_station["W"] else self.config["pillarW"]
        end_raw = self.config["mapH"]-self.config["stationW"]-self.config["operW"] \
            if self.has_station["S"] else self.config["mapH"] - self.config["pillarW"]
        end_col = self.config["mapW"]-self.config["stationW"]-self.config["operW"] \
            if self.has_station["E"] else self.config["mapW"] - self.config["pillarW"]

        for i in range(start_raw, end_raw,
                       self.config["storageSize"][1]+self.config["corridorW"]):
            for j in range(start_col, end_col,
                           self.config["storageSize"][0]+self.config["corridorW"]):
                if i+self.config["storageSize"][1] > end_raw or \
                    j+self.config["storageSize"][0] > end_col:
                    continue
                for ii in range(self.config["storageSize"][1]):
                    self.warehouse[i+ii][j-1] = "S"
                    self.warehouse[i+ii][j+self.config["storageSize"][0]] = "S"
                    for jj in range(self.config["storageSize"][0]):
                        self.warehouse[i+ii][j+jj] = "@"
                        if ii == 0:
                            self.warehouse[i+ii-1][j+jj] = "S"
                        elif ii == self.config["storageSize"][1]-1:
                            self.warehouse[i+ii+1][j+jj] = "S"

                #update map actual end row and column in self
                self.map_row_end = i+self.config["storageSize"][1]+1
                self.map_column_end = j+self.config["storageSize"][0]


    def check_fillin(self,row_start,row_end,column_start,column_end):
        for i in range(row_start,row_end):
            if i >= self.config["mapH"] or i < 0:
                return False
            for j in range(column_start,column_end):
                if j >= self.config["mapW"] or j < 0:
                    return False
                if self.warehouse_record[i][j] !=  "." and self.warehouse_record[i][j] !=  "S":
                    return False
        return True


    # def load_more_storages(self):
    #     start_raw_fix = STATION_SIZE[0] + self.config["operW"] if self.has_station["N"] else self.config["pillarW"]
    #     start_col_fix = STATION_SIZE[0] + self.config["operW"] if self.has_station["W"] else self.config["pillarW"]
    #     end_raw_fix = self.map_row_end
    #     end_col_fix = self.map_column_end

    #     start_raw= start_raw_fix - 1
    #     start_col= start_col_fix - 1

    #     #fill in north
    #     for col in range(start_col+1,end_col_fix-self.config["storageSize"][0]+1,self.config["storageSize"][0]+1):
    #         for row in range(start_raw-1,self.config["storageSize"][1]-1,-1*(self.config["storageSize"][1]+1)):
    #             #check if current range can be fill or not
    #             if self.check_fillin(row-self.config["storageSize"][1],row+1,col,col+self.config["storageSize"][0]+1):
    #                 #add the storage line by line
    #                 for h in range(self.config["storageSize"][1]):
    #                     if col == start_col+1:
    #                         self.warehouse[row-h][col-1] = 'S'
    #                     for i in range(self.config["storageSize"][0]):
    #                         self.warehouse[row-h][col+i] = '@'
    #                     self.warehouse[row-h][col+self.config["storageSize"][0]] = 'S'
    #                 for i in range(self.config["storageSize"][0]):
    #                     self.warehouse[row-self.config["storageSize"][1]][col+i] = 'S'

    #     start_raw = start_raw_fix-1
    #     end_col = end_col_fix
    #     #fill in east
    #     for col in range(end_col+1,self.config["mapW"],self.config["storageSize"][0]+1):
    #         for row in range(start_raw,end_raw_fix - self.config["storageSize"][1],self.config["storageSize"][1]+1):
    #             #check if current range can be fill or not
    #             if self.check_fillin(row,row+STATION_SIZE[1]+1,col,col+self.config["storageSize"][0]+1):
    #                 #add the storage line by line
    #                 for i in range(self.config["storageSize"][0]):
    #                     self.warehouse[row][col+i] = 'S'
    #                 for h in range(self.config["storageSize"][1]):
    #                     self.warehouse[row+h+1][col+self.config["storageSize"][0]] = 'S'
    #                     for i in range(self.config["storageSize"][0]):
    #                         self.warehouse[row+h+1][col+i] = '@'
    #                 for i in range(self.config["storageSize"][0]):
    #                     self.warehouse[row+self.config["storageSize"][1]+1][col+i] = 'S'


    #     end_raw = end_raw_fix - 1
    #     start_col = start_col_fix
    #     # fill in south
    #     for col in range(self.config["mapW"]-1,start_col-self.config["storageSize"][0],-1*(self.config["storageSize"][0]+1)):
    #         for row in range(end_raw,len(self.warehouse),self.config["storageSize"][1]+1):
    #             # check if current range can be fill or not
    #             if self.check_fillin(row,row+STATION_SIZE[1]+1,col - self.config["storageSize"][0] - 1,col):
    #                 # add the storage line by line
    #                 for i in range(self.config["storageSize"][0]):
    #                     self.warehouse[row][col-i-1] = 'S'
    #                 for h in range(self.config["storageSize"][1]):
    #                     self.warehouse[row+h+1][col] = 'S'
    #                     for i in range(self.config["storageSize"][0]):
    #                         self.warehouse[row+h+1][col-i-1] = '@'
    #                     self.warehouse[row+h+1][col-self.config["storageSize"][0]-1] = 'S'
    #                 for i in range(self.config["storageSize"][0]):
    #                     self.warehouse[row+self.config["storageSize"][1]+1][col-i-1] = 'S'

    #     start_raw = start_raw_fix
    #     start_col = start_col_fix-1
    #     end_raw = end_raw_fix-1

    #     # fill in west
    #     for col in range(start_col,self.config["storageSize"][0]-1,-1*(self.config["storageSize"][0]+1)):
    #         for row in range(end_raw,self.config["storageSize"][1]-1,-1*(self.config["storageSize"][1]+1)):
    #             #check if current range can be fill or not
    #             if self.check_fillin(row-self.config["storageSize"][1]-1,row+1,col - self.config["storageSize"][0] - 1,col):
    #                 #add the storage line by line
    #                 for i in range(self.config["storageSize"][0]):
    #                     self.warehouse[row][col-i-1] = 'S'
    #                 for h in range(self.config["storageSize"][1]):
    #                     self.warehouse[row-h-1][col] = 'S'
    #                     for i in range(self.config["storageSize"][0]):
    #                         self.warehouse[row-h-1][col-i-1] = '@'
    #                     self.warehouse[row-h-1][col-self.config["storageSize"][0]-1] = 'S'
    #                 for i in range(self.config["storageSize"][0]):
    #                     self.warehouse[row-self.config["storageSize"][1]-1][col-i-1] = 'S'


    def save_map(self):
        with open(os.path.join(self.cur_path, self.config["mapName"]),
                  mode="w", encoding="utf-8") as fout:
            fout.write("type octile\n")
            fout.write(f"height {self.config['mapH']}\n")
            fout.write(f"width {self.config['mapW']}\n")
            fout.write("map\n")
            for i in range(self.config["mapH"]):
                fout.write("".join(self.warehouse[i])+"\n")

            #uncommment for testing
            # fout.write("\n")
            # for i in range(self.config["mapH"]):
            #     fout.write("".join(self.warehouse_record[i])+"\n")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Take config.yaml as input!")
    parser.add_argument("--config", type=str, help="path to the configuration file", default=None)
    args = parser.parse_args()

    generator = WarehouseGenerator(input_arg=args)
    generator.load_stations()
    generator.load_storages()
    # generator.load_more_storages()
    generator.save_map()
