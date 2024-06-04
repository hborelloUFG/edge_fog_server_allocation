#!/usr/bin/env python
# coding: utf-8

# 1. Minimização da quantidade de nós alocados:

import sys
sys.path.append('../../modules')  # Replace with the actual path to your module folder

# Verifica se pelo menos um argumento foi passado
if len(sys.argv) < 2:
    argumento = 1
else:
    # O primeiro argumento (sys.argv[0]) é o nome do script, então o argumento real começa em sys.argv[1]
    argumento = int(sys.argv[1])

import my_data as dt
import my_placements as mp
import my_networks as mnet

import pandas as pd
import numpy as np
import random as rd
import matplotlib.pyplot as plt
import networkx as nx

import time
np.set_printoptions(suppress=True)

def get_placement_greed(nodes_data, services_data, T=1000):

    time_placements = []
    best_placements = []
    n_services = len(services_data)

    start_time = time.time()
    # rd.seed(32)

    # services receives services in random organization
    # print('Number of services:', len(services_data))
    for i in range(len(services_data)*4):
        services = [[int(i) for i in row] for row in services_data]
        nodes = [[int(i) for i in row] for row in nodes_data]
        
        # sort nodes beginning to nodes with major resources
        nodes = sorted(nodes, key=lambda x: (x[1], x[2], x[3], x[4]), reverse=True)
        
        rd.shuffle(services)
        placements = []
        allocated = []
        
        for n in nodes:
            for s in services:
                if n[1] >= s[1] and n[2] >= s[2] and n[3] >= s[3] and n[4] >= s[4]:
                    n[1] -= s[1]
                    n[2] -= s[2]
                    n[3] -= s[3]
                    n[4] -= s[4]

                    placements.append([n[0], s[0]])
                    allocated.append(n[0])
                    services.remove(s)
            if services == []:
                # print('todos os serviços foram alocados!')
                break
        # print(i, len(set(allocated)), len(services))
        if n_services >= len(set(allocated)):
            best_placements = placements
            n_services = len(set(allocated))

    # print('placements: ', placements)
    time_placements.append('{:.8f}'.format(time.time() - start_time))

    return best_placements, time_placements

topology = 'germany'
folder = 'orign/'
columns = ['id', 'cpu', 'memory', 'storage', 'bandwidth']

# capacity percent: 0.8 = 80%
cp = 1.0

dict_placements = dict()
time_apps = dict()

# get topology
df_nodes, df_edges = dt.get_topology(topology, capacity_percent=cp, folder= '../../..')
G = mnet.create_graph_topology(df_nodes, df_edges)

dict_placements = dict()
dict_applications = dict()
dict_sorted_applications = dict()

tax_sucess = 0

print('Nodes capacity reduced to '+str(cp*100)+'%' )

for i in range(0, 20):
    application = 'App' + str(i)
    
    df_services, df_choreog = dt.get_application(folder+application, folder= '../../..')

    services = df_services[columns].to_numpy()

    dict_applications[application] = services

    # sort dict_applications by length of services
    dict_sorted_applications = {k: v for k, v in sorted(dict_applications.items(), key=lambda item: len(item[1]))}


allocated_services = []
allocated_nodes = []
placements = []
time_placements = dict()

dict_placements = dict()

for application, services in dict_sorted_applications.items():

    nodes = pd.DataFrame(df_nodes, columns=columns).to_numpy().astype('float')
    nodes_norm, services_norm = dt.normalize_data(nodes, services)

    placements, time_placement = get_placement_greed(nodes, services)
    dict_placements[application] = placements, time_placement

    # print('Placement of ' + application + ' is finished!')

import pickle
with open('results/'+topology+'/m1/pkl/' + 'heuristic_' + str(argumento) + '.pkl', 'wb') as f:
    pickle.dump(dict_placements, f)

# dict to csv
import csv
w = csv.writer(open('results/'+topology+'/m1/csv/' + 'heuristic_' + str(argumento) + '.csv', 'w'))
for key, val in dict_placements.items():
    w.writerow([key, val])

import datetime
now = datetime.datetime.now()
print('Finished placement!', now.strftime("%Y-%m-%d %H:%M:%S"))

