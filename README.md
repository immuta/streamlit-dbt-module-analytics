# Data Product Modularity Explorer

This Streamlit application parses a dbt project structure and examines the modularity of different "products" within it.

## Packages, products and modules, oh my!

There are myriad ways to describe a set of relations in a SQL database. "Packages" and "products" may be a new veneer over the old "schemas" and "marts", but I think there is something new here. Other 

What the Product Driven Architecture :heart: aims for is establishing clarity around:

- Inputs
- Outputs
- Ownership
- Expectations

No knowledge external to the product should be required for use of the product. Furthermore, ownership should be tied as closely as possible to the original application system and domain as possible.

## Data Product Analytics

This package will output two graphs:

1. A "product-level" graph that summarizes all the data products within the dbt project. This currently requires a consistent directory structure.
2. A "model-level" graph, broken out by the selected data product that, in particular, shows the dependencies between models external to the data product.

## Recommended Directory Structure

The parser is based on the FQN: `<package>.<product_category>.<product_name>.<product_subfolders>.<model_name>`. The two-level structure was chosen because `dbt` already follows it with its built-in sources: `<package>.sources.<source-name>.<model-name>`.

An example is below:

```{bash}
- applications
- - salesforce
- - - base (21)
- - - final (6)
- - zendesk
- - - base (10)
- - - final (4)
- data_science
- - lead_scoring
- - - staging (9)
- - - final (3)
- marts
- - sales
- - - final (8)
- - marketing
- - - final (5)
```

The "data products" included in this example project are:

- applications.salesforce
- applications.zendesk
- data_science.lead_scoring
- marts.sales
- marts.marketing

