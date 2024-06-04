# This module gets the data and build network graphs for 
# topology network and services choreography

# import libraries

import numpy as np
import networkx as nx

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches

def create_graph_topology(df_net, df_edges):
    
    G = nx.Graph()

    # create a column named hop in df_edges 
    df_edges['hop'] = 1

    # Add nodes
    for i in range(len(df_net)):
        x = df_net.iloc[i, 1]
        y = df_net.iloc[i, 2]
        G.add_node(i,pos=(x,y))

    # Add edges
    for i in range(len(df_edges)):
        s = df_edges.iloc[i, 1]
        d = df_edges.iloc[i, 2]
        w = df_edges.iloc[i, 4]
        b = df_edges.iloc[i, 3]
        h = df_edges.iloc[i, 5]

        # format precision of weights
        w = float("{:.2f}".format(w))
        # b = float("{:.2f}".format(b))
        G.add_edge(s, d, latency=w, bandwidth=b, hop=h)

    return G

def create_graph_services(df_chgph):
    
    G = nx.DiGraph()

    # Add edges
    for i in range(len(df_chgph)):
        s = df_chgph.iloc[i, 1]
        d = df_chgph.iloc[i, 2]
        p = df_chgph.iloc[i, 3]

        # format precision of weights
        p = float("{:.2f}".format(p))
        G.add_edge(s, d, payload=p)

    return G

def floyd_warshall(G, weight='latency'):
    # get the shortest path 
    dists = nx.floyd_warshall_numpy(G, weight=weight)

    return dists

def floyd_warshall_all(G):
    # get the shortest path 
    dists_bw = nx.floyd_warshall_numpy(G, weight='bandwidth')
    dists_lt = nx.floyd_warshall_numpy(G, weight='latency')
    dists_hp = nx.floyd_warshall_numpy(G, weight='hop')

    return dists_bw, dists_lt, dists_hp

def plot_data_graph(G, Pos=False, GreenList=[], edgeWight='latency', title='Plotting Data', colorNodes='lightblue', nodeSize=300):
    fig = plt.figure(1, figsize=(20, 12), dpi=60)
    
    if Pos:
        pos = nx.get_node_attributes(G, 'pos')
        nx.draw_networkx(G, pos, node_size=300, node_color='LightCoral')
        nx.draw_networkx_nodes(G, pos, node_size=300, nodelist=GreenList, node_color='LightGreen')
        nx.draw_networkx_labels(G, pos, font_color='white')
        labels = nx.get_edge_attributes(G,edgeWight)
        nx.draw_networkx_edge_labels(G,pos,edge_labels=labels)
    else:
        # Draw the graph
        pos = nx.spring_layout(G)  # Layout algorithm
        labels = nx.get_edge_attributes(G,edgeWight)
        nx.draw_networkx_edge_labels(G,pos,edge_labels=labels)
        nx.draw_networkx(G, pos, with_labels=True, node_size=nodeSize, node_color=colorNodes, font_size=10, font_color='darkblue', edge_color='gray')

    plt.title(title, fontsize=15)
    plt.show()

def plot_topology(G, greenList=[], alocatedList=[], netPath=[], edgeWight='latency', nodesColor='LightCoral', title='Topology'):
    pos=nx.get_node_attributes(G,'pos')
    fig = plt.figure(1, figsize=(20, 12), dpi=60)
    nx.draw_networkx_nodes(G, pos, label=True)
    nx.draw_networkx_labels(G, pos, font_color='black')
    nx.draw_networkx_edges(G, pos, alpha=0.5)

    # Show latency in the graph
    labels = nx.get_edge_attributes(G,edgeWight)
    nx.draw_networkx_edge_labels(G,pos,edge_labels=labels)

    nx.draw_networkx_nodes(G, pos, node_size=300, node_color=nodesColor)
    nx.draw_networkx_nodes(G, pos, node_size=300, nodelist=greenList, node_color='LightGreen')
    nx.draw_networkx_nodes(G, pos, node_size=300, nodelist=alocatedList, node_color='gold')

    nx.draw_networkx_edges(
        G,
        pos,
        edgelist=netPath,
        width=8,
        alpha=0.5,
        edge_color="tab:blue",
    )
    plt.title(title, fontsize=15)

    # plot legend nodes
    red_patch = mpatches.Patch(color='red', label='Out of selection')
    green_patch = mpatches.Patch(color='green', label='Pre-selected nodes')
    gold_patch = mpatches.Patch(color='gold', label='Selected nodes: ' + str(alocatedList))
    plt.legend(handles=[red_patch, green_patch, gold_patch])
    plt.show()

# Get network path
def path_to_network_path(lst):
    network_path = []
    for sublist in lst:
        pairs = zip(sublist, sublist[1:])
        for pair in pairs:
            network_path.append(pair)
    return network_path

# Calculating latency
def get_path_weight(G, network_path, weight='latency'):
    latency = 0
    for edge in network_path:
        latency += G[edge[0]][edge[1]][weight]
    return latency

def get_path_list(G, allocated_nodes):
    fog_path_list = []
    for i in range(len(allocated_nodes)-1):
        fog_path_list.append((nx.shortest_path(G, allocated_nodes[i], allocated_nodes[i+1])))

    fog_path_list = path_to_network_path(fog_path_list)
    return fog_path_list

def count_distinct_edges(path_list):
    distinct_pairs = set()
    
    for pair in path_list:
        distinct_pairs.add(tuple(sorted(pair))) # sort to avoid duplicates
    
    return len(distinct_pairs)

def count_repeted_edges(path_list):
    repeted_edges = {}
    
    for pair in path_list:
        if pair in repeted_edges:
            repeted_edges[pair] += 1
        else:
            repeted_edges[pair] = 1
    
    repeted_edges = {k: v for k, v in repeted_edges.items() if v > 1}
    
    return len(repeted_edges)


def calc_latecy(G, allocated_nodes, weight='latency'):
    fog_path_list = get_path_list(G, allocated_nodes)
    network_path = path_to_network_path(fog_path_list)
    return get_path_weight(G, network_path, weight=weight)