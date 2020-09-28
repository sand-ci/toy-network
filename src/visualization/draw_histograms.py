import numpy as np
import pandas as pd
import networkx as nx
import matplotlib as mpl
import matplotlib.pyplot as plt
from pathlib import Path
from cycler import cycler
from itertools import combinations

plt.rcParams.update({'font.size': 16})

PROJECT_ROOT = Path.cwd().parent
colors = [color_dicts['color'] for color_dicts in list(mpl.rcParams['axes.prop_cycle'])]

# Load data to allow histogram comparisons
pl = pd.read_csv(PROJECT_ROOT / "data" / "external" / "packetloss_distribution_kibana.csv")
hops = pd.read_csv(PROJECT_ROOT / "data" / "external" / "hop_distribution_kibana.csv")
delay = pd.read_csv(PROJECT_ROOT / "data" / "external" / "OWD_histogram_offset.csv")

# Adjust labels and fix datatypes
hops = hops.rename(columns={'n_hops: Descending': 'n_hops'})
hops['Count'] = 6 * hops['Count'] / hops['Count'].max()
delay = delay.rename(columns={'Mean latency [ms]': 'latency'})
# delay['latency'] = delay['latency'] + 50
# delay['Count'] = 6 * delay['Count'] / delay['Count'].max()
pl['Count'] = pl['Count'].str.findall('(\d+)').apply("".join)
pl['Count'] = np.power(pl['Count'].astype(int), .5) #/ pl['Count'].astype(int).max()
pl['Count'] = 40 * pl['Count'] / pl['Count'].max()


# Converts a dictionary into a list of unique values and their count
def counter(dictionary):
    value_count = {}
    for value in dictionary.values():
        value = str(value)
        if value in value_count:
            value_count[value] = value_count[value] + 1
        else:
            value_count[value] = 1
    sorted_value_count = sorted([(int(value), value_count[value]) for value in value_count], 
                                key=lambda x:int(x[0]))
    return sorted_value_count


def packetloss_hist(name, *args):
    file_name = str(name) + 'packetloss_hist.png'
    file_path = str(PROJECT_ROOT / 'reports' / 'figures' / file_name)
    
    fig, ax = plt.subplots(figsize=(15, 10))
    i = 0
    hist_data = []
    legend_elements = []
    for arg in args:
        i += 1
        hist_data.append([arg[key] for key in arg.keys()])
        legend_elements.append(plt.Line2D([0], [0], color=colors[i], label='Toy Distribution ' + str(i)))

    if hist_data:
        plt.hist(hist_data, bins=20, color=colors[1 : i+1])

    ax1 = ax.twinx()

    pl.plot(ax=ax1, x='packet_loss', y='Count', kind='scatter', label='True distribution')
    legend_elements.append(plt.Line2D([0], [0], marker='o', color='tab:blue', label='True distribution (scaled)', markerfacecolor='tab:blue', markersize=3))

    ax.set_ylim(bottom=0, top=42)
    ax1.set_ylim(bottom=0, top=42)
    ax1.set_axis_off()

    ax.set_xlabel('Packet loss')
    ax.set_ylabel('Number of paths (normalized to toy max)')

    plt.title("Number of paths between PS nodes with a given packetloss rate")
    plt.legend(handles=legend_elements)
    plt.savefig(file_path)
    plt.show()


def hops_hist(name, *args):
    file_name = str(name) + 'hops_hist.png'
    file_path = str(PROJECT_ROOT / 'reports' / 'figures' / file_name)
    
    fig, ax = plt.subplots(figsize=(15,10))
    ax.set_xlabel('Number of Hops')
    ax.set_ylabel('Number of paths (normalized to toy max)')

    i = 0
    legend_elements = []
    width = 1 / (len(args) + 1)

    for arg in args:
        i += 1
        legend_elements.append(plt.Line2D([0], [0], color=colors[i], label='Toy Distribution ' + str(i)))
        lengths = counter(arg)
        hist_data = [length[1] for length in lengths]
        for length in lengths:
            for _ in range(length[1]):
                hist_data.append(length[0])
#         ax = plt.hist(hist_data, bins=20, color=colors[i], alpha=.5, label='Measured distr ' + str(i))
        plt.bar([length[0] + (i - .5) * width for length in lengths], [length[1] for length in lengths], width, color=colors[i], label='Toy distribution ' + str(i))

    ax.set_ylim(bottom=0, top=6.3)
    ax.set_xticks([i for i in range(23)])

    ax1 = ax.twinx()
    ax1.set_ylim(bottom=0, top=6.3)
    ax1.set_axis_off()
    
    hops.plot(ax=ax1, x='n_hops', y='Count', kind='scatter', label='True distribution')
    legend_elements.append(plt.Line2D([0], [0], marker='o', color='tab:blue', label='True distribution (scaled)', markerfacecolor='tab:blue', markersize=3))

    plt.title("Number of paths between PS nodes with a given number of hops")
    plt.legend(handles=legend_elements)
    plt.savefig(file_path)
    plt.show()
    

def latency_hist(name, *args):
    file_name = str(name) + 'latency_hist.png'
    file_path = str(PROJECT_ROOT / 'reports' / 'figures' / file_name)
    
    fig, ax = plt.subplots(figsize=(15, 10))
    i = 1
    delay.plot(ax=ax, x='latency', y='Count', kind='scatter')
    for arg in args:
        lengths = counter(arg)
        hist_data = []
        for length in lengths:
            for _ in range(length[1]):
                hist_data.append(length[0])
        ax = plt.hist(hist_data, bins=20, color=colors[i], alpha=.5)
#         ax = plt.scatter([length[0] for length in lengths], [length[1] for length in lengths], color=colors[i], label='Toy distribution ' + str(i))
        i += 1
    ax.set_xlabel("Latency (ms)")
    ax.set_ylabel("Number of paths")
    ax.axvline(x=0, linestyle='--', color='r')
    plt.title("Number of paths between PS nodes with a given latency")
    plt.savefig(file_path)
    plt.show()
    
    
def edges_hist(G):
    file_name = G.graph['name'] + '.' + G.graph['version'] + 'edges_hist.png'
    file_path = str(PROJECT_ROOT / 'reports' / 'figures' / file_name)
    
    ps_pairs = list(combinations(G.graph['psnodes'], 2))
    latency = {}
    packetloss = {}

    for edge in ps_pairs:
        latency[str(edge)] = 0
        packetloss[str(edge)] = 1

    for edge in G.edges:
        if 'paths' in G.edges[edge]:
            for path in G.edges[edge]['paths']:
                latency[path] = latency[path] + G.edges[edge]['latency']
                packetloss[path] = packetloss[path] * (1 - G.edges[edge]['packetloss'])

    for path in packetloss:
        packetloss[path] = 1 - packetloss[path]

    latency_keys = [str(key) for key in (list(latency.keys()))]
    latency_values = list(latency.values())
    pl_keys = [str(key) for key in list(packetloss.keys())]
    pl_values = list(packetloss.values())

    fig, axs = plt.subplots(2, 1, figsize=(25, 15))
    axs[0].bar(latency_keys, latency_values)
    axs[0].tick_params(labelrotation=60)
    axs[0].set_title('Total Latency')
    axs[1].bar(pl_keys, pl_values)
    axs[1].tick_params(labelrotation=60)
    axs[1].set_title('Percent Packetloss')

    plt.savefig(file_path)
    plt.show()
    

def candidate_hist(G, H, trimmed_candidate_count=[], candidate_count=[]):
    file_name = G.graph['name'] + '_' + G.graph['version'] + 'v' + H.graph['version'] + '_candidate_hist.png'
    file_path = str(PROJECT_ROOT / 'reports' / 'figures' / file_name)

    fig, ax = plt.subplots(2, 1, figsize=(10,10))
    fig.suptitle('Ambiguity when determining which edge was deleted from $G$ to create $H$')
    
    ax[0].bar(list(trimmed_candidate_count.keys()), trimmed_candidate_count.values())
    ax[0].set_xlabel('Number of potentially deleted edges')
    ax[0].set_ylabel('Trial count')
    ax[0].set_xticks([i for i in range(1, max(trimmed_candidate_count.keys()) + 1)])
    ax[0].set_title('Considering only the edges tied for most frequently removed from paths')
    
    ax[1].bar(list(candidate_count.keys()), candidate_count.values())
    ax[1].set_xlabel('Number of potentially deleted edges')
    ax[1].set_ylabel('Trial count')
    ax[1].set_xticks([i for i in range(1, max(candidate_count.keys()) + 1)])
    ax[1].set_title('Considering all edges no longer on any path in $H$')
    
    fig.tight_layout(rect=[0, 0.03, 1, 0.95])

    plt.savefig(file_path)
    plt.show()
    

def plot_traceroute_changes(edges_impacted, edge_removed):
    fig, ax = plt.subplots(figsize=(15, 7))

    ax.set_title('Impact of removing ' + str(edge_removed) + ' on traceroutes')
    ax.set_ylabel('Number of paths an edge was formerly on')
    ax.set_xlabel('Edges formerly on paths')

    ax.bar([str(edge) for edge in edges_impacted.keys()], edges_impacted.values())
    ax.tick_params(labelrotation=10)
    ax.set_yticks([i for i in range(int(max(edges_impacted.values()))+1)])

    file_name = 'Traceroute-' + str(edge_removed[0]) + '_' + str(edge_removed[1]) + '.png'
    plt.savefig(str(PROJECT_ROOT / 'reports' / 'figures' / file_name))
    plt.show()
    
