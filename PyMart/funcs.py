from .base import FrontBase, DataBase, DataSet

def list_databases(**url_kwargs):
    """
    Lists all databases found on ENSEMBL's biomart and
    returns them in the form of a pandas dataframe

    Optional keyword arguments:
        "host" : str = "http://www.ensembl.org"
        "path" : str = "/biomart/martservice"
        "port" : int = 80
        "virtual_schema" : str = "default"

    Example:
        INPUT:
        >>> databases = list_databases()

        OUTPUT:
        >>> Display name 'Ensembl Genes 108' corresponds to 'ENSEMBL_MART_ENSEMBL'
        >>> Display name 'Mouse strains 108' corresponds to 'ENSEMBL_MART_MOUSE'
        >>> Display name 'Sequence' corresponds to 'ENSEMBL_MART_SEQUENCE'
        >>> Display name 'Ontology' corresponds to 'ENSEMBL_MART_ONTOLOGY'
        >>> Display name 'Genomic features 108' corresponds to 'ENSEMBL_MART_GENOMIC'
        >>> Display name 'Ensembl Variation 108' corresponds to 'ENSEMBL_MART_SNP'
        >>> Display name 'Ensembl Regulation 108' corresponds to 'ENSEMBL_MART_FUNCGEN'

    """
    url_kwargs =  {k:v for k,v in url_kwargs.items() if k in ["host","path","port","virtual_schema"]}
    return FrontBase(**url_kwargs).print_databases()

def find_dataset(database_name,species,**url_kwargs):
    """
    Finds all datasets within a given database for a given species
    and returns them in the form of a dictionary where keys correspond to
    what is displayed, and values correspond to internal name.
    The values then can be passed to DataSet object or "fetch_dataset" function
    to retrieve all data associated with the dataset.

    To find all valid BioMart databases use "list_databases" function

    database_name : str
        Name of the BioMart database that will be queried.
        Case insensitive.
    species : str
        Name of the species that will be queried.
    Oprtional keyword arguments:
        "host" : str = "http://www.ensembl.org"
        "path" : str = "/biomart/martservice"
        "port" : int = 80
        "virtual_schema" : str = "default"

    Example:
        INPUT:
        >>> dic = find_dataset("ensembl mart ensembl","mouse")

        OUTPUT:
        >>> Query database name 'ensembl mart ensembl' corresponds to 'ENSEMBL_MART_ENSEMBL'
        >>> For queried species 'mouse', the database contains the following datasets:
        >>> Display name 'Steppe mouse genes (MUSP714)' corresponds to 'mspicilegus_gene_ensembl'
        >>> Display name 'Algerian mouse genes (SPRET_EiJ_v1)' corresponds to 'mspretus_gene_ensembl'
        >>> Display name 'Ryukyu mouse genes (CAROLI_EIJ_v1.1)' corresponds to 'mcaroli_gene_ensembl'
        >>> Display name 'Mouse Lemur genes (Mmur_3.0)' corresponds to 'mmurinus_gene_ensembl'
        >>> Display name 'Mouse genes (GRCm39)' corresponds to 'mmusculus_gene_ensembl'
        >>> Display name 'Shrew mouse genes (PAHARI_EIJ_v1.1)' corresponds to 'mpahari_gene_ensembl'
        >>> Display name 'Northern American deer mouse genes (HU_Pman_2.1)' corresponds to 'pmbairdii_gene_ensembl'


    """
    databases = FrontBase(**url_kwargs).databases
    alt_name = database_name.replace(" ","_").upper()

    database = databases[(databases["name"].isin([alt_name,database_name]))|
                        (databases["display_name"].isin([alt_name,database_name]))]

    if len(database)==0:
        raise ValueError(f"No database found for query '{database_name}'")

    database.reset_index(inplace=True,drop=True)
    database = database.iloc[0,:]

    print(f"""Query database name '{database_name}' corresponds to '{database["name"]}'""")
    print(f"For queried species '{species}', the database contains the following datasets: ")

    species_df = DataBase(name=database["name"]).print_species(species)
    return dict(zip(species_df["display_name"],species_df["name"]))

def _fetch_dataset(dataset_name=None,database_name=None,species_name=None,**url_kwargs):
    """
    Precursor to "fetch_data", so I don't bloat code
    """

    if dataset_name is not None:
        return DataSet(name=dataset_name,**url_kwargs)
    if (database_name is not None) and (species_name is not None):
        datadict = find_dataset(database_name,species_name,**url_kwargs)
        if len(datadict)>1:
            raise ValueError("Too many datasets for given query, narrow the query")
        dataset_name = list(datadict.values())[0]
        return DataSet(name=dataset_name,**url_kwargs)
    raise ValueError("Pass either valid dataset name, or a combination of valid database name with a valid species name")

def fetch_data(dataset_name = None,database_name = None,species_name = None,
               attributes = None,filters = None,
               hom_species = None,hom_query = None,only_unique = True,**url_kwargs):
    """
    Fetches data from BioMart servers.
    The procedure consists of three operations :
        1) Specifying dataset via "dataset_name" or "database_name"/"species_name"
        2) Choosing attributes and filters to use in querying. (optional)
        3) Fetching homology towards other species.

    #### SPECIFYING DATASET ####
    To specify dataset that will be fetched, there are two options:

        1) Specify dataset by its internal BioMart name.
        Example:
            >>> dataset_name = "hsapiens_gene_ensembl"
        Will traverse genes ("_gene_ensembl") of humans ("hsapeins").

        2) Specify database and species that will be queried.
        Example:
            >>> database_name = "ensembl mart ensembl"
            >>> species_name = "human"
        Will traverse genes ("ensembl mart ensembl") of humans.

    #### CHOOSING ATTRIBUTES AND FILTERS ####
    To specify columns of dataset that will be fetched, pass an iterable
    to "attributes" parameter. If "attributes" is None, default attributes are used.

    To pre-filter dataset and thus increase the speed of query, pass a python dictionary
    as "filter_attributes".

    Example:
            >>> dataset_name = "hsapiens_gene_ensembl"
            >>> attributes = ["ensembl_gene_id","Chromosome/scaffold name","manbearpig_homology_perc",]
            >>> filters ={"Type":["pseudogene","protein_coding"],
                       "chromosome_name": ["1","2"],
                       "transcript_tsl":False,
                       "manbearpig_gene":True,
                       }
            The above will fetch data for genes in humans with columns of data being
            ENSEMBL ID, chromosome number. It will filter for only protein coding and pseudogenes
            found only on first two chromosomes who have no Transcription Support Level.

            Elements that are not found in databases (e.g. "manbearpig_gene") are quietly ignored.

    ### FETCHING HOMOLOGY INFORMATION ####
    Additional element are homologies towards other species. To specify species you want to find
    homology towards use "hom_species", and to specify what attributes of homology use "hom_query".

    Example:
        >>> dataset_name = "amexicanus_gene_ensembl"
        >>> hom_species = ["human","mmusculus","ZebraFish"]
        >>> hom_query = ["ensembl_gene","associated_gene_name","orthology_confidence","perc_id"]

        The above will find homology in Mexican Tetra genes ("amexicanus_gene_ensembl") towards
        three species specified in "hom_species". Information about homology is contained in
        "hom_query" - information related to ENSEMBL Gene IDs of ortholog genes in that species
        ("ensembl_gene_id"),their names ("associated_gene_name"),
        confidency in orthology ("orthology_confidence"),
        and what percentage of ortholog genes ("perc_id") are identical to their corresponding gene
        in Mexican tetra.

    """
    dataset = _fetch_dataset(dataset_name,database_name,species_name,**url_kwargs)

    if attributes is None:
        attributes = dataset.attributes[dataset.attributes.default]["name"].tolist()
    if (hom_species is not None) and (hom_query is not None):
        attributes = attributes + dataset.extract_homology_attributes(hom_species,hom_query)

    return dataset.fetch(attributes,filters,only_unique)

def get_attributes(dataset_name = None,database_name = None,species_name = None,
                   display=False,**url_kwargs):
    """
    Returns all attributes for a given dataset in the form out pandas DataFrame.

    If "display" is set to True, prints out all the attributes.
    """
    dataset = _fetch_dataset(dataset_name,database_name,species_name,**url_kwargs)
    if display:
        dataset.print_attributes()
    return dataset.attributes

def get_filters(dataset_name = None,database_name = None,species_name = None,
                   display=False,**url_kwargs):
    """
    Returns all filters for a given dataset in the form out pandas DataFrame.

    If "display" is set to True, prints out all the filters.
    """

    dataset = _fetch_dataset(dataset_name,database_name,species_name,**url_kwargs)
    if display:
        dataset.print_filters()
    return dataset.filters
