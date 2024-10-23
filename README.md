# ITU BSc Project 2023

## Note  
The original data in the P1_Affiliates.xlsx file that the code worked with was considered somewhat sensitive, 
so I've replaced it with a file containing unrelated random information, RandomPeople.xlsx. 
This random data was created so that one can still see how the code used to work, 
but it does make the generated results meaningless.  



## Setup  
  
**Have a folder with the following files:**  
	- The latest Solr release downloaded from https://solr.apache.org/downloads.html and extracted to the folder (project used version: solr-9.2.0)  
	- P1_Affiliates.xlsx  
	- manual_exps.txt  
	- psetup.py  
	- pquery.py  
	- prestore.py  
	- pbackup.py  
	- pstat.ipynb  


**Start Solr and create collection by opening a command prompt, going to the directory "solr-#.#.#/bin", and running:**  
```
solr start -e schemaless -Dsolr.modules=extraction
```  

**Setup the Solr collection by opening a terminal (may need to be run as administrator), going to the directory "solr-#.#.#", and running:** 
```
curl -X POST -H 'Content-type:application/json' -d '{  
  "add-requesthandler": {  
	"name": "/update/extract",  
	"class": "solr.extraction.ExtractingRequestHandler",  
	"defaults":{ "lowernames": "true", "captureAttr":"true"}  
  }  
}' 'http://localhost:8983/solr/gettingstarted/config'  
```

## Usage  
  
*If Solr has been setup before, but is now stopped, start it with the "solr start -e schemaless -Dsolr.modules=extraction" line.*  
*The curl to setup the Solr collection doesn't need to be used again if it has been done before.*  
*The Solr collection should also still contain any indexed documents between sessions.*  

**psetup.py**  
	- Creates the Affiliate_jsons folder.  
	- Requests forskningsportal.dk for the json files of publications for each affiliate and places them in the Affiliate_jsons folder.  
	- Generates doc_key.txt, aff_key.txt, and auth_key.txt files.  
	- Edits the solr.in.cmd file in the "solr-#.#.#/bin" directory in order to allocate some more memory for Solr to work with.  
	- Deletes any documents currently in Solr collection, then indexes the publications with open access PDFs into the Solr collection.  

**pquery.py**  
	- Initiates the query process so the user can make a query and receive a ranked list of up to the 10 most relevant affiliates found.  

**prestore.py**  
	- Restores Solr collection of PDFs from most recent backup.  

**pbackup.py**  
	- Creates backup of PDFs currently in Solr collection. Can keep up to 5 backups.  

**pstat.ipynb**  
	- Notebook that contains the code for the statistical analyses and figures used in the BSc Project's report.  
