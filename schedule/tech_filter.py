import sys
import os
schedule_path = os.path.dirname(os.path.abspath(__file__))
parent_path = os.path.join(schedule_path, "..")
sys.path.append(parent_path)

from methods.macros import POSTINGS_PATH
import json
from datetime import datetime
from methods.transformations import apply_filters_transformations, select_keywords, filter_out_keywords, filter_on_points

FILE_PATH = f"{POSTINGS_PATH}/tech/newly_added_postings.json"
OUTPUT = f"C:/GitHubRepo/cv-automation/src/cvscripts/generation/"

title_keywords = [
    "data", "research", "python", "software", "developer", "graph", "network", "time",
    "geograph", "engineer", "business", "analytics", "forward deployed", 
]
title_capital_keywords = ["AI", "ML", "LLM", "GIS"]
description_keywords = [
    "graph", "network", "machine learning", "deep learning", "operations research",
    "artificial intelligence", "analytics", "time series", "data mining", "causal", #"visualization",
    "fabric", "duckdb", "knime", "neo4j", "scala", "nosql", "big data", "sparql", "rdf", #"python", "power bi",
    "ontology", "social network", "biotech", "bioinformatics", "healthcare", "biology", 
    "theory", "theoretic", "science", "scientist", "scientific", "algorithm", "algorithms",
    "research", "conference", "publication", "phd", "advanced degree", "msc", "master's", "masters",
    "geospatial", "spatial", "geograph", "sensor", "remote sensing", "radar",
    "lidar", "embedded", "computer vision", "image processing", #"robot",
]
desctiption_capital_keywords = ["AI", "ML", "NLP", "GNN", "R&D", "Master", "GIS"]

filter_out_title_keywords = [
    "java", "angular", "react", "plsql", "oracle", "salesforce",
    "cloudera", "apache flink", "servicenow",
    "sap", "human resources", #"marketing",
    "teamlead", "team lead", "manager", "leiter", #"intern", "internship",
    "test engineer", "cybersecurity engineer", "test automation", "qa engineer",
    "linux engineer", "site reliability", "customer support", "customer service",
]
filter_out_title_capital_keywords = ["UX", "C#", ".NET", "PHP"]

def main(current_postings:dict=None, output_path:str=None):
    if current_postings is None:
        with open(FILE_PATH, 'r', encoding='utf-8') as f:
            current_postings = json.load(f)
    filtered_results = apply_filters_transformations(
        current_postings,
        [
            (select_keywords, {
                'title_keywords': title_keywords,
                'title_capital_keywords': title_capital_keywords,
                'description_keywords': description_keywords,
                'description_capital_keywords': desctiption_capital_keywords
                },),
            (filter_out_keywords, {
                'title_keywords': filter_out_title_keywords,
                'title_capital_keywords': filter_out_title_capital_keywords
                },),
            (filter_on_points, {})
        ]
    )
    #filtered_results = apply_filters(
    #    current_postings,
    #    functions=[select_keywords, filter_out_keywords, filter_on_points],
    #    kwargs_list=[{
    #        'title_keywords': title_keywords,
    #        'title_capital_keywords': title_capital_keywords,
    #        'description_keywords': description_keywords,
    #        'description_capital_keywords': desctiption_capital_keywords
    #    },
    #    {
    #        'title_keywords': filter_out_title_keywords,
    #        'title_capital_keywords': filter_out_title_capital_keywords
    #    },
    #    {}
    #    ]
    #)
    
    add_back = ["karriere.at7670267", "karriere.at7670270"] #TODO think of something
    for key in add_back:
        if key in current_postings:
            filtered_results[key] = current_postings[key]
    
    if output_path:
        if not output_path.endswith('.json'):
            output_path = output_path + '/' if not output_path.endswith('/') else output_path
            output_path = os.path.join(output_path, f'filtered_postings_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(filtered_results, f, indent=4, ensure_ascii=False)
    return filtered_results

if __name__ == "__main__":
    main(output_path=OUTPUT)