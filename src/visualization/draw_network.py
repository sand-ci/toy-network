import numpy as np
import networkx as nx
import matplotlib as mpl
import matplotlib.pyplot as plt
from pathlib import Path
from cycler import cycler
from itertools import combinations
import src.data.make_network as mn

PROJECT_ROOT = Path.cwd().parent
node_color = { 'normal': '#484848',
#                 'perfsonar': '#8c564b',
                'perfsonar': '#0a7cb3',
                'hub': '#9467bd',
                'src': '#0a7cb3',
                'dest': '#ff2b83',
                'srcdest': '#ad2bff',
                'bad': '#ff832b' }
edge_style_cycle = list(cycler('ls', ['-', '--', ':', '-.']) 
                        * mpl.rcParams['axes.prop_cycle'])

# https://stackoverflow.com/questions/58173295/how-to-make-x-and-y-axes-appear-with-networkx-nx-draw
def draw_network(G, edge_label=None, paths=True, ps_pairs=[]):
    file_name = G.graph['name'] + '.' + G.graph['version'] + '.png'
    file_path = str(PROJECT_ROOT / 'reports' / 'figures' / file_name)
    
    # Node labels, location and color
    label_dict = dict(zip(list(G.nodes()),list(G.nodes())))
    pos_dict = nx.get_node_attributes(G, 'coordinates')
    node_colors = make_node_color_list(G, ps_pairs)

    # Edge
    if paths:
        op_edges, op_colors, op_ls, mp_edges, mp_colors, mp_ls, np_edges = make_edge_style_lists(G, ps_pairs)
    else:
        np_edges = G.edges

    fig, ax = plt.subplots(figsize=(12,12))
    plt.title(G.graph['name'] + ' version: '+ G.graph['version'])

    # Draw nodes and normal edges
    nx.draw(G, pos_dict, labels=label_dict, node_size=250, ax=ax, font_size=10, font_color='w', 
            node_color=node_colors, edgelist=np_edges)

    if paths:
        # Draw path edges
        nx.draw(G, pos_dict, nodelist=[], ax=ax, edgelist=op_edges, style=op_ls, 
                edge_color=op_colors, width=3)
        nx.draw(G, pos_dict, nodelist=[], ax=ax, edgelist=mp_edges, style=mp_ls, 
                edge_color=mp_colors, width=3, alpha = .5)

    if edge_label:
        nx.draw_networkx_edge_labels(G, pos_dict, edge_labels=nx.get_edge_attributes(G, edge_label), rotate=False)

    ax.set_axis_on()
    ax.tick_params(left=True, bottom=True, labelleft=True, labelbottom=True)
    
    plt.savefig(file_path)

    
def make_node_color_list(G, ps_pairs):
    color_list = []
    ps_nodes = []
    if ps_pairs:
        for pair in ps_pairs:
            ps_nodes.extend([pair[0], pair[1]])
    else:
        ps_nodes = G.graph['psnodes']
    for node in G.nodes():
        if G.nodes[node]['hub']:
            color_list.append(node_color['hub'])
        elif G.nodes[node]['perfsonar'] and node in ps_nodes:
            color_list.append(node_color['perfsonar'])
        else:
            color_list.append(node_color['normal'])
            
    return color_list


def make_edge_style_lists(G, ps_pairs=[]):
    ps_pairs = mn.path_edgelist(G, ps_pairs)

    # Edges that have one path
    op_edges = []
    op_colors = []
    op_ls = []

    # Edges that have multiple paths
    mp_edges = []
    mp_colors = []
    mp_ls = []

    # Edges not on any paths
    np_edges = []

    paths = {}
    i = 0
    
    for edge in G.edges():
        if 'paths' in G.edges[edge[0], edge[1]]:
            on_path = False
            path = G.edges[edge[0], edge[1]]['paths'][0]
            if path in ps_pairs:
                if path not in paths:
                    paths[path] = edge_style_cycle[i % len(edge_style_cycle)]
                    i += 1
                op_colors.append(paths[path]['color'])
                op_ls.append(paths[path]['ls'])
                op_edges.append(edge)
                on_path = True

            if len(G.edges[edge[0], edge[1]]['paths']) > 1:
                for path in G.edges[edge[0], edge[1]]['paths'][1:]:
                    if path in ps_pairs:
                        if path not in paths:
                            paths[path] = edge_style_cycle[i % len(edge_style_cycle)]
                            i += 1
                        mp_colors.append(paths[path]['color'])
                        mp_ls.append(paths[path]['ls'])
                        mp_edges.append(edge)
                        on_path = True
            
            if not on_path:
                np_edges.append(edge)
        else:
            np_edges.append(edge)
    return op_edges, op_colors, op_ls, mp_edges, mp_colors, mp_ls, np_edges
    
