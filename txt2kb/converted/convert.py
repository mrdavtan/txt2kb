import json
import re
import sys
from datetime import datetime

def extract_data_from_html(html_file):
    with open(html_file, 'r') as file:
        html_content = file.read()

    # Extract nodes data
    nodes_match = re.search(r'nodes = new vis\.DataSet\(\[(.*?)\]\);', html_content, re.DOTALL)
    nodes_data = nodes_match.group(1)
    nodes = json.loads(f'[{nodes_data}]')

    # Extract edges data
    edges_match = re.search(r'edges = new vis\.DataSet\(\[(.*?)\]\);', html_content, re.DOTALL)
    edges_data = edges_match.group(1)
    edges = json.loads(f'[{edges_data}]')

    return nodes, edges

def convert_to_json(nodes, edges):
    # Convert nodes to the desired format
    formatted_nodes = []
    for node in nodes:
        formatted_node = {
            "id": node["id"],
            "label": node["label"],
            "color": node["color"],
            "shape": node["shape"]
        }
        formatted_nodes.append(formatted_node)

    # Convert edges to the desired format
    formatted_edges = []
    for edge in edges:
        formatted_edge = {
            "source": edge["from"],
            "target": edge["to"],
            "label": edge["label"],
            "title": edge["title"],
            "arrows": edge["arrows"]
        }
        formatted_edges.append(formatted_edge)

    # Create the final JSON structure
    json_data = {
        "nodes": formatted_nodes,
        "links": formatted_edges
    }

    return json_data

def save_json_to_file(json_data, output_file):
    with open(output_file, 'w') as file:
        json.dump(json_data, file, indent=2)

def main(html_file):
    nodes, edges = extract_data_from_html(html_file)
    json_data = convert_to_json(nodes, edges)

    # Generate the output JSON file name based on the current date and time
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    output_file = f"multiday_network_{timestamp}.json"

    save_json_to_file(json_data, output_file)
    print(f'Conversion completed. JSON data saved to {output_file}.')

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python script.py <input_html_file>')
        sys.exit(1)

    html_file = sys.argv[1]
    main(html_file)
