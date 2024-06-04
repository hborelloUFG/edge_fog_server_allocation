#!/usr/bin/env python
# coding: utf-8

import sys
sys.path.append('../../modules')  # Replace with the actual path to your module folder

import gurobipy as gp
import numpy as np
import pandas as pd
import time
import datetime

import my_data as dt
import my_placements as mp
import my_networks as mnet

np.set_printoptions(suppress=True)

columns = ['id', 'cpu', 'memory', 'storage', 'bandwidth']

topology = 'germany'
folder = 'orign/'

cp = 1
tempo = 30

def get_nodes_hops():
    df_nodes, df_edges = dt.get_topology(topology, capacity_percent=cp, folder= '../../..')

    nodes_data = df_nodes[columns].to_numpy().astype('float')
    G = mnet.create_graph_topology(df_nodes, df_edges)
    hops = mnet.floyd_warshall(G, weight='hops')
    
    return nodes_data, hops

def get_apps(application='App4'):

    df_services, df_choreog = dt.get_application(folder+application, folder= '../../..')
    services_data = df_services[columns].to_numpy().astype('float')
    
    for i, s in enumerate(services_data):
              services_data[i][0] = i
    return services_data

def get_placement_lp(nodes, services, hops, lp):

    qtd_nodes = len(nodes)
    qtd_services = len(services)

    m = gp.Model()
    m.setParam(gp.GRB.param.OutputFlag, 0)
    # m.setParam(gp.GRB.param.Threads, 4)
    m.setParam(gp.GRB.param.TimeLimit, 60*tempo)

    # define variables
    x = m.addVars(qtd_services, qtd_nodes, vtype=gp.GRB.BINARY, name='x')
    u = m.addVars(qtd_services, qtd_nodes, qtd_nodes, vtype=gp.GRB.BINARY, name='u')
    s = hops
    C = nodes
    d = services

    # objective function
    # $\displaystyle z = \sum_{j_1=1}^{n}\sum_{j_2=1}^{n}\sum_{i=2}^{m} s_{j_1,j_2} \cdot u^i_{j_1,j_2}$
    m.setObjective(gp.quicksum(s[j1, j2] * u[i, j1, j2] for j1 in range(qtd_nodes) for j2 in range(qtd_nodes) for i in range(qtd_services)), gp.GRB.MINIMIZE)

    # Constraints
    # $\displaystyle \sum\limits_{i=1}^{m}(d_{i,k} \cdot x_{i,j}) \leqslant C_{j,k}, \qquad \forall\ j = 1, \dots, n;  k = 1, \dots, 4$
    for j in range(qtd_nodes):
        for k in range(4):
            m.addConstr(gp.quicksum(d[i, k] * x[i, j] for i in range(qtd_services)) <= C[j, k])

    # $\displaystyle \sum\limits_{j=1}^{n}(x_{i,j}) = 1, \qquad \forall i \in \{2,3,...,m\}$
    for i in range(qtd_services):
        m.addConstr(gp.quicksum(x[i, j] for j in range(qtd_nodes)) == 1)

    # $\displaystyle x_{i-1,j_1} + x_{i,j_2} \leqslant u^i_{j_1,j_2}+1, \forall\ i = 2, \dots, m; j_1, j_2 = 1, \dots n$
    for i in range(1, qtd_services):
        for j1 in range(qtd_nodes):
            for j2 in range(qtd_nodes):
                m.addConstr(x[i-1, j1] + x[i, j2] <= u[i, j1, j2] + 1)

    # m.write('m3_model_' + str(lp) + '.lp')
    m.optimize()

    placements = []
    for i in range(qtd_services):
            for j in range(qtd_nodes):
                if round(x[i, j].x) > 0:
                    placements.append([j, i])

    # print the optimal solution number
    # print(m.Runtime)
    # print(m.SolCount)
    # print(m.ObjVal)
    # print status
    # print(gp.GRB.Status.OPTIMAL)

    # Get the status code of the solution
    status_code = m.getAttr("Status")

    return placements, m.Runtime, m.ObjVal, status_code

nodes, hops = get_nodes_hops()
dict_placements = dict()
now = datetime.datetime.now()
print('Start at:', now.strftime("%Y-%m-%d %H:%M:%S"))

for apps in range(0,20):
    a = 'App'+str(apps)

    print(a, end=' -- ')
    services = get_apps(application=a)
    p, t, s, o = (get_placement_lp(nodes, services, hops, apps))

    print(s, t, o, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    dict_placements[a] = p, t


import csv
w = csv.writer(open('m3_linear_exp_'+topology+'_'+str(tempo)+'min.csv', 'w'))
for key, val in dict_placements.items():
    w.writerow([key, val])

import pickle
with open('m3_linear_exp_'+topology+'_'+str(tempo)+'min.pkl', 'wb') as f:
    pickle.dump(dict_placements, f)

now = datetime.datetime.now()
print('End at:', now.strftime("%Y-%m-%d %H:%M:%S"))
