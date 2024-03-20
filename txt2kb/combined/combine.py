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
    net = Network(directed=True, width="3000px", height="2000px", bgcolor="#333333")
    added_node_ids = set()  # Track added nodes

    # Define network options, including node and edge styles
    options = """
    {
        "nodes": {
            "font": {
                "color": "black"
            },
            "color": {
                "border": "#2B7CE9",
                "background": "#AAAAAA",
                "highlight": {
                    "border": "#2B7CE9",
                    "background": "#AAAAAA"
                }
            }
        },
        "edges": {
            "color": {
                "color": "#FAE833",
                "highlight": "#FAE833"
            },
            "smooth": false
        }
    }
    """

    net.set_options(options)

    # Add nodes to the network, setting node color to #AAAAAA and including additional properties in the title
    for node_data in nodes:
        node_id = node_data['id']
        article_uuid = node_data.get('article_uuid', '')
        article_date = node_data.get('article_date', '')
        article_source = node_data.get('article_source', '')
        article_url = node_data.get('article_url', '')
        # Construct a detailed title with the additional properties
        detailed_title = f"UUID: {article_uuid}<br>Date: {article_date}<br>Source: {article_source}<br>URL: <a href='{article_url}' target='_blank'>{article_url}</a>"
        # Update node data with the detailed title and set color
        node_data['title'] = detailed_title
        node_data['color'] = "#AAAAAA"
        # Add the node to the network
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
    output_html = f"multiday_network_{current_datetime}.html"
    net.save_graph(output_html)
    print(f"Network visualization saved to {output_html}.")

# Assuming all your HTML files are in the same directory
html_files = glob.glob('/home/davtan/code/txt2kb/txt2kb/*.html')

# Combining data from all HTML files
combined_nodes, combined_edges = combine_networks(html_files)

# Creating and saving the combined network
create_combined_network(combined_nodes, combined_edges)
