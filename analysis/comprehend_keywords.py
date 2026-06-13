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

with open(f"{RELATIVE_POSTINGS_PATH}_2024-12-17.json", "r") as f:
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
