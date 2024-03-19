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
    unique_nodes = set()
    unique_edges = set()
    for html_file in html_files:
        nodes, edges = extract_data_from_html(html_file)
        for node in nodes:
            node_tuple = tuple(node.items())
            if node_tuple not in unique_nodes:
                combined_nodes.append(node)
                unique_nodes.add(node_tuple)
        for edge in edges:
            edge_tuple = tuple(edge.items())
            if edge_tuple not in unique_edges:
                combined_edges.append(edge)
                unique_edges.add(edge_tuple)
    return combined_nodes, combined_edges

def create_combined_network(nodes, edges, output_html='combined_network.html'):
    net = Network(directed=True, width="3000px", height="2000px", bgcolor="#333333")

    # Customize node appearance
    net.set_options("""
        var options = {
            "nodes": {
                "font": {
                    "color": "black"
                },
                "color": {
                    "highlight": {
                        "background": "#DDDDDD"
                    }
                }
            },
            "edges": {
                "color": {
                    "color": "#FAE833",
                    "highlight": "#FAE833"
                }
            }
        }
    """)

    node_ids = set()  # Keep track of node IDs
    for node in nodes:
        n_id = node.get('id')
        node.pop('id', None)
        node['color'] = "#AAAAAA"  # Set the color for each node
        net.add_node(n_id, **node)
        node_ids.add(n_id)  # Add node ID to the set
    for edge in edges:
        from_id = edge.get('from')
        to_id = edge.get('to')
        if from_id not in node_ids or to_id not in node_ids:
            print(f"Skipping edge: {from_id} -> {to_id} (missing node)")
            continue  # Skip the edge if either source or target node is missing
        edge.pop('from', None)
        edge.pop('to', None)
        net.add_edge(from_id, to_id, **edge)
    # Get current date and time
    current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Update output file name with date and time
    output_html = f"multiday_network_{current_datetime}.html"
    net.save_graph(output_html)
    print(f"Network visualization saved to {output_html}.")

# Assuming all your HTML files are in the same directory
html_files = glob.glob('/home/davtan/code/txt2kb/txt2kb/combined/*.html')

# Combining data from all HTML files
combined_nodes, combined_edges = combine_networks(html_files)

# Creating and saving the combined network
create_combined_network(combined_nodes, combined_edges)
