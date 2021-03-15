# -*- coding: utf-8 -*-
"""
Created on Wed Jan 30 13:26:35 2019

@author: wongm
"""
import re
from core.model import Surface, Territory, Population, POD



def create_territories(filename):
    surfaces = {}
    territories = {}
    adjacency_matrix = {}
    state = "TERRITORIES"
    
    f = open(filename, "r")
    for x in f:
        #ignore comments and empty lines
        if x != "\n" and x[0] != "#":
            if "TERRITORIES" in x:
                state = "TERRITORIES"
            elif "CONNECTIONS" in x:
                state = "CONNECTIONS"
            else:
                if state is "TERRITORIES":
                    t = parse_territory(x)
                    if t != None:
                        territories[t.name] = t
                        for land in t.lands:
                            surfaces[land.name] = land
                        for air in t.airs:
                            surfaces[air.name] = air
                        for sea in t.seas:
                            surfaces[sea.name] = sea
                elif state is "CONNECTIONS":
                    surface_pair = [tok.strip() for tok in x.split(",")]
                    if len(surface_pair) == 2:
                        if surface_pair[0] in surfaces.keys() and surface_pair[1] in surfaces.keys():
                            
                            surface1 = surfaces[surface_pair[0]]
                            surface2 = surfaces[surface_pair[1]]
                            if surface1.connect(surface2):
                                adjacency_matrix[surface1.name + ":" + surface2.name] = True
                                adjacency_matrix[surface2.name + ":" + surface1.name] = True
                                            
    return territories, surfaces, adjacency_matrix
             
    
def parse_territory(line):
    toks = line.split(":")
    territory_str = toks[0]
    
    nodes_str = toks[1].split(";")
    
    surfaces = []
    for node_str in nodes_str:
        surface = parse_surface_node(node_str)
        if surface != None:
            surfaces.append(surface)

    territory_info = territory_str.split(",")
    
    
    z = re.match("([A-Za-z0-9_\-\s]+)[(]([A-Za-z0-9_\-\s]+)[)]", territory_info[0])
    t = None
    if z:
        node_info = [tok.strip() for tok in z.groups()]
        t = Territory(node_info[0], surfaces)
        if node_info[1] == "C":
            #t.create_population(Population.CITY)
            t.size = Population.CITY
        elif node_info[1] == "V":
            #t.create_population(Population.VILLAGE)
            t.size = Population.VILLAGE
        elif node_info[1] == "T":
            #t.create_population(Population.TOWN)
            t.size = Population.TOWN
            
            
    if len(territory_info) > 1:
        for t_info in territory_info[1:]:
            z = re.match("([A-Za-z0-9_\-\s]+)[(]([A-Za-z0-9_\-\s]+)[)]", t_info)
            if z:
                node_info = [tok.strip() for tok in z.groups()]
                if node_info[0] == "POD" and node_info[1].lower() == "air":
                    t.add_pod(POD(POD.AIR))
                elif node_info[0] == "POD" and node_info[1].lower() == "sea":
                    t.add_pod(POD(POD.SEA))
                    
    return t
    
    

    
def parse_surface_node(line):
    if line[0] == "L":
        z = re.match("([A-Za-z0-9_\-\s]+)[(]([0-9]+)[,]([0-9]+)[,]([0-9]+)[)]", line)
    else:
        z = re.match("([A-Za-z0-9_\-\s]+)[(]([0-9]+)[,]([0-9]+)[)]", line)
    
    if z:
        node_info = [tok.strip() for tok in z.groups()]
        node_name = node_info[0]
        
        #LAND surface
        if node_name[0] == "L":
            l = Surface(node_name, Surface.LAND, float(node_info[3]))
            l.x = float(node_info[1])
            l.y = float(node_info[2])
            return l
        #AIR surface
        elif node_name[0] == "A":
            a = Surface(node_name, Surface.AIR)
            a.x = float(node_info[1])
            a.y = float(node_info[2])
            return a
        #SEA (WATER) surface
        elif node_name[0] == "S":
            s = Surface(node_name, Surface.WATER)
            s.x = float(node_info[1])
            s.y = float(node_info[2])
            return s
    
        
             
        
if __name__ == '__main__':
    create_territories("territory_def.txt")