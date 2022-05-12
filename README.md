# ALTO4 to TEI P5
This application prepares a TEI edition of a digitzed document whose pages were transcribed and encoded in ALTO4 files using the HTR tool [eScriptorium](https://traces6.paris.inria.fr/).

It follows [SegmOnto's](https://github.com/SegmOnto/) controlled vocabulary and has been designed as part of the [Gallic(orpor)a](https://github.com/Gallicorpora) pipeline.

## Requirements
### Compatibility
- Currently, the application is designed to work exclusively with Gallica's sources, as part of the BNFLab's Gallic(orpor)a project.

### ALTO Tags
- The zone and line tags in the ALTO file need to follow the SegmOnto guidelines.

### File structure
- The application requires folders which contain each page's XML-ALTO4 file. The folder name must be the ARK identifier from Gallica.
- The ALTO4 files must be named with their folio number preceded by the letter `f`. They can include prefixes before the folio number. 

In example:

```
___data/
   |   btv1b8613380t.xml (TEI output)
   |   btv1b86146004.xml (TEI output)
   |___btv1b8613380t/
   |   |   btv1b8613380t_f4.xml (ALTO input)
   |   |   btv1b8613380t_f5.xml (ALTO input)
   |   |   ...
   |___btv1b86146004/
   |   |   f6.xml (ALTO input)
   |   |   f7.xml (ALTO input)
   |   |   ...

```
## Strategy
The document's metadata are extracted from both the digitization's IIIF manifest and from the BnF's SRU API, which draws on the BnF catalogue. On Gallica, every digitized source's IIIF manifest should include a valid reference to the document's ARK (Archival Resource Key) in the BnF catalogue. When this identifier is valid, the application retrieves rich metadata from the SRU API and pairs it with some metadata from the IIIF manifest. When the identifier is invalid, it relies exclusively on metadata in the digitized document's IIIF manifest. These two endpoints complement each other and compensate for missing data. However, the SRU API data is only applied to the document if an exact match to the document's unique ARK is found in the catalogue. This strict condition prevents any false data from being wrongly included in the document's metadata.

## Method. Task 1: Extract metadata from internet

The module `./transform/elements/api/teiheader_data.py` scrapes and cleans relevant metadata from the internet. The first endpoint is the digitized document's IIIF manifest. The manifest's response follows the IIIF community's recommendations and the data are sent in a dictionary.

**IIIF Manifest Data**

label in IIIF manifest | value | new dictionary key
|:--:|:--:|:--:|
`"Relation"`|uri to document in BnF catalogue (ex. ht<span>tp://catalogue.bnf.fr/ark:/...)|`"Relation"`
--|ARK component of `"Relation"` value|`"Catalogue ARK"`
`"Repository"`|name of conservation institution (BnF)|`"Repository"`
`"Shelfmark"`|document's shelfmark in conservation institution |`"Shelfmark"`
`"Title"`|title of document|`"Title"`
`"Language"`|language of document's text|`"Language"`
`"Creator"`|person accredited with document's creation|`"Creator"`
`"Date"`|date of document|`"Date"`

To acquire more detailed bibliographic information about the digitized document, the module also requests data from the BnF's SRU API. The response follows the Unimarc schema and the data are sent in XML.

**SRU API Unimarc Data**

|Unimarc data||value|new dictionary key|
|:--:|:--:|:--:|:--:|
|`@tag` of `<datafield>`|`@code` of `<subfield>`|||
||||
|200|a|clean title|`"title"`|
|210|a|place of publication|`"pubplace"`|
|102|a|place of publication's country code|`"pubplace_key"`|
|210|c|publisher|`"publisher"`|
|210|d|date of publication|`"date"`|
|801|a|conservation institution's country|`"country"`|
|930|a|conservation institution's shelfmark for the document|`"idno"`|
|200|a|document's type|`"objectdesc"`|
||||
||||**dict keys for list item, stored in key `"authors"`**|
|700 and/or 701|o|identifier if first four characters are `"ISNI"`|`"isni"`|
|700 and/or 701|a|author's primary name, typically the surname|`"primary_name"`|
|700 and/or 701|b|name links extracted from author's secondary name ("van der", "de la", "de", "du", "des", "von", "van")|`"namelink"`|
|700 and/or 701|b|author's secondary name, without name links|`"secondary_name"`|
--|--|concatanation of first 2 characters of primary name plus author's position in list|`"xmlid"`|
||||
|`@tag` of `<controlfield>`|--|||
|003|--|persistent ID given by the BnF (ex. ht<span>tp://catalogue.bnf.fr/ark:/...)|`"ptr"`|


## Method. Task 2: Input doc metadata

The module `./transform/elements/teiheader.py` retrieves the dictionaries `manifest_data` and `unimarc_data` created in the first task and enters them into a TEI framework.

### 2.1. Create blank tree
First, an instantiation of the class `BlankTree` generates a default `<teiHeader>`. This tree is partially completed using default values dictated in the application's configuration file. These default data include who is responsible for the processed transcriptions, their transformation into a new TEI publication, etc. Certain elements in the blank tree are made accessible in the `BlankTree` class' method `.children`. These important XML-TEI elements are annotated in the example below with two asterisks.

```
<teiHeader>
   <fileDesc>
      <titleStmt>
      ** <title>...</title> --> .children["ts_title"]
      ** <author>...</author> --> .children["ts_author"]
         <respStmt> --> .children["respStmt"]
         ++ <resp>...</resp>
         ++ <persName>...</persName>
      </titleStmt>
      <extent>
      #  <measure unit="image" n=""/> --> .children["measure"]
      </extent>
      <publicationStmt> --> .children["publicationStmt"]
      ++ <publisher>...</publisher>
      ++ <authority>...</authority>
      ++ <availability status="", n="">
         ++ <licence target=""/>
         </availability>
      #  <date when=""/>
      </publicationStmt>
      <sourceDesc>
         <bibl>
         ** <ptr target=""/> --> .children["ptr"]
         ** <author ref="">...</author> --> .children["bib_author"]
         ** <title>...</title> --> .children["bib_title"]
         ** <pubPlace key="">...</pubPlace> --> .children["pubPlace"]
         ** <publisher>...</publisher> --> .children["publisher"]
         ** <date>...</date> --> .children["date"]
         </bibl>
         <msDesc>
            <msIdentifier>
            ** <country key=""/> --> .children["country"]
            ++ <settlement>...</settlement>
            ** <repository>...</repository> --> .children["respository"]
            ** <idno>...</idno> --> .children["idno"]
               <altIdentifier>
               #  <idno type="ark"/>
               </altIdentifier>
            </msIdentifier>
            <physDesc>
               <objectDesc>
               ** <p>...</p> --> .children["p"]
               </objectDesc>
            </physDesc>
         </msDesc>
      </sourceDesc>
   </fileDesc>
   <profileDesc>
      <langUsage>
      ** <language ident=""/> --> .children["language"]
      </langUsage>
   </profileDesc>
</teiHeader>
```

key|description
--|--
**|data in IIIF manifest and/or SRU API response
++|data drawn from mutable config file
\#|data automatically generated by application
-->|point to variable containing this eTree element
.children[]|class instance variable of `.teiheader.BlankTree`

### 2.2. Fill tree
After creating the blank tree, the module populates the child elements with their relevant data.

|XML-TEI element|`.children` key|`manifest_data` key|`unimarc_data` key|
|:--:|:--:|:--:|:--:|
|||||
|.//author /name|child of `"ts_author"` and `"bib_author"`|`"Creator"`|--|
|.//author @xml:id or @ref|descendant of `"ts_author"`and `bib_author`|generated upon input|`"authors"[i]["xmlid"]`|
|.//author /persName /forename|descendant of `"ts_author"` and `bib_author`|--|`"authors"[i]["secondary_name"]`|
|.//author /persName /namelink|descendant of `"ts_author"`and `bib_author`|--|`"authors"[i]["namelink"]`|
|.//author /persName /surname|descendant of `"ts_author"`and `bib_author`|--|`"authors"[i]["primary_name"]`|
|.//author /persName /ptr|descendant of `"ts_author"`and `bib_author`|--|`"authors"[i]["isni"]`|
|||||
|.//titleStmt /title|`"ts_title"`|`"Title"`|`"title"`|
|.//bibl /ptr @target|`"ptr"`|--|`"ptr"`|
|.//bibl /title|`"bib_title"`|`"Title"`|`"title"`|
|.//bibl /pupPlace|`"pubPlace"`|--|`"pubplace"`|
|.//bibl /pubPlace @key|`"pubPlace"`|--|`"pubplace_key"`|
|.//bibl /publisher|`"publisher"`|--|`"publisher"`|
|.//bibl /date|`"date"`|`"Date"`|`"date"`|
|.//msIdentifier /country @key|`"country"`|--|`"country"`|
|.//msIdentifier /repository|`"repository"`|`"Repository"`|--|
|.//msIdentifier /idno|`"idno"`|`"Shelfmark"`|`"idno"`|
|.//physDesc /objectDesc /p|`"p"`|--|`"objectdesc"`|
|.//profileDesc /langUsage /language|`"language"`|`"Language"`|--|
|.//profileDesc /langUsage /language @ident| `"language"`|--|`"lang"`|
