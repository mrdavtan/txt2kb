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
            for node in nodes:
                node['article_uuid'] = node.get('article_uuid', '')
                node['article_date'] = node.get('article_date', '')
                node['article_source'] = node.get('article_source', '')
        # Extracting edges
        edges_match = re.search(r"edges = new vis\.DataSet\((.*?)\);", content, re.DOTALL)
        if edges_match:
            edges_str = edges_match.group(1)
            edges = eval(edges_str)
    return nodes, edges

def combine_networks(html_files):
    """Combine nodes and edges from multiple HTML files into a single network."""
    combined_nodes, combined_edges = [], []
    unique_uuids = set()
    for html_file in html_files:
        nodes, edges = extract_data_from_html(html_file)
        for node in nodes:
            if node['id'] not in unique_uuids:  # Ensure unique nodes by ID
                combined_nodes.append(node)
                unique_uuids.add(node['id'])
        combined_edges.extend(edges)
    return combined_nodes, combined_edges

def create_combined_network(nodes, edges, output_html='combined_network.html'):
    net = Network(directed=True, width="3000px", height="2000px", bgcolor="#eeeeee")
    added_node_ids = set()  # Track added nodes

    # Add nodes to the network
    for node_data in nodes:
        node_id = node_data['id']
        net.add_node(node_id, **node_data)
        added_node_ids.add(node_id)  # Remember added nodes

    # Add edges to the network, ensuring both nodes exist
    for edge in edges:
        from_id = edge.pop('from')
        to_id = edge.pop('to')
        if from_id in added_node_ids and to_id in added_node_ids:
            net.add_edge(from_id, to_id, **edge)
        else:
            print(f"Skipping edge from {from_id} to {to_id}: One or both nodes not found.")

    # Save and print the network visualization's file name
    current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_html = f"combined_network_{current_datetime}.html"
    net.save_graph(output_html)
    print(f"Network visualization saved to {output_html}.")

# Assuming all your HTML files are in the same directory
html_files = glob.glob('/home/davtan/code/txt2kb/txt2kb/*.html')

# Combining data from all HTML files
combined_nodes, combined_edges = combine_networks(html_files)

# Creating and saving the combined network
create_combined_network(combined_nodes, combined_edges)

