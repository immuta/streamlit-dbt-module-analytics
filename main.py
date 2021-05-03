#%%
import json
import matplotlib.pyplot as plt
import networkx as nx
import pandas
import seaborn as sns
import streamlit
import logging

from utils import (
    create_pydot_viz,
    extract_attributes,
    extract_data_graph,
    node_formats,
    read_graph,
    read_manifest,
    read_node_graph,
)

logging.basicConfig()


default_excludes = []


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
    edge_df["is_internal_edge"] = edge_df["source_product_name"] == edge_df["target_product_name"]
    return node_df, edge_df

def construct_product_df(node_df, edge_df):
    # Build the product dataframe
    product_df = (
        node_df.groupby(["product_name"])
        .agg(
            node_count=("unique_id", "count"),
            product_layers = ('product_layer', pandas.Series.nunique),
            product_category = ("product_category", "first"),
            dbt_package = ("package_name", "first")
        )
    )

    count_internal_edges = edge_df.loc[edge_df["is_internal_edge"]].groupby("source_product_name").agg(count_internal_edges=("source_product_name", "count"))
    count_output_edges = edge_df.loc[edge_df["is_internal_edge"] == False].groupby("source_product_name").agg(
        count_output_edges=("target_product_name", "count"),
        count_output_products=("target_product_name", pandas.Series.nunique)
    )
    count_input_edges = edge_df.loc[edge_df["is_internal_edge"] == False].groupby("target_product_name").agg(
        count_input_edges=("source_product_name", "count"),
        count_input_products=("source_product_name", pandas.Series.nunique)
    )

    product_df = product_df.join(count_internal_edges).join(count_output_edges).join(count_input_edges).fillna(0)
    return product_df

def create_product_graph(edge_df):
    gdf = edge_df.groupby(["source_product_name", "target_product_name"]).agg(weight=("source", "count")).reset_index()
    G = nx.DiGraph()
    for ii, s in gdf.iterrows():
        G.add_edge(s["source_product_name"], s["target_product_name"], weight=s['weight'])
    return G

# Prep visual
manifest = read_manifest("examples/immuta/manifest.json")
node_df, edge_df = extract_dataframes(manifest)
product_df = construct_product_df(node_df, edge_df)
G_products = create_product_graph(edge_df)



logging.info("Finished parsing data")

#%%
# Streamlit Application

streamlit.set_page_config(page_title="dbt Graph Analysis", layout="wide")

streamlit.title("dbt Graph Analysis")
streamlit.markdown(
    """
    This Streamlit application reads in a dbt_ graph, performs some light
    network analysis at the global level, and then provides functionality
    for exploring individual nodes and their dependencies."""
)
streamlit.header("Global Analysis")
streamlit.markdown(
    """
    Below is a summary of the nodes contained in this graph.
"""
)

col1, col2 = streamlit.beta_columns([1, 3])
with col1:
    streamlit.dataframe(product_df)
with col2:
    full_viz = create_pydot_viz(G_products, exclude_nodes=default_excludes)
    streamlit.graphviz_chart(full_viz)


streamlit.header("Single Product Analysis")
streamlit.markdown(
    """
    The section beelow summarizes a single group of nodes in this graph.
"""
)
selected_product = streamlit.selectbox(
    label="Package to drill down on",
    options=product_df.index,
    index=0,
)

selected_nodes = product_df.loc[selected_product].name

G_single = nx.DiGraph()
for u, v, e in G_products.edges(data=True):
    if u in selected_nodes or v in selected_nodes:
        G_single.add_edge(u, v, **e)

nx.set_node_attributes(G_single, product_df.loc[list(G_single.nodes)].to_dict(orient="index"))

single_viz = create_pydot_viz(G_single, exclude_nodes=default_excludes)

streamlit.graphviz_chart(single_viz)

# %%
