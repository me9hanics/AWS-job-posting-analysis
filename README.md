# AWS-job-posting-analysis
A project collecting job postings from scraping job postings from websites such as [Karriere.at](karriere.at), extracting information such as description keywords, running AWS Cloud Computing tools to obtain insightful information.

The current implementation only has a pipeline for scraping job postings from karriere.at, but extending it to enterprise websites is planned.

## Why not LinkedIn / Indeed ?

LinkedIn and Indeed have indicated in their robots.txt that they do not allow web scraping of their job postings.<br>
(Indeed does not allow `/Jobs` subdirectory to be scraped - meanwhile LinkedIn might [allow scraping to some limits for any user](https://evaboot.com/blog/does-linkedin-allow-scraping#3-linkedin-scraping-limitations), it requires logging in with a real account to view job postings, making it not worth the risk considering their strict policies and [powerful prevention teams](https://www.linkedin.com/blog/engineering/trust-and-safety/using-deep-learning-to-detect-abusive-sequences-of-member-activi).)

We have to suffice to karriere.at, and company websites for now, their robots.txt files do not disallow our "bot".

A reasonable goal in the future is to collect a set of companies hiring in relevant fields, check their website if their `robots.txt` allows scraping, and using the implemented scraping tools to collect job postings from each website.