# AWS-job-posting-analysis: Scraping the karriere.at website for job postings + Using AWS services to extract English key phrases

A project collecting job postings from scraping job postings from websites such as [Karriere.at](karriere.at), extracting information such as description keywords, running AWS Cloud Computing tools to obtain insightful information.

The current implementation only has a pipeline for scraping job postings from karriere.at, but extending it to enterprise websites is planned. The pipeline deals with and makes use of the fact that majority of the postings are written German.

## Description

The project consists of two main parts:

- Data collection: Scraping and processing job postings from the karriere.at website, in specific categories (e.g. Data Science and Vienna). Specifically, we use the job titles and descriptions.
- Key phrases extraction with AWS servives: Using Amazon Comprehend's `detect_key_phrases` and `detect_dominant_language` methods to extract key phrases from the job descriptions.

## Why not LinkedIn / Indeed ?

LinkedIn and Indeed have indicated in their `robots.txt` that they do not allow web scraping of their job postings. If you are not familiar with the concept of `robots.txt`, it's basically a programmatic ruleset provided by the website provider intended for bots that gather information from website, defining which subpages are allowed to be inspected and used for information processing.<br>
(Indeed does not allow `/Jobs` subdirectory to be scraped - meanwhile LinkedIn might [allow scraping to some limits for any user](https://evaboot.com/blog/does-linkedin-allow-scraping#3-linkedin-scraping-limitations), it requires logging in with a real account to view job postings, making it not worth the risk considering their strict policies and [powerful prevention teams](https://www.linkedin.com/blog/engineering/trust-and-safety/using-deep-learning-to-detect-abusive-sequences-of-member-activi).)

We have to suffice to karriere.at, and company websites for now, those do not disallow our bot's data collection.

A reasonable goal in the future is to collect a set of companies hiring in relevant fields, check their website if their `robots.txt` allows scraping, and using the implemented scraping tools to collect job postings from each website. For this reason, much of the code is designed to be modular, instead of hardcoded and specific.

## Data collection

Scraping job postings with descriptions from the karriere.at website is in some retrospect simple, but challenging.<br>
There seems to be no restrictions to even HTTP requests with no authentication, and often, simple web scraping tricks work to gather some information. However, quite often the simple methods might not return desired results, making it beneficial to use more advanced tools - in particular, `Selenium`. Even to job posting subpages a simple request will not return the full HTML, we need to use a headless browser to render the page, and then scrape.

We cannot just open job postings directly, those have IDs that we can find through firstly opening category pages, and gathering the IDs from there. Then, we can open each job posting page and scrape the description.

Based on this, the pipeline consists of two parts, with the following steps:

**Part 1**: Gathering job posting IDs
- Constructing the to-be-scraped URLs from the base URL and categories - this is quite straightforward as the website uses a simple URL structure.
- Opening each URL with `Selenium`,
- Detecting if a cookie popup is present, and closing it
- In a loop, till no more job postings are loaded:
    - Scrolling to the bottom of the page to get to the "load more" button
    - Clicking the "load more" button until no more job postings are loaded
- Scraping the full HTML, containing all job postings in the category
- Processing: Extracting the job posting IDs and titles from the HTML; descriptions are not yet available.

**Part 2**: Gathering job posting descriptions
- For each job posting ID, open the respective URL
- Wait for the page to load, optionally close the cookie popup
- Scrape the full HTML, containing the job posting description
- Processing: Extract the text from the correct HTML elements, strip it from HTML tags
- Save the job postings with ID, title, description (and base url) to a JSON file. 

Here is an image representing various steps of the process:

![Pipeline](https://raw.githubusercontent.com/me9hanics/AWS-job-posting-analysis/refs/heads/main/imgs/process.png)

The CSS selectors for the popup closing (`.onetrust-close-btn-handler`), the "load more" button (`.m-loadMoreJobsButton__button`), and the job posting elements (`div.m-jobsListItem__container div.m-jobsListItem__dataContainer h2.m-jobsListItem__title a.m-jobsListItem__titleLink`) were found via the Edge browser's (Chrome) developer tools, among other things. The URL IDs contain the job posting IDs, which are also stored in this jobs-list-item element, alongside the title (but not the description).

A gist is available [here](https://gist.github.com/me9hanics/65175381063f7fe2e27d6a1dca53e6cb), containing the important methods. The repository containing the full code can be found on [GitHub](https://github.com/me9hanics/AWS-job-posting-analysis) - note that this includes a notebook instead of the `karriereat.py` file.<br>
The most specific / high level methods are in the `karriereat.py` file (see gist), the methods used inside these functions can be found in the [`methods` modules folder](https://github.com/me9hanics/AWS-job-posting-analysis/tree/main/methods).<br>
As said before, the pipeline is designed to be extendable to other websites with desirably low effort, hence options in the methods such as pre-load and post-load waiting times, keeping or closing driver instances, and so on.

After running the pipeline and saving the job postings with descriptions to a JSON file, we can proceed to the key phrase extraction process. Here are some statistics, that we will later rely on for the extraction, and the cost calculations:

```
Number of postings: 462
Total number of characters in descriptions: 1783171
Average number of characters per description (excluding 0-length descriptions): 3876.46
Total number of words: 226275
Average number of words (excluding 0-length descriptions): 491.90
```

Not all of the postings will be used for our analysis, and different languages need to be handled differently. These are steps for the key phrase extraction process.

## Key phrases extraction

We would like to extract terms that are appear more frequently in these job descriptions than expected by chance (analogous to the idea of TF-IDF), and are relevant for our job search - we are interested in key phrases that frequently appear in the job postings that are relevant to us.

On the simplest level, this can be achieved by at least two separate methods: locally using a library such as `spaCy`, or using a cloud service provider's strong service, such as Amazon Comprehend. It's worthy to look at the difference between the results of these two methods.

### Comparison of Amazon Comprehend and spaCy

Let's take the following example job description:

```
description = "One bank.  Many career paths. #makeITmatter Conversational AI Specialist\
        (all humans)Location: Vienna, Wien, AustriaWorking-Hours: fulltime_permanentDivision: Data2BusinessCompany: Erste Digital \
        Apply now We are part of Erste Group - the largest banking group in Central and Eastern Europe with more than 2,500 \
        branches and over 45,000 employees. More than 2,000 IT experts and enthusiasts are the bank's Digital Muscle. \
        What to do:Develop and implement conversational AI (e.g. AI models to analyze and interpret audio data from call centers). \
        Collaborate with cross-functional teams to integrate AI solutions into our customer service operations. Continuously monitor \
        and improve the performance of AI models. Stay up-to-date with the latest advancements in AI and NLP technologies. Provide \
        technical expertise and guidance to team members and stakeholders. Utilize agentic AI use case skills to enhance the functionality \
        and effectiveness of AI solutions. You check these boxes:Bachelor's or Master's degree in Computer Science, Data Science, AI, or a \
        related field. Proven experience in developing and deploying AI models ..."
```

With a simple use of Amazon Comprehend (`response = comprehend.detect_key_phrases(Text=description, LanguageCode="en")`), we gather the following key phrases, with their respective confidence levels (frequency can also be gathered):

```
Amazon Comprehend:

- One bank: 99.42% confidence
- Many career paths: 86.96% confidence
- AI: 51.70% confidence
- all humans: 93.39% confidence
- Location: 97.99% confidence
- Vienna, Wien, AustriaWorking: 97.95% confidence
- Hours: 63.07% confidence
- fulltime_permanentDivision: 67.19% confidence
- Data2BusinessCompany: 96.18% confidence
- Erste Digital         Apply: 85.47% confidence
- part: 99.95% confidence
- Erste Group: 99.93% confidence
- the largest banking group: 99.91% confidence
- Central and Eastern Europe: 98.66% confidence
- more than 2,500         branches: 99.98% confidence
- over 45,000 employees: 85.32% confidence
- More than 2,000 IT experts and enthusiasts: 98.18% confidence
- the bank: 99.99% confidence
- Digital Muscle: 99.81% confidence
- conversational AI: 94.48% confidence
- e.g. AI models: 96.60% confidence
- audio data: 99.92% confidence
- call centers: 99.89% confidence
...

```

```
spaCy:


'AI': 10,
'models': 3,
'bank': 2,
'Erste': 2,
'Digital': 2,
'solutions': 2,
'Science': 2,
'career': 1,
'paths': 1,
'makeITmatter': 1,
'Conversational': 1,
'Specialist': 1,
'humans)Location': 1,
'Vienna': 1,
'Wien': 1,
'AustriaWorking': 1,
'Hours': 1,
'fulltime_permanentDivision': 1,
'Data2BusinessCompany': 1,
...
```

While many of the job descriptions are in German, the keywords that we really care about are in English - this may come as a useful filter

44.1 seconds for 462 job postings

## Analysis of key phrases gathered with Amazon Comprehend

Code:

```python

# %%
import json
import pprint
from collections import Counter

import boto3
import matplotlib.pyplot as plt
import nltk

nltk.download("stopwords")
from nltk.corpus import stopwords

pp = pprint.PrettyPrinter(indent=2)
comprehend = boto3.client(service_name="comprehend", region_name="eu-west-1")

# %%
# Load job descriptions

with open("source/save/postings_2024-12-17.json", "r") as f:
    postings = json.load(f)

# 462 job postings
banned_words = [
    "manager",
    "management",
    "professor",
    "team leader",
    "teamleader",
    "teamleiter",
    "team leiter",
    "internship",
    "jurist",
    "lawyer",
    "auditor",
]
postings_filtered = {
    key: value
    for key, value in postings.items()
    if not any(banned_word in value["title"].lower() for banned_word in banned_words)
}  # 352 job postings, 25% less!
descriptions = [posting["description"] for posting in postings_filtered.values() if posting["description"]]

# %%
# Key phrases detection

# While many of the job descriptions are in German, the keywords that we really care about are in English - this may come as a useful filter
keywords = []

for description in descriptions:
    # Detect language first, to then input for key phrases detection
    short_description = description[:299]  # 3 units
    response = comprehend.detect_dominant_language(Text=short_description)
    lang = response["Languages"][0]["LanguageCode"]  # main language
    response = comprehend.detect_key_phrases(Text=description, LanguageCode=lang)
    key_words = [phrase["Text"] for phrase in response["KeyPhrases"]]
    keywords.extend(key_words)


# %%
# Selection of promising keyphrases

stopwords_english = set(stopwords.words("english"))
stopwords_german = set(stopwords.words("german"))
stopwords_all = stopwords_english.union(stopwords_german)
stopwords_lowercase = set(word.lower() for word in stopwords_all)
keywords_filtered = [kw for kw in keywords if kw.lower() not in stopwords_lowercase]
keyphrases = [keyword for keyword in keywords if len(keyword.split()) > 1]
keyphrases_filtered = [kw for kw in keyphrases if not any(word.lower() in stopwords_lowercase for word in kw.split())]

keyword_counts = Counter(keywords_filtered)
keyphrase_counts = Counter(keyphrases_filtered)

# Only keep keywords and phrases with count > 1
keywords_filtered = [kw for kw in keywords_filtered if keyword_counts[kw] > 1]
keyphrases_filtered = [kw for kw in keyphrases_filtered if keyphrase_counts[kw] > 1]

# %%
# Plotting


def plot_top_keywords_keyphrases(keyword_counts, keyphrase_counts, columns=15, title=None):
    top_keywords = keyword_counts.most_common(columns)
    top_keyphrases = keyphrase_counts.most_common(columns)
    keyword_labels, keyword_frequencies = zip(*top_keywords)
    keyphrase_labels, keyphrase_frequencies = zip(*top_keyphrases)

    fig, ax = plt.subplots(2, 1, figsize=(14, 10))

    if title:
        fig.suptitle(title, fontsize=16, y=0.95)

    ax[0].bar(keyword_labels, keyword_frequencies, color="blue")
    ax[0].set_title("Most common keywords", fontsize=14)
    ax[0].set_ylabel("Frequency")
    ax[0].tick_params(axis="x", rotation=45)

    ax[1].bar(keyphrase_labels, keyphrase_frequencies, color="green")
    ax[1].set_title("Most common keyphrases", fontsize=14)
    ax[1].set_ylabel("Frequency")
    ax[1].tick_params(axis="x", rotation=45)

    fig.tight_layout(rect=[0, 0, 1, 0.95])
    plt.show()


title = "Most common keywords and keyphrases (352 job descriptions) - corrected for stopwords"
plot_top_keywords_keyphrases(keyword_counts, keyphrase_counts, title=title)


# %%
from langdetect import LangDetectException, detect


def is_not_german(text):
    try:
        if len(text) > 2:  # Skip short texts
            return detect(text) != "de"
    except LangDetectException:
        pass
    return False


keywords_nongerman = [keyword for keyword in keywords_filtered if is_not_german(keyword)]
keyphrases_nongerman = [keyphrase for keyphrase in keyphrases_filtered if is_not_german(keyphrase)]


# %%
# Plotting

keyword_counts_nongerman = Counter(keywords_nongerman)
keyphrase_counts_nongerman = Counter(keyphrases_nongerman)

title = "Most common keywords and keyphrases (352 job descriptions) - corrected for stopwords, filter German keywords"

plot_top_keywords_keyphrases(keyword_counts_nongerman, keyphrase_counts_nongerman, title=title)
# %%
```

If we first try to just list the keywords, and key phrases (phrases with more than one word) that appear in the job descriptions, the most frequent key phrases list includes too many German terms. If we filter out stopwords, we get better results:

![Most common keywords and keyphrases (352 job descriptions) - corrected for stopwords](https://raw.githubusercontent.com/me9hanics/AWS-job-posting-analysis/refs/heads/main/imgs/keyphrases.png)

However, this is still far from desirable. We can filter out key phrases that appear to be in German - to save costs, we can use the `langdetect` library to detect the language of the key phrases, and only keep the English ones. This is a simple, but slow method.

After filtering out German key phrases:

![Most common keywords and keyphrases (352 job descriptions) - corrected for stopwords, filter German keywords](https://raw.githubusercontent.com/me9hanics/AWS-job-posting-analysis/refs/heads/main/imgs/keyphrases_nongerman.png)

## Costs

NLP requests are measured in units of 100 characters, with a 3 unit (300 character) minimum charge per request
Key Phrase Extraction	$0.0001 per unit (for small scale)

3 units * 352 job postings * $0.0001/unit ~ 0.1 USD
On average, 3900 characters - 39 units * 352 job postings * $0.0001/unit ~ 1.37 USD


Initial, small scale attempts cost ~
1213 characters, 160 words - 13 units

One time run on the full dataset:
39 units * 462 job postings * $0.0001/unit ~ 1.80 USD
Two previous runs on the filtered dataset:
2 * 39 units * 352 job postings * $0.0001/unit ~ 2.74 USD

Overall costs: 0.1 + 1.37 + 1.80 + 2.74 ~ 6.01 USD
