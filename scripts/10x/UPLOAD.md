# How to upload datasets
1. you need a .csv file with your collected metadata (columns should have the names of the features in the metadata schema) + four specific columns
- uid: downloaded datasets and metadata rows are associated via uid --> you need a column 'uid' in your metadata file and a folder on the cluster that starts with the uid and contains the converted .zarr file
- Description: the description to be added
- Replicate: specify which replicate or sub-sample of a sample (eg. Description = 'Xenium Mouse Brain', Replicate = 'FF' -->  will be stored as 'Xenium Mouse Brain (FF)')
- Collection Description: if you want to add the dataset to a certain collection, add the name of the collection here. Currently, the datasets are not automatically bundled, but that will change in the future

2. run 'upload.py'
- specify data_path: the path that contains your data in subfolders starting with the respective 'uid' of the metadata .csv
- dry-run runs the curation without uploading the dataset
- error and update logs are created after the run

# How to adapt for new technology to sddb
1. check the 'SampleLevel' metadata fields in 'src/spatialdata_db/generate_spatialdata_schemas.py' and decide which additional features are required

2. If you need a new categorical feature to curate the metadata, create it similar to
<pre><code>```python 
preservation_method = ln.ULabel(name='Preservation Method', is_type=True).save()
ln.ULabel(name='FFPE', type=preservation_method).save()
ln.ULabel(name='Fresh Frozen', type=preservation_method).save()
ln.ULabel(name='Fixed Frozen', type=preservation_method).save()
ln.ULabel(name='unknown', type=preservation_method).save() ```</code></pre>

3. Create your add-on schema like:
<pre><code>```python 
xenium_specific_schema = ln.Schema(
    name='XeniumSpecifc',
    features=[
        ln.Feature(name='Panel Type', dtype='cat[ULabel[Panel Type]]', coerce_dtype=True).save(),
        ln.Feature(name='Panel', dtype=str, coerce_dtype=True).save(),
        ln.Feature(name='Number of Cells', dtype=int).save(),
        ln.Feature(name='Number of Add-on Genes', dtype=int).save().with_config(optional=True),
        ln.Feature(name='Median Transcripts per Cell', dtype=float).save().with_config(optional=True),
        ln.Feature(name='Region Area', dtype=float).save().with_config(optional=True),
        ln.Feature(name='Total Cell Area', dtype=float).save().with_config(optional=True),
    ]
).save()

varT_schema = ln.Schema(itype=bt.Gene.ensembl_gene_id).save()
ln.Schema(
    otype="SpatialData",
    name='Xenium',
    slots={
        "attrs:metadata_general": ln.Schema.get(name='SampleLevel'),
        "attrs:metadata_xenium": xenium_specific_schema,
        "tables:table:var.T": varT_schema
    }
).save()
```</code></pre>

4. follow the TODO's in upload.py 
