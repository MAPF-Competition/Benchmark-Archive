import numpy as np
import argparse

import random
import json

import logging
import os
from typing import List
import sys

class WarehouseTaskGenerator:
    def __init__(self) -> None:
        pass

    def get_loc_id(self, x,y,rows,cols):
        return x*cols+y
    
    def get_loc_xy(self,loc,rows,cols):
        x=loc//cols
        y=loc%cols
        return x,y


    def manhattan_dist(self,loc1,loc2,rows,cols):
        x1 = loc1 // cols  # Compute x coordinate
        y1 = loc1 % cols   # Compute y coordinate
        x2 = loc2 // cols  # Compute x coordinate
        y2 = loc2 % cols   # Compute y coordinate
        return abs(x1-x2)+abs(y1-y2)
        

    def read_maps(self, map_name:str):
        e_locations=[]
        s_locations=[]

        if not os.path.exists(map_name):
            logging.error("\nNo map file is found!")
            sys.exit()

        with open(map_name, "r") as file_content:
            lines = file_content.readlines()
            rows,cols=int(lines[1].split()[1]), int(lines[2].split()[1])
            for x, line in enumerate(lines[4:]):
                for y, char in enumerate(line.strip()):
                    if char == "E":
                        e_locations.append(self.get_loc_id(x,y,rows,cols))
                    elif char=='S':
                        s_locations.append(self.get_loc_id(x,y,rows,cols))
        return e_locations,s_locations,rows,cols
    
    def load_grid_map(self,filename):
        with open(filename, 'r') as file:
            lines = file.readlines()

        # Extract the grid dimensions from the file
        width = int(lines[2].split()[1])
        height = int(lines[1].split()[1])
        grid_lines = lines[4:]  # The actual grid map starts at the 5th line
        
        grid_map = []
        for line in grid_lines:
            grid_map.append(list(line.strip()))

        return np.array(grid_map), width, height


    def plot_grid_map(self, grid_map, heatmap, groups, m_buckets):
        import matplotlib.pyplot as plt
        from matplotlib.colors import Normalize
        import numpy as np

        # Create a color map for the grid
        color_map = {
            '@': 'black',  # Obstacles
            # '.': 'white',  # Empty cells
            'E': 'red',    # Emitters
            'S': 'green'   # Stations
        }

        # Create a color map for the groups
        cmap_name = 'rainbow'
        cmap = plt.get_cmap(cmap_name)
        colors = [cmap(i/(m_buckets-1)) for i in range(m_buckets)]
        groups_color = {i: colors[i] for i in range(m_buckets)}

        # Determine grid dimensions
        grid_height, grid_width = grid_map.shape

        # Create a heatmap matrix to match grid dimensions
        heatmap_matrix = np.zeros((grid_height, grid_width))

        # Fill the heatmap matrix with visit counts
        for id, visits in heatmap.items():
            row, col = self.get_loc_xy(id, grid_height, grid_width)
            heatmap_matrix[grid_height-1-row, col] =  visits#int((1/visits)*16)

        # Normalize the heatmap to enhance contrast
        norm_heatmap = Normalize(vmin=heatmap_matrix.min(), vmax=heatmap_matrix.max())
        # norm_heatmap = Normalize(vmin=200, vmax=400)
        # Create a group matrix to match grid dimensions
        group_matrix = np.full((grid_height, grid_width), -1)  # Initialize with -1 (indicating no group)
        
        # Fill the group matrix with group IDs
        for id, group_id in groups.items():
            row, col = self.get_loc_xy(id, grid_height, grid_width)
            group_matrix[row, col] = group_id

        # Create a figure and axis for subplots
        # fig, axs = plt.subplots(nrows=2, figsize=(12, 8))
        fig, ax = plt.subplots(figsize=(12, 8))
        ax.imshow(grid_map != '@', cmap='gray', extent=[0, grid_width, 0, grid_height], origin='upper')
        ax.imshow(heatmap_matrix, cmap='plasma', alpha=0.9, extent=[0, grid_width, 0, grid_height], 
                    origin='lower', norm=norm_heatmap)
        

        for y in range(grid_height):
            for x in range(grid_width):
                char = grid_map[y, x]
                if char in color_map:
                    ax.scatter(x + 0.5, grid_height - y - 0.5, color=color_map[char], marker='o', s=5, alpha=0.5)
        ax.set_xlim(0, grid_width)
        ax.set_ylim(0, grid_height)
        ax.set_aspect('equal')
        ax.axis('off')  # Turn off the axis
        ax.set_title('HeatMap of S Locations')
        fig.colorbar(plt.cm.ScalarMappable(cmap='plasma', norm=norm_heatmap), ax=ax, label='Number of Tasks',fraction=0.046, pad=0.04)
        plt.savefig("distribution.png", format='png', bbox_inches='tight', dpi=500)


        # Plot the heatmap in the first subplot
        # axs[0].imshow(grid_map != '@', cmap='gray', extent=[0, grid_width, 0, grid_height], origin='upper')
        # axs[0].imshow(heatmap_matrix, cmap='plasma', alpha=0.9, extent=[0, grid_width, 0, grid_height], 
        #             origin='lower', norm=norm_heatmap)
        

        # for y in range(grid_height):
        #     for x in range(grid_width):
        #         char = grid_map[y, x]
        #         if char in color_map:
        #             axs[0].scatter(x + 0.5, grid_height - y - 0.5, color=color_map[char], marker='o', s=5, alpha=0.5)
        # axs[0].set_xlim(0, grid_width)
        # axs[0].set_ylim(0, grid_height)
        # axs[0].set_aspect('equal')
        # axs[0].axis('off')  # Turn off the axis
        # axs[0].set_title('HeatMap of S Locations')
        # fig.colorbar(plt.cm.ScalarMappable(cmap='plasma', norm=norm_heatmap), ax=axs[0], label='Number of Tasks',fraction=0.046, pad=0.04)

        # Plot the task groups in the second subplot
        fig, ax = plt.subplots(figsize=(12, 8))
        for y in range(grid_height):
            for x in range(grid_width):
                group_id = group_matrix[y, x]
                if group_id != -1:  # Only fill cells that are part of a group
                    color = groups_color.get(group_id, 'gray')  # Default to gray if unknown group
                    rect = plt.Rectangle((x, grid_height - y - 1), 1, 1, facecolor=color)
                    ax.add_patch(rect)
        ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=color) for color in groups_color.values()],
                    labels=[f'Group {group_id}' for group_id in groups_color.keys()], loc='center left', bbox_to_anchor=(1.05, 0.5))
        # Adjust the second subplot settings
        ax.set_xlim(0, grid_width)
        ax.set_ylim(0, grid_height)
        ax.set_aspect('equal')
        ax.axis('off')  # Turn off the axis
        ax.set_title('Task Groups')

        # Save the figure
        # plt.savefig('grid_map_heatmap_and_groups_new.pdf', format='pdf', bbox_inches='tight')
        plt.savefig('buckets.png', format='png', bbox_inches='tight', dpi=500)
        # plt.show()

    def read_traversable(self, map_name:str):
        traversable=[]

        if not os.path.exists(map_name):
            logging.error("\nNo map file is found!")
            sys.exit()

        with open(map_name, "r") as file_content:
            lines = file_content.readlines()
            rows,cols=int(lines[1].split()[1]), int(lines[2].split()[1])
            for x, line in enumerate(lines[4:]):
                for y, char in enumerate(line.strip()):
                    if char != "@":
                        traversable.append(self.get_loc_id(x,y,rows,cols))

        return traversable


    def random_generate(self,taskNum,map_name,task_type_rl=[0.5,0.5], minEPT=1, maxEPT=2):
        e_locations,s_locations,rows,cols=self.read_maps(map_name)
        tasks=[]
        for i in range(taskNum):
            #determine if the task is E or S
            locNum=np.random.randint(minEPT,maxEPT+1)
            locs=[]
            for i in range(locNum):
                prob=np.random.random()
                if prob<task_type_rl[0]:
                    task=np.random.choice(e_locations)
                else:
                    task=np.random.choice(s_locations)
                locs.append(task)
            tasks.append(locs)
        return tasks


    def generate_txt(self, tasks:List,file_name:str):
        with open(file_name,"w") as file:
            file.write( "# version for LoRR 2024\n")
            file.write(str(len(tasks))+"\n")
            for task in tasks:
                for i, loc in enumerate(task):
                    file.write(str(loc))
                    if i!=len(task)-1:
                        file.write(",")
                file.write("\n")
        print("successfully saved as",file_name)

    def generate_endpoint_with_distribution(self,s_location, e_locations, f):
        prob=[f(s_location, e_location) for e_location in e_locations]
        prob=prob/np.sum(prob)
        endpoint=np.random.choice(e_locations, p=prob)
        return endpoint



    def generate_next_task_with_distribution(self,e_locations,s_locations,buckets,prob, eta=-1):
        p=list(prob.values())
        if eta==-1:
            eta=np.random.randint(2)
        if eta==0:
            ei=np.random.choice(e_locations)
            return ei
        elif eta==1:
            selected_bucket=[]
            while len(selected_bucket)==0:
                selected_bucket = np.random.choice(list(buckets.keys()),p=list(prob.values()))
                selected_location = np.random.choice(buckets[selected_bucket])
                return selected_location
            
    def generate_next_task_amazon_distribution(self,e_locations,s_locations,last_location,rows,cols,bucket_num=5, eta=-1, e_biases=None, inverse=False):
        """_summary_

        Args:
            e_locations (_type_): _description_
            s_locations (_type_): _description_
            bucket_num (_type_): _description_
            prob (_type_): _description_
            eta (int, optional): _description_. Defaults to -1.
            sample strategy (function, optional): _description_. Defaults to None. User defined sample strategy

        Returns:
            _type_: generate next task with distribution close to amazon distribution
        """
        
        if eta==0:
           
            if e_biases is None:
                # choose an e location randomly
                ei=np.random.choice(e_locations)
            else:
                # choose an e location based on sample strategy user defined
                p=np.array(e_biases)
                p=p/np.sum(p)
                ei=np.random.choice(e_locations, p=p)
            return ei
        else:

            #choose an s location based on distance distribution, last_location is the last e location
            buckets,prob=self.preprocess_for_one_location(last_location,s_locations,rows,cols,bucket_num)
            selected_bucket=[]
            pval = list(prob.values())
            if inverse:
                pval = [1-p for p in pval]
                # normalize
                pval = [p/sum(pval) for p in pval]
            while len(selected_bucket)==0:
                selected_bucket = np.random.choice(list(buckets.keys()),p=pval)
                selected_location = np.random.choice(buckets[selected_bucket])
                return selected_location

    def preprocess(self, e_locations,s_locations,rows,cols,num_buckets):
        # num_buckets = len(s_locations)  # Number of buckets (m)
        avgdist_min = min(sum(self.manhattan_dist(s,e,rows,cols) for e in e_locations) / len(e_locations) for s in s_locations)
        avgdist_max = max(sum(self.manhattan_dist(s,e,rows,cols) for e in e_locations) / len(e_locations) for s in s_locations)

        ranges = np.linspace(avgdist_min, avgdist_max, num_buckets+1)
        
        buckets = {i: [] for i in range(num_buckets)}
        # print(buckets,s_locations,e_locations)

        for s in s_locations:
            avgdist = sum(self.manhattan_dist(s,e,rows,cols)  for e in e_locations) / len(e_locations)
            
            bucket_index = int(np.searchsorted(ranges, avgdist, side='right')) - 1
            
            if bucket_index==num_buckets:
                bucket_index-=1
            buckets[bucket_index].append(s)
     
        portions = np.array([1 / (2 ** i) for i in range(num_buckets)])
        norm = sum(portions)

        portions = portions / norm
        prob = {i: portions[i] for i in range(num_buckets)}
    
        return buckets, prob
    
    def preprocess_for_one_location(self, e_location,s_locations,cols,rows,num_buckets):
        # num_buckets = len(s_locations)  # Number of buckets (m)

        avgdist_min = min(self.manhattan_dist(s,e_location,rows,cols) for s in s_locations)
        avgdist_max = max(self.manhattan_dist(s,e_location,rows,cols) for s in s_locations)

        ranges = np.linspace(avgdist_min, avgdist_max, num_buckets+1)

        buckets = {i: [] for i in range(num_buckets)}
        # print(buckets,s_locations,e_locations)

        for s in s_locations:
            
            avgdist = self.manhattan_dist(s,e_location,rows,cols)
            bucket_index = int(np.searchsorted(ranges, avgdist, side='right')) - 1
            
            if bucket_index==num_buckets:
                bucket_index-=1
            # print(bucket_index)
            buckets[bucket_index].append(s)
     
        portions = np.array([1 / (2 ** i) for i in range(num_buckets)])
        norm = sum(portions)

        portions = portions / norm
        prob = {i: portions[i] for i in range(num_buckets)}
    
        return buckets, prob



    def distribute_generate(self,taskNum,map_name,m_buckets, minEPT=1, maxEPT=2):
        e_locations,s_locations,rows,cols=self.read_maps(map_name)
        tasks=[]
        assert(m_buckets>0)
        buckets,prob=self.preprocess(e_locations,s_locations,rows,cols,m_buckets)
        while len(tasks)<taskNum:
            LocNums = np.random.randint(minEPT, maxEPT+1)
            locs=[]
            for i in range(LocNums):
                task=self.generate_next_task_with_distribution(e_locations,s_locations,buckets,prob)
                locs.append(task)
            tasks.append(locs)
        return tasks
    
    def plot_heatmap_example(self, map_name ):
        import matplotlib.pyplot as plt
        import collections
        e_locations,s_locations,rows,cols=self.read_maps(map_name)
        # e_location=np.random.choice(e_locations)
        e_location=525
        
        x,y=self.get_loc_xy(e_location,rows,cols)

        grid_map, width, height = self.load_grid_map(map_name)
        buckets, prob = self.preprocess_for_one_location(e_location,s_locations,width, height,5)
        p=list(prob.values())

        tasks=[]
        for i in range(100000):
            selected_bucket = np.random.choice(list(buckets.keys()),p=p)
            selected_location = np.random.choice(buckets[selected_bucket])
            tasks.append(selected_location)
        heatmap=collections.defaultdict(int)
        for task in tasks:
            heatmap[task]+=1
        groups=dict()
        for b_id, task_ids in buckets.items():
            for task_id in task_ids:
                groups[task_id]=b_id
        self.plot_grid_map(grid_map, heatmap, groups)

    

    def plot_heatmap(self, map_name, tasks, m_buckets):
        import matplotlib.pyplot as plt
        import collections
        heatmap=collections.defaultdict(int)
        for task in tasks:
            heatmap[task[1]]+=1
        grid_map, width, height = self.load_grid_map(map_name)
        e_locations,s_locations,rows,cols=self.read_maps(map_name)
        buckets,prob=self.preprocess(e_locations,s_locations,rows,cols,m_buckets)
        groups=dict()
        for b_id, task_ids in buckets.items():
            for task_id in task_ids:
                groups[task_id]=b_id
        self.plot_grid_map(grid_map, heatmap, groups, m_buckets)

    def read_task_file(self,filename):
        tasks=[]
        with open(filename, 'r') as file:
            lines = file.readlines()
            # The first line is the number of tasks (you can use it if needed)
            number_of_tasks = int(lines[1].strip())
            # Each subsequent line contains two vertex IDs (errands)
            for line in lines[2:]:
                vertex1, vertex2 = map(int, line.strip().split(','))
                tasks.append((vertex1, vertex2))
        return tasks

    def generate_sim_warehouse_tasks(self,taskNum,map_name,m_buckets, minEPT=1, maxEPT=2, task_txt="warehouse_large_new.tasks"):
        """_summary_

        Args:
            taskNum (_type_): _description_
            map_name (_type_): _description_
            m_buckets (_type_): _description_
            minEPT (int, optional): _description_. Defaults to 1.
            maxEPT (int, optional): _description_. Defaults to 2.
            task_txt (str, optional): _description_. Defaults to "warehouse_large_new.tasks".

        Returns:
            _type_: _description_
        """
        e_locations,s_locations,rows,cols=self.read_maps(map_name)
        tasks=[]
        buckets,prob=self.preprocess(e_locations,s_locations,rows,cols,m_buckets)
        tasks=self.read_task_file(task_txt)
        while len(tasks)<taskNum:
            LocNums = 2
            locs=[]
            # print("LocNums",LocNums)
            for i in range(LocNums):
                task=self.generate_next_task_with_distribution(e_locations,s_locations,buckets,prob, i%2)
                locs.append(task)
            tasks.append(locs)
        self.plot_heatmap(map_name, tasks)
        return tasks
    
    def generate_amazon_warehouse_tasks(self,taskNum,map_name,m_buckets, minEPT=1, maxEPT=2, task_txt="warehouse_large_amazon.tasks",e_biases=None, inverse=False):
        """_summary_

        Args:
            taskNum (_type_): _description_
            map_name (_type_): _description_
            m_buckets (_type_): _description_
            minEPT (int, optional): _description_. Defaults to 1.
            maxEPT (int, optional): _description_. Defaults to 2.
            task_txt (str, optional): _description_. Defaults to "warehouse_large_amazon.tasks".
            e_biases (list, optional): _description_. Defaults to None.
            inverse (bool, optional): _description_. Defaults to False.
        Returns:
            _type_: new task generation policy
        """
        e_locations,s_locations,rows,cols=self.read_maps(map_name)
 
        tasks=[]
        buckets,prob=self.preprocess(e_locations,s_locations,rows,cols,m_buckets)
        # tasks=self.read_task_file(task_txt)

        while len(tasks)<taskNum:
            LocNums = 2
            locs=[]

            last_s_location = None
            for i in range(LocNums):
                task=self.generate_next_task_amazon_distribution(e_locations, s_locations,last_s_location,rows,cols, m_buckets, i%2, e_biases, inverse=inverse)
                locs.append(task)
                last_s_location = task
            tasks.append(locs)
        # print("tasks",(np.array(tasks)).shape)
        self.plot_heatmap(map_name, tasks, m_buckets)
        return tasks

    def generate_agents(self,num_agents,map_name,agentFile):
        # num_agents = argsnum_agents
        traversable = self.read_traversable(map_name)
        agents = random.sample(traversable, num_agents)
        with open(agentFile,mode="w", encoding="utf-8") as f:
            f.write("# version for LoRR 2024\n")
            f.write("{}\n".format(num_agents))
            f.writelines([str(a)+"\n" for a in agents])
        return True

    def generate_problem(self,map_name,agent_file,team_size,task_file,tasks_reveal,problemName):
        problem_file = {
                "mapFile": map_name,
                "agentFile": agent_file,
                "teamSize": team_size,
                "taskFile": task_file,
                "numTasksReveal": tasks_reveal,
                "version": "2024 LoRR"
                # "taskAssignmentStrategy": "roundrobin"
            }
        with open(problemName, mode="w", encoding="utf-8") as fout:
            json.dump(problem_file, fout, indent=4)

    def generate_task(self, distributed=0):
        if distributed:
            tasks = self.distribute_generate()
        else:
            tasks = self.random_generate()
        return tasks


def parse_arguments():
    parser = argparse.ArgumentParser(description='=============League of Robot Runners Warehouse Task Generator version 2024.===========')
    parser.add_argument('--mapFile', help='Map file name', required=True)
    parser.add_argument('--taskNum', type=int, default=10000, help='Number of tasks (>=1)')
    parser.add_argument('--m_buckets',type=int,default=-1,help='Number of buckets for task generation with distribution. By default, m_buckets =-1, and random policy for task generation will be used')
    parser.add_argument('--task_type_rl', nargs='+', type=float, default=[0.5, 0.5],
                        help='Relative likelihood of selecting an "E" or an "S" location. Default value= [0.5,0.5]')
    parser.add_argument('--e_bucket_rl', nargs='+', type=float, default=[0.25, 0.25, 0.25, 0.25],
                        help='Relative likelihood of each "E" bucket. Default value=[0.25, 0.25, 0.25, 0.25]')
    parser.add_argument('--s_bucket_rl', nargs='+', type=float, default=[1],
                        help='Relative likelihood of each "S" bucket')
    parser.add_argument('--minEPT', type=int, default=1, help='Minimum number of errands per task (>=1)')
    parser.add_argument("--maxEPT", type=int, default=3, help="Maximum number of errands per task (>=1)")
    parser.add_argument('--taskFile',default="tasks.tasks",help="The name of the generated task file (Default value='tasks.tasks')")
    parser.add_argument("--e_biases", nargs="+", type=float, default=None, help="The biases for the e locations")
    parser.add_argument("--inverse", action="store_true", help="If this flag is set, the Inverse Amazon Distribution will be used.")
    parser.add_argument("--mode", type=int, default=2024, help="The mode of the task generation policy, select between 2023 and 2024. Default value=2024")


    args = parser.parse_args()
    print_info(args)
    return args


def print_info(args):
    if args.m_buckets==-1:
        print("Task generation policy: Random")
    else:
        print("Task generation policy: Based on average distance")
    print(f"--map: {args.mapFile} (Description: Map file name.)")
    print(f"--taskNum: {args.taskNum} (Description: Number of tasks.)")
    print(f"--minEPT: {args.minEPT} (Description: Minimum number of errands per task.)")
    print(f"--maxEPT: {args.maxEPT} (Description: Maximum number of errands per task.)")
    print(f"--task_type_rl: {args.task_type_rl} (Description: Relative likelihood of selecting an E or an S location.)")
    print(f"--taskFile: {args.taskFile} (Description: Name of the output file.)")
    print(f"--m_buckets: {args.m_buckets} (Description: Number of the buckets.)")
    print(f"--e_biases: {args. e_biases} (Description: The list of biases for choosing e locations.)")
    print(f"--inverse: {args.inverse} (Description: If this flag is set, the Inverse Amazon Distribution will be used.)")
    print(f"--mode {args.mode} (Description: The mode of the task generation policy. Choose between year 2023 and 2024.)")



if __name__=="__main__":
    args=parse_arguments()
    TG=WarehouseTaskGenerator()
    if args.m_buckets==-1:
        tasks=TG.random_generate(args.taskNum,args.mapFile,args.task_type_rl,args.minEPT,args.maxEPT)
    else:
        # tasks=TG.distribute_generate(args.taskNum,args.mapFile,args.m_buckets,args.minEPT,args.maxEPT)    used in 2023 LoRR
        # tasks=TG.generate_sim_warehouse_tasks(args.taskNum,args.mapFile,args.m_buckets,args.minEPT,args.maxEPT)  used in 2024 LoRR
        match args.mode:
            case 2023:
                tasks=TG.distribute_generate(args.taskNum,args.mapFile,args.m_buckets,args.minEPT,args.maxEPT)
            case 2024:
                tasks=TG.generate_amazon_warehouse_tasks(
                    taskNum=args.taskNum,
                    map_name=args.mapFile,
                    m_buckets=args.m_buckets,
                    minEPT=args.minEPT,
                    maxEPT=args.maxEPT,
                    e_biases=args.e_biases,
                    inverse=args.inverse
                    )
    TG.generate_txt(tasks,args.taskFile)
    # generate_agents(args.num_agents,args.map,args.agents)
    # generate_problem(args.map,args.agents,args.team_size,args.output,args.tasks_reveal,args.problem)


'''
example
 python3 ./script/task_generator.py --map ./warehouse.domain/maps/warehouse_large.map  --taskNum 100 --taskFile ./tasks.tasks --m_buckets 5
'''