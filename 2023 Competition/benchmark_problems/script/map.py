import os
import logging


def load_map(map_name:str)L
    grid=[]

    if not os.path.exists(map_name):
        logging.error("\nNo map file is found!")
        sys.exit()


    with open(map_name, "r") as file_content:
        lines = file_content.readlines()
        rows,cols=int(lines[1].split()[1]), int(lines[2].split()[1])
        size = rows*cols
        grid =[None] * size

        for x, line in enumerate(lines[4:]):
            for y, char in enumerate(line.strip()):
                if char != "@" and char!="T":
                    grid[x*cols+y] = False
                else:
                    grid[x*cols+y] = True

    return grid

def get_connected_component(grid: list):
    
