# import libraries
import numpy as np

# This module prepare data to service placement

# update nodes capacities after placement
def update_nodes(nodes, placement):
    print(placement)
    for node in nodes:
        for p in placement:
            if node[0] == p[0]:
                node[1] = node[1] - p[1]
                node[2] = node[2] - p[2]
                node[3] = node[3] - p[3]
                node[4] = node[4] - p[4]

    print(nodes)

# get services and nodes allocated
def get_services_nodes_allocated(placements):
    services_placed = []
    nodes_allocated = []
    for value in placements:
        services_placed.append(value[0][:])
        nodes_allocated.append(value[1][:5])

    return services_placed, nodes_allocated

# get services and nodes allocated
def get_data_nodes_allocated(allocated_nodes, nodes):
    data_nodes_allocated = []
    
    for value in allocated_nodes:
        data_nodes_allocated.append(nodes[value][:5])

    return data_nodes_allocated

# Calculate the fit values for deploying the service on possible nodes
def calculate_best_fit(service, nodes):
    fit_values = []

    for node in nodes:
        
        # cpu_capacity = node[1] - service[1]
        # memory_capacity = node[2] - service[2]
        # storage_capacity = node[3] - service[3]
        # bandwidth_capacity = node[4] - service[4]

        cpu_capacity =  service[1] / node[1]
        memory_capacity =  service[2] / node[2]
        storage_capacity =  service[3] / node[3]
        bandwidth_capacity =  service[4] / node[4]

        # Calculate the fit value for each node
        fit_value = max(cpu_capacity, memory_capacity, storage_capacity, bandwidth_capacity)
        fit_values.append(fit_value)

    nodes_with_fit = np.insert(nodes, 5, fit_values, axis=1)
    nodes_with_fit = nodes_with_fit[nodes_with_fit[:, 5].argsort()]

    return nodes_with_fit


# get node with capacities to receive service and calculate best-fit of them
def get_nodes_with_best_fit(service, nodes):
    service_nodes = []

    for node in nodes:
        comparison = np.all(service[1:]<=node[1:])
        if comparison:
            # append nodes
            service_nodes.append(node)
            
    service_nodes = calculate_best_fit(np.array(service), np.array(service_nodes))
    return service_nodes

def get_nodes_best_fit_all(services, nodes):

    nodes_best_fit_all = np.zeros((len(services), len(nodes)))
    nodes_best_fit_all[nodes_best_fit_all == 0] = np.inf

    for i, service in enumerate(services):
        nodes_best_fit = get_nodes_with_best_fit(service, nodes)
        nodes_utilization = calc_resource_utilization2(service, get_nodes_satisfy(service, nodes))

        for j, n in enumerate(nodes_best_fit[:, 0]): 
            nodes_best_fit_all[i, j] = nodes_utilization[j]

    return nodes_best_fit_all

def calc_resource_utilization(service, nodes):
    # Calculate resource utilization using list comprehension
    resource_utilization = [
        (((service[1] / n[1]) * 100) + 
        ((service[2] / n[2]) * 100) + 
        ((service[3] / n[3]) * 100) + 
        ((service[4] / n[4]) * 100)) / 4
        for n in nodes
    ]

    return resource_utilization

def calc_resource_utilization2(service, nodes):

    resources_utilization = [(np.sum(service[1:]) / np.sum(n[1:]))*100 for n in nodes]

    return resources_utilization


# get node with capacities to receive service and calculate best-fit of them
def get_nodes_satisfy(service, nodes):
    nodes_satisfy = []

    for node in nodes:  
        comparison = np.all(service[1:]<=node[1:])
        if comparison:
            nodes_satisfy.append(node)
            
    return nodes_satisfy

def calc_global_resources_utilization(services, nodes):
    # Calculate resource utilization using list comprehension
    # sum all values of each column
    all_service = np.sum(services, axis=0)
    all_node = np.sum(nodes, axis=0)

    # calculate the resource utilization
    resource_utilization = (np.sum((all_service[1:])) / np.sum(all_node[1:]))

    return resource_utilization

def get_data_allocated_nodes(df_nodes, allocated_nodes):
    data_allocated_nodes = []
    for i in range (len(allocated_nodes)):
        # append to data_allocated_nodes nodes of df_nodes with id in allocated_nodes
        data_allocated_nodes.append(df_nodes[df_nodes['id'] == allocated_nodes[i]].to_numpy()[0])

    # tranform data_allocated_nodes to numpy array
    data_allocated_nodes = np.array(data_allocated_nodes)
    # drop columns 1 and 2
    data_allocated_nodes = np.delete(data_allocated_nodes, [1,2], axis=1)
    return data_allocated_nodes
