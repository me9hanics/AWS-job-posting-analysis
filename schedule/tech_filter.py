import sys
import os
schedule_path = os.path.dirname(os.path.abspath(__file__))
parent_path = os.path.join(schedule_path, "..")
sys.path.append(parent_path)

from methods.configs import POSTINGS_PATH
import json
from datetime import datetime, timedelta
from methods.transformations import (apply_filters_transformations, select_keywords, filter_out_keywords,
                                     filter_on_points, filter_on_date)

NEWLY_ADDED_FILE_PATH = f"{POSTINGS_PATH}/tech/newly_added_postings.json"
CURRENT_FILE_PATH = f"{POSTINGS_PATH}/tech/current_postings.json"
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

filter_out_description_keywords = [r"sehr\s+gut(e)?\s+deutsch", r"fluency\s+in\s+german", r"fluent\s+in\s+german",
                                   r"deutschkenntnisse verhandlungssicher",
                                   r"(fliessend(e)?|verhandlungssicher(e)?|fundiert(e)?)\s+und\s+deutsch",
                                   r"(fliessend(e)?|verhandlungssicher(e)?|fundiert(e)?)\s+englisch(-)?\s+und\s+deutsch"
                                   ]

def add_back_postings(postings:dict, additions:dict, keys:list=[]):
    if not keys:
        keys = additions.keys()
    for key in keys:
        if key in additions:
            postings[key] = additions[key]
    return postings

def main(postings:dict=None, output_path:str=None, min_date:datetime=None,
         input_path:str=NEWLY_ADDED_FILE_PATH):
    if postings is None:
        with open(input_path, 'r', encoding='utf-8') as f:
            postings = json.load(f)
    filtered_results = apply_filters_transformations(
        postings,
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
            (filter_out_keywords, {
                'description_keywords': filter_out_description_keywords
                },),
            (filter_on_points, {}),
            (filter_on_date, {'min_date': min_date} ),
        ]
    )
    #filtered_results = add_back_postings(filtered_results, postings, ["karriere.at7670267", "karriere.at7670270"])
    
    if output_path:
        if not output_path.endswith('.json'):
            output_path = output_path + '/' if not output_path.endswith('/') else output_path
            output_path = os.path.join(output_path, f'filtered_postings_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(filtered_results, f, indent=4, ensure_ascii=False)
    return filtered_results

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Filter tech job postings')
    parser.add_argument('--current', '-c', nargs='?', const=21, type=int, metavar='DAYS',
                       help='Use current postings instead of newly added, and filter to last N days (default: 21)')
    args = parser.parse_args()
    
    input_path = NEWLY_ADDED_FILE_PATH
    min_date = None
    
    if args.current is not None:
        input_path = CURRENT_FILE_PATH
        days = args.current
        min_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        print(f"Using all active postings and filtering to last {days} days")
    
    main(output_path=OUTPUT, input_path=input_path, min_date=min_date)