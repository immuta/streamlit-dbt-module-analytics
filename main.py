#%%
import json
import matplotlib.pyplot as plt
import networkx as nx
import random
import seaborn as sns
import streamlit
import logging

from process import (
    read_graph,
    read_manifest,
    read_node_graph,
    create_product_graph,
    construct_product_df,
    extract_dataframes,
    read_node_graph,
    extract_attributes,
    extract_data_graph,
)
from utils import (
    create_pydot_viz,
    node_formats,
)

logging.basicConfig()


streamlit.set_page_config(page_title="dbt Graph Analysis", layout="wide")


#%%
# Streamlit Application

streamlit.title("dbt Graph Analysis")
streamlit.markdown(
    """
    This Streamlit application reads in a dbt_ graph, performs some light
    network analysis at the global level, and then provides functionality
    for exploring individual nodes and their dependencies."""
)
manifest = streamlit.file_uploader(
    "Upload your manifest file.",
    type="json",
    accept_multiple_files=False
)

# Prep data
logging.info("Beginning data parsing.")

if not manifest:
    manifest = read_manifest("examples/immuta/manifest.json")
node_df, edge_df = extract_dataframes(manifest)
product_df = construct_product_df(node_df, edge_df)
G_products = create_product_graph(edge_df)

logging.info("Finished parsing data")


## Global analyssi

streamlit.header("Global Analysis")
streamlit.markdown(
    """
    Below is a summary of the nodes contained in this graph.
"""
)
left_width, right_width = (3, 7)
col1, col2 = streamlit.beta_columns([left_width, right_width])
with col1:
    streamlit.markdown(
    """
    ### Global Product Graph

    The adjacent graph shows the number of model references (edges)
    connecting each adta product to each other within the global dbt
    graph.
    """)
with col2:
    product_exclusions = streamlit.multiselect(
        label="Products to exclude from graph.", options=product_df.index, default=[]
    )
    full_viz = create_pydot_viz(G_products, exclude_nodes=product_exclusions)
    streamlit.graphviz_chart(full_viz)

col1, col2 = streamlit.beta_columns([left_width, right_width])
with col1:
    streamlit.markdown(
    """
    ### Global Product Analysis

    The adjacent dataframee contains statistics on each product and is interactive.
    """)
with col2:
    streamlit.dataframe(product_df)


## Deep dive

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

selected_nodes = node_df.loc[node_df['product_name'] == selected_product].index

G_single = nx.DiGraph()
for ii, s in edge_df.iterrows():
    if s["source"] in selected_nodes or s["target"] in selected_nodes:
        G_single.add_edge(s["source_product_node_name"], s["target_product_node_name"], weight=1, **s.to_dict())

nx.set_node_attributes(
    G_single,
    node_df.set_index("product_node_name").loc[list(G_single.nodes)].to_dict(orient="index")
)

single_viz = create_pydot_viz(G_single)

streamlit.graphviz_chart(single_viz)

# %%
