#!/usr/bin/env python
# coding: utf-8

# Minimização da quantidade de “saltos” de um nó para outro:

# Replace with the actual path to your module folder
import sys
sys.path.append('../../modules')  

# Verifica se pelo menos um argumento foi passado
if len(sys.argv) < 2:
    argumento = 0

# O primeiro argumento (sys.argv[0]) é o nome do script, então o argumento real começa em sys.argv[1]
argumento = int(sys.argv[1])

# import libraries
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

# load data from files
topology = 'germany'
folder = 'orign/'
columns = ['id', 'cpu', 'memory', 'storage', 'bandwidth']

# capacity percent: 0.8 = 80%
cp = 1.0
tax_sucess = 0

dict_placements = dict()
time_apps = dict()

# get topology
df_nodes, df_edges = dt.get_topology(topology, capacity_percent=cp, folder= '../../..')
G = mnet.create_graph_topology(df_nodes, df_edges)
hops = mnet.floyd_warshall(G, weight='hops')

dict_placements = dict()
dict_applications = dict()
dict_sorted_applications = dict()

print('Nodes capacity reduced to '+str(cp*100)+'%' )

for i in range(0, 20):
    application = 'App' + str(i)
    df_services, df_choreog = dt.get_application(folder+application, folder= '../../..')

    services = df_services[columns].to_numpy()
    services = [[int(i) for i in row] for row in services]
    
    # change the first column to integer sequence
    services = [[i] + service[1:] for i, service in enumerate(services)]

    dict_applications[application] = services

    # sort dict_applications by length of services
    dict_sorted_applications = {k: v for k, v in sorted(dict_applications.items(), key=lambda item: len(item[1]))}

    # print('Application: '+application)

def get_data(nodes_data, services_data):

    # prepare data
    services = {}
    for i in range(len(services_data)):
        services[i] = services_data[i][1:]

    nodes = {}
    for i in range(len(nodes_data)):
        nodes[i] = nodes_data[i][1:]

    return services, nodes

def count_hops(allocations):

    hops_counter = 0
    for n in range(len(allocations)-1):
            source = [allocations[n]][0]
            target = [allocations[n+1]][0]
            hops_counter += hops[source][target]
        
    return hops_counter

def next_nodes(node, hops):
    row = hops[node]
    list_hops = []
    for i in range(len(row)):
        if row[i] != 0:
            list_hops.append((i, row[i]))
            
    return sorted(list_hops, key=lambda x: x[1])

def check_resource(service, node):
    if node[0] >= service[0] and node[1] >= service[1] and node[2] >= service[2] and node[3] >= service[3]:
        return True
    else:
        return False
    
def get_next_node_with_resources(service, n_nodes, nodes):
    for n in n_nodes:
        if check_resource(service, nodes[n[0]]):
            return n
    return n
    
def get_residual_resource(s_data, n_data):
    n_data[0] -= s_data[0]
    n_data[1] -= s_data[1]
    n_data[2] -= s_data[2]
    n_data[3] -= s_data[3]
    
    return n_data

def get_residual_resources(services, node):
    residual = node.copy()
    for service in services:
        residual[0] -= service[0]
        residual[1] -= service[1]
        residual[2] -= service[2]
        residual[3] -= service[3]
    return residual


# In[54]:


import copy
import time

def get_placement(services, nodes, hops):

    final_allocations = []
    time_placements = time.time()
    num_hops = 10000
    

    # loop for all nodes in the network
    for n, node_data in nodes.items():
        allocated_nodes = []
        placements = []
        instance_nodes = copy.deepcopy(nodes)
        # print('Beginning in node:', n, end=': ')
        # loop for all services in the application
        j1 = n
        for s, service_data in services.items():

            if check_resource(service_data, instance_nodes[j1]):
                allocated_nodes.append(j1)
                placements.append([j1, s])
                instance_nodes[j1] = get_residual_resource(service_data, instance_nodes[j1])
            else:
                n_nodes = next_nodes(j1, hops)
                j1 = get_next_node_with_resources(service_data, n_nodes, instance_nodes)[0]
                stop = 0
                while not check_resource(service_data, instance_nodes[j1]):
                    n_nodes = next_nodes(j1, hops)
                    j1 = get_next_node_with_resources(service_data, n_nodes, instance_nodes)[0]

                    if stop == 49:
                        break
                    stop += 1
                instance_nodes[j1] = get_residual_resource(service_data, instance_nodes[j1])
                allocated_nodes.append(j1)
                placements.append([j1, s])

        if num_hops > count_hops(allocated_nodes):
            num_hops = count_hops(allocated_nodes)
            final_allocations = placements
    time_placements = time.time() - time_placements
    return final_allocations, num_hops, time_placements

# run for all applications
# ===============================================
allocated_services = []
allocated_nodes = []
placements = []
time_placements = dict()

dict_placements = dict()
nodes_data = pd.DataFrame(df_nodes, columns=columns).to_numpy().astype('int')
nodes_data = [[int(i) for i in row] for row in nodes_data]

for app, services_data in dict_sorted_applications.items():
    services, nodes = get_data(nodes_data, services_data)
    
    p, h, t = get_placement(services, nodes, hops)
    dict_placements[app] = p, ['{:.8f}'.format(t)]

import pickle
with open('results/'+topology+'/m3/pkl/' + 'heuristic_' + str(argumento) + '.pkl', 'wb') as f:
    pickle.dump(dict_placements, f)

# dict to csv
import csv
w = csv.writer(open('results/'+topology+'/m3/csv/' + 'heuristic_' + str(argumento) + '.csv', 'w'))
for key, val in dict_placements.items():
    w.writerow([key, val])

import datetime
now = datetime.datetime.now()
print('Finished placement!', now.strftime("%Y-%m-%d %H:%M:%S"))

