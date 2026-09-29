import numpy as np
import time
import json
import requests
from jobscraping.config.configs import RELATIVE_POSTINGS_PATH
from jobscraping.scrapers import sites

websites = {
    "karriereat": sites.KarriereAT(),
}

def __main__():
    #TODO - fix (i.e. update)
    postings = {}
    for website, scraper in websites.items():
        try:
            results =scraper.gather_data(descriptions=False)
        except:
            continue
        postings.update(results)
    
    date_today = time.strftime("%Y-%m-%d")
    with open(f"{RELATIVE_POSTINGS_PATH}_{date_today}.json", "w") as f:
        json.dump(postings, f)


if __name__ == "__main__":
    __main__()
