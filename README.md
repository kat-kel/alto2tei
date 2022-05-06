# ALTO4 to TEI P5
This application prepares a TEI edition of a digitzed document whose pages were transcribed and encoded in ALTO4 files using the HTR tool [eScriptorium](https://traces6.paris.inria.fr/).

It follows [SegmOnto's](https://github.com/SegmOnto/) controlled vocabulary and has been designed as part of the [Gallic(orpor)a](https://github.com/Gallicorpora) pipeline.

## Requirements
### Compatibility
- The application is currently designed to work with Gallica's digitized sources, principally textual sources.

#### File structure
- The application requires folders which contain the XML-ALTO4 files. The folder name must be the ARK identifier from Gallica.
- The ALTO4 files must be named with their folio number preceded by the letter `f`. They can include prefixes before the folio number.

`data`
    |_____`btv1b8613380t/`
    |       |_____________`btv1b8613380t_f#.xml`
    |_____`btv1b86146004/`
            |_____________`f#.xml`    
