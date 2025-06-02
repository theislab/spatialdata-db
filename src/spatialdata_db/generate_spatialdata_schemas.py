import lamindb as ln
import bionty as bt

product = ln.ULabel(name='Product', is_type=True).save()
ln.ULabel(name='In Situ Gene Expression', type=product).save()
ln.ULabel(name='Spatial Gene Expression', type=product).save()
ln.ULabel(name='CytAssist Spatial Gene and Protein Expression', type=product).save()

biomaterial_type = ln.ULabel(name='Biomaterial Type', is_type=True).save()
ln.ULabel(name='Specimen from Organism', type=biomaterial_type).save()
ln.ULabel(name='Cell Culture', type=biomaterial_type).save()
ln.ULabel(name='Organoid', type=biomaterial_type).save()

modality = ln.ULabel(name='Modality', is_type=True).save()
ln.ULabel(name='RNA', type=modality).save()
ln.ULabel(name='protein', type=modality).save()
ln.ULabel(name='RNA|protein', type=modality).save()

license = ln.ULabel(name='License', is_type=True).save()
ln.ULabel(name='Creative Commons Attribution 4.0 International', type=license).save()

chemistry_version = ln.ULabel(name='Chemistry Version', is_type=True).save()
ln.ULabel(name='Xenium v1', type=chemistry_version).save()
ln.ULabel(name='Xenium prime', type=chemistry_version).save()
ln.ULabel(name='Visium v1', type=chemistry_version).save()
ln.ULabel(name='Visium CytAssist v2', type=chemistry_version).save()

preservation_method = ln.ULabel(name='Preservation Method', is_type=True).save()
ln.ULabel(name='FFPE', type=preservation_method).save()
ln.ULabel(name='Fresh Frozen', type=preservation_method).save()
ln.ULabel(name='Fixed Frozen', type=preservation_method).save()
ln.ULabel(name='unknown', type=preservation_method).save()

staining_method = ln.ULabel(name='Staining Method', is_type=True).save()
ln.ULabel(name='H&E', type=staining_method).save()
ln.ULabel(name='IF', type=staining_method).save()
ln.ULabel(name='DAPI', type=staining_method).save()
ln.ULabel(name='Antibodies', is_type=True).save()

# we could go more into details here
instrument = ln.ULabel(name='Instrument', is_type=True).save()
ln.ULabel(name='Xenium Analyzer', type=instrument).save()
ln.ULabel(name='Illumina NovaSeq', type=instrument).save()
ln.ULabel(name='Visium CytAssist', type=instrument).save()
ln.ULabel(name='Illumina NovaSeq 6000', type=instrument).save()

software_versions = ['Xenium Onboard Analysis v2.0.0', 'Xenium Onboard Analysis v1.9.0',
       'Xenium Onboard Analysis v1.6.0', 'Xenium Onboard Analysis v1.7.0',
       'Space Ranger v2.1.0', 'Xenium Onboard Analysis v1.5.0',
       'Xenium Onboard Analysis v1.4.0', 'Space Ranger v2.0.1',
       'Xenium Onboard Analysis v1.3.0', 'Xenium Onboard Analysis v1.0.2',
       'Space Ranger v2.0.0', 'Space Ranger v1.3.0',
       'Space Ranger v1.2.0', 'Space Ranger v1.1.0',
       'Space Ranger v1.1.3', 'Space Ranger v1.0.0']

software = ln.ULabel(name='Software', is_type=True).save()
for version in software_versions:
    ln.ULabel(name=version, type=software).save()

panel_type = ln.ULabel(name='Panel Type', is_type=True).save()
ln.ULabel(name='Custom Add-on', type=panel_type).save()
ln.ULabel(name='Predesigned', type=panel_type).save()

probe_set = ln.ULabel(name='Probe Set', is_type=True).save()
ln.ULabel(name='Visium Human Transcriptome Probe Set v2.0', type=probe_set).save()
ln.ULabel(name='Visium Mouse Transcriptome Probe Set', type=probe_set).save()

slide_area_values = ['A1', 'D1', 'A', 'B', 'C1', 'B1', 'A2']
slide_area = ln.ULabel(name='Slide Area', is_type=True).save()
for value in slide_area_values:
    ln.ULabel(name=value, type=slide_area).save()

transcriptome_values = ['GRCh38-2020-A', 'mm10-2020-A', 'mm10-3.0.0', 'GRCh38-3.0.0']
transcriptome = ln.ULabel(name='Transcriptome', is_type=True).save()
for value in transcriptome_values:
    ln.ULabel(name=value, type=transcriptome).save()

sample_level_schema = ln.Schema(
    name='SampleLevel',
    features=[
        ln.Feature(name='Product', dtype='cat[ULabel[Product]]', coerce_dtype=True).save(),
        ln.Feature(name='Assay', dtype=bt.ExperimentalFactor.name, coerce_dtype=True).save(),
        ln.Feature(name='Biomaterial Type', dtype='cat[ULabel[Biomaterial Type]]', coerce_dtype=True).save(),
        ln.Feature(name='Organism', dtype=bt.Organism.name, coerce_dtype=True).save(),
        ln.Feature(name='Tissue', dtype=bt.Tissue.name, coerce_dtype=True).save(),
        ln.Feature(name='Modality', dtype='cat[ULabel[Modality]]', coerce_dtype=True).save(),
        ln.Feature(name='Dataset Url', dtype=str, coerce_dtype=True).save(),
        ln.Feature(name='License', dtype='cat[ULabel[License]]', coerce_dtype=True).save().with_config(optional=True),
        ln.Feature(name='Publication Date', dtype=str, coerce_dtype=True).save(),

        ln.Feature(name='Replicate', dtype=str, coerce_dtype=True).save().with_config(optional=True),
        ln.Feature(name='Sample ID at Source', dtype=str, coerce_dtype=True).save(),

        ln.Feature(name='Development Stage', dtype=bt.DevelopmentalStage.name, coerce_dtype=True).save().with_config(optional=True),
        ln.Feature(name='Disease', dtype=bt.Disease.name, coerce_dtype=True).save(),
        ln.Feature(name='Disease Details', dtype=str, coerce_dtype=True).save().with_config(optional=True),

        ln.Feature(name='Chemistry Version', dtype='cat[ULabel[Chemistry Version]]', coerce_dtype=True).save(),
        ln.Feature(name='Chemistry Details', dtype=str, coerce_dtype=True).save().with_config(optional=True),
        ln.Feature(name='Preservation Method', dtype='cat[ULabel[Preservation Method]]', coerce_dtype=True).save().with_config(optional=True),
        ln.Feature(name='Staining Method', dtype='cat[ULabel[Staining Method]]', coerce_dtype=True).save().with_config(optional=True),
        ln.Feature(name='Instrument(s)', dtype='cat[ULabel[Instrument]]', coerce_dtype=True).save().with_config(optional=True),
        ln.Feature(name='Software', dtype='cat[ULabel[Software]]', coerce_dtype=True).save().with_config(optional=True),
        ln.Feature(name='Number of Target Genes', dtype=int, coerce_dtype=True).save().with_config(optional=True),
    ]
).save()

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

visium_specific_schema = ln.Schema(
    name='VisiumSpecifc',
    features=[
        ln.Feature(name='Probe Set', dtype=str).save().with_config(optional=True),
        ln.Feature(name='Sequencing Configuration', dtype=str).save().with_config(optional=True),
        ln.Feature(name='Slide Area', dtype='cat[ULabel[Slide Area]]', coerce_dtype=True).save().with_config(optional=True),
        ln.Feature(name='Number of Spots', dtype=int).save(),
        ln.Feature(name='Genes Detected', dtype=int).save(),
        ln.Feature(name='Median Genes per Spot', dtype=float).save().with_config(optional=True),
        ln.Feature(name='Mean Reads per Spot', dtype=float).save().with_config(optional=True),
        ln.Feature(name='Transcriptome', dtype='cat[ULabel[Transcriptome]]', coerce_dtype=True).save(),
        ln.Feature(name='Microscope', dtype=str).save().with_config(optional=True),
        ln.Feature(name='Objective', dtype=str).save().with_config(optional=True),
        ln.Feature(name='Numerical Aperture', dtype=str).save().with_config(optional=True),
        ln.Feature(name='Camera', dtype=str).save().with_config(optional=True),
        ln.Feature(name='Exposure', dtype=str).save().with_config(optional=True),
        ln.Feature(name='Gain', dtype=str).save().with_config(optional=True),
    ]
).save()

varT_schema = ln.Schema(itype=bt.Gene.ensembl_gene_id).save()

ln.Schema(
    otype="SpatialData",
    name='Visium',
    slots={
        "attrs:metadata_general": sample_level_schema,
        "attrs:metadata_visium": visium_specific_schema,
        "tables:table:var.T": varT_schema
    }
).save()

ln.Schema(
    otype="SpatialData",
    name='Xenium',
    slots={
        "attrs:metadata_general": sample_level_schema,
        "attrs:metadata_xenium": xenium_specific_schema,
        "tables:table:var.T": varT_schema
    }
).save()