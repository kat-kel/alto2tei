# ALTO4 to TEI P5
This application prepares a TEI edition of a digitzed document whose pages were transcribed and encoded in ALTO4 files using the HTR tool [eScriptorium](https://traces6.paris.inria.fr/).

It follows [SegmOnto's](https://github.com/SegmOnto/) controlled vocabulary and has been designed as part of the [Gallic(orpor)a](https://github.com/Gallicorpora) pipeline.

# How To Use
## Requirements
- Python 3.7
- Bash
- A file-naming system that organizes all of a transcription's ALTO-XML files into a single sub-directory, whose name is identical to the document's Archival Resource Key (ARK). In example, all transcribed pages of the document whose ARK is `btv1b8613380t` are stored in the directory `./data/btv1b8613380t/`.
   ```
   alto2tei/  
   │   README.md
   │   ...
   │
   └───data/
   │   │
   │   └───btv1b8613380t/
   │   │   │   f1.xml
   │   │   │   f2.xml
   │   │   │   ...
   │   └───btv1b8613380t/
   │       │   f1.xml
   │       │   f2.xml
   │       │   ...
   ```


## Steps
1. Download this repository from GitHub.
   ```shell
   $ git clone git@github.com:kat-kel/alto2tei.git
   $ cd alto2tei
   ```
2. Create and activate a virtual environment in which to install the application.
   ```shell
   $ python3.7 -m ".venv-alto2tei"
   $ source .venv-alto2tei/bin/activate
   ```
3. Install the application.
   ```shell
   $ bash install.sh
   ```
4. Configure the application.

   `./config.yml`
   ```yaml
   data:
      # specify the relative path of your data files
      path: "./data"
   ```
5. Use the application.
   ```shell
   $ alto2tei --config config.yml --version "3.0.13" --header --sourcedoc --body
   ```

# Compatability
## Document Metadata
Currently, the application is designed to scrape metadata for the `<teiHeader>` from three resources related to the Bibliothèque nationale de France's Gallica repository.
   1. [Gallica's](https://api.bnf.fr/fr/api-iiif-de-recuperation-des-images-de-gallica) servers
   2. Bibliothèque nationale de France's [catalogue général](https://catalogue.bnf.fr)
   3. SUDOC's [Répertoire des centres de ressources](http://www.sudoc.abes.fr/cbs/xslt/)

Therefore, only transcriptions of digital exemplars from Gallica can take full advantage of the application's automatically generated `<teiHeader>`. However, the URI syntax that this application uses to retrieve data from Gallica's servers is [the same syntax](https://iiif.io/api/image/3.0/) used by any other institution that participates, like the Bibliothèque nationale de France, in the IIIF. To adjust this URI and work with transcriptions of digital exemplars stored on other institutions' servers, edit the parameters "scheme," "server," and "prefix" in this application's configuration file. These parameters will be inserted into a string with the following pythonic syntax:
```python
f"{scheme}://{server}{manifest_prefix}{ARK}{manifest_suffix}"
```
The first three parameters in the IIIF URI can be modified in the configuration file as follows:
```yaml
  scheme: "https"
  server: "gallica.bnf.fr"
  manifest_prefix: "/iiif/ark:/12148/"
  image_prefix: "/iiif/ark:/12148/" # for Gallica, same as manifest
  manifest_suffix: "/manifest.json"
```
An example of this URI, constructed for the document with the ARK "bpt6k324358v" is:
>`https://gallica.bnf.fr/iiif/ark:/12148/bpt6k324358v/manifest.json`

The application has been designed and tested on IIIF manifest data typical of text documents distributed on Gallica. Its adaptability to how other institutions have encoded data in a IIIF manifest cannot be guaranteed.

## Transcription Data
The application can produce a `<sourceDoc>` from any ALTO 4 files that were created by the Kraken engine, including those produced inside the eScriptorium interface. The source document does not need to be part of the Bibliothèque nationale de France's collections, its digital exemplars do not need to be distributed on Gallica, and the machine transcription does not need to have been made with models trained on the SegmOnto controlled vocabulary. The TEI element `<sourceDoc>` that this application generates adapts to any ALTO 4 files that resemble the formats produced by Kraken's engine.

## Pre-Annotated Text Body
Currently, the application is designed to recognize zones and lines of text on a page whose labels conform to SegmOnto's controlled vocabulary. The application cannot generate a `<body>` from ALTO-XML files in which a line or zone's `@TAGREF` is not part of the SemgOnto vocabulary.

However, with an XSL Transformation, a user can extract specific lines of text from the `<sourceDoc>` according to their own `@TAGREF` system and create them in the `<body>`.