#psetup.py
#Project Data Setup Program
#by Daniel H

#Imports
import pandas as pd
import numpy as np
from collections import defaultdict
import itertools

import os
import requests
import urllib
import json



#P1 Affiliates
p1_master = pd.read_excel('RandomPeople.xlsx')
p1_master.dropna(axis=1, how='all')

#Personal Information
p1_info = p1_master.iloc[:,:18]
#Fields/Focuses
#p1_fields = p1_master.iloc[:,[0, 1] + list(range(18, 33))]
#Participation
#p1_roles = p1_master.iloc[:,[0, 1] + list(range(33, 48))]



#Creates forskningsportal request urls for every P1 Affiliate's name
urls = list()
for i in range(p1_info.shape[0]):
    urls.append([p1_info.iloc[i, 0] + " " + p1_info.iloc[i, 1], "https://local.forskningsportal.dk/local/dki-cgi/ws/search?f0=RTY&q0=pub&exp=CON%3D(" + urllib.parse.quote(p1_info.iloc[i, 1]) + "%2C%20" + urllib.parse.quote(p1_info.iloc[i, 0]) + ")&sort=year%20desc"])

#Creates Affiliate_jsons folder if it doesn't exist
if not os.path.exists("Affiliate_jsons"):
    os.mkdir("Affiliate_jsons")

#Creates json files of the arrays of publication jsons for each P1 Affiliate
print("Number of json files to request from forskningsportal.dk:", len(urls))
i = 0
for name, url in urls:
    if i % 10 == 0:
        print(i)
    i += 1
    #Gets the queryID for a name search from a request for up to the first 5 jsons
    publications = requests.get(url)
    #Gets the uri for a queryID that can export all the publication jsons
    publications = requests.get("https://local.forskningsportal.dk/local/dki-cgi/ws/export/?id=" + publications.json()["queryID"] + "&type=jarr")
    #Gets the array of publication jsons from the uri
    publications = requests.get("https://local.forskningsportal.dk" + publications.json()["uri"])
    if publications.status_code == 200:
        #Saves to file
        file_path = "Affiliate_jsons/" + name.replace(" ", "_") + ".json"
        with open(file_path, "w") as file:
            file.write(json.dumps(publications.json(), indent=4))
print(len(urls))


#Initiates dataframe to input extracted information into
p1_p = p1_info[["First Name(s)", "Last Name", "Orcid"]].copy()
p1_p["jsons"] = p1_p.apply(lambda x: (x["First Name(s)"] + " " + x["Last Name"]).replace(" ", "_") + ".json", axis=1)
p1_p["name_vars"] = [set() for _ in range(len(p1_p.index))]
p1_p["pdf_links"] = [list() for _ in range(len(p1_p.index))]
p1_p["doc_authors"] = [list() for _ in range(len(p1_p.index))]

#Loops through files in Affiliate_jsons folder
for i, file_name in enumerate(p1_p["jsons"]):
    #Checks that file exists before opening
    if os.path.exists("Affiliate_jsons/" + file_name):
        #Opens file
        with open("Affiliate_jsons/" + file_name) as file:
            #Loads file
            publications = json.load(file)
        #Checks if orcid is known for affiliate
        orc = 0
        if isinstance(p1_p.loc[i, "Orcid"], str):
            orc = p1_p.loc[i, "Orcid"][-19:]
        #Loops through publications in jsons file to find verified name variations using orcid if available
        for p in publications:
            #Creates names and orcids list to keep track of name-orcid pairs for publication
            names = list()
            orcids = list()
            for person in p["person"]:
                names.append(str(person["first"]) + " " + str(person["last"]))
                if "orcid" in person:
                    orcids.append(person["orcid"])
                else:
                    orcids.append(None)
            #Checks if affiliate's orcid appeared in orcid list and then saves the matching name if it did
            if orc in orcids:
                p1_p.loc[i, "name_vars"].add(names[orcids.index(orc)].lower())
        #Loops through publications in jsons file again to check if any of the name variations shows up for each publication
        for p in publications:
            #Checks if the publication has open access links
            if "oa_link" in p:
                #Looks for an open access link of type "loc". The "rem" and "doi" links often cause errors or just return htmls, not pdfs.
                for link in p["oa_link"]:
                    if link["type"] == "loc":
                        if "url" in link:
                            #If no verified name variations were found, it ignores verification and saves every PDF link
                            if len(p1_p.loc[i, "name_vars"]) == 0:
                                p1_p.loc[i, "pdf_links"].append(link["url"])
                                p1_p.loc[i, "doc_authors"].append(len(p["person"])) #author count
                            #Name variation verification process
                            else:
                                #Searches for name in author list of publication that matches a name in the name variation list
                                for person in p["person"]:
                                    if str(person["first"] + " " + person["last"]).lower() in p1_p.loc[i, "name_vars"]:
                                        #Double checks that orcid matches if matching name was found and orcid is available before saving PDF link
                                        if "orcid" in person:
                                            if person["orcid"] == orc:
                                                p1_p.loc[i, "pdf_links"].append(link["url"])
                                                p1_p.loc[i, "doc_authors"].append(len(p["person"])) #author count
                                                break
                                        #If orcid is unavailable for matching name, it goes ahead with saving the PDF link
                                        else:
                                            p1_p.loc[i, "pdf_links"].append(link["url"])
                                            p1_p.loc[i, "doc_authors"].append(len(p["person"])) #author count
                                            break



#Creates dictionary to track document-affiliate relationships
doc_affs = defaultdict(list)
#Creates dictionary to track each document with an ID
doc_key = defaultdict(list)
#Creates dictionary to track each affiliate with an ID
aff_key = defaultdict(list)

#Assigns each document a list of affiliates associated with it, as well as each affiliate an ID
for i, row in p1_p.iterrows():
    for doc in row["pdf_links"]:
        doc_affs[doc].append(i)
    aff_key[i].extend([row["First Name(s)"], row["Last Name"]])

#Assigns each document an ID as well now
for i, doc in enumerate(doc_affs.keys()):
    doc_key[i].extend([doc, doc_affs[doc]])



#Stores additional data pquery.py requires so setup doesn't have to be run alongside it every time
with open("doc_key.txt", "w") as file:
    json.dump(doc_key, file)
with open("aff_key.txt", "w") as file:
    json.dump(aff_key, file)



#Creates link key
link_key = {v[0]: k for k, v in doc_key.items()}

#Creates author count key
auth_key = dict()
for i, row in p1_p.iterrows():
    for i, doc in enumerate(row["pdf_links"]):
        auth_key[link_key[doc]] = row["doc_authors"][i]

#Stores author count key so setup doesn't have to be run alongside pquery.py every time
with open("auth_key.txt", "w") as file: #author count
    json.dump(auth_key, file)



#Deletes all documents in collection
requests.post("http://localhost:8983/solr/gettingstarted/update?commit=true", json={'delete':{'query': '*:*'}})

#Increases memory for Solr to work with so as not to have it crash when trying to index a large document
for p in os.listdir():
    if p[:4] == "solr" and p[-3:] != "tgz":
        path = p + "/bin/solr.in.cmd"
with open(path, "r") as temp:
    temp2 = temp.readlines()
    for i, line in enumerate(temp2):
        #Finds line in solr.in.cmd that needs to be edited
        if line[:26] == "REM set SOLR_JAVA_MEM=-Xms":
            temp2[i] = "set SOLR_JAVA_MEM=-Xms2g -Xmx2g\n"
#Rewrites the solr.in.cmd file
with open(path, "w") as temp:
    temp.writelines(temp2)



#Indexes PDFs into Solr using the pdf links
print("Number of documents to attempt to index into Solr:", len(doc_key))
ID = 0
#Loops through PDF links
for i in range(0, len(doc_key)):
    if i % 100 == 0:
        print(ID)
    #Extracts PDF from link
    document = requests.get(doc_key[ID][0])
    if document.status_code == 200:
        #Indexes extracted PDF into Solr collection
        requests.post("http://localhost:8983/solr/gettingstarted/update/extract?literal.id="+str(ID)+"&commit=true&ignoreTikaException=true", data=document.content)
            #can add custom fields/info alongside pdf data with "&literal.<field>=info"
    ID += 1
print(len(doc_key))
print("Done")


