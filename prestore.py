import requests
#Restores Solr collection of PDFs from most recent backup
requests.post("http://localhost:8983/solr/gettingstarted/replication?command=restore")