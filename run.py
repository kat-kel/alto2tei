from collections import namedtuple
from pathlib import Path
from datetime import datetime

import yaml

from src.build import XMLTEI
from src.write_output import Write

# consult the project's configuration
with open("src/config.yml") as cf_file:
        config = yaml.safe_load(cf_file.read())
        p = Path(config.get(("data"))["path"])

# get filepath and name information on every folder/document and its ALTO files 
# in the path specificed in config.py's "data"
Docs = namedtuple("Docs", ["doc_name", "filepaths"])
docs = [Docs    (d.name,                                        # name of document folder
                [f for f in d.iterdir() if f.suffix==".xml"]) # relative filepath for file
        for d in p.iterdir() if d.is_dir()]

# process each folder/document
for d in docs:
    x = XMLTEI(d.doc_name, d.filepaths)
    print("\n=====================================")
    print(f"\33[32m~ now processing document {d.doc_name} ~\x1b[0m")

    # -- phase 1 -- metadata preparation
    print(f"\33[33mmapping metadata\x1b[0m")
    t0 = datetime.utcnow()
    x.prepare_data()
    t1 = datetime.utcnow()
    dif = t1-t0
    print(f"|________finished in {dif.seconds}.{dif.microseconds} seconds.")

    # -- phase 2 -- XML-TEI construction of <teiHeader> and <sourceDoc>
    print(f"\33[33mcreating <teiHeader> and <sourceDoc>\x1b[0m")
    t0 = datetime.utcnow()
    x.build_tree()
    t1 = datetime.utcnow()
    dif = t1-t0
    print(f"|________finished in {dif.seconds}.{dif.microseconds} seconds.")

    # -- phase 3 -- extract and annotate text in <body>
    print(f"\33[33mextracting and annotating text in <body>\x1b[0m")
    t0 = datetime.utcnow()
    root = x.annotate_body()
    t1 = datetime.utcnow()
    dif = t1-t0
    print(f"|________finished in {dif.seconds}.{dif.microseconds} seconds.")

    # -- output XML-TEI file --
    
    Write(d.doc_name, x.root).write()  # write_output.py
