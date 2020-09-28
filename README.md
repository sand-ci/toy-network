Toy Network
==============================

A toy network for testing network tomography approaches. The primary driver is currently the Jupyter notebook that was used for testing, though key functions for generating graphs and visualizations of both graphs and graph data have been factored out into their respective files in the src folder.

Project Organization
------------

    ├── LICENSE
    ├── README.md          <- The top-level README for developers using this project.
    │
    ├── requirements.txt   <- The requirements file for reproducing the analysis environment, e.g.
    │                         generated with `pip freeze > requirements.txt`
    │
    ├── setup.py           <- makes project pip installable (pip install -e .) so src can be imported
    │
    ├── data
    │   ├── external       <- Data from third party sources.
    │   ├── interim        <- Intermediate data that has been transformed.
    │   ├── processed      <- The final, canonical data sets for modeling.
    │   └── raw            <- The original, immutable data dump.
    │
    ├── notebooks          <- Jupyter notebooks. Naming convention is a number (for ordering),
    │	│		      the creator's initials, and a short `_` delimited description, e.g.
    │   │                     `1.0-jqp-initial-data-exploration`.
    │   └── 0.0_eq_graph_test.ipynb 
    │
    ├── reports            <- Generated analysis as HTML, PDF, LaTeX, etc.
    │   └── figures        <- Generated graphics and figures to be used in reporting
    │
    └── src                <- Source code for use in this project.
        ├── __init__.py    <- Makes src a Python module
        │
        ├── data           <- Scripts to download or generate data
        │   └── make_networks.py
        │
        └── visualization  <- Scripts to create exploratory and results oriented visualizations
            ├── draw_histograms.py
            └── draw_networks.py


--------

<p><small>Project based on the <a target="_blank" href="https://drivendata.github.io/cookiecutter-data-science/">cookiecutter data science project template</a>. #cookiecutterdatascience</small></p>
