#%%
import json
import matplotlib.pyplot as plt
import networkx as nx
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

# Prep data
logging.info("Beginning data parsing.")

manifest = read_manifest("examples/immuta/manifest.json")
node_df, edge_df = extract_dataframes(manifest)
product_df = construct_product_df(node_df, edge_df)
G_products = create_product_graph(edge_df)

logging.info("Finished parsing data")

#%%
# Streamlit Application

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
    product_exclusions = streamlit.multiselect(
        label="Products to exclude from graph.", options=product_df.index, default=[]
    )
    full_viz = create_pydot_viz(G_products, exclude_nodes=product_exclusions)
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

nx.set_node_attributes(
    G_single, product_df.loc[list(G_single.nodes)].to_dict(orient="index")
)

single_viz = create_pydot_viz(G_single)

streamlit.graphviz_chart(single_viz)

# %%
