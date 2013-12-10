# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <markdowncell>

# #Casetree plot
# 
# * Caitlin Rivers
# 
# * Virginia Bioinformatics Institute at Virginia Tech
# 
# * [cmrivers@vbi.vt.edu](cmrivers@vbi.vt.edu)
# 
# -------------
# 
# Casetrees are a type of plot I've developed^ to visualize case clusters in an outbreak. They are particularly useful for visualizing emerging zoonoses.
# 
# My wish list for improvements includes:
# 
# * add an option to include nodes that have no secondaries, i.e. are not part of a human to human cluster
# 
# * improve spacing so that nodes are fanned out more evenly, particularly when there are a lot of secondary nodes
# 
# * reduce overlap of nodes
# 
# * create a legend to label which colors correspond to which node attributes
# 
# * improve color choice so it produces a more reliablely attractive color palette
# 
# ^ *I have seen similar examples in the literature, so I am not the first to think of this. See Antia et al (Nature 2003).*

# <codecell>

from __future__ import division
import pandas as pd
import numpy as np
from random import choice
import matplotlib as mpl
import matplotlib.pyplot as plt
import networkx as nx

#optional, if you have mpltools installed
#from mpltools import style 
#style.use('ggplot')

# <markdowncell>

# The network data used for this plot is generated by cluster_builder.py, which is available in cmrivers/epipy. The data used are from the 2013 MERS-CoV outbreak (data also available in repo).

# <codecell>

def example_data():
    epi = pd.load('../cluster_network.pkl')
    epi.time = pd.to_datetime(epi.time)
    epi['pltdate'] = [mpl.dates.date2num(i) for i in epi.time]

    return epi

# <markdowncell>

# Build a directed graph from the case id and the source id. Node color is determined by node attributes, e.g. case severity or gender.

# <codecell>

def build_graph(df, case_id, color, index, source, date):
    """
    Generate graph from data on transmission tree.
    df = pandas dataframe """
    G = nx.DiGraph()
    G.add_nodes_from(df[case_id])
    
    edgelist = [pair for pair in df[[source]].dropna().itertuples()]
    G.add_edges_from(edgelist)
    nx.set_node_attributes(G, date, df[date].to_dict())
    nx.set_node_attributes(G, source, df[source].to_dict())
    nx.set_node_attributes(G, color, df[color].to_dict())
    
    G = nx.DiGraph.reverse(G)
    
    return G

# <codecell>

def plotting(G, node_size='on'):
    """ 
    Plot casetree
    G = networkx object
    node_size = on (display node) or off (display edge only). Default is on.
    """
    fig = plt.figure()
    fig.set_size_inches(12, 8)
    ax = fig.add_axes([1, 1, 1, 1])
    ax.xaxis_date()
    ax.set_aspect('auto')

    axprop =  plt.axis()

    mycoords = _layout(G, axprop)
    plt.ylim(ymin=-.05, ymax=max([value[1] for value in mycoords.itervalues()])+1)
     
    values, legend = _colors(G, 'color') #this legend doesn't actually do anything. 
    
    if node_size == 'on':
        node_size = 200
    elif node_size == 'off':
        node_size = 0
        
    nx.draw_networkx(G, with_labels=False, pos=mycoords, node_color = values, node_size=node_size, alpha=.4)

    fig.autofmt_xdate()
    

# <codecell>

def _colors(G, color):
    """
    Determines colors of the node based on node attribute, e.g. case severity or gender.
    G = networkx object
    color = name of node attribute in the graph that will be used to assign color
    """
    vals = []
    for node in G.nodes():
        vals.append(G.node[node]['color'])
            
    possibilities = [i for i in np.random.rand(len(vals),1)]
    val_map = {}
    for node in G.nodes():
        pick = choice(possibilities)
        val_map[G.node[node]['color']] = pick        
        possibilities.remove(pick)

    values = []
    legend = {}
    for node in G.nodes():
        color = G.node[node]['color']
        G.node[node]['new_color'] = val_map[color]
        values.append(G.node[node]['new_color'])
        
        if G.node[node]['color'] not in legend:
            legend[G.node[node]['color']] = G.node[node]['new_color']
    
    return values, legend

# <codecell>

def _generations(G, node):
    """ Determines the generation of the node, e.g. how many links up the chain of transmission it is. This value is used as the y coordinate.
    G = networkx object
    node = node in network
    """
    levels = 0
    
    while node != G.node[node]['source_node']:
        node = G.node[node]['source_node']
        levels += 1
        
    return levels

# <markdowncell>

# This is the heart of the spacing. This is where changes need to be made to improve the layout.

# <codecell>

def _layout(G, axprop):
    """Determine x and y coordinates of each node.
    G = networkx object
    axprop = matplotlib axis object
    """
    
    positions = []
    
    for i in G.nodes():
        # if node does not have a source, assume it is the index node of a cluster. Position it at generation 0 along the y axis.
        if np.isnan(G.node[i]['source_node']) == True:
            lst = [G.node[i]['date'], 0.1]
            
        else:
            # if node does have a source, assume it is a secondary case in a cluster.
            # determine the generation of the node by tracing down the transmission tree (see _generations())
            # if the coordinates this generates already exist, jitter the x and y coordinates to make space
            degree = G.out_degree(i)/90 #this does not do anything, but I hope to use angles to improve the node spacing
            ix = G.node[i]['source_node']
            ycord = _generations(G, i)
            xcord = G.node[ix]['pltdate']
            
            xrng = axprop[1] - axprop[0]
            jitter = random.uniform(-1*xrng/len(G.nodes()), xrng/len(G.nodes()))
            
            if ycord > 1: #do not jitter index nodes
                try:
                    xcord = G.node[ix]['xcord'] #this finds the xcord of the source node, which will position the secondary node directly above it.
                except: 
                    xcord = xcord
            else:
                if [xcord, ycord] in positions:
                    xcord = xcord + jitter
                    ycord = ycord + random.uniform(-.2, .2, 1)
          
            lst = [xcord, ycord]
        
        G.node[i]['xcord'] = xcord
        positions.append(lst)

        
    return dict(zip(G, np.array(positions)))

# <markdowncell>

# Wish list: generate a legend so we know {'color':'node attribute'}

# <codecell>

df = example_data()
G = build_graph(df, color='color', case_id='case_id', source='source_node', index='index_node', date='pltdate')
testplot = plotting(G,  node_size='on')
plt.title('MERS-CoV clusters')
plt.ylabel('Generations')
plt.savefig('../casetree.png', bbox_inches='tight')

# <codecell>


