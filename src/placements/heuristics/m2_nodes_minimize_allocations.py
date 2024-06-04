#!/usr/bin/env python
# coding: utf-8

# In[1]:


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


# In[3]:


def get_placement(nodes_data, services_data):

    # create a list to store the nodes that are already allocated
    allocated_nodes = []
    allocated_services = []
    placements =  []
    time_placements = []

    start_time = time.time()

    # iterate over the services
    for i in range(len(services_data)):
        # check if the service has already been allocated
        if i in allocated_services:
            continue

        # get the requirements of the current service
        cpu, mem, sto, bw = services_data[i][1:]

        # create a list to store the nodes that can accommodate the current service
        able_nodes = []

        # iterate over the nodes
        for j in range(len(nodes_data)):
            # check if the node is already allocated
            if j in allocated_nodes:
                continue

            # get the capacity of the current node
            node_cpu, node_mem, node_sto, node_bw = nodes_data[j][1:]

            # check if the node can accommodate the current service
            if cpu <= node_cpu and mem <= node_mem and sto <= node_sto and bw <= node_bw:
                able_nodes.append(j)

        # check if there are any nodes that can accommodate the current service
        if len(able_nodes) == 0:
            print(f"No nodes available for service {i}")
        else:
            # allocate the service to the first able node
            allocated_node = able_nodes[0]
            allocated_nodes.append(allocated_node)
            allocated_services.append(i)
            # print(f"Service {i} allocated to node {allocated_node}")
            placements.append([allocated_node, i])


            # subtract the node capabilities
            nodes_data[allocated_node][1] -= cpu
            nodes_data[allocated_node][2] -= mem
            nodes_data[allocated_node][3] -= sto
            nodes_data[allocated_node][4] -= bw

            # check if there are any subsequent services that can be allocated to the same node
            for k in range(i+1, len(services_data)):
                # check if the service has already been allocated
                if k in allocated_services:
                    continue

                # get the requirements of the current service
                cpu, mem, sto, bw = services_data[k][1:]

                # get the capacity of the allocated node
                node_cpu, node_mem, node_sto, node_bw = nodes_data[allocated_node][1:]

                # check if the node can accommodate the current service
                if cpu <= node_cpu and mem <= node_mem and sto <= node_sto and bw <= node_bw:
                    allocated_services.append(k)
                    # print(f"Service {k} allocated to node {allocated_node}")
                    placements.append([allocated_node, k])

                    # subtract the node capabilities
                    nodes_data[allocated_node][1] -= cpu
                    nodes_data[allocated_node][2] -= mem
                    nodes_data[allocated_node][3] -= sto
                    nodes_data[allocated_node][4] -= bw

    time_placements.append('{:.8f}'.format(time.time() - start_time))

    return allocated_services, allocated_nodes, placements, time_placements


# In[4]:


topology = 'germany'
folder = 'orign/'
columns = ['id', 'cpu', 'memory', 'storage', 'bandwidth']

# capacity percent: 0.8 = 80%
cp = 1.0

dict_placements = dict()
time_apps = dict()

# get topology
df_nodes, df_edges = dt.get_topology(topology, capacity_percent=cp, folder='../../..')
G = mnet.create_graph_topology(df_nodes, df_edges)

dict_placements = dict()
dict_applications = dict()
dict_sorted_applications = dict()

tax_sucess = 0

print('Nodes capacity reduced to '+str(cp*100)+'%' )

for i in range(0, 20):
    application = 'App' + str(i)
    df_services, df_choreog = dt.get_application(folder+application, folder='../../..')

    services = df_services[columns].to_numpy()

    dict_applications[application] = services

    # sort dict_applications by length of services
    dict_sorted_applications = {k: v for k, v in sorted(dict_applications.items(), key=lambda item: len(item[1]))}


# In[5]:


allocated_services = []
allocated_nodes = []
placements = []
time_placements = dict()

dict_placements = dict()

for application, services in dict_sorted_applications.items():

    nodes = pd.DataFrame(df_nodes, columns=columns).to_numpy().astype('float')
    nodes_norm, services_norm = dt.normalize_data(nodes, services)

    # services_apps[application] = services
    allocated_services, allocated_nodes, placements, time_placement = get_placement(nodes, services)
    dict_placements[application] = placements, time_placement
    # time_placements[application] = time_placement

    # print('Placement of ' + application + ' is finished!')


import pickle
with open('results/'+topology+'/m2/pkl/' + 'heuristic_' + str(argumento) + '.pkl', 'wb') as f:
    pickle.dump(dict_placements, f)

# dict to csv
import csv
w = csv.writer(open('results/'+topology+'/m2/csv/' + 'heuristic_' + str(argumento) + '.csv', 'w'))
for key, val in dict_placements.items():
    w.writerow([key, val])

import datetime
now = datetime.datetime.now()
print('Finished placement!', now.strftime("%Y-%m-%d %H:%M:%S"))
print(topology)
