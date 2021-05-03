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


def create_pydot_viz(G, selected_node=None, exclude_nodes=[]):
    node_list = []
    node_str = ""
    G = G.subgraph(n for n in G.nodes if n not in exclude_nodes)

    categories = list(set(n.split(".")[0] for n in G.nodes))
    format_dict = dict(zip(categories, node_formats[: len(categories)]))

    for n, e in G.nodes(data=True):
        category = n.split(".")[0]
        formatting = format_dict.get(category)  # , node_formats["default"]).copy()
        formatting["label"] = n
        if n == selected_node:
            formatting["fillcolor"] = "green"
        format_str = " ".join(f'{k}="{v}"' for k, v in formatting.items())
        node_str += f'"{n}" [{format_str}]\n'
        node_list.append(n)

    edge_str = ""
    for u, v, e in G.edges(data=True):
        edge_str += '"{}" -> "{}" [label="{}"]\n'.format(u, v, e["weight"])

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
