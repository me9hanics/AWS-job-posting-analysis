"""
Runtime configuration for AWS Job Posting Analysis.

This module contains environment-specific and tunable configuration parameters.
These values typically change based on deployment environment, user preferences,
or periodic tuning and should be modified separately from core code logic.

Configs include:
- File paths and URLs
- Thresholds and weights (scoring parameters)
- User preferences (locations, job preferences)
- Website-specific scraping rules
"""

import re
# ============================================================================
# FILE PATHS AND DIRECTORIES
# ============================================================================
# These are environment-specific paths that may change per deployment

REPO_ROOT_PATH = "C:/GitHubRepo/AWS-job-posting-analysis"
SAVING_PATH = f"{REPO_ROOT_PATH}/data/save"
RELATIVE_SAVING_PATH = "data/save"
POSTINGS_PATH = f"{SAVING_PATH}/postings"
RELATIVE_POSTINGS_PATH = f"{RELATIVE_SAVING_PATH}/postings"
EXCELS_PATH = f"{SAVING_PATH}/excels"
RELATIVE_EXCELS_PATH = f"{RELATIVE_SAVING_PATH}/excels"
COMPANIES_PATH = f"{SAVING_PATH}/companies"
RELATIVE_COMPANIES_PATH = f"{RELATIVE_SAVING_PATH}/companies"

# ============================================================================
# USER PREFERENCES, POINTS, THRESHOLDS
# ============================================================================
# These are adjustable preferences and thresholds

SALARY_BEARABLE = 3400 

LOCATIONS_DESIRED = ["vienna", "wien", "österreich", "austria", "remote"]
LOCATIONS_SECONDARY = ["st. pölten", "sankt pölten", "wiener neudorf", "linz", "krems", "nussdorf",
                       "klosterneuburg", "schwechat", "brunn am gebirge", "graz"]

COMPLEXSCI_KEYWORDS = ["complexity science", "complexity systems", "complexity system", "complex network", "complex networks"]
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

BASE_PHRASES = {
    "locations" : ["vienna"],
    "titlewords": ["machine learning", "machine learning engineer", "machine learning scientist",
                   "ML engineer", "ML researcher", "ML developer", "AI ML", "research engineer",
                   "AI engineer", "AI scientist", "AI researcher", "AI developer",
                   "data science", "data scientist", "data mining", "web scraping",
                   "data engineer", "data engineering", "data engineering developer",
                   "data analysis", "data analytics", "data analyst",  "NLP engineer", "time series",
                   "business intelligence", "business analyst", #"bi analyst", "business intelligence analyst",
                   "graph theory", "graph database", "operation research", "knowledge graph",
                   "complexity science", "statistician", "scientist", "mathematician", #"network science", "combinatorics",
                   "life science", "computational biology", "bioinformatics", "bioengineer", "biotech",
                   "molecular biology", "chemistry informatics", 
                   "energy systems", "power grid",
                   "Python engineer", "DataOps", "full stack data scientist", "forward deployed engineer",
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
    "description_keywords_order": [
        "complexity science", "network science", "graph theory", "network medicine", "graph data",
        "aithyra", "hungarian", "network biology", "graph machine learning", "graph deep learning",
        "graph neural network", "operations research", "gnn", "geospatial", "neo4j", "graph database",
        "knowledge graph", "bioinformatic", "time series", "complex systems", "graph",
        "claude code", "claude", "spec-driven", "codex", "copilot",
        "biology", "nlp", "data mining", "phd", "advanced degree", "algorithm",
        "marketing", "sales", "audit", "manager", "owner", "consultant", "consulting", "officer",
        "head", "management", "machine learning engineer", "forward deployed", "python",
        "ETL", "ML", "AI", "sparql", "conference", "researcher", "scraping", "geodata",
        "combinatori", "optimization", "knime", "data collection", "analytics", "bioengineer",
        "causal", "inference", "lidar", "radar", "HR", "research", "weather forecast", "forecasting",
        "robot", "sensor", "ai agents", "neural network", "semantic web", "spatial", "duckdb",
        "master", "msc", "deepmind", "R&D", "embedding", "modeling", "modelling",
        "predictive", "biotech", "ELT", "thesis", "dissertation", "technik", "student",
        "lead", "leader", "deep learning", "insurance", "open source",
        "full stack", "full-stack", "fabric", "r&d", "security", "data management",
        "data modeling", "data modelling", "knowledge management", "API", "reinforcement learning",
        "scientific", "physics", "maps", "geometry", "social network", "risk", "control",
        "safety", "machine learning", "genetics", "data analysis", "estimation", "full stack data scientist",
        "docker", "electro", "signal", "platform engineer", "complexity", "theory", "power bi",
        "qlik", "pattern recognition", "ontology", "molecules", "simulation", "quantitative", "cell",
        "molecular", "protein", "postgres", "microcontroller", "big data", "postgres", "mysql",
        "LLM", "electrical", "statistic", "circuit", "ci cd", "ci/cd", "energy", "relocation",
        "vision", "electric", "home office", "chemistry", "health", "healthcare",
        "jinja", "github", "c++", "d3", "AWS", "probability", "clinical", "patient", "pharma",
        "scale", "image processing", "data warehous", "wireless", "spectral", "semiconductor",
        "design", "visualization", "hardware", "video", "audio", "smart", "senior", "telecom",
        "digital", "compression", "fpga", "verilog", "power", "media", "computer vision", "rdf",
        "owl", "vector", "neural", "information", "pipeline", "dashboard", "GIS", "analyst",
        "banking", "deutsch", "java", "product", "quality", "agile", "requirement", "assurance",
        "SEO", "devops", "cyber", "test", "mcp", "english",
        "lead", "junior", "daten", "llm", "cloudpak", "django", "scala",
        "spark", "hadoop", "kafka", "airflow", "apache", "html", "javascript", "react", "angular",
        "node", "flask", "cloud", "workflow", "kubernetes", "jenkins", "terraform", "azure", "gcp",
        "gitlab", "bitbucket", "sonarqube", "excel", "powerpoint", "b2c", "b2b", "lean",
        "data-driven", "data driven", "kpi", "customer service", "communication", "stakeholder", "scrum",
        "real estate", "holding", "purchasing", "accounting", "accountant",
        "data scientist", "data science", "data engineering", "data engineer", "scientist", "engineer", "developer",
        "stack developer", "data",
    ]
}
BASE_PHRASES["titlewords_dashed"] = [word.replace(" ", "-") for word in BASE_PHRASES["titlewords"]]

BASE_KEYWORD_SCORING = {
    "complexity_networks": {
        "ignore_case": {
            "flags": re.IGNORECASE,
            "patterns": {
                r"complexity science": 3.0, r"network science": 3.0, r"graph theory": 2.6,
                r"graph data": 2.5, r"network medicine": 2.1, r"network biology": 1.8,
                r"graph machine learning": 1.8, r"graph deep learning": 1.6, r"graph neural network": 1.4,
                r"\bgnn\b": 1.3, r"complex systems": 1.1, r"graph": 1.0,
                r"operations research": 1.2, r"social network": 0.5, r"complexity": 0.2,
            }
        }
    },
    "knowledge_graphs": {
        "ignore_case": {
            "flags": re.IGNORECASE,
            "patterns": {
                r"graph database": 1.6, r"knowledge graph": 1.5, r"neo4j": 1.4,
                r"sparql": 0.9, r"semantic web": 0.5, r"knowledge management": 0.4,
                r"ontology": 0.3, r"\bowl\b": 0.1, r"\brdf\b": 0.1,
                r"extract\s+(meaning|knowledge)": 0.7,
            }
        }
    },
    "geospatial": {
        "ignore_case": {
            "flags": re.IGNORECASE,
            "patterns": {
                r"geospatial": 1.4, r"geodata": 0.8, r"spatial": 0.7,
                r"maps": 0.4, r"geometry": 0.4,
            }
        },
        "case_sensitive": {
            "flags": 0,
            "patterns": {r"\bGIS\b": 0.1}
        }
    },
    "biotech_lifesciences": {
        "ignore_case": {
            "flags": re.IGNORECASE,
            "patterns": {
                r"aithyra": 1.8, r"bioinformatic": 1.1, r"bioengineer": 0.8,
                r"neuro(?:science|scientist|degener.*?)": 0.8, r"brain": 0.8, r"biotech": 0.5,
                r"biological": 0.4, r"genetics": 0.4, r"molecules": 0.3, r"molecular": 0.3, r"protein": 0.3,
                r"biology": 0.3, r"chemistry": 0.2, r"health(?:care)?": 0.2, r"pharma": 0.2, r"cell": 0.2,
                r"clinical": 0.1, r"patient": 0.1,
            }
        }
    },
    "science_research": {
        "ignore_case": {
            "flags": re.IGNORECASE,
            "patterns": {
                r"algorithm": 1.2, r"phd": 1.1, r"\bmath": 1.0, r"advanced degree": 1.0,
                r"conference": 0.9, r"researcher": 0.9, r"combinatori": 0.8, r"optimization": 0.8,
                r"\bmsc\b": 0.7, r"research": 0.7, r"causal": 0.7, r"inference": 0.7,
                r"forecasting": 0.6, r"master": 0.6, r"model(?:l)?ing": 0.5,
                r"scientific": 0.4, r"physics": 0.4, r"theory": 0.3, r"simulation": 0.3, r"quantitative": 0.3,
                r"statistic": 0.25, r"probability": 0.2, r"scale": 0.2,
                r"numerical": 0.1, r"information": 0.1,
                r"dissertation": -0.5, r"thesis": -0.5, r"student": -0.5, r"technik": -0.5,
            }
        },
        "case_sensitive": {
            "flags": 0,
            "patterns": {r"\bR&D\b": 0.2}
        }
    },
    "data_science": {
        "ignore_case": {
            "flags": re.IGNORECASE,
            "patterns": {
                r"data scientist": 1.4, r"data science": 1.2, r"data mining": 1.1, r"time series": 1.1,
                r"scraping": 0.9, r"data collection": 0.8, r"analytics": 0.8, r"data engineering": 0.7,
                r"ai agents": 0.6, r"data engineer": 0.5, r"predictive": 0.5, r"data management": 0.5,
                r"data model(?:l)?ing": 0.4, r"estimation": 0.4, r"data analysis": 0.4, r"\bdata\b": 0.35,
                r"big data": 0.3, r"data warehous": 0.2, r"design": 0.15,
                r"pipeline": 0.1, r"dashboard": 0.1,
            }
        },
        "case_sensitive": {
            "flags": 0,
            "patterns": {r"\bETL\b": 0.9, r"\bELT\b": 0.5}
        }
    },
    "machine_learning_ai": {
        "ignore_case": {
            "flags": re.IGNORECASE,
            "patterns": {
                r"machine learning engineer": 1.0, r"machine learning": 0.9, r"neural network": 0.6,
                r"deep learning": 0.5, r"reinforcement learning": 0.4, r"\bnlp\b": 0.4,
                r"pattern recognition": 0.3, r"image processing": 0.2,
                r"computer vision": 0.1, r"neural": 0.1,
            }
        },
        "case_sensitive": {
            "flags": 0,
            "patterns": {r"\bAI\b": 0.8, r"\bML\b": 0.9, r"\bLLM\b": 0.25}
        }
    },
    "ai_tools_platforms": {
        "ignore_case": {
            "flags": re.IGNORECASE,
            "patterns": {
                r"claude code": 1.2, r"claude": 1.0, r"spec[-\s]?driven": 0.8,
                r"codex": 0.6, r"copilot": 0.5,
            }
        }
    },
    "job_titles_roles": {
        "ignore_case": {
            "flags": re.IGNORECASE,
            "patterns": {
                r"scientist": 1.2, r"forward deployed": 1.0, r"engineer": 0.45, r"developer": 0.4,
                r"full[\s-]stack": 0.4, r"platform engineer": 0.3, r"analyst": 0.1, r"senior": 0.1,
                r"leiter": -1.5, r"manager": -0.9, r"owner": -0.9, r"officer": -0.8,
                r"security": -0.4, r"safety": -0.4, r"support": -0.3, r"quality": -0.2,
            }
        },
        "case_sensitive": {
            "flags": 0,
            "patterns": {r"\bHR\b": -0.7}
        }
    },
    "tech_tools": {
        "ignore_case": {
            "flags": re.IGNORECASE,
            "patterns": {
                r"\bpython\b": 1.0, r"knime": 0.8, r"\bsql\b": 0.5, r"duckdb": 0.5, r"open source": 0.45,
                r"fabric": 0.4, r"docker": 0.35, r"postgres": 0.3, r"power bi": 0.3, r"qlik": 0.3, r"matplotlib": 0.3,
                r"mysql": 0.2, r"jinja": 0.2, r"github": 0.2, r"\bc\+\+": 0.2, r"\bd3\b": 0.2,
                r"visualization": 0.15, r"\bgit\b": 0.1, r"vector": 0.1,
                r"microsoft": -0.2, r"linux": -0.4, r"test": -0.3, r"java": -0.2, r"devops": -0.1, r"cyber": -0.1,
            }
        },
        "case_sensitive": {
            "flags": 0,
            "patterns": {
                r"\bAPI\b": 0.4, r"\bREST\b": 0.15, r"\bCI[/-]CD\b": 0.2,
                r"\bAWS\b": 0.2, r"\bMCP\b": 0.2,
                r"\bSAP\b": -0.6, r"\bSAS\b": -0.6, r"\bSEO\b": -0.2,
            }
        }
    },
    "engineering_hardware": {
        "ignore_case": {
            "flags": re.IGNORECASE,
            "patterns": {
                r"lidar": 0.7, r"radar": 0.7, r"robot": 0.6, r"sensor": 0.6, r"embedded": 0.5,
                r"signal": 0.35, r"electro": 0.3, r"microcontroller": 0.3, r"electrical": 0.25, r"circuit": 0.25,
                r"energy": 0.1, r"electric": 0.2, r"smart": 0.2, r"audio": 0.2, r"video": 0.2, r"vision": 0.2,
                r"wireless": 0.15, r"spectral": 0.15, r"semiconductor": 0.15, r"hardware": 0.15,
                r"telecom": 0.1, r"compression": 0.1, r"fpga": 0.1, r"verilog": 0.1, r"digital": 0.1, r"media": 0.1,
                r"power": 0.05, r"power grid": 0.1,
            }
        }
    },
    "business_finance": {
        "ignore_case": {
            "flags": re.IGNORECASE,
            "patterns": {
                r"real estate": -1.0, r"holding": -1.0, r"purchasing": -1.0, r"accountant": -1.0, r"accounting": -1.0,
                r"sales": -1.0, r"audit": -1.0, r"consulting?": -0.7, r"(tax|steuer)": -0.7,
                r"acquisition": -0.6, r"merger": -0.6, r"stack developer": -0.6, r"insurance": -0.5,
                r"control": -0.4, r"risk": -0.4, r"finanz?": -0.3, r"bank(?:ing)?": -0.3,
                r"assurance": -0.3, r"agile": -0.3, r"requirement": -0.3, r"product": -0.2,
            }
        }
    },
    "languages_location_extra": {
        "ignore_case": {
            "flags": re.IGNORECASE,
            "patterns": {
                r"hungarian": 1.9, r"hungary": 0.7, r"english": 0.2, r"deutsch": -0.2,
                r"sehr\s+gut(e)?\s+deutsch": -1.1, r"wort\s+(&|und)\s+schrift": -0.4,
                r"fluency\s+in\s+german": -1.1, r"fluent\s+in\s+german": -1.1,
                r"deutschkenntnisse verhandlungssicher": -1.1,
                r"5(\+)?\s+years\s+of": -0.8, r"7(\+)?\s+years\s+of": -1.9,
                r"5(\+)?\s+jahre\s+erfahrung": -0.8, r"7(\+)?\s+jahre\s+erfahrung": -1.9,
                r"home office": 0.15, r"relocation": 0.2,
            }
        }
    },
}

BASE_TITLE_SCORING = {
    "ignore_case": {
        "flags": re.IGNORECASE,
        "patterns": {
            r"management": -0.7, r"head": -0.7, r"lead(?:er)?": -0.5, r"architect": -0.3
        }
    }
}

BASE_COMPANY_SCORING = {
    "ignore_case": {
        "flags": re.IGNORECASE,
        "patterns": {
            r"aithyra": 1.5, r"\bait\b": 0.8, r"science": 0.5,
            r"amazon": 0.5, r"google": 0.5, r"meta": 0.3, r"microsoft": 0.5,
            r"nvidia": 0.5, r"ibm": 1.0, r"deepmind": 1.0,
            r"österreichische post": 0.2,
            r"capgemini": -0.5, r"accenture": -0.5, r"deloitte": -0.5,
            r"lotterien": -1.0, r"win2day": -1.0,
        }
    }
}

DEDUCT_COMPANIES = [r"\böbb\b", r"\bwkö\b", r"\bwko\b", r"anexia", r"techtalk"]
