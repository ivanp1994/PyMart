# -*- coding: utf-8 -*-
"""
To connect to front page use
    >>> front = FrontBase()

To reset connection parameters use
    >>> front.reset_connection_params()

Valid arguments to pass are:
    "host",
    "path",
    "port",

To list databases as a pdanas dataframe use:
    >>> database = front.list_databases()

Or to print them out use:
    >>> front.print_databases()

Once you have the database's display name and its BioMart ID you can connect
to it via DataBase object

    >>> name = 'ENSEMBL_MART_ENSEMBL'
    >>> display_name = 'Ensembl Genes 108' (this argument is optional)
    >>> database = DataBase(name=name,display_name=display_name)

To find species-specific datasets, use method "find_species".
It "find_species" takes one argument corresponding to name of the species.
The argument can be case insensitive (i.e. "huMaN" will default to "human"),
and can contain underscore (i.e. "TasmanIan_dEvil" will default to "tasmanian devil").

Example:
    >>> human_db = database.find_specie("hUmaN")
    >>> tasmanian_db = database.find_specie("tAsManian_devil")
    >>> mouse_db = database.find_specie("Mouse")

If there is no specie named, a ValueError will be thrown. Example.
    >>> manbearpig_db = database.find_specie("manbearpig")

    >>> ValueError: Database does not contain 'manbearpig'

To print out all species, use method "print_species".
Example:
    >>> database.print_species("turtle")

    >>> Display name 'Chinese softshell turtle genes (PelSin_1.0)' corresponds to 'psinensis_gene_ensembl'
    >>> Display name 'Painted turtle genes (Chrysemys_picta_bellii-3.0.3)' corresponds to 'cpbellii_gene_ensembl'
    >>> Display name 'Three-toed box turtle genes (T_m_triunguis-2.0)' corresponds to 'tctriunguis_gene_ensembl'

Once dataset is found, it can be accessed via DataSet class.
    >>> dataset = DataSet(name="psinensis_gene_ensembl")

Every dataset has a dataframe of Attributes and Filters.
To see them use .attributes or .filters attributes.
Example:
    >>> atts = dataset.attributes
    >>> filters = dataset.filters

To print them out use "print_attributes" or "print_filters" methods
Example:
    >>> dataset.print_attributes()
    >>> dataset.print_filters()

Alternatively, one can return a List of objects via .populate_filters() or .populate_attributes()
methods.
Example:
    >>> attributes = dataset.populate_attributes()
    >>> filters = dataset.populate_filters()

To re-populate filters or attributes, pass "force=True" to either "populate_filters"
or "populate_attributes" methods

To fetch the data from a given dataset use "fetch" method on a given dataset.
Example:
    >>> data = dataset.fetch()

Fetch takes in the following parameters:
    "attributes":
        A list of attributes (columns) of data.
        Attributes are accessed via .attributes attribute.
        You can use either attributes correspoding to "name" or "display_name".
        Attributes that are not found in either are simply removed.
        Example:
            >>> attributes = ["ensembl_gene_id","Chromosome/scaffold name","manbearpig_homology_perc",]
            >>> data = dataset.fetch(attributes=attributes)

        Will fetch dataset with columns "Gene stable ID" and "Chromosome/scaffold name".
        There is no attribute called "manbearpig_homology_perc" so it will be quietly ignored.
    "filters":
        A python dictionary used to pre-filter the dataset.
        Valid filters are accessed via .filters attribute.
        You can use keys corresponding to "name" or "display_name".
        Filters that are not found in either are simply removed.

        Example:
            >>> filters ={"Type":["pseudogene","protein_coding"],
                       "chromosome_name": ["1","2"],
                       "transcript_tsl":False,
                       "manbearpig_gene":True,
                       }
            >>> data = dataset.fetch(filters=filters)

        Will fetch dataset where biotype is "pseudogene" or "protein_coding",
        is found on chromosome 1 and two, and Transcript Support Level is excluded.
        Manbearpig Gene is ignored since it doesn't exist.
    "only_unique":
        Specifies if the rows should be unique. By default set to True.

===============================================================================

The folowing example retrieves dataset from "Ensembl Gene 108" database for "Mexican tetra".
To query the dataset, use "fetch" method on it.

    >>> database_name = "Ensembl Gene 108"
    >>> specie = "mexican tetra"

    >>> fronta = FrontBase()
    >>> databases = fronta.print_databases()
    >>> gene_database_name = databases.loc[databases.display_name=="Ensembl Genes 108"]["name"].values[0]

    >>> gene_database = DataBase(name=gene_database_name)
    >>> specie_dataset_name = gene_database.print_species(specie)["name"].values[0]
    >>> specie_dataset = DataSet(name=specie_dataset_name)

    >>> data = specie_dataset.fetch()

===============================================================================

The folowing example retrieves dataset from "Ensembl Gene 108" database for "Mexican tetra".
It specifically requests attributes related to genetic information ("base_attributes"):
    - ENSEMBL Gene IDs and their external names ("ensembl_gene_id","external_gene_name")
    - Their chromosome position ("chromosome_name","start_position","end_position")

It then supplements that with information about homology towards three species ("hom_species"),
information ("hom_query") related to ENSEMBL Gene IDs of ortholog genes in that species ("ensembl_gene_id"),
their names ("associated_gene_name"), confidency in orthology ("orthology_confidence"), and
what percentage of ortholog genes are identical to their corresponding gene in Mexican tetra.


>>> specie_dataset_name = "amexicanus_gene_ensembl"
>>> hom_species = ["human","mmusculus","ZebraFish"]
>>> hom_query = ["ensembl_gene","associated_gene_name","orthology_confidence","perc_id"]
>>> gene_attributes = ["ensembl_gene_id","description","external_gene_name","chromosome_name","start_position","end_position"]

>>> specie_dataset = DataSet(name=specie_dataset_name)

>>> homology_attributes = specie_dataset.extract_homology_attributes(hom_species,hom_query)
>>> data = specie_dataset.fetch(attributes=gene_attributes+homology_attributes)
Created on Wed Jan 11 14:52:39 2023
@author: ivanp
"""


from dataclasses import dataclass, field
from typing import Dict, List
from xml.etree import ElementTree
from io import StringIO
from time import perf_counter

import re
import requests
import pandas as pd


@dataclass
class Base:
    """
    Base class for all others
    """
    host: str = "http://www.ensembl.org"
    path: str = "/biomart/martservice"
    port: int = 80
    virtual_schema: str = "default"

    @property
    def url(self):
        """Url to connect to database"""
        return f"{self.host}:{self.port}{self.path}"

    def get(self, **params):
        """Base method for fetching a query"""
        r = requests.get(self.url, params=params)
        r.raise_for_status()
        return r

    def reset_connection_params(self, **kwargs):
        """Resets any part of url using specified keyarguments"""
        self.host = kwargs.get("host", self.host)
        self.path = kwargs.get("path", self.path)
        self.port = kwargs.get("port", self.port)
        self.virtual_schema = kwargs.get("virtual_schema", self.virtual_schema)


@dataclass
class DataBase(Base):
    """
    Each instance of this class corresponds to a particular BioMart database.
    This class has three attributes:
        "name" - which is internal name on BioMart servers,
        "display_name" - which is how the database is displayed (optional)
        "datasets" - which is a pandas dataframe containing all datasets
        contained in oen base

    """
    name: str = ""
    display_name: str = ""
    _datasets: pd.DataFrame = field(init=False)

    def __post_init__(self):
        self._datasets = pd.DataFrame(columns=["name", "display_name"])

    def _get_datasets(self):
        """
        dataset constructor
        """
        if self.name:
            response = self.get(type='datasets', mart=self.name)

            # Read result frame from response.
            result = pd.read_csv(StringIO(response.text), sep='\t',
                                 header=None, )[[1, 2]]

            result.columns = ["name", "display_name"]
            return result
        return self._datasets

    @property
    def datasets(self):
        """
        pandas dataframe containing information about all datasets
        within a particular instance of this class
        """
        if len(self._datasets) == 0:
            self._datasets = self._get_datasets()
        return self._datasets

    def find_species(self, specie):
        """
        Finds the dataset corresponding to a given specied in the database.
        The "specie" parameter muse be a string found in either "display_name"
        or "name" columns of datasets. Case insensitive.
        """
        ds = self.datasets
        if len(ds) == 0:
            if not self.name:
                raise ValueError("No name for a given database")
            raise ValueError("No datasets found for name")

        result = ds[ds.display_name.str.contains(specie, case=False, regex=True) |
                    ds["name"].str.contains(specie, case=False, regex=True)]
        if len(result) == 0:
            specie = specie.replace("_", " ")
            result = ds[ds.display_name.str.contains(
                specie, case=False, regex=True)]
        if len(result) == 0:
            raise ValueError(f"Database does not contain '{specie}'")
        return result

    def print_species(self, specie):
        """
        Prints out the dataset(s) for the queried species
        """
        df = self.find_species(specie)
        for _, row in df.iterrows():
            print(
                f"Display name '{row.display_name}' corresponds to '{row['name']}'")
        return df


@dataclass
class FrontBase(Base):
    """
    This is the front "page" of BioMart.
    This class contains all BioMart databases.
    """

    xml_map: Dict[str, str] = field(default_factory=lambda:
                                    {
                                        "name": "name",
                                        "display_name": "displayName",
                                        "host": "host",
                                        "path": "path",
                                        "virtual_schema": "serverVirtualSchema"
                                    }
                                    )
    _databases: List[DataBase] = field(default_factory=list)

    @property
    def databases(self):
        """All databases in the form of a pandas dataframe"""
        if len(self._databases) == 0:
            self._databases = self._get_databases()
        return pd.DataFrame(self._databases)

    def _get_databases(self):
        """Constructor function for databases (1/2)"""
        r = self.get(type="registry")
        xml = ElementTree.fromstring(r.content)
        return [self._db_from_xml(node) for node in xml.findall('MartURLLocation')]

    def _db_from_xml(self, node):
        """Constructor function for databases (2/2)"""
        params = {k: node.attrib[v] for k, v in self.xml_map.items()}
        return DataBase(**params)

    def list_databases(self):
        """Returns databases in the form of pandas dataframe"""
        return self.databases

    def print_databases(self):
        """Prints out all databases """
        for _, row in self.databases.iterrows():
            print(
                f"""Display name '{row.display_name}' corresponds to '{row["name"]}'""")
        return self.list_databases()


@dataclass
class Attribute:
    """
    Basic class for attributes of
    a particular dataset. Used to construct
    attributes dataframe quickly.
    """
    name: str
    display_name: str
    description: str
    default: bool = False


@dataclass
class Filter:
    """
    Basic class for attributes of
    a particular dataset. Used to construct
    attributes dataframe quickly.
    """
    name: str
    display_name: str
    description: str
    type: str
    operator: str
    sub_options: bool
    options: pd.DataFrame

    def explain_filter(self, print_options=True):
        """
        Explains filter - prints out what the filter does
        """
        print(
            f"Filter's display name is '{self.display_name}' and its internal name is '{self.name}'")
        print(
            f"Filter's operator is '{self.operator}' and its type is '{self.type}'")
        if self.sub_options and print_options:
            print("It has sub options:")
            print(self.options.to_string(index=False, justify="center"))


@dataclass
class DataSet(Base):
    """
    This is the main interface towards getting
    data from BioMart. Every instance of this class roughly corresponds to
    one species. For example, dataset with name "hsapiens_gene_ensemble" corresponds
    to data about genes in homo sapiens.
    This class contains information about a particular dataset with most salient
    attributes being:
        "name" - internal name used to access the data on BioMart servers
        "display_name" - how this dataset is displayed on the web page
        "attributes" - attributes (columns) of datasets that are fetched,
            displayed in the form of a pandas dataframe
        "filters" - filters used to pre-filter, and thus reduce the time
            of fetching data, displayed in the form of pandas dataframe
        "homology" - a dataframe containing homology information towards
            other species

    """
    name: str = ""
    display_name: str = ""
    _config_xml: object = None
    _attributes: List[Attribute] = field(default_factory=list)
    _filters: List[Filter] = field(default_factory=list)
    _homology: pd.DataFrame = field(init=False)

    def __post_init__(self):
        _homology = pd.DataFrame()

    @property
    def config_xml(self):
        """Configuration xml file - used to fetch datasets"""
        if self._config_xml is None:
            self._config_xml = self._get_config_xml()
        return self._config_xml

    def _get_config_xml(self):
        """Constructor for config_xml file"""
        r = self.get(type='configuration', dataset=self.name)
        if "Problem retrieving configuration" in r.text:
            raise KeyError("Problem retrieving configuration")
        return ElementTree.fromstring(r.content)

    @property
    def attributes(self):
        """Attributes in the form of dataframe"""
        if len(self._attributes) == 0:
            self.populate_attributes()
        return pd.DataFrame(self._attributes)

    @property
    def filters(self):
        """Filters in the form of dataframe"""
        if len(self._filters) == 0:
            self.populate_filters()
        df = pd.DataFrame(self._filters)
        df.pop("options")
        return df

    @property
    def homology(self):
        """Data about homology towards other species"""
        if len(self._homology) == 0:
            self.populate_homology()
        return self._homology

    def populate_attributes(self, force=False):
        """Constructor for attributes property"""
        if len(self._attributes) > 0 and not force:
            return self._attributes

        for page_index, page in enumerate(self.config_xml.iter("AttributePage")):
            for desc in page.iter("AttributeDescription"):
                attrib = desc.attrib
                is_default = (attrib.get("default", "") ==
                              "true") and (page_index == 0)

                at = Attribute(name=attrib['internalName'],
                               display_name=attrib.get('displayName', ''),
                               description=attrib.get('description', ''),
                               default=is_default)
                self._attributes.append(at)
        return self._attributes

    def populate_filters(self, force=False):
        """Constructor for filters property"""
        if len(self._filters) > 0 and not force:
            return self._filters

        for node in self.config_xml.iter("FilterDescription"):

            attrib = node.attrib
            # check for submenus
            if len(list(node)) == 0:
                options = pd.DataFrame()
                sub_options = False
            else:
                options = pd.DataFrame(
                    [sub_el.attrib for sub_el in list(node)])
                sub_options = True

            ft = Filter(name=attrib["internalName"],
                        type=attrib.get("type", ""),
                        description=attrib.get("description", ""),
                        display_name=attrib.get("displayName", ""),
                        operator=attrib.get("qualifier", ""),
                        sub_options=sub_options,
                        options=options
                        )
            self._filters.append(ft)
        return self._filters

    def populate_homology(self, force=False):
        """Constructor for homology property"""
        if len(self._homology) > 0 and not force:
            return self._homology

        homology_dataset = self.attributes[self.attributes.name.str.contains(
            "homolog")].copy()

        def match_homology(string):
            match = re.match("(?P<spc>[^_]*)_homolog_(?P<wht>.*$)", string)
            if match:
                groups = match.groupdict()
                return groups["spc"], groups["wht"]
            return None, None

        homology_dataset[["specie_name", "qualifier_name"]] = homology_dataset.apply(lambda row: match_homology(row["name"]),
                                                                                     axis=1, result_type="expand")
        homology_dataset = homology_dataset[~(
            homology_dataset.specie_name.isna())]
        homology_dataset.drop(["description", "default"], axis=1, inplace=True)

        _sep = homology_dataset.loc[homology_dataset.qualifier_name == "ensembl_gene"].copy(
        )
        _sep["display_name"] = _sep["display_name"].str.replace(
            "gene stable ID", "", regex=False)

        species_mapper = dict(zip(_sep["specie_name"], _sep["display_name"]))
        homology_dataset["specie_display_name"] = homology_dataset["specie_name"].map(
            species_mapper)
        homology_dataset["qualifier_display_name"] = homology_dataset.apply(lambda row: row["display_name"].replace(row["specie_display_name"], ""),
                                                                            axis=1)
        self._homology = homology_dataset

    def print_attributes(self):
        """Prints out attributes"""
        print(self.attributes.to_string(index=False, justify="center"))

    def print_filters(self):
        """Prints out filters"""
        print(self.filters.to_string(index=False, justify="center"))

    def explain_filter(self, index, print_options=True):
        """
        Explains a filter. Pass either a string to denote a filter's name (internal or displayed),
        or a index correspoding to filter's location in dataframe
        """
        if isinstance(index, str):
            select = self.filters[(self.filters.name == index) |
                                  (self.filters.display_name == index)]
            if len(select) == 0:
                raise ValueError(f"No filter for name '{index}'")
            index = select.index.values[0]

        elif isinstance(index, int):
            ...
        else:
            raise ValueError("Pass either a string type or index type")

        self._filters[index].explain_filter(print_options)

    @staticmethod
    def add_attributes(name, subelem):
        """Add attributes to query"""
        at_el = ElementTree.SubElement(subelem, "Attribute")
        at_el.set("name", name)

    @staticmethod
    def add_filters(filter_row, filter_query, subelem):
        """Add filters to query"""
        value = filter_query.get(filter_row["name"], None)
        if value is None:
            value = filter_query.get(filter_row["display_name"], None)
        if value is None:
            raise ValueError(
                f"""There is no value specified for key '{filter_row["name"]}'""")

        ft_el = ElementTree.SubElement(subelem, "Filter")
        ft_el.set("name", filter_row["name"])

        if filter_row["type"] == "boolean":
            if value is True or value in ["included", "only"]:
                ft_el.set("excluded", "0")
            elif value is False or value in ["excluded"]:
                ft_el.set("excluded", "1")
            else:
                raise ValueError(f"Invalid value for boolean filter : {value}")

        elif isinstance(value, (list, tuple)):
            value = ",".join([str(x) for x in value])
            ft_el.set("value", value)

        else:
            ft_el.set("value", str(value))

    def fetch(self, attributes=None, filters=None, only_unique=True):
        """
        The most important method in this class. Retrieves data
        associated with a particular instance of this class.

        attributes : iterable of str
            An iterable of attributes. Attributes are columns of data.
            Every value within this iterable should correspond to either internal name
            ("name") or displayed name ("display_name"). Invalid elements, those that are
            not found in .attributes attribute are simply removed.
            If left as None, only default attributes are queried.

        filters : python dictionary of str: object.
            You can use keys corresponding to "name" or "display_name" of .filter attribute.
            Filters that are not found in either are simply removed.

        only_unique : boolean
            Whether or not to return the unique rows.

        Example query:

            >>> attributes = ["ensembl_gene_id","Chromosome/scaffold name","manbearpig_homology_perc",]
            >>> filters ={"Type":["pseudogene","protein_coding"],
                       "chromosome_name": ["1","2"],
                       "transcript_tsl":False,
                       "manbearpig_gene":True}
            >>> data = self.fetch(attributes=attributes,filters=filters)

            The above snippet of code will search "Homo sapiens" dataset of "Ensembl Genes 108" database,
            and return pandas dataframe with columns relating to Ensembl Gene ID ("ensembl_gene_id"),
            which chromosome a gene is in ("Chromosome/scaffold name"). There is no such thing as
            "manbearpig_homology_perc", so the attribute is ignored.
            The dataset will be filtered to retain only protein coding and pseudogenes,
            found only on chromosomes 1 and 2, without Transcription Support Level.
            There is no filter named "mabearpig_gene", so the filter is ignored
        """

        query = ElementTree.Element("Query")
        query.set("virtualSchemaName", self.virtual_schema)
        query.set("formatter", "CSV")
        query.set("header", "1")
        query.set("uniqueRows", str(int(only_unique)))
        query.set("datasetConfigVersion", "0.6")

        dataset = ElementTree.SubElement(query, 'Dataset')
        dataset.set('name', self.name)
        dataset.set('interface', 'default')

        if attributes is None:
            attributes = self.attributes[self.attributes.default]
        else:
            attributes = self.attributes[(self.attributes.name.isin(attributes)) |
                                         (self.attributes.display_name.isin(attributes))]

        attributes = attributes["name"].apply(
            self.add_attributes, subelem=dataset)

        if filters is not None:
            filter_df = self.filters[(self.filters.name.isin(filters.keys())) |
                                     (self.filters.display_name.isin(filters.keys()))].copy()
            filter_df.apply(self.add_filters, axis=1,
                            filter_query=filters, subelem=dataset)
        _s = perf_counter()
        r = self.get(query=ElementTree.tostring(query))
        _e = perf_counter()
        print(f"Dataset fetched in {_e-_s:.2f} seconds")
        if 'Query ERROR' in r.text:
            raise ValueError(r.text)

        return pd.read_csv(StringIO(r.text),)

    def extract_homology_attributes(self, species, query):
        """
        Extracts information about homology in the dataset
        towards other species.

        species : python iterable of str
            The list of species a query is directed towards.
            Every element can correspond to either internal name (e.g. "hsapiens")
            or displayed name (e.g. "human"). Case insensitive.
        query : python iterable of str
            What information is returned. Must correspond to "qualifier_name" column
            of "homology" attribute.

        Returns a list of attributes corresponding to the information queried

        Example:
            >>> species = ["human","mmusculus","ZebraFish"]
            >>> query = ["ensembl_gene","associated_gene_name","orthology_type","orthology_confidence","perc_id"]
            >>> hom_attributes = self.fetch(species,query)

        The above snippet of code tries to find homology data towards human ("human"),
        house mouse ("mmusculus") and zebrafish ("ZebraFish"). Specifically, it requires
        the Ensembl Gene ID of a gene ("ensembl_gene"), its name ("associdated_gene_name"),
        what type of orthology it is ("orthology type"), how confident the call is ("orthology_confidence"),
        and what percentage of gene is identical to given query gene.

        There will be a total of 15 (3 species and 5 queries) attributes.

        """
        hm = self.homology

        result = list()
        for specie in species:
            sp_df = hm[(hm.specie_name.str.contains(specie, case=False, regex=False)) | (
                hm.specie_display_name.str.contains(specie, case=False, regex=False))]
            result.append(sp_df)

        result = pd.concat(result, ignore_index=True)
        result = result[result.qualifier_name.isin(query)]

        return result["name"].tolist()
