#pquery.py
#Project Solr Query Program
#by Daniel H

#Imports
from collections import defaultdict
import requests
import json



#Loads data that query functions require so at to not require setup be run alongside it
with open("doc_key.txt", "r") as file:
    doc_key = json.loads(file.read(), object_hook=lambda d: {int(k): v for k, v in d.items()})
with open("aff_key.txt", "r") as file:
    aff_key = json.loads(file.read(), object_hook=lambda d: {int(k): v for k, v in d.items()})



#Loads author count data that query functions require so as to not require setup be run alongside it to perform author count relevancy alterations
with open("auth_key.txt", "r") as file:
    auth_key = json.loads(file.read(), object_hook=lambda d: {int(k): v for k, v in d.items()})



#Solr query that returns relevancy scores for relevant documents
def solr(query, params):
    #Query request
    q_response = requests.get("http://localhost:8983/solr/gettingstarted/select", params=params)
    
    #Extracts document ID and relevancy score for each document in response
    scores_auth = dict()
    for i in range(len(q_response.json()["response"]["docs"])):
        ID = q_response.json()["response"]["docs"][i]["id"]
        score = q_response.json()["response"]["docs"][i]["score"]
        #Stores the relevancy score and the IDs of the affiliates who authored the document alongside the document's ID
        #scores[ID] = [score, doc_key[int(ID)][1]]
        scores_auth[ID] = [score/auth_key[int(ID)], doc_key[int(ID)][1]] #author count
    
    #print(json.dumps(q_response.json(), sort_keys=True, indent=4))
    #print(q_response.json()["debug"]["explain"]["ID"]) #replace "ID" with an ID of a document in the q_response that you wish to analyze.
        #tf stands for term frequency:
            #the more times a search term appears in a document, the higher the score
        #idf stands for inverse document frequency:
            #matches on rarer terms count more than matches on common terms

    return scores_auth



#Calculates affiliate expertise scores from the document relevancy scores and ranks them
def aff_scores(scores):
    aff_dict = defaultdict(list)
    rank = 0
    #Stores the relevant document ranks and relevancy scores for each affiliate
    for score, affs in scores.values():
        for aff in affs:
            aff_dict[aff].append([rank, score])
        rank += 1
    #Expertise evaluation equation from "Design and Evaluation of a University-wide Expert Search Engine" by Ruud Liebregts and Toine Bogers
    aff_exp = {aff:sum([score + (2/(rank+1)) for rank, score in values]) for aff, values in aff_dict.copy().items()}
    aff_exp = dict(sorted(aff_exp.items(), key=lambda item: item[1], reverse=True))
    
    return aff_exp



#Utilizes the above solr and aff_scores functions to print a ranked list of the top 10 most relevant affiliates for the user's query
def user_query(query):
    query = query.replace("(", "\"").replace(")", "\"")
    
    #Parameters that Solr utilizes to calculate relevancy of documents to a query
    params = {
        "defType": "dismax",  #query parser meant for simple user input
        "q": query,  #query input
        "qf": "content",  #query field(s)
        "pf": "content^5.0",  #exact full query phrase + weight
        "ps": "10",  #allows for ^pf to include up to n words between pieces of the query phrase
        "fl": "id,score",  #ensures document id and score is visible
        "rows": "50",  #top n relevant documents
        #"debugQuery": "on",  #debugger to view score calculations (see commented print lines in solr function above)
    }
    
    #Results from the solr and aff_scores functions
    results = aff_scores(solr(query, params))
    
    #Prints top 10 affiliates
    i = 0
    for aff in list(results.keys())[:10]:
        i += 1
        print(str(i)+":", " ".join(aff_key[aff]))
        #print(list(results.values())[i-1])  #calculated relevancy score
    
    return results



#Provides query input functionality
query = input("Query: ")
user_query(query)
#Encapsulating a set of words in parantheses ensures they're only searched for as a single term and not individually. 
#E.g. "Recurrent (Neural Networks)" will search for "Recurrent", "Neural Networks", 
#and "Recurrent Neural Networks"; but not individual uses of "Neural" or "Networks".


