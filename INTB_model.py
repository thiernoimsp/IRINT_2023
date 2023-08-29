from docplex.mp.model import Model
from docplex.mp.progress import *
import sys
import os
import random
import time
import networkx as nx
from collections import defaultdict
from more_itertools import powerset
from random import randint
from Save_Solution import Save_Solution
from itertools import chain, combinations



seed = 2023
random.seed(seed)

class NetworkGenerator:
    def __init__(self, nD: int, nV: int, nM: int, nF: int, min_capacity: int, max_capacity: int):
        D = list(range(nD)) # number of devices
        V = list(range(nV))
        Size = {}
        V_d = defaultdict(list)
        F = list(range(nF))
        M = list(range(nM))
                
        
        # generate the network infrastructure
        G = nx.barabasi_albert_graph(nD, 4)
        #D = list(G.nodes)
        
        # generate size of telemetry items between 2 and 8
        for v in V:
            Size[v] = random.randrange(min_capacity,max_capacity+1, 2)
        
        # adiing telemetry items to all nodes
        #for d in D:
        #    V_d[d] = V
            
        
        # Create an empty dictionary to store the neighbors of each node
        neighbors = {}

        # Iterate over all nodes in the network
        for d in G.nodes():
            # Get the neighbors of the current node
            neighbors_d = list(G.neighbors(d))
            # Add the current node and its neighbors to the dictionary
            neighbors[d] = neighbors_d
        
        
        
        # adding telemetry to all nodes
        # Size of the embedded telemetry items of each device
        #V_d_size = random.randint(l, nV)

        # Randomly select items from the the set of telemetry items of minimum size of length of monitoring requirement l
        for d in D:
            #V_d[d] = random.sample(V, random.randint(l, nV))
            V_d[d] = random.sample(V, random.randint(nV, nV))
            V_d[d].sort(reverse=False)
            #V_d[d] = random.sample(V, V_d_size)
            
        # getting the total number of telemetry item embedded in the network
        total_items = sum(map(len, V_d.values()))
        
        
        
        # setting monitoring requirements with different lengths and overlapping items
        max_len_requemerint = 4
        #Generate the requirements
        requirements = []
        while len(requirements) < len(M):
            random.shuffle(V)
            requirement_length = random.choice(range(1, min(len(V) + 1, max_len_requemerint + 1)))
            requirement = V[:requirement_length]
            requirements.append(requirement)

        # add missing elements to the corresponding requirements
        elements_in_requirements = set(x for sublist in requirements for x in sublist)
        missing_elements = set(V) - elements_in_requirements
        for element in missing_elements:
            for i, requirement in enumerate(requirements):
                if element not in requirement:
                    if len(requirement) >= max_len_requemerint:
                        continue
                    requirements[i].append(element)
                    break


   
        # setting the requirement for each monitoring application
        R_m = {}
        for m in M:
            R_m[m] = requirements[m]
            
        # all spatial add a before Rs and uncomment the above lines to use only some of the spatials
        Rs = {}
        for m in M:
            Rs[m] = [list(x) for x in powerset(R_m[m]) if x]
            
        # selecting some spatial
        ##Rs = {}
        ##for m in M:
        ##    Rs[m] = random.sample(aRs[m], random.randint(1, len(aRs[m])))
            
        # defining temporal
        Rt = {}
        for m in M:
            Rt[m] = Rs[m]
            
        
        
        
                
        # reading required deadlines
        TT = {}
        for m in M:
            for P in range(len(Rs[m])):
                TT[P] = randint(0, 20)

        HH = {}
        for m in M:
            for P in range(len(Rt[m])):
                HH[P] = randint(0, 20)
                
        # Generate F flows
        flows_info = list()
        flows = {}
        for f in F:
            # Choose a random source and destination
            source = random.randint(0, nD-1)
            destination = random.randint(0, nD-1)
            # Make sure the source and destination are not the same
            while source == destination:
                destination = random.randint(0, nD-1)
            # Choose a random capacity for the flow
            #capacity = random.randint(min_capacity, 3*max_capacity)
            capacity = random.randrange(2,20, 2)
            #capacity = random.randint(20, 60)
            # Add the flow to the dictionary
            flows[f] = [source, destination, capacity]
            flows_info.append(([f, source, destination, capacity]))

        # getting the source, destination and capacity of each flow
        S_f = [source[0] for source in flows.values()]
        D_f = [destination[1] for destination in flows.values()]
        K_f = [capacity[2] for capacity in flows.values()]
        
        
                
        # getting the shortest path for each flow
        shortest_path = {}
        for f in F:
            s = S_f[f]
            d = D_f[f]
            shortest_path[f] = nx.shortest_path(G, s, d)
        
        

        # getting the flows crossing each device
        Flows_Crossing_d = defaultdict(list)
        for d in D:
            for f in F :
                if d in shortest_path[f]:
                    Flows_Crossing_d[d].append(f)
                    
        
        
                
        
        #define the parameters
        self.nD = nD
        self.nV = nV
        self.nM = nM
        self.nF = nF
        self.total_items = total_items
        self.min_capacity = min_capacity
        self.max_capacity = max_capacity
        self.D = D
        self.neighbors = neighbors
        self.V = V
        self.V_d = V_d
        self.Size = Size
        self.M = M
        self.R_m = R_m
        self.Rs = Rs
        self.Rt = Rt
        self.TT = TT
        self.HH = HH
        self.F = F
        self.S_f = S_f
        self.D_f = D_f
        self.K_f = K_f
        
        self.flows_info = flows_info
        #self.max_route = max_route
        self.shortest_path = shortest_path
        self.Flows_Crossing_d = Flows_Crossing_d
        # monitoring requirement and spatial dependencies
        self.R_m = R_m
        self.Rs = Rs


track_progress = list()
class MipGapPrinter(ProgressListener):
    def __init__(self):
        #ProgressListener.__init__(self, ProgressClock.Gap)
        ProgressListener.__init__(self, ProgressClock.Objective)

    def notify_progress(self, pdata):
        gap = pdata.mip_gap
        ms_time = 1000* pdata.time
        obj = pdata.current_objective
        data = [int(pdata.current_objective), round(pdata.mip_gap*100, 2), round(pdata.time, 2)]
        track_progress.append(data)
        #print('-- new gap: {0:.1%}, time: {1:.0f} ms, obj :{2:.2f}'.format(gap, ms_time, obj))
        #print(track_progress)
        if pdata.has_incumbent():
          track_progress.append([int(pdata.incumbent_objective), round(pdata.mip_gap*100, 2), round(pdata.time, 2)])
        return track_progress
        
        
class Compact_Formulation_Mixte:
    """ 
    This class implement the new proposed model using gurobi 
    """
    def __init__(self, inst):
        model = Model('OINT')
        
        # Create decision variables
        
        s_b = {(m,d,P): model.binary_var(name='s_b_{}_{}_{}'.format(m,d,P)) for m in inst.M for d in inst.D for P in range(len(inst.Rs[m]))}
        t_b = {(m,P): model.binary_var(name='t_b_{}_{}'.format(m,P)) for m in inst.M for P in range(len(inst.Rt[m]))}
        
        y = {(d,v,f): model.binary_var(name='y_{}_{}_{}'.format(d,v,f)) for d in inst.D for v in inst.V for f in inst.F}
        
        s = {(m,d,P): model.integer_var(name='s_{}_{}_{}'.format(m,d,P)) for m in inst.M for d in inst.D for P in range(len(inst.Rs[m]))}
        
        t = {(m,P): model.integer_var(name='t_{}_{}'.format(m,P)) for m in inst.M for P in range(len(inst.Rt[m]))}
        
            
                    
        # a single telemetry item should be a collected by a single flow
        for d in inst.D:
            for v in inst.V_d[d]:
                model.add_constraint(model.sum(y[d, v, f] for f in inst.F) <=1)
        
        # capacity of given flows should not be exceeded
        for f in inst.F:
            model.add_constraint(model.sum(inst.Size[v] * y[d, v, f] for d in inst.shortest_path[f] for v in inst.V_d[d]) <=  inst.K_f[f])
            model.add_constraint(model.sum(y[d,v,f] for d in [j for j in inst.D if j not in inst.shortest_path[f]] for v in inst.V_d[d] ) <= 0)
            
                
        # counting spatial dependencies
        for m in inst.M:
            for d in inst.D:
                for P in range(len(inst.Rs[m])):
                    model.add_constraint(s[m,d,P] == model.sum(y[d, v, f] for v in inst.Rs[m][P] for f in inst.F))
                    
        # counting temporal
        for m in inst.M:
            for P in range(len(inst.Rt[m])):
                if inst.HH[P] > inst.TT[P]:
                    model.add_constraint(t[m,P] == model.sum(y[d, v, f] for d in inst.D for v in inst.Rs[m][P] for f in inst.F))
                    
        # spatial dependencies
        for m in inst.M:
            for d in inst.D:
                for P in range(len(inst.Rs[m])):
                    model.add_constraint(s_b[m,d,P] <= s[m,d,P]/len(inst.Rs[m][P]))
                    
        # temporal dependencies
        for m in inst.M:
            for P in range(len(inst.Rt[m])):
                model.add_constraint(t_b[m,P] <= t[m,P]/len(inst.Rt[m][P]))
                        
        # the objective function
        obj_function = model.sum(s_b[m,d,P] for m in inst.M for d in inst.D for P in range(len(inst.Rs[m]))) + model.sum(t_b[m,P] for m in inst.M for P in range(len(inst.Rt[m])))
        model.maximize(obj_function)
        
        
        
        # creating class variables
        self.inst = inst
        self.model = model
        self.s_b = s_b
        self.t_b = t_b
        self.s = s
        self.t = t
        self.y = y
        
    def optimize(self):
        # connect a listener to the model
        #self.model.add_progress_listener(MipGapPrinter())
        printer = MipGapPrinter()
        self.model.add_progress_listener(printer)
        # setting cplex parameters
        #self.model.parameters.relax_type = "LP"
        self.model.parameters.timelimit.set(600)
        self.model.parameters.threads.set(4)
        
        solution = self.model.solve(log_output = True)
        #checkfi  the solution is not None
        if solution is None:
            print('Error: No solution found')
            Sol_info = [len(self.inst.D), len(self.inst.F), len(self.inst.V), len(self.inst.M), '--', '--', '--', '--', '--']
        else:
            print(self.model.get_solve_details())
            print(f'Objective value: {solution.objective_value}')
                
            
                
            # getting the spatial dependencies
            spatial = list()
            for m in self.inst.M:
                for d in self.inst.D:
                    #if len(inst.Rsd[m,d]) > 0:
                    for P in range(len(self.inst.Rs[m])):
                        #for P in range(len(self.inst.Rsd[m,d])):
                        if self.s_b[m,d,P].solution_value == 1:
                            data = [m,d,P]
                            spatial.append(data)
                                
            # getting temporal dependencies
            temporal = list()
            for m in self.inst.M:
                for P in range(len(self.inst.Rt[m])):
                    if self.t_b[m,P].solution_value == 1:
                        data = [m,P]
                        temporal.append(data)
                        
            # getting the collected telemetry item 
            collected = list()
            for d in self.inst.D:
                for v in self.inst.V_d[d]:
                    for f in self.inst.F:
                        if self.y[d,v,f].solution_value == 1:
                            data = [d,v,f]
                            collected.append(data)
                            
            #saving the solution
            Sol_info = [len(self.inst.D), len(self.inst.F), len(self.inst.V), len(self.inst.M), self.inst.total_items, len(collected), int(solution.objective_value), round(int(self.model.solution.solve_details.best_bound),2), round((self.model.solve_details.mip_relative_gap)*100,2), round(self.model.solve_details.time, 2)]
            print(Sol_info)
                            
            # saving the data 
            Sol_data = [spatial, temporal, collected, self.inst.V_d, self.inst.flows_info, self.inst.R_m, self.inst.Rs, solution]
                        
        return Sol_info, Sol_data




if __name__ == "__main__":
    if len(sys.argv) != 7:
        print('Usage: python3.7 INTB_model.py [number nodes] [number items] [number monitoring application] [number flows] [min_capacity] [max_capacity]')
        sys.exit(1)
    #network = sys.argv[1]
    nD = int(sys.argv[1])
    nV = int(sys.argv[2])
    nM = int(sys.argv[3])
    nF = int(sys.argv[4])
    #pGF = int(sys.argv[5])
    min_capacity = int(sys.argv[5])
    max_capacity = int(sys.argv[6])
    start_time = time.time()
    inst = NetworkGenerator(nD,nV,nM,nF,min_capacity,max_capacity)
    mixte = Compact_Formulation_Mixte(inst)
    Sol_info, Sol_data = mixte.optimize()
    solution = Save_Solution(inst)
    Total_Runtime = round((time.time() - start_time),2)
    Sol_info.append(Total_Runtime)
    
    
    
    # Create a folder to store the output if it does not exist
    Sol_Path = "./Solution_INTB_model/" + str(inst.nD) + "_" + str(inst.nV) + "_" + str(inst.nM) + "_" + str(inst.min_capacity) + "_" + str(inst.max_capacity) + "_" + str(seed)
    if not os.path.exists(Sol_Path):
        os.makedirs(Sol_Path)
    
    #saving the solution information
    sol = Sol_Path + "/" + "Sol_INTB_" + str(inst.nD) + ".txt"
    solution.write_solution(sol, Sol_info)
    
    #saving the listener information
    sol_listener = Sol_Path + "/" + "Listener_Info_" + str(inst.nD) + "_" + str(inst.nF) + ".txt"
    track_progress.append([Sol_info[5], Sol_info[7], Sol_info[8]])
    solution.write_solution_listener(sol_listener, track_progress)
    
    # saving spatial
    spatial = Sol_Path + "/" + "Spatial_" + str(inst.nD) + "_" + str(inst.nF) + ".txt"
    solution.write_solution_listener(spatial, Sol_data[0])
    
    # saving temporal
    temporal = Sol_Path + "/" + "Temporal_" + str(inst.nD) + "_" + str(inst.nF) + ".txt"
    solution.write_solution_listener(temporal, Sol_data[1])
    
    # save collected
    collected = Sol_Path + "/" + "Collected_" + str(inst.nD) + "_" + str(inst.nF) + ".txt"
    solution.write_solution_listener(collected, Sol_data[2])
    
    # embedded item
    embedded = Sol_Path + "/" + "Embedded_" + str(inst.nD) + "_" + str(inst.nF) + ".txt"
    solution.write_solution_flows_path(embedded, Sol_data[3])
    
    # flows info
    flows_info = Sol_Path + "/" + "Flows_Info_" + str(inst.nD) + "_" + str(inst.nF) + ".txt"
    solution.write_solution_listener(flows_info, Sol_data[4])
    
    # monitoring requirement and spatial dependencies
    requirements = Sol_Path + "/" + "Monitoring_Info" + str(inst.nD) + "_" + str(inst.nF) + ".txt"
    solution.write_monitoring_requirements_info(requirements, Sol_data[5])
    solution.write_monitoring_requirements_info(requirements, Sol_data[6])
