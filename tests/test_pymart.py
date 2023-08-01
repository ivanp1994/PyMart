# -*- coding: utf-8 -*-
"""
Created on Tue Aug  1 09:33:08 2023

@author: ivanp
"""
import requests
import pytest
import pandas as pd
import pymart as pm

#tests whether invalid connections are detected
@pytest.mark.parametrize("url_param",[("host","http://www.nosembl.org"),("path","/criomart/martservice"),("port",666)])
def test_invalid_connargs(url_param):
    url_kwargs = {url_param[0]:url_param[1]}
    with pytest.raises((requests.exceptions.ConnectionError,requests.exceptions.HTTPError)):
        pm.list_databases(**url_kwargs)

#tests that the invalid datasets are caught
@pytest.mark.parametrize("param",[(None,"ensembl mart ensembl","mouse"),(None,None,None),(None,"ensembl mart ensembl","manbearpig")])
def test_fake_datasets(param):
    kwargs = dict(zip(["dataset_name","database_name","species_name"],param))
    with pytest.raises(ValueError):
        pm.fetch_data(**kwargs)

def _validate_dataframe(df):
    assert isinstance(df,pd.DataFrame)
    assert len(df)>0
    assert "name" in df.columns
    assert "display_name" in df.columns   
    
#tests that the proper display connection returns everythong on the frontbase
def test_proper_default_connection():
    databases = pm.FrontBase().list_databases()
    _validate_dataframe(databases)

#tests attributes and filters from astyanax mexicanus
def test_attribute_getter():
    attrs = pm.get_attributes("amexicanus_gene_ensembl",display=False)
    _validate_dataframe(attrs)

def test_filter_getter():
    fils = pm.get_filters("amexicanus_gene_ensembl",display=False)
    _validate_dataframe(fils)

#tests if we find mmusculus_gene_ensembl and we correctly get attributes
def test_mousedataset():
    attributes = ["ensembl_gene_id","Chromosome/scaffold name","manbearpig_homology_perc",]
    filters ={"Type":["pseudogene","protein_coding"],"chromosome_name": ["1","2"],"transcript_tsl":False,"manbearpig_gene":True,}
    mouse_data_1 = pm.fetch_data(dataset_name="mmusculus_gene_ensembl",attributes = attributes,filters=filters)
    assert mouse_data_1.shape[1]==2
    

