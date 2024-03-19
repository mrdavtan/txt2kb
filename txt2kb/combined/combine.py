#!/bin/env python3

from pyvis.network import Network
import re
import glob
from datetime import datetime

def extract_data_from_html(html_path):
    """Extract nodes and edges data from a given HTML file path."""
    nodes, edges = [], []
    with open(html_path, 'r', encoding='utf-8') as file:
        content = file.read()
        # Extracting nodes
        nodes_match = re.search(r"nodes = new vis\.DataSet\((.*?)\);", content, re.DOTALL)
        if nodes_match:
            nodes_str = nodes_match.group(1)
            nodes = eval(nodes_str)
        # Extracting edges
        edges_match = re.search(r"edges = new vis\.DataSet\((.*?)\);", content, re.DOTALL)
        if edges_match:
            edges_str = edges_match.group(1)
            edges = eval(edges_str)
    return nodes, edges

def combine_networks(html_files):
    """Combine nodes and edges from multiple HTML files into a single network."""
    combined_nodes = []
    combined_edges = []
    for html_file in html_files:
        nodes, edges = extract_data_from_html(html_file)
        combined_nodes.extend(nodes)
        combined_edges.extend(edges)
    # Removing potential duplicates
    combined_nodes = [dict(t) for t in {tuple(node.items()) for node in combined_nodes}]
    combined_edges = [dict(t) for t in {tuple(edge.items()) for edge in combined_edges}]
    return combined_nodes, combined_edges

def create_combined_network(nodes, edges, output_html='combined_network.html'):
    net = Network(directed=True, width="3000px", height="2000px", bgcolor="#eeeeee")
    for node in nodes:
        n_id = node.get('id')
        node.pop('id', None)
        net.add_node(n_id, **node)
    for edge in edges:
        from_id = edge.get('from')
        to_id = edge.get('to')
        edge.pop('from', None)
        edge.pop('to', None)
        net.add_edge(from_id, to_id, **edge)
    # Get current date and time
    current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Update output file name with date and time
    output_html = f"combined_network_{current_datetime}.html"
    net.save_graph(output_html)
    print(f"Network visualization saved to {output_html}.")

# Assuming all your HTML files are in the same directory
html_files = glob.glob('/home/davtan/code/txt2kb/txt2kb/combined/*.html')

# Combining data from all HTML files
combined_nodes, combined_edges = combine_networks(html_files)

# Creating and saving the combined network
create_combined_network(combined_nodes, combined_edges)
