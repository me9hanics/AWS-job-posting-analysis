import numpy as np
from bs4 import BeautifulSoup
import time
import json
import requests
from methods import sites

websites = {
    "karriereat": sites.KarriereATScraper(),
}

def __main__():
    postings = {}
    for website, scraper in websites.items():
        try:
            results =scraper.gather_data(descriptions=False)
        except:
            continue
        postings.update(results)
    
    date_today = time.strftime("%Y-%m-%d")
    with open(f"source/save/postings_{date_today}.json", "w") as f:
        json.dump(postings, f)


if __name__ == "__main__":
    __main__()