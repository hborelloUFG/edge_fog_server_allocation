import sys
sys.path.append('../../modules')  # Replace with the actual path to your module folder

# Verifica se pelo menos um argumento foi passado
if len(sys.argv) < 2:
    argumento = 1
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
    
    qtd_nodes = len(nodes)
    qtd_services = len(services)

    m = gp.Model()
    m.setParam(gp.GRB.param.OutputFlag, 0)
    # m.setParam(gp.GRB.param.Threads, 4)
    # m.setParam(gp.GRB.param.TimeLimit, 5*60)

    # define variables
    x = m.addVars(qtd_services, qtd_nodes, vtype=gp.GRB.BINARY, name='x')
    y = m.addVars(qtd_nodes, vtype=gp.GRB.BINARY, name='y')
    C = nodes
    d = services

    m.setObjective(
        gp.quicksum(
            gp.quicksum((y[j] * C[j][k])-(x[i,j] * d[i][k]) for j in range(qtd_nodes)) for i in range(qtd_services) for k in range(1, 5)
        ), gp.GRB.MINIMIZE
    )
    
    # define constraints
    m.addConstrs(gp.quicksum(x[i, j] for j in range(qtd_nodes)) == 1 for i in range(qtd_services))

    for k in range(1, 5):
        m.addConstrs(gp.quicksum(x[i, j] * services[i, k] for i in range(qtd_services)) <= nodes[j, k] for j in range(qtd_nodes))
    
    m.addConstrs(gp.quicksum(x[i, j] for i in range(qtd_services)) <= qtd_services * y[j] for j in range(qtd_nodes))

    # m.write('model.lp')
    m.optimize()
    
    # print solution
    placements = []
    nodes_allocated = []
    for i in range(qtd_services):
        for j in range(qtd_nodes):
            if round(x[i, j].x) > 0:
                placements.append([j, i])
                nodes_allocated.append(j)
    
    return placements, nodes_allocated, m.Runtime

folder = 'orign/'
topology = 'melbourne'
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
dict_placements_times = dict()

tax_sucess = 0

print('Nodes capacity reduced to '+str(cp*100)+'%' )

for i in range(0, 20):
    application = 'App' + str(i)
    df_services, df_choreog = dt.get_application(folder+application, folder= '../../..')

    services = df_services[columns].to_numpy()

    dict_applications[application] = services

    # sort dict_applications by length of services
    dict_sorted_applications = {k: v for k, v in sorted(dict_applications.items(), key=lambda item: len(item[1]))}

now = datetime.datetime.now()
print('Start at:', now.strftime("%Y-%m-%d %H:%M:%S"))
count = 1
for application, services in dict_sorted_applications.items():

    nodes = pd.DataFrame(df_nodes, columns=columns).to_numpy().astype('float')

    nodes_norm, services_norm = dt.normalize_data(nodes, services)

    # services_apps[application] = services
    placements, nodes_allocated, time_placement = get_placement_lp(nodes, services)

    dict_placements[application] = placements, ['{:.8f}'.format(time_placement)]
    dict_placements_times[application] = ['{:.8f}'.format(time_placement)]

    print(count,'- Placement of ' + application + ' is finished!', len(services), time_placement, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    # print(placements)
    count +=1

print('Placements Finished!!!')


import pickle
with open('m2_linear_exp_'+topology+'.pkl', 'wb') as f:
    pickle.dump(dict_placements, f)

# dict to csv
import csv
w = csv.writer(open('m2_linear_exp_'+topology+'.csv', 'w'))
for key, val in dict_placements.items():
    w.writerow([key, val])

now = datetime.datetime.now()
print('End at:', now.strftime("%Y-%m-%d %H:%M:%S"))

print(topology)




