import json
import pandas
import networkx as nx


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
    node_df = df.join(enriched_df)
    node_df["product_node_name"] = node_df.apply(lambda s: f"{s['product_name']}.{s['name']}", axis=1)
    return node_df


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


def extract_dataframes(manifest):
    node_df = read_node_graph(manifest)

    G = read_graph(manifest)
    edge_df = nx.to_pandas_edgelist(G).reset_index()
    edge_df = pandas.merge(
        edge_df,
        node_df.rename(columns={c: f"source_{c}" for c in node_df.columns}),
        left_on="source",
        right_index=True,
    )
    edge_df = pandas.merge(
        edge_df,
        node_df.rename(columns={c: f"target_{c}" for c in node_df.columns}),
        left_on="target",
        right_index=True,
    )
    edge_df["is_internal_edge"] = (
        edge_df["source_product_name"] == edge_df["target_product_name"]
    )
    return node_df, edge_df


def construct_product_df(node_df, edge_df):
    # Build the product dataframe
    product_df = node_df.groupby(["product_name"]).agg(
        node_count=("unique_id", "count"),
        product_layers=("product_layer", pandas.Series.nunique),
        product_category=("product_category", "first"),
        dbt_package=("package_name", "first"),
    )

    count_internal_edges = (
        edge_df.loc[edge_df["is_internal_edge"]]
        .groupby("source_product_name")
        .agg(count_internal_edges=("source_product_name", "count"))
    )
    count_output_edges = (
        edge_df.loc[edge_df["is_internal_edge"] == False]
        .groupby("source_product_name")
        .agg(
            count_output_edges=("target_product_name", "count"),
            count_output_products=("target_product_name", pandas.Series.nunique),
        )
    )
    count_input_edges = (
        edge_df.loc[edge_df["is_internal_edge"] == False]
        .groupby("target_product_name")
        .agg(
            count_input_edges=("source_product_name", "count"),
            count_input_products=("source_product_name", pandas.Series.nunique),
        )
    )

    product_df = (
        product_df.join(count_internal_edges)
        .join(count_output_edges)
        .join(count_input_edges)
        .fillna(0)
    )
    return product_df


def create_product_graph(edge_df):
    gdf = (
        edge_df.groupby(["source_product_name", "target_product_name"])
        .agg(weight=("source", "count"))
        .reset_index()
    )
    G = nx.DiGraph()
    for ii, s in gdf.iterrows():
        G.add_edge(
            s["source_product_name"], s["target_product_name"], weight=s["weight"]
        )
    return G
