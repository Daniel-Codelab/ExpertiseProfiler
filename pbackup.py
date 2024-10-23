import requests
#Creates backup of PDFs currently in Solr collection. Can keep up to 5 backups.
requests.post("http://localhost:8983/solr/gettingstarted/replication?command=backup&numberToKeep=5")