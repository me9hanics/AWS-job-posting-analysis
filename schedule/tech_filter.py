import sys
import os
schedule_path = os.path.dirname(os.path.abspath(__file__))
parent_path = os.path.join(schedule_path, "..")
sys.path.append(parent_path)

from methods.macros import POSTINGS_PATH
import json

title_keywords = [
    "data", "research", "python", "software", "developer", "graph", "network", "time",
    "geograph", "engineer", "business", "analytics", "forward deployed", 
]
title_capital_keywords = ["AI", "ML", "LLM", "GIS"]
description_keywords = [
    "graph", "network", "machine learning", "deep learning", "artificial intelligence",
    "analytics", "time series", "data mining", "causal", #"visualization",
    "fabric", "duckdb", "knime", "neo4j", "scala", "nosql", "big data", "sparql", "rdf", #"python", "power bi",
    "ontology", "social network", "biotech", "bioinformatics", "healthcare", "biology", 
    "theory", "theoretic", "science", "scientist", "scientific", "algorithm", "algorithms",
    "research", "conference", "publication", "phd", "advanced degree", "msc",
    "geospatial", "spatial", "geograph", "sensor", "remote sensing", "radar",
    "lidar", "embedded", "computer vision", "image processing", #"robot",
]
desctiption_capital_keywords = ["AI", "ML", "NLP", "GNN", "R&D", "Master", "GIS"]

filter_out_title_keywords = [
    "java", "angular", "react", "plsql", "oracle", "salesforce",
    "cloudera", "apache flink",
    "sap", "human resources", #"marketing",
    "teamlead", "team lead", "manager", "leiter", #"intern", "internship",
    "test engineer", "cybersecurity engineer", "test automation", "qa engineer",
    "linux engineer", "site reliability", "customer support", "customer service",
]
filter_out_title_capital_keywords = ["UX", "C#", ".NET", "PHP"]

FILE_PATH = f"{POSTINGS_PATH}/tech/current_postings.json"
OUTPUT_PATH = f"C:/GitHubRepo/cv-automation/src/cvscripts/generation/filtered_postings.json"

def select_keywords(postings, title_keywords=[], title_capital_keywords=[],
                    description_keywords=[], description_capital_keywords=[]):
    filtered = {}
    for key, value in postings.items():
        title = value.get('title', '').lower()
        description = value.get('description', '').lower()
        if any(term.lower() in title for term in title_keywords) or \
           any(term.lower() in description for term in description_keywords) or \
           any(term in title for term in title_capital_keywords) or \
           any(term in description for term in description_capital_keywords):
            filtered[key] = value
    return filtered

def filter_out_keywords(postings, title_keywords=[], title_capital_keywords=[],
                         description_keywords=[], description_capital_keywords=[]):
    filtered = postings.copy()
    for key, value in postings.items():
        title = value.get('title', '')
        description = value.get('description', '')
        if any(term.lower() in title.lower() for term in title_keywords) or \
           any(term.lower() in description.lower() for term in description_keywords) or \
           any(term in title for term in title_capital_keywords) or \
           any(term in description for term in description_capital_keywords):
            filtered.pop(key, None)
    return filtered

def filter_on_points(postings, min_points=0.01, default_points=0):
    filtered = {key: value for key, value in postings.items() if value.get('points', default_points) >= min_points}
    return filtered

def apply_filters(postings, functions = [], kwargs_list = []):
    filtered = postings
    for func, kwargs in zip(functions, kwargs_list):
        filtered = func(filtered, **kwargs)
    return filtered

def main(current_postings=None, output_path=None):
    if current_postings is None:
        with open(FILE_PATH, 'r', encoding='utf-8') as f:
            current_postings = json.load(f)
    filtered_results = apply_filters(
        current_postings,
        functions=[select_keywords, filter_out_keywords, filter_on_points],
        kwargs_list=[{
            'title_keywords': title_keywords,
            'title_capital_keywords': title_capital_keywords,
            'description_keywords': description_keywords,
            'description_capital_keywords': desctiption_capital_keywords
        },
        {
            'title_keywords': filter_out_title_keywords,
            'title_capital_keywords': filter_out_title_capital_keywords
        },
        {}
        ]
    )
    
    add_back = ["karriere.at7670267", "karriere.at7670270"]
    for key in add_back:
        if key in current_postings:
            filtered_results[key] = current_postings[key]
    
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(filtered_results, f, indent=4, ensure_ascii=False)
    return filtered_results

if __name__ == "__main__":
    main(output_path=OUTPUT_PATH)