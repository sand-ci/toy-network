from datetime import datetime
from pathlib import Path
import networkx as nx
from networkx.algorithms.connectivity.edge_kcomponents import bridge_components
from networkx.algorithms.boundary import edge_boundary
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import euclidean_distances
from itertools import combinations
from copy import deepcopy
import re

PROJECT_ROOT = Path.cwd().parent

# Packet loss rates and the probability of their occurence taken from the sqrt of the counts given a month of Kibana data
pl = pd.read_csv(PROJECT_ROOT / "data" / "external" / "packetloss_distribution_kibana.csv")
pl['Count'] = pl['Count'].str.findall('(\d+)').apply("".join)
pl['Count'] = pl['Count'].astype(int)
pl['sqrt'] = np.sqrt(pl['Count'])
pl['sqrt_freq'] = pl['sqrt']/pl['sqrt'].sum()

pl_rate = pl['packet_loss'].tolist()
pl_prob = pl['sqrt_freq'].tolist()

# Latency rates and their probability are similarly derived
owd = pd.read_csv(PROJECT_ROOT / "data" / "external" / "OWD_histogram_offset.csv")
owd = owd.rename(columns={'Mean latency [ms]': 'latency'})
owd['latency'] = owd['latency'] + 50
owd['prob'] = owd['Count']/owd['Count'].sum()

latency_owd = owd['latency'].tolist()
latency_prob = owd['prob'].tolist()

# Hops are used to determine how much latency/packet loss to assign to a given edge
hops = pd.read_csv(PROJECT_ROOT / "data" / "external" / "hop_distribution_kibana.csv")
hops = hops.rename(columns={'n_hops: Descending': 'n_hops'})
hops['w_hops'] = hops['n_hops'] * hops['Count']
ave_hops = hops['w_hops'].sum() / hops['Count'].sum()


def load_network(name, version):
    if not version:
        graph_file = name + '.gz'
        graph_path = PROJECT_ROOT / 'data' / 'raw' / graph_file
    elif str(version).isnumeric():
        graph_file = name + '.' + str(version) + '.gz'
        graph_path = PROJECT_ROOT / 'data' / 'interim' / graph_file
    else:
        graph_file = name + '.' + str(version) + '.gz'
        graph_path = PROJECT_ROOT / 'data' / 'final' / graph_file

    G = nx.read_gml(graph_path)
    
    for edge in G.edges:
        if 'paths' in G.edges[edge]:
            if not isinstance(G.edges[edge]['paths'], list):
                G.edges[edge]['paths'] = [G.edges[edge]['paths']]
    
    return G


def save_network(G, version=0):
    if version:
        G.graph['version'] = str(version)
    
    if 'version' not in  G.graph:
        G.graph['version'] = '0'
        graph_file = G.graph['name'] + '.gz'
        graph_path = PROJECT_ROOT / 'data' / 'raw' / graph_file
    elif G.graph['version'].isnumeric():
        G.graph['version'] = str(int(G.graph['version']) + 1)
        graph_file = G.graph['name'] + '.' + G.graph['version'] + '.gz'
        graph_path = PROJECT_ROOT / 'data' / 'interim' / graph_file
    else:
        graph_file = G.graph['name'] + '.' + G.graph['version'] + '.gz'
        graph_path = PROJECT_ROOT / 'data' / 'final' / graph_file
    
    nx.write_gml(G, graph_path)
    return G


def make_detailed_network(graph_name="Network", total_size=100, max_neighbors=4, hub_depth=5, ps_nodes=10, k=1, path_criteria='latency'):
    G = make_network(graph_name, total_size, max_neighbors, hub_depth, k)
    G = add_perfsonar(G, ps_nodes)
    if G:
        G = add_shortest_paths(G, path_criteria)
        return G
    else:
        return make_detailed_network(graph_name, total_size, max_neighbors, hub_depth, ps_nodes, k)


def make_network(graph_name="Network", total_size=100, max_neighbors=4, hub_depth=5, k=1):
    G = nx.Graph(name=graph_name + "_" + str(datetime.timestamp(datetime.now())))

    # Generate hubs to serve as the backbone of the network
    G, index = add_hub(G, index=0, x_range=(0, total_size), y_range=(0, total_size), hub_depth=hub_depth)
    
    # Create nodes with random x and y coordinate attributes
    for n in range(0, total_size):
        if str(n) not in G.nodes():
            G.add_node(str(n), coordinates=(np.random.randint(0,total_size), np.random.randint(0,total_size)), hub=0, perfsonar=False)

    # Ensure nodes are sorted to before distances are calculated to allow indexing of source-destination pairs
    node_coordinates = sorted(nx.get_node_attributes(G, 'coordinates').items(), key=lambda x:int(x[0]))
    
    # https://stackoverflow.com/questions/54732086/finding-euclidean-distance-between-all-pair-of-points
    distances = np.array(euclidean_distances([c[1] for c in node_coordinates]))
    
    distances_dict = {}
    for i in range(len(node_coordinates)):
        temp_dict = {}
        for j in range(len(node_coordinates)):
            temp_dict[node_coordinates[j][0]] = distances[i][j]
        distances_dict[node_coordinates[i][0]] = temp_dict.copy()
            
    
    # https://stackoverflow.com/questions/16817948/i-have-need-the-n-minimum-index-values-in-a-numpy-array
    # This only works because we are numbering nodes sequentially from 0 (i.e., their key and their index is the same)
    closest_neighbors = [list(arr.argsort()[1:max_neighbors + 1]) for arr in distances]
    
    closest_neighbors_dict = {}
    for i in range(len(node_coordinates)):
        closest_neighbors_dict[node_coordinates[i][0]] = [str(n) for n in closest_neighbors[i]]
    
    for node in list(G.nodes()):
        neighbors = closest_neighbors_dict[node][:np.random.randint(1, max_neighbors + 1)]
        for neighbor in neighbors:
            add_detailed_edge(G, (node, neighbor))
    
    for edge in nx.k_edge_augmentation(G, k):
        add_detailed_edge(G, (edge[0], edge[1]))

    G = save_network(G)
    return G


def change_network(G, version = None, remove_ps_nodes=[], add_ps_nodes=[], remove_edges=[], add_edges=[]):
    G = deepcopy(G)
    
    if version:
        G.graph['version'] = version
    
    if remove_ps_nodes:
        for node in remove_ps_nodes:
            G = remove_perfsonar_node(G, node)
    
    if add_ps_nodes:
        for node in add_ps_nodes:
            G = add_perfsonar_node(G, node)
    
    if remove_edges:
        for edge in remove_edges:
            G.remove_edge(str(edge[0]), str(edge[1]))
    
    if add_edges:
        for edge in add_edges:
            add_detailed_edge(G, (edge[0], edge[1]))

    G = add_shortest_paths(G)
    return G


def add_detailed_edge(G, edge, latency=None, packetloss=None):
    if latency is None:
        latency = int(distance(G.nodes[str(edge[0])]['coordinates'], G.nodes[str(edge[1])]['coordinates']))
#         latency = int(np.random.choice(latency_owd, p=latency_prob) / ave_hops)

    if packetloss is None:
        packetloss = np.power(np.random.choice(pl_rate, p=pl_prob), (1 / ave_hops))
    G.add_edge(str(edge[0]), str(edge[1]), latency=latency, packetloss=packetloss)

    return G


def change_edge(G, edge, latency=None, packetloss=None):
    G = deepcopy(G)
    
    if latency is None:
        latency = G.edges[edge]['latency']

    if packetloss is None:
        packetloss = G.edges[edge]['packetloss']
    
    G = add_detailed_edge(G, edge, latency, packetloss)
    G = add_shortest_paths(G)
    return G


def add_hub(G, index, x_range, y_range, hub_depth, parent=None):
    G.add_node(str(index), coordinates=(np.random.randint(x_range[0], x_range[1]), np.random.randint(y_range[0], y_range[1])), hub=hub_depth, perfsonar=False)

    if parent is not None:
        add_detailed_edge(G, (index, parent))

    parent = str(index)
    index += 1
    
    if hub_depth:
        quadrants = np.random.choice([1, 2, 3, 4], np.random.randint(1,4))
        
        if 1 in quadrants:
            G, index = add_hub(G, index, (x_range[0], (x_range[1] + x_range[0]) / 2), (y_range[0], (y_range[1] + y_range[0]) / 2), hub_depth - 1, parent)
        if 2 in quadrants:
            G, index = add_hub(G, index, (x_range[0], (x_range[1] + x_range[0]) / 2), ((y_range[1] + y_range[0]) / 2, y_range[1]), hub_depth - 1, parent)
        if 3 in quadrants:
            G, index = add_hub(G, index, ((x_range[1] + x_range[0]) / 2, x_range[1]), (y_range[0], (y_range[1] + y_range[0]) / 2), hub_depth - 1, parent)
        if 4 in quadrants:
            G, index = add_hub(G, index, ((x_range[1] + x_range[0]) / 2, x_range[1]), ((y_range[1] + y_range[0]) / 2, y_range[1]), hub_depth - 1, parent)
    
    return G, index


def add_perfsonar(G, ps_nodes=10, override=False):
    graph_file = G.graph['name'] + '.gz'
    graph_path = PROJECT_ROOT / 'data' / 'raw' / graph_file
    G.graph['psnodes'] = []
    
    # Subgraphs that are connected by only one edge
    subgraphs = [list(sg) for sg in bridge_components(G)]
    
    # If there are more subgraphs than PerfSonar nodes, we make a new network before doing further computation
    if len(subgraphs) > ps_nodes and not override:
        return
    
    # A dictionary with the betweenness value for each value (expensive)
    cbc = nx.betweenness_centrality(G)
    
    
    # To allow sorting on centrality, it needs to be callable as a function
    def centrality(node):
        return cbc[node]
    
    
    # To allow sorting subgraphs on size and centrality of first element (latter is needed for subgraphs of size 1)
    def size_centrality_sort(subgraph):
        return (len(subgraph), centrality(subgraph[0]))


    # Subgraphs sorted by centrality. Less central items should be favored for perfsonar nodes
    subgraphs = [sorted(sg, key=centrality) for sg in subgraphs]
    subgraphs.sort(key=size_centrality_sort)
    
    ps_count = 0
    for subgraph in subgraphs:
        i = 0
        ps_add = 1 + round((ps_nodes - len(subgraphs)) * len(subgraph) / G.number_of_nodes())

        while i < ps_add:
            node = subgraph[i]
            i += 1

            # Ensure perfsonar nodes aren't neighbors
            ps_neighbor = False
            for neighbor in G.neighbors(node):
                if G.nodes[neighbor]['perfsonar']:
                    ps_neighbor = True
                    break

            if not G.nodes[node]['hub'] and not ps_neighbor:
                G.nodes[node]['perfsonar'] = True
                G.graph['psnodes'].append(node)
                ps_count += 1
                ps_add -= 1
    
    ps_add = ps_nodes - ps_count
    while ps_add > 0:
        node = subgraphs[-1][i]
        i += 1
        
        # Ensure perfsonar nodes aren't neighbors
        ps_neighbor = False
        for neighbor in G.neighbors(node):
            if G.nodes[neighbor]['perfsonar']:
                ps_neighbor = True
                break

        if not G.nodes[node]['hub'] and not ps_neighbor:
            G.nodes[node]['perfsonar'] = True
            G.graph['psnodes'].append(node)
            ps_count += 1
            ps_add -= 1

    G = save_network(G)
    return G


def add_perfsonar_node(G, node):
    node = str(node)
    if node in G.nodes and node not in G.graph['psnodes']:
        G.graph['psnodes'].append(node)
        G.nodes[node]['perfsonar'] = True
    return G


def remove_perfsonar_node(G, node):
    node = str(node)
    if node in G.nodes and node in G.graph['psnodes']:
        G.graph['psnodes'].remove(node)
        G.nodes[node]['perfsonar'] = False
    return G


def add_shortest_paths(G, criteria='latency'):
    # Remove previous shortest paths
    for edge in G.edges:
        if 'paths' in G.edges[edge]: 
            G.edges[edge].pop('paths')
        if 'spaths' in G.graph:
            G.graph.pop('spaths')

    ps_pairs = combinations([node for node in G.graph['psnodes']], 2)
    sp = {}
    spaths = {}

    for pair in ps_pairs:
        # GML will not write unless this is a string
#         sp[str(pair)] = nx.shortest_path(G, pair[0], pair[1], weight='latency')
        try:
            sp[pair_to_string(pair)] = nx.shortest_path(G, pair[0], pair[1], weight='latency')
        except:
            pass
    
    for path in sp:
        str_path = string_to_pair(path)
        
        for i in range(len(sp[path])-1):
            src = sp[path][i]
            dest = sp[path][i+1]
            
            if 'paths' in G.edges[src, dest]: 
                G.edges[src, dest]['paths'].append(str_path)
            else:
                G.edges[src, dest]['paths'] = [str_path]

    G.graph['spaths'] = sp
    G = save_network(G)
    return G


def pair_to_string(pair):
    return 's' + pair[0] + 'd' + pair[1]


def string_to_pair(s):
    digit_list = re.findall('\d+', s)
    return str((digit_list[0], digit_list[1]))


def path_edgelist(G, ps_pairs=[]):
    if not ps_pairs:
        ps_pairs = [str(pair) for pair in combinations([node for node in G.graph['psnodes']], 2)]
    else:
        new_ps_pairs = []
        for pair in list(ps_pairs):
            new_ps_pairs.append(str((pair[0], pair[1])))
            new_ps_pairs.append(str((pair[1], pair[0])))
        ps_pairs = new_ps_pairs
    return ps_pairs


def get_path_lengths(G):
    path_hops = {}
    path_latency = {}
    path_pl = {}
    for e in G.edges:
        for path in combinations(G.graph['psnodes'], 2):
            path = str((path[0], path[1]))
            if 'paths' in G.edges[e] and path in G.edges[e]['paths']:
                if path in path_hops:
                    path_hops[path] = path_hops[path] + 1
                    path_latency[path] = path_latency[path] + G.edges[e]['latency']
                    path_pl[path] = path_pl[path] * (1 - G.edges[e]['packetloss'])
                else:
                    path_hops[path] = 1
                    path_latency[path] = G.edges[e]['latency']
                    path_pl[path] = (1 - G.edges[e]['packetloss'])
    return path_hops, path_latency, path_pl


def get_path_changes(G, H):
    path_changes = {}
    G_path_edges = []
    H_path_edges = []
    
    for path in G.graph['spaths']:
        for i in range(len(G.graph['spaths'][path]) - 1):
            src = G.graph['spaths'][path][i]
            dest = G.graph['spaths'][path][i+1]
            G_path_edges.append((src, dest))
            G_path_edges.append((dest, src))

    for path in H.graph['spaths']:
        for i in range(len(H.graph['spaths'][path]) - 1):
            src = H.graph['spaths'][path][i]
            dest = H.graph['spaths'][path][i+1]
            H_path_edges.append((src, dest))
            H_path_edges.append((dest, src))
    
    # Convert to dict and back to list to remove duplicates while maintaining order
    G_path_edges = list(dict.fromkeys(G_path_edges))
    H_path_edges = list(dict.fromkeys(H_path_edges))
    
    for path in H.graph['spaths']:
        if H.graph['spaths'][path] != G.graph['spaths'][path]:
            removed_edges = []
            added_edges = []
            
            # Create list of all edges in G's path (later pruned of persistent edges)
            for i in range(len(G.graph['spaths'][path])-1):
                src = G.graph['spaths'][path][i]
                dest = G.graph['spaths'][path][i+1]
                removed_edges.append((src, dest))
            
            # Create list of removed edges
            for i in range(len(H.graph['spaths'][path])-1):
                src = H.graph['spaths'][path][i]
                dest = H.graph['spaths'][path][i+1]
                
                # Remove edges that are in H from the removed_edges list, add to the added_edges list if not in G
                if (src, dest) in removed_edges:
                    removed_edges.remove((src, dest))
                elif (dest, src) in removed_edges:
                    removed_edges.remove((dest, src))
                else:
                    added_edges.append((src, dest))
            
            path_changes[string_to_pair(path)] = (removed_edges, added_edges)

    changed_edges = {}
    for path in path_changes:
        for edge in path_changes[path][0]:
            # Ensure that only edges completely removed from H are included
            if edge not in H_path_edges:
                edge_flipped = (edge[1], edge[0])
                if edge in changed_edges:
                    changed_edges[edge] = changed_edges[edge] + 1
                elif edge_flipped in changed_edges:
                    changed_edges[edge_flipped] = changed_edges[edge_flipped] + 1
                else:
                    changed_edges[edge] = 1

    return path_changes, changed_edges


# https://semantive.com/high-performance-computation-in-python-numpy-2/
# https://gist.github.com/SemantiveCode/de37c380367338871580da602dacf8ab
def distance(v, u):
    return sum((v_i - u_i)**2 for v_i, u_i in zip(v, u))**0.5


def edge_deletion_candidates(G):
    candidate_count = {}
    trimmed_candidate_count = {}

    for edge in G.edges:
        H = change_network(G, remove_edges=[edge])
        _, changed_edges = get_path_changes(G, H)
        edge_candidates = []

        if changed_edges:
            most_freq = max(changed_edges.values())
            
            # Only consider the most frequently removed edge as a candidate for the edge that was potentially deleted
            for e in changed_edges:
                if changed_edges[e] == most_freq:
                    edge_candidates.append(e)

            # Candidates if considering all removed edges
            if len(changed_edges) in candidate_count:
                candidate_count[len(changed_edges)] = candidate_count[len(changed_edges)] + 1
            else:
                candidate_count[len(changed_edges)] = 1

            # Candidates if considering only most frequent removed edges
            if len(edge_candidates) in trimmed_candidate_count:
                trimmed_candidate_count[len(edge_candidates)] = trimmed_candidate_count[len(edge_candidates)] + 1
            else:
                trimmed_candidate_count[len(edge_candidates)] = 1

    return trimmed_candidate_count, candidate_count

