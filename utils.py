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


def read_manifest(p):
    with open(p, "r") as f:
        manifest = json.loads(f.read())
    return manifest


def read_node_graph(manifest, product_exclusions=[]):
    df1 = pandas.DataFrame.from_dict(manifest["nodes"], orient="index")
    df2 = pandas.DataFrame.from_dict(manifest["sources"], orient="index")
    df = df1.append(df2)
    df = df.loc[df["resource_type"].isin(["seed", "source", "model"])]
    enriched = df["fqn"].apply(
        extract_attributes, product_exclusions=product_exclusions
    )
    enriched_df = pandas.DataFrame.from_dict(enriched.to_dict(), orient="index")
    return df.join(enriched_df)


def read_graph(manifest):
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

    data_graph = extract_data_graph(G)

    return data_graph


def extract_data_graph(G):
    "Returns subset of graph containing data nodes"
    allowed_resources = ["seed", "source", "model"]
    data_nodes = [
        n for n, e in G.nodes(data=True) if e.get("resource_type") in allowed_resources
    ]
    return G.subgraph(data_nodes)


def extract_attributes(fqn, product_exclusions: list = []):
    enriched = {
        "product_category": None,
        "product_layer": None,
        "product_name": None,
    }
    if fqn[1] in product_exclusions or len(fqn) < 4:
        return enriched

    enriched["product_category"] = fqn[1]
    enriched["product_layer"] = fqn[3] if len(fqn) > 4 else "_root_"
    enriched["product_name"] = fqn[1] + "." + fqn[2]
    return enriched


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
