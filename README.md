Reducing FIES data with CERES
-----------------------------

   1. Run ```reducing/mkCeresReffile.py --filter``` to check for the targets in the database
      1. Update TCSTGT header keyword to help matches if in DB but not found
      1. Add new objects to eblm_parameters table if not present
   1. Run ```reducing/mkCeresReffile.py --reffile``` to make the reference file and add a row to the database for each spectrum
      1. Check the spectral type and proper motion etc. are included in reffile.txt
   1. Reduce each night's data using CERES:
      1. ```cd ~/Dropbox/PythonScripts/cere/fies```
      1. ```python fiespipe.py /path/to/data -fibre FIB -binning BIN -npools NPOOLS```
   1. Run ```database/ingestFiesResults.py``` to ingest the CERES output into the database
