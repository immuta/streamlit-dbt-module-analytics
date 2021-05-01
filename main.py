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
)

logging.basicConfig()


default_categories = [
    "applications", 
    "derived",
    "exposures",
    "external",
    "marts",
    "sources",
]
default_excludes = [
    # "external.looker"
]

custom_formats = {}
for ii, cat in enumerate(default_categories):
    custom_formats[cat] = node_formats[ii]

G = read_graph("examples/immuta/manifest.json")

models = {}
for node, data in G.nodes(data=True):
    try:
        package_data = extract_attributes(data["fqn"], default_categories)
        models[data["unique_id"]] = {
            "resource_type": data["resource_type"],
            "depends_on": data.get("depends_on", {}).get("nodes", []),
            **package_data
        }
    except IndexError:
        logging.debug('Error with %s', '.'.join(data["fqn"]))

model_df = pandas.DataFrame.from_dict(models, orient="index")
package_df = model_df.groupby(["package", "name", "category", "layer"]).size().reset_index()

# df = pandas.DataFrame.from_records(edges)
df = nx.to_pandas_edgelist(G).reset_index()

for attr in ["dbt_project", "category", "name", "layer", "package"]:
    df[f"source_{attr}"] = df["source"].apply(lambda x: models.get(x, {}).get(attr))
    df[f"target_{attr}"] = df["target"].apply(lambda x: models.get(x, {}).get(attr))

gdf = df.groupby(["source_package", "target_package"]).size().reset_index()
gdf["internal_edge"] = gdf["source_package"] == gdf["target_package"]


G_products = nx.DiGraph()
for ii, s in gdf.iterrows():
    G_products.add_edge(s["source_package"], s["target_package"], weight=s[0])


viz = create_pydot_viz(G_products, exclude_nodes=default_excludes, custom_formats=custom_formats)

logging.info("Finished parsing data")

#%%
# Streamlit Application

streamlit.set_page_config(page_title="dbt Graph Analysis", layout="centered")

streamlit.title("dbt Graph Analysis")
streamlit.markdown("""
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
streamlit.dataframe(model_df.groupby(["category", "name"]).size())


streamlit.graphviz_chart(viz)


# %%
# First group is dbt project
# Second group is package type
# Third group package name
# Fourth group is optional model type
# def extract_model_info(package_types: list)





# %%

#%%


# #%%
# edges = []
# for node, data in models.items():
#     v = data["package"]
#     for ref in data["depends_on"]:
#         try:
#             u = models[ref]["package"]
#             edges.append({
#                 "source": u,
#                 "target": v,
#                 "source_node": node,
#                 'target_node': ref
#             })
#         except KeyError as e:
#             logging.info(node)

# %%
