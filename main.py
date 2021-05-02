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

manifest = read_manifest("examples/immuta/manifest.json")
G = read_graph(manifest)
node_df = read_node_graph(manifest)
product_df = (
    node_df.groupby(["product_name"])
    .agg(node_count=("unique_id", "count"))
)

edf = nx.to_pandas_edgelist(G).reset_index()
edf = pandas.merge(
    edf,
    node_df.rename(columns={c: f"source_{c}" for c in node_df.columns}),
    left_on="source",
    right_index=True,
)
edf = pandas.merge(
    edf,
    node_df.rename(columns={c: f"target_{c}" for c in node_df.columns}),
    left_on="target",
    right_index=True,
    suffixes=["", "_target"],
)

gdf = edf.groupby(["source_product_name", "target_product_name"]).size().reset_index()
gdf["internal_edge"] = gdf["source_product_name"] == gdf["target_product_name"]


G_products = nx.DiGraph()
for ii, s in gdf.iterrows():
    G_products.add_edge(s["source_product_name"], s["target_product_name"], weight=s[0])

full_viz = create_pydot_viz(G_products, exclude_nodes=default_excludes)

logging.info("Finished parsing data")

#%%
# Streamlit Application

streamlit.set_page_config(page_title="dbt Graph Analysis", layout="centered")

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


streamlit.dataframe(product_df)
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
