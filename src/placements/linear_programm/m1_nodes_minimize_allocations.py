#!/usr/bin/env python
# coding: utf-8

import sys
sys.path.append('../../modules')  # Replace with the actual path to your module folder

# Verifica se pelo menos um argumento foi passado
if len(sys.argv) < 2:
    argumento = 0
else:
    # O primeiro argumento (sys.argv[0]) é o nome do script, então o argumento real começa em sys.argv[1]
    argumento = int(sys.argv[1])

import gurobipy as gp
import numpy as np
import pandas as pd
import datetime

import my_data as dt
import my_placements as mp
import my_networks as mnet

np.set_printoptions(suppress=True)

def get_placement_lp(nodes, services):
    # define a list of nodes
    nodes_list = list()
    for i in nodes:
        nodes_list.append(int(i[0]))
    
    # define a list of services
    services_list = list()
    for i in services:
        services_list.append(int(i[0]))
    
    qtd_nodes = len(nodes)
    qtd_services = len(services)
    
    # define a dictinary of nodes
    nodes_cpu = dict()
    nodes_mem = dict()
    nodes_sto = dict()
    nodes_bw = dict()
    for n in range(qtd_nodes):
        nodes_cpu[nodes_list[n]] = nodes[n, 1]
        nodes_mem[nodes_list[n]] = nodes[n, 2]
        nodes_sto[nodes_list[n]] = nodes[n, 3]
        nodes_bw[nodes_list[n]]  = nodes[n, 4]
    
    # define a dictinary of services
    services_cpu = dict()
    services_mem = dict()
    services_sto = dict()
    services_bw = dict()
    for s in range(qtd_services):
        services_cpu[services_list[s]] = services[s, 1]
        services_mem[services_list[s]] = services[s, 2]
        services_sto[services_list[s]] = services[s, 3]
        services_bw[services_list[s]]  = services[s, 4]
    
    m = gp.Model()
    m.setParam(gp.GRB.param.OutputFlag, 0)
    m.setParam(gp.GRB.param.Threads, 4)
    # m.setParam(gp.GRB.param.TimeLimit, 5*60)
    
    # define variables
    x = m.addVars(services_list, nodes_list, vtype=gp.GRB.BINARY)
    z = m.addVars(nodes_list, vtype=gp.GRB.BINARY)

    # define objective
    m.setObjective(
        gp.quicksum(z[n] for n in nodes_list), sense=gp.GRB.MINIMIZE
    )

    # define constraints
    c1 = m.addConstrs(gp.quicksum(x[s, n] for n in nodes_list) == 1 for s in services_list)

    c2 = m.addConstrs(gp.quicksum(x[s, n] * services_cpu[s] for s in services_list) <= nodes_cpu[n] for n in nodes_list)
    c3 = m.addConstrs(gp.quicksum(x[s, n] * services_mem[s] for s in services_list) <= nodes_mem[n] for n in nodes_list)
    c4 = m.addConstrs(gp.quicksum(x[s, n] * services_sto[s] for s in services_list) <= nodes_sto[n] for n in nodes_list)
    c5 = m.addConstrs(gp.quicksum(x[s, n] * services_bw[s] for s in services_list) <= nodes_bw[n] for n in nodes_list)

    c6 = m.addConstrs(gp.quicksum(x[s, n] for s in services_list) <= qtd_services * z[n] for n in nodes_list)
    
    # Optimize model
    m.optimize()
    
    # print solution
    placements = []
    nodes_allocated = []
    for s in services_list:
        for n in nodes_list:
            if round(x[s, n].x) > 0:
                placements.append([n, s])
                nodes_allocated.append(n)
    
    return placements, nodes_allocated, m.Runtime

topology = 'melbourne'
columns = ['id', 'cpu', 'memory', 'storage', 'bandwidth']

# capacity percent: 0.8 = 80%
cp = 1.0

dict_placements = dict()
time_apps = dict()

# get topology
df_nodes, df_edges = dt.get_topology(topology, capacity_percent=cp, folder= '../../..')
print((df_edges))
G = mnet.create_graph_topology(df_nodes, df_edges)

dict_placements = dict()
dict_applications = dict()
dict_sorted_applications = dict()
dict_placements_times = dict()

tax_sucess = 0
folder = 'orign/'

print('Nodes capacity reduced to '+str(cp*100)+'%' )
now = datetime.datetime.now()
print('Start at:', now.strftime("%Y-%m-%d %H:%M:%S"))

for i in range(0, 20):
    application = 'App' + str(i)
    df_services, df_choreog = dt.get_application(folder+application, folder= '../../..')

    services = df_services[columns].to_numpy()

    dict_applications[application] = services

    # sort dict_applications by length of services
    dict_sorted_applications = {k: v for k, v in sorted(dict_applications.items(), key=lambda item: len(item[1]))}

count = 1
for application, services in dict_sorted_applications.items():

    nodes = pd.DataFrame(df_nodes, columns=columns).to_numpy().astype('float')

    nodes_norm, services_norm = dt.normalize_data(nodes, services)

    # services_apps[application] = services
    placements, nodes_allocated, time_placement = get_placement_lp(nodes, services)

    dict_placements[application] = placements
    # dict_placements[application] = placements, ['{:.8f}'.format(time_placement)]
    # dict_placements_times[application] = ['{:.8f}'.format(time_placement)]

    print('Placement of ' + application + ' is finished!', len(services), time_placement, datetime.datetime.now())
    count += 1

print('Placements Finished!!!')

import pickle
with open('m1_linear_exp_'+topology+'.pkl', 'wb') as f:
    pickle.dump(dict_placements, f)

# dict to csv
import csv
w = csv.writer(open('m1_linear_exp_'+topology+'.csv', 'w'))
for key, val in dict_placements.items():
    w.writerow([key, val])

now = datetime.datetime.now()
print('End at:', now.strftime("%Y-%m-%d %H:%M:%S"))
