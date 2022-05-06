# ALTO4 to TEI P5
This application prepares a TEI edition of a digitzed document whose pages were transcribed and encoded in ALTO4 files using the HTR tool [eScriptorium](https://traces6.paris.inria.fr/).

It follows [SegmOnto's](https://github.com/SegmOnto/) controlled vocabulary and has been designed as part of the [Gallic(orpor)a](https://github.com/Gallicorpora) pipeline.

## Requirements
### Compatibility
- The application is currently designed to exclusively work with Gallica's sources.

### ALTO Tags
- The zone and line tags in the ALTO file need to follow the SegmOnto guidelines.

### File structure
- The application requires folders which contain the XML-ALTO4 files. The folder name must be the ARK identifier from Gallica.
- The ALTO4 files must be named with their folio number preceded by the letter `f`. They can include prefixes before the folio number.

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
