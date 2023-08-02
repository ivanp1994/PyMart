

# PyMart
Python interface towards ENSEMBL's BioMart.


[![Licence](https://img.shields.io/badge/license-MIT-blue.svg)](https://raw.githubusercontent.com/irahorecka/sgd-rest/main/LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Linting](https://github.com/ivanp1994/PyMart/actions/workflows/flaking.yaml/badge.svg)](https://github.com/ivanp1994/PyMart/actions/workflows/flaking.yaml) [![Tests](https://github.com/ivanp1994/PyMart/actions/workflows/testing.yaml/badge.svg)](https://github.com/ivanp1994/PyMart/actions/workflows/testing.yaml)

# Installation and requirements
The only requirements are requests and pandas library, and those are things you likely already have.
PyMart makes use of `dataclass` which is Python 3.7+ minimum, and so the minimum Python environment if Python 3.8.

Additional things used for testing are specified in "requirements_dev" and those are things like pytest for code testing,
flake8 for code linting, etc.

Simply clone the repository and install via `pip install .` 
(Not yet added to PyPi)

# Usage

## Listing available databases

The first drop-down menu [ENSEMBL BioMart](https://www.ensembl.org/info/data/biomart/index.html)'s data mining tool shows all databases 
that are found on BioMart servers. To list those databases use the `list_databases` function of the module.
For example:
```
    import pymart as pm
    database_df = pm.list_databases()
 ```
Will output the following:
```
    Display name 'Ensembl Genes 108' corresponds to 'ENSEMBL_MART_ENSEMBL'
    Display name 'Mouse strains 108' corresponds to 'ENSEMBL_MART_MOUSE'
    Display name 'Sequence' corresponds to 'ENSEMBL_MART_SEQUENCE'
    Display name 'Ontology' corresponds to 'ENSEMBL_MART_ONTOLOGY'
    Display name 'Genomic features 108' corresponds to 'ENSEMBL_MART_GENOMIC'
    Display name 'Ensembl Variation 108' corresponds to 'ENSEMBL_MART_SNP'
    Display name 'Ensembl Regulation 108' corresponds to 'ENSEMBL_MART_FUNCGEN'
```

In the above example, what's displayed when user clicks on 'Ensembl Genes 108' is database under BioMart's internal name 'ENSEMBL_MART_ENSEMBL'.
This database consists of many (usually one per species) datasets. `database_df` is a pandas DataFrame with two columns corresponding
to internal name and the name displayed in the drop-down menu.

## Finding desired dataset

To find the desired dataset, use the `find_dataset` function of the module.
The function takes two arguments, `database_name` which corresponds to a valid BioMart database, and `species` which corresponds to a valid species.
`database_name` can either correspond to case insensitive display name (e.g. *Ensembl Genes 108*) or case insensitive internal name (e.g. *ENSEMBL_MART_ENSEMBL*)
with the caveat that one can pass either spaces replaced by underscores or vice-versa.

Likewise `species` argument needs to be a string contained in either internal name (e.g. *mmusculus*) or displayed name (e.g. *Zebrafish*).

For example:
```
    import pymart as pm
    datasets = pm.find_dataset("ensembl mart ensembl","mouse")
```
Will output the following:
```
    Query database name 'ensembl mart ensembl' corresponds to 'ENSEMBL_MART_ENSEMBL'
    For queried species 'mouse', the database contains the following datasets: 
    Display name 'Ryukyu mouse genes (CAROLI_EIJ_v1.1)' corresponds to 'mcaroli_gene_ensembl'
    Display name 'Northern American deer mouse genes (HU_Pman_2.1)' corresponds to 'pmbairdii_gene_ensembl'
    Display name 'Mouse genes (GRCm39)' corresponds to 'mmusculus_gene_ensembl'
    Display name 'Algerian mouse genes (SPRET_EiJ_v1)' corresponds to 'mspretus_gene_ensembl'
    Display name 'Mouse Lemur genes (Mmur_3.0)' corresponds to 'mmurinus_gene_ensembl'
    Display name 'Steppe mouse genes (MUSP714)' corresponds to 'mspicilegus_gene_ensembl'
    Display name 'Shrew mouse genes (PAHARI_EIJ_v1.1)' corresponds to 'mpahari_gene_ensembl'
```
To narrow the selection, instead of "mouse" use more precise "mmus":
```
   import pymart as pm
   datasets = pm.find_dataset("ensembl mart ensembl","mouse")
```
The output is now:
```
    Query database name 'ensembl mart ensembl' corresponds to 'ENSEMBL_MART_ENSEMBL'
    For queried species 'mmus', the database contains the following datasets: 
    Display name 'Mouse genes (GRCm39)' corresponds to 'mmusculus_gene_ensembl'
```    

## Fetching data from a given dataset 

The real function is fetching large data from a given BioMart dataset. In the above example,
we've narrowed that the information about genes for *Mus musculus* is found in `mmusculus_gene_ensembl` dataset. Now the main function is to fetch
all genetic information that we want. To do that, use `fetch_data` function. There are three main components to using it properly.

### 1. Specifying datasets

You can specify dataset you want by two main ways. First is to directly pass your dataset as `dataset_name` parameter. In our example, this would be 'mmusculus_gene_ensembl'.
The other way is to specify which database we want and which species we want to fetch dataset from via `database_name` and `species_name`, skipping the `find_dataset` option.
However, an error will occur if there is more than one dataset corresponding to species query. For example, using "mouse" as `species_name` will trigger an error as there are
multiple species with "mouse" in their name.

Example:
```
   import pymart as pm
   mouse_data_1 = pm.fetch_data(dataset_name="mmusculus_gene_ensembl")
   mouse_data_2 = pm.fetch_data(database_name="ensembl mart ensembl",species_name="mmus")
```

The databases fetched are identical.


### 2. Finding out information about given dataset

Once the desired dataset is found, elements of those dataset must be found. Every BioMart dataset has *attributes* which are columns of dataset corresponding to a feature of the database (e.g. attribute *Gene stable ID* represents ENSEMBL Gene ID in the Ensembl Genes 108 database) and *filters* which are used to filter the elements of the dataset (e.g. filtering for a particular chromosome via "Chromosome/scaffold" option). To inspect given dataset with respect to filters and attributes, use the functions `get_filters` and `get_attributes` respectively.
These two functions specify a dataset via `dataset_name` or via `database_name` and `species` parameters, much like the function `fetch_data`. Additional parameter is `display` which if set to True will print out all rows of attributes or filters.

Example:
```
    import pymart as pm
    dataset_name = "amexicanus_gene_ensembl"
    attributes = pm.get_attributes(dataset_name,display=True)
    filters = pm.get_filters(dataset_name,display=True)
```

The above code will print out all atributes and filters related to genes of Mexican tetra and return them in the form of pandas dataframe. It can then be inspected and used to decide what will be fetched and filtered.


### 3. Specifying columns ("attributes") of data and filtering.

Attributes are columns of selected dataset, and control the dimensionality of the data. Passing N attributes will result in M x N pandas DataFrame where M are the rows correspoding to elements of a selected dataset, (e.g. a particular gene or a transcript in Ensembl Genes database) and N are columns of said data. Attributes are specified with `attributes` parameter. Every attribute has its internal name (how it's parsed internally) and its display name (how it's displayed for the user). For example, `ensembl_gene_id` corresponds to display name of `Gene stable ID`. You can specify either one. All attributes that are not found in the dataset are quietly ignored.

Example:
```
    import pymart as pm
    attributes = ["ensembl_gene_id","Chromosome/scaffold name","manbearpig_homology_perc",]
    mouse_data_1 = pm.fetch_data(dataset_name="mmusculus_gene_ensembl",attributes = attributes)
```
In the above example, we fetch dataset corresponding to genes of *Mus musculus*. We find the ENSEMBL Gene Stable ID ("ensembl_gene_id"), on which chromosome it's located on, and the last element ("manbearpig_homology_perc") is simply ignored. If no attributes are passed, default attributes are fetched instead. 

Additional parameter that can be passed is `filters`. Filters are largely similar to attributes, but instead of passing a simple iterator, a python dictionary should be passed. The keys of that dictionary should correspond to either display name or name of the filter, and values should correspond to desired values. Filters come in differenty types - e.g. boolean (set to `True` or `False`) or text filters (set to some values).  

Example:
```
    import pymart as pm
    filters ={"Type":["pseudogene","protein_coding"],
            "chromosome_name": ["1","2"],
            "transcript_tsl":False,
            "manbearpig_gene":True,
            }
    mouse_data = pm.fetch_data(dataset_name="mmusculus_gene_ensembl",filters=filters)
```

The above example fetches only pseudogenes and protein coding genes found on chromosomes 1 and 2, who have no Transcript Support Level. There is no such thing as "manbearpig_gene".

### 4. Specifying homologies

There is an additional feature of specifying [gene homology](https://en.wikipedia.org/wiki/Sequence_homology). Every gene dataset contains information about homologies in other species - e.g. Human to Mouse orthologs. There are two parameters in `fetch_dataset` function which deal exclusively with homologies. These are `hom_species` and `hom_query`. 

Example:
```
    import pymart as pm
    dataset_name = "amexicanus_gene_ensembl"
    hom_species = ["human","mmusculus","ZebraFish"]
    hom_query = ["ensembl_gene","associated_gene_name","orthology_type","orthology_confidence","perc_id"]
    data = pm.fetch_data(dataset_name=dataset_name,hom_species=hom_species,hom_query=hom_query)
```
The above example fetches gene data from Mexican tetra (*Astyanax mexicanus*), and tries to find homology towards three species:
    1. Humans ("human")
    2. Mouse ("mmusculus")
    3. Zebrafish ("ZebraFish")
The selected queries are their equivalent ENSEMBL Gene IDs, their name, what type of orthology, how confident the orthology score is, and what percentage is the target gene identical to the queried gene (in our case how similar is the human/mouse/zebrafish gene to its Mexican tetra equivalent).

There will be a total of 15 (3 species x 5 queries) additional homology columns.
