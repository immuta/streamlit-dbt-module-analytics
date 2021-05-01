import json
import networkx as nx
import pandas

# Shapes; https://graphviz.org/doc/info/shapes.html
node_formats = [
    {
        "shape": "box",
        "fillcolor": "white",
        "fontcolor": "black",
        "color": "green",
        "style": "filled",
    },
    {
        "shape": "ellipses",
        "fillcolor": "white",
        "fontcolor": "black",
        "color": "black",
        "style": "filled",
    },
    {
        "shape": "cds",
        "fillcolor": "white",
        "fontcolor": "black",
        "color": "blue",
        "style": "filled",
    },
    {
        "shape": "cds",
        "fillcolor": "white",
        "fontcolor": "black",
        "color": "yellow",
        "style": "filled",
    },
    {
        "shape": "component",
        "fillcolor": "white",
        "fontcolor": "black",
        "color": "red",
        "style": "filled",
    },
    {
        "shape": "note",
        "fillcolor": "white",
        "fontcolor": "black",
        "color": "teal",
        "style": "filled",
    },
    {
        "shape": "diamond",
        "fillcolor": "white",
        "fontcolor": "black",
        "color": "orange",
        "style": "filled",
    },
    {
        "shape": "diamond",
        "fillcolor": "white",
        "fontcolor": "black",
        "color": "purple",
        "style": "filled",
    },
]



def read_graph(p="manifest.json"):
    with open(p, "r") as f:
        manifest = json.loads(f.read())

    G = nx.DiGraph()
    for n, d in manifest["nodes"].items():
        G.add_node(n, **d)
    for n, d in manifest["sources"].items():
        G.add_node(n, **d)
    for n, d in manifest["exposures"].items():
        G.add_node(n, **d)

    for n, children in manifest["child_map"].items():
        for child in children:
            G.add_edge(n, child)
    for n, parents in manifest["parent_map"].items():
        for parent in parents:
            G.add_edge(parent, n)
    
    return G

def extract_data_graph(G):
    "Returns subset of graph containing data nodes"
    allowed_resources = ["seed", "source", "model", "analysis", "snapshot"]
    data_nodes = [
        n for n, e in G.nodes(data=True) if e.get("resource_type") in allowed_resources
    ]
    return G.subgraph(data_nodes)

def extract_attributes(fqn, package_types: list):
    if fqn[1] not in package_types or len(fqn) < 4:
        raise IndexError("No match for %s", ".".join(fqn))
    data = {
        "dbt_project": fqn[0],
        "category": fqn[1],
        "name": fqn[2],
        "layer": fqn[3] if len(fqn) > 4 else "_root_",
        "package": fqn[1] + "." + fqn[2]
    }

    return data


def create_pydot_viz(
        G,
        selected_node=None,
        exclude_nodes=[],
        custom_formats = {}
    ):
    node_list = []
    node_str = ""
    G = G.subgraph(n for n in G.nodes if n not in exclude_nodes)

    for n, e in G.nodes(data=True):
        category = n.split('.')[0]
        formatting = custom_formats.get(category) #, node_formats["default"]).copy()
        formatting["label"] = n
        if n == selected_node:
            formatting["fillcolor"] = "green"
        format_str = " ".join(f'{k}="{v}"' for k, v in formatting.items())
        node_str += f'"{n}" [{format_str}]\n'
        node_list.append(n)

    edge_str = ""
    for u, v, e in G.edges(data=True):
        edge_str += '"{}" -> "{}" [label="{}"]\n'.format(u, v, e['weight'])

    dot_viz = f"""
    digraph models {{
        rankdir="LR"
        nodesep=0.1
        graph [margin=0 ratio=auto size=10]
        node [fontsize=10 height=0.25]
        edge [fontsize=10]
        {node_str}
        {edge_str}
    }}
    """
    return dot_viz