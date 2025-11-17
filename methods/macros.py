REPO_ROOT_PATH = "C:/GitHubRepo/AWS-job-posting-analysis"
SAVING_PATH = f"{REPO_ROOT_PATH}/data/save"
RELATIVE_SAVING_PATH = "data/save"
POSTINGS_PATH = f"{SAVING_PATH}/postings"
RELATIVE_POSTINGS_PATH = f"{RELATIVE_SAVING_PATH}/postings"
EXCELS_PATH=f"{SAVING_PATH}/excels"
RELATIVE_EXCELS_PATH = f"{RELATIVE_SAVING_PATH}/excels"
COMPANIES_PATH = f"{SAVING_PATH}/companies"
RELATIVE_COMPANIES_PATH = f"{RELATIVE_SAVING_PATH}/companies"

SALARY_BEARABLE = 3400

BASE_RULES = {"website":"karriere.at",
              "scraping_base_url": "https://www.karriere.at/jobs",
              "close_website_popup":False,
              "usecase":'http',
              "load_page_button_selector":".onetrust-close-btn-handler",
              "load_page_press_button_until_gone_selector":".m-loadMoreJobsButton__button",
              "gather_data_selector":'div.m-jobsListItem__container div.m-jobsListItem__dataContainer h2.m-jobsListItem__title a.m-jobsListItem__titleLink',
              "request_wait_time":0.15,
              "title_path":None,
              "company_path":None,
              "salary_path":None,
              }
BASE_KEYWORDS = {
    "locations" : ["vienna"],
    "titlewords": ["machine learning", "machine learning engineer", "machine learning scientist",
                   "ML engineer", "ML researcher", "ML developer", "AI ML",
                   "AI engineer", "AI scientist", "AI researcher", "AI developer",
                   "data science", "data scientist", "data mining", "web scraping",
                   "data engineer", "data engineering", "data engineering developer",
                   "data analysis", "data analytics", "data analyst",  "NLP engineer", "time series",
                   "business intelligence", "business analyst", #"bi analyst", "business intelligence analyst",
                   "graph theory", "network science", "graph database", "operation research",
                   "complexity science", "statistician", "scientist", "mathematician", #"network science", "combinatorics",
                   "life science", "computational biology", "bioinformatics", "bioengineer", "biotech",
                   "Python engineer", "DataOps", "full stack data scientist",
                   "forward deployed engineer",
                   "software engineer", "software developer", #"full stack developer",
                  ],
    "banned_words": ["manager", "team leader", "teamleader", "teamleiter", "team leiter", "geschäft",
                    "jurist", "lawyer", "rechsanwalt", "legal", "audit", "advisor", "owner", "officer", "controller",
                    "head of", "director", "leitung", "secretary", "recruit", "professur", #"professor", 
                    "ärtzin",
                    "m365", "azure", "cyber security", #"microsoft"
                    "praktikum", "praktikant", #"internship", "intern", "trainee",
                    ],
    "banned_capital_words": ["SAP", "HR"],
    "highlighted_company_titles": ["graph", "science", "research", "engineer", "data", "algo", "math",
                                   "optimization", "complexity", "analytics", "analysis", "conference",
                                   "lab", "center", "institute", "university",
                                   "aithyra", "amazon", "google", "meta", "microsoft", "nvidia", "ibm",
                                   ],
}
BASE_KEYWORDS["titlewords_dashed"] = [word.replace(" ", "-") for word in BASE_KEYWORDS["titlewords"]]

BASE_RANKINGS ={
    "ranking_lowercase":{
                #TODO organize them into categories (nested dict) - category to be used in figuring out the type of job e.g. research
                #TODO refactor and put into separate file - have e.g. translations/synonyms/etc. for each keyword in its own dict. Basically groups of connected keywords
                #general and science terms
                "math":1, "data":0.35, "combinatori":0.8, "statistic":0.25, "neural":0.1, "information":0.1, "algorithm":1.2,
                "complexity science":3, "complexity":0.3, "theory":0.3, "research": 0.7, "scientific":0.4, "physics":0.4,
                "operations research":1.5, "optimization":1, "numerical":0.1, "modelling":0.5, "modeling":0.5, "probability":0.2,
                "complex systems":1.2, "simulation":0.3, "quantitative":0.3, "scale":0.2, 
                #titles
                "engineer": 0.45, "developer": 0.4, "scientist": 1, "researcher": 0.9, "analyst": 0.1, "r&d":0.4,
                #rank
                "senior": 0.1,
                #graphs/networks/geo (extra high points as most terms are part of the description, never in title)
                "graph":2, "network science":3, "graph theory":2.6, "graph data":2.5, "graph database":1.6,
                "graph machine learning": 1.8, "graph deep learning": 1.6, "gnn":1.2, "graph neural network":1.4,
                "social network":0.5, "geospatial":1.4, "spatial":0.7, "maps":0.4, "geometry":0.4, "geodata": 0.8,
                #life sciences tech
                "aithyra":1.8, "bioinformatic": 1.1, "biotech":0.5, "bioengineer":0.8,
                "health":0.2, "healthcare":0.2, "biology":0.3, "biological":0.4, "chemistry":0.1,
                "network biology":1.8, "network medicine":2.1, "cell":0.2, "molecular":0.3, "protein":0.3, "brain":0.8,
                "patient":0.1, "genetics":0.4, "pharma":0.2, "clinical":0.1,
                #machine learning
                "machine learning":0.9, "neural network":0.6, "deep learning":0.5, "reinforcement learning":0.4,
                "image processing":0.2, "pattern recognition":0.3, "computer vision":0.1, "machine learning engineer":1,
                #specialized data science
                "data mining":1.1, "data collection":0.8, "data analysis":0.4, "predictive":0.5, "estimation":0.4,
                "analytics":0.8, "time series":1.1, "nlp": 0.4, "forecasting":0.6, "weather forecast":0.7,
                "causal":0.7, "inference": 0.7,                
                #data visualization, dashboards, reporting
                "power bi": 0.3, "qlik":0.3, "visualization":0.15, "dashboard":0.1, "d3":0.2, "matplotlib":0.3,
                #databases and data storage
                "neo4j":1.3, "postgres":0.3, "mysql":0.2, "duckdb":0.5, "fabric":0.4, "vector":0.1,
                #other data science terms
                "data science":1.2, "data scientist":1.3, "data management":0.5, "full stack":0.4, "full-stack":0.4,
                "data engineering": 0.7, "data engineer": 0.5, "big data":0.3, "data warehous":0.2,#e/ing
                "scraping":0.9, "pipeline":0.1, "data modeling": 0.4, "data modelling": 0.4, "design":0.15,
                #tech stack
                "python":1, "sql":0.5, "c++":0.2, 
                "knime":0.8,  "docker":0.35, "jinja":0.2, "git": 0.1, "github":0.2,
                #IT
                "forward deployed":1.0, "platform engineer":0.3,
                #engineering
                "lidar": 0.7, "radar": 0.7, "vision":0.2, "sensor": 0.6, "robot":0.6, "embedded":0.5, "electrical":0.25,
                "electric":0.2, "electro":0.3, "microcontroller":0.3, "hardware":0.15,"digital":0.1, "compression":0.1, 
                "spectral":0.15, "media":0.1, "signal":0.35, "audio":0.2, "video":0.2, "wireless":0.15, "telecom":0.1,
                "circuit":0.25, "energy":0.2, "power":0.1, "semiconductor":0.15, "fpga":0.1, "verilog":0.1, "smart":0.2,
                #details
                "conference":0.9, "home office":0.15, "open source":0.45, "relocation":0.2,
                #languages
                "hungarian":1.9, "hungary":0.7, "english":0.3,
                #other
                "deepmind":0.6, "master":0.6, "msc":0.7, "phd":1.1, "advanced degree":1.0, #"bachelor":0.1, "bsc":0.1,
                ####Negative rankings
                #type of work
                "consultant":-0.7, "consulting":-0.7, "audit":-1, "risk":-0.4, "control":-0.4, "holding":-1,
                "purchasing":-1, "accounting": -1, "accountant": -1, "marketing": -1, "sales": -1, "thesis":-0.5,
                "technik":-0.5, "dissertation": -0.5,
                #field
                "financ":-0.3, "finanz":-0.3, "bank":-0.3, "banking":-0.1, "insurance":-0.5, "steuer":-0.7, 
                #rank
                "leiter":-1.5, "leader":-0.5, "lead": -0.5, "manager":-1, "management":-0.7, "owner":-1, "officer":-0.8,
                "head":-0.7, "architect":-0.3, "student":-0.5, "support":-0.3,
                #tech
                "cyber":-0.1, "security":-0.4, "devops":-0.1, "java":-0.2, "test":-0.3,
                "stack developer":-0.6, "linux":-0.3, "safety":-0.4, "quality":-0.2,
                #work related keywords
                "product": -0.2, "agile":-0.3, "requirement":-0.3,
                "merger": -0.6, "acquisition": -0.6, "real estate": -1, "assurance": -0.3,
                #languages
                "deutsch": -0.2,
                #other
                "microsoft": -0.4,
                },
    "ranking_case_sensitive":{"ETL":0.9, "ELT":0.5, "AI":0.5, "ML":0.7, "API":0.4, "REST":0.15,
                           "CI/CD":0.2, "CI CD":0.2, "AWS":0.2, "GIS": 0.1,
                           #Negative rankings
                           "SAP":-0.7, "HR":-0.7, "SAS":-0.5, "SEO": -0.3,
                           },
    "neutral":[
        #rank
        "lead", "junior",
        #data
        "daten", "llm",
        #data software
        "cloudpak", "django", "scala", "spark", "hadoop", "kafka", "airflow", "apache",
        #web
        "html", "javascript", "react", "angular", "node", "flask",
        #IT
        "cloud", "workflow", #"ci/cd", "ci cd",
        #IT software
        "kubernetes", "jenkins", "terraform", "azure", "gcp", "gitlab", "bitbucket", "sonarqube",
        "excel", "powerpoint", 
        #other
        "b2c", "b2b", "lean", "data-driven", "data driven", "kpi", "customer service", "communication",
        "stakeholder", "scrum",
    ]
}

COMPLEXSCI_KEYWORDS = ["complexity science", "complex systems", "complex system", "complex network", "complex networks"]
GRAPH_KEYWORDS = ["graph data", "graph theory", "graph", "neo4j", "operations research", "social network",
                  "knowledge graph", "gnn", "graph neural network", "graph machine learning"]
SEMANTIC_WEB_KEYWORDS = ["sparql", "semantic web", "rdf", "owl", "linked data", "ontology"]
GEOSPATIAL_KEYWORDS = ["geospatial", "spatial", "geographic", "geographical", "gis"]
BIOTECH_KEYWORDS = ["network medicine", "network biology", "biotech", "bioinformatic", "bioinformatics",
                    "computational biology"]
RELEVANT_TECH_KEYWORDS = ["fabric", "duckdb", "vector", "knime"]
TITLE_KEYWORDS = ["full stack", "full-stack", "forward deployed", "platform engineer"]
SCIENCE_KEYWORDS = ["research", "theory", "theoretical", "scientific", "algorithm", "data", "science", "math", "causal",
                    "inference", "causal inference", "conference", "phd", "master", "msc", "advanced degree"]
DATA_SCIENCE_KEYWORDS = ["data science", "data mining", "time series", "natural language processing", "nlp", 
                          "analytics", "web scraping", "scraping", "scrape"]
MACHINE_LEARNING_KEYWORDS = ["machine learning", "deep learning", "neural network", "reinforcement learning",
                             "computer vision", "image processing", "pattern recognition", "opencv", "audio",
                             "artificial intelligence", "ai"]
ENGINEERING_KEYWORDS = ["sensor", "radar", "lidar", "robotics", "robot", "embedded", "c++"]
MAIN_DESCRIPTION_KEYWORDS = (COMPLEXSCI_KEYWORDS + GRAPH_KEYWORDS + SEMANTIC_WEB_KEYWORDS +
                             GEOSPATIAL_KEYWORDS + BIOTECH_KEYWORDS + RELEVANT_TECH_KEYWORDS +
                             TITLE_KEYWORDS + SCIENCE_KEYWORDS + DATA_SCIENCE_KEYWORDS +
                             MACHINE_LEARNING_KEYWORDS + ENGINEERING_KEYWORDS)