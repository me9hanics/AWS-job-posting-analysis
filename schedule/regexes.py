"""
    Notes:
    - Use patterns under "ignore_case" with re.IGNORECASE.
    - Use patterns under "case_sensitive" as-is.
"""
### Take into account how easy it is for a regex to be matched in an irrelevant context.
### E.g., "lead" commonly appears in descriptions, but don't necessarily indicate a "lead" role.


REGEX_LOOKUP = {
### BIOGRAPHICAL
    "language_geography": {
        "ignore_case": [
            r"international",
            r"global",
            r"remote",
            r"relocation",
            r"eu citizenship",
            r"home office",

            r"hungarian",
            r"hungary",
            r"english",
            r"ukrainian",
            r"russian",
            r"eastern\s+europ",
            r"spanish",
            r"german",
            r"deutsch",

            r"verhandlungssicher",
            r"deutschkenntnisse",
            r"deutschkenntnisse verhandlungssicher",
            r"muttersprache",
            r"sehr\s+gut(e)?\s+deutsch",
            r"wort\s+(&|und)\s+schrift",
            r"fluency\s+in\s+german",
            r"fluent\s+in\s+german",
        ]
    },
    "education_worktype": {
        "ignore_case": [
            r"advanced degree",
            r"conference",
            r"\bmsc\b",
            r"master",
            r"phd",
            r"dissertation",
            r"thesis",
            r"student",
            r"researcher",
            r"technik", #typically negative, due to not speaking german
            r"audit",
            r"consultant",
        ]
    },

    "seniority_negative": {
        "ignore_case": [
            r"senior",
            r"manager",
            r"head of",
            r"director",
            r"principal",
            r"\b(?:5|five)\+?\s+(?:years|yrs)\s+(?:of\s+)?(?:experience)?\b"
            r"\b(?:7|seven)\+?\s+(?:years|yrs)\s+(?:of\s+)?(?:experience)?\b"
            r"\b(?:5|fünf)\+?\s+jahre\s+(?:berufs)?erfahrung\b"
            r"\b(?:7|sieben)\+?\s+jahre\s+(?:berufs)?erfahrung\b"
        ]
    },
### FIRMS
    "companies": {
        "ignore_case": [
            r"wolf\s+theiss",
            r"schönherr",
            r"baker\s+mckenzie",
            r"\be\+h\b",
            r"leitner",
            r"binder\s+grösswang",
            r"deloitte",
            r"kpmg",
            r"raiffeisen",
            r"erste\s+bank",
            r"erste\s+group",
            r"ey\s+law",
        ]
    },
### TOPICS
    "tech_tools": {
        "ignore_case": [
            r"\bpython\b",
            r"knime",
            r"\bsql\b",
            r"duckdb",
            r"open source",
            r"fabric",
            r"docker",
            r"postgres",
            r"power bi",
            r"qlik",
            r"matplotlib",
            r"mysql",
            r"jinja",
            r"github",
            r"\bc\+\+",
            r"\bd3\b",
            r"visualization",
            r"\bgit\b",
            r"vector",
            r"microsoft",
            r"linux",
            r"test",
            r"java",
            r"devops",
            r"cyber",
        ],
        "case_sensitive": [
            r"\bAPI\b",
            r"\bREST\b",
            r"\bCI[/-]CD\b",
            r"\bAWS\b",
            r"\bMCP\b",
            r"\bSAP\b",
            r"\bSAS\b",
            r"\bSEO\b",
        ]
    },
    "science_research": {
        "ignore_case": [
            r"algorithm",
            r"phd",
            r"scientific",
            r"physics",
            r"\bmath",
            r"combinatori",
            r"research",
            r"optimization",
            r"causal",
            r"inference",
            r"forecasting",
            r"model(?:l)?ing",
            r"theory",
            r"simulation",
            r"quantitative",
            r"statistic",
            r"probability",
            r"scale",
            r"numerical",
            r"information",
        ],
        "case_sensitive": [
            r"\bR&D\b",
        ]
    },
    "job_titles_roles": {
        "ignore_case": [
            r"scientist",
            r"forward deployed",
            r"engineer",
            r"developer",
            r"full[\s-]stack",
            r"platform engineer",
            r"analyst",
            r"senior",
            r"leiter",
            r"manager",
            r"owner",
            r"officer",
            r"security",
            r"safety",
            r"support",
            r"quality",
        ],
        "case_sensitive": [
            r"\bHR\b",
        ]
    },
    "business_analyst": {
        "ignore_case": [
            r"business\s+analyst",
            r"system[s]?\s+analyst",
            r"product\s+analyst",
            r"requirements\s+analyst",
            r"functional\s+analyst",
            r"business\s+systems?\s+analyst",
            r"process\s+analyst",
            r"operations\s+analyst",
            r"implementation\s+analyst",
            r"crm\s+analyst",
            r"compliance\s+analyst",
            r"risk\s+analyst",
            r"data\s+analyst",
            r"quantitative",
            r"analytics",
            r"\bA\s*/\s*B\s*(?:test(?:ing)?|experiment(?:s|ation)?)\b",
            #r"prioritization",
            r"cross-functional"
        ]
    },
    "economics": {
        "ignore_case": [
            r"economics",
            r"economist",
            r"economic",
        ]
    },
    "product_management": {
        "ignore_case": [
            r"product\s+manager",
            r"junior\s+product",
            r"product\s+management",
            r"product\s+owner",
            r"product\s+strategy",
            r"roadmap",
            r"mvp",
        ]
    },
    "process_governance": {
        "ignore_case": [
            r"business\s+process",
            r"process\s+management",
            r"process\s+improvement",
            r"it\s+governance",
            r"governance",
            r"risk",
            r"control",
            r"compliance",
            r"privacy",
            r"data\s+protection",
            r"gdpr",
            r"it\s+law",
        ]
    },
    "digital_business": {
        "ignore_case": [
            r"digital\s+transformation",
            r"digital\s+strategy",
            r"digital\s+product",
            r"data[-\s]?driven",
        ]
    },
    "analysis_tools": {
        "ignore_case": [
            r"\bsql\b",
            r"power\s+bi",
            r"tableau",
            r"excel",
            r"jira",
            r"confluence",
            r"crm",
            r"salesforce",
        ]
    },
    "analytics_general": {
        "ignore_case": [
            r"business\s+intelligence",
            r"\binsights?\b",
            r"\bkpi(s)?\b",
            r"\breporting\b",
            r"forecasting",
            r"statistical",
            r"quantitative\s+analysis",
        ]
    },
    "ai_signals": {
        "ignore_case": [
            r"artificial\s+intelligence",
            r"machine\s+learning",
        ],
        "case_sensitive": [
            r"\bAI\b",
            r"\bML\b",
        ]
    },
    "customer_focus": {
        "ignore_case": [
            r"customer",
            r"stakeholder",
            r"requirements",
            r"presentation",
            r"communication",
        ]
    },
    "complexity_networks": {
        "ignore_case": [
            r"complexity science",
            r"network science",
            r"graph theory",
            r"graph data",
            r"network medicine",
            r"network biology",
            r"graph machine learning",
            r"graph deep learning",
            r"graph neural network",
            r"\bgnn\b",
            r"complex systems",
            r"graph",
            r"operations research",
            r"social network",
            r"complexity",
        ]
    },
    "knowledge_graphs": {
        "ignore_case": [
            r"graph database",
            r"knowledge graph",
            r"neo4j",
            r"sparql",
            r"semantic web",
            r"knowledge management",
            r"ontology",
            r"\bowl\b",
            r"\brdf\b",
            r"extract\s+(meaning|knowledge)",
        ]
    },
    "geospatial": {
        "ignore_case": [
            r"geospatial",
            r"geodata",
            r"spatial",
            r"earth",
            r"earth observation",
            r"openstreetmap",
            r"maps",
            r"geometry",
        ],
        "case_sensitive": [
            r"\bGIS\b",
        ]
    },
    "biotech_lifesciences": {
        "ignore_case": [
            r"aithyra",
            r"bioinformatic",
            r"bioengineer",
            r"neuro(?:science|scientist|degener.*?)",
            r"brain",
            r"biotech",
            r"biological",
            r"genetics",
            r"molecules",
            r"molecular",
            r"protein",
            r"biology",
            r"chemistry",
            r"health(?:care)?",
            r"pharma",
            r"cell",
            r"clinical",
            r"patient",
        ]
    },
    "data_science": {
        "ignore_case": [
            r"data scientist",
            r"data science",
            r"data mining",
            r"time series",
            r"scraping",
            r"data collection",
            r"analytics",
            r"data engineering",
            r"ai agents",
            r"data engineer",
            r"predictive",
            r"data management",
            r"data model(?:l)?ing",
            r"estimation",
            r"data analysis",
            r"\bdata\b",
            r"big data",
            r"data warehous",
            r"design",
            r"pipeline",
            r"dashboard",
        ],
        "case_sensitive": [
            r"\bETL\b",
            r"\bELT\b",
        ]
    },
    "machine_learning_ai": {
        "ignore_case": [
            r"machine learning engineer",
            r"machine learning",
            r"neural network",
            r"deep learning",
            r"reinforcement learning",
            r"\bnlp\b",
            r"pattern recognition",
            r"image processing",
            r"computer vision",
            r"neural",
        ],
        "case_sensitive": [
            r"\bAI\b",
            r"\bML\b",
            r"\bLLM\b",
        ]
    },
    "ai_tools_platforms": {
        "ignore_case": [
            r"claude code",
            r"claude",
            r"spec[-\s]?driven",
            r"codex",
            r"copilot",
        ]
    },
    "engineering_hardware": {
        "ignore_case": [
            r"lidar",
            r"radar",
            r"robot",
            r"sensor",
            r"embedded",
            r"signal",
            r"electro",
            r"microcontroller",
            r"electrical",
            r"circuit",
            r"energy",
            r"electric",
            r"smart",
            r"audio",
            r"video",
            r"vision",
            r"wireless",
            r"spectral",
            r"semiconductor",
            r"hardware",
            r"telecom",
            r"compression",
            r"fpga",
            r"verilog",
            r"digital",
            r"media",
            r"power",
            r"power grid",
        ]
    },
    "business_finance": {
        "ignore_case": [
            r"real estate",
            r"holding",
            r"purchasing",
            r"accountant",
            r"accounting",
            r"sales",
            r"audit",
            r"consulting?",
            r"(tax|steuer)",
            r"acquisition",
            r"merger",
            r"stack developer",
            r"insurance",
            r"control",
            r"risk",
            r"finanz?",
            r"bank(?:ing)?",
            r"assurance",
            r"agile",
            r"requirement",
            r"product",
        ]
    },
### LEGAL
    "arbitration_dispute": {
        "ignore_case": [
            r"arbitration",
            r"schiedsanwalt",
            r"schiedsvergleich",
            r"dispute\s+resolution",
            r"arbitral",
            r"mediation",
            r"tribunal",
            r"dispute",
            r"litigation",
        ],
        "case_sensitive": [
            r"\bUNCITRAL\b",
            r"\bICC\b",
            r"\bICSID\b",
            r"\bLCIA\b",
        ]
    },
    "foreign_international_law": {
        "ignore_case": [
            r"foreign\s+law",
            r"international\s+law",
            r"international",
        ],
        "case_sensitive": [
            r"\bWTO\b",
        ]
    },
    "capital_markets_finance": {
        "ignore_case": [
            r"capital\s+markets",
            r"anti-money\s+laundering",
            r"banking",
            r"finance",
            r"anti-money",
            r"laundering",
        ],
        "case_sensitive": [
            r"\bEMIR\b",
        ]
    },
    "human_rights": {
        "ignore_case": [
            r"human\s+rights?",
            r"anti-corruption",
            r"humanitarian",
            r"rule\s+of\s+law",
            r"refugee",
            r"migration",
        ]
    },
    "business_corporate_law": {
        "ignore_case": [
            r"junior\s+compliance\s+officer",
            r"cross-border",
            r"corporate\s+law",
            r"trade\s+compliance",
            r"economic\s+law",
            r"transactional",
            r"contract",
            r"trade",
            r"business law",
            r"commercial",
            r"compliance",
            r"wirtschaftsrecht",
            r"sanction",
            r"m&a",
        ],
        "case_sensitive": [
            r"\bESG\b",
        ]
    },
    "tech_law": {
        "ignore_case": [
            r"\bai\s+law",
            r"\bai\s+governance",
            r"\bit\s+law",
            r"intellectual\s+property",
            r"\bip\s+law",
            r"data\s+protection",
            r"data\s+privacy",
            r"datenschutz",
            r"technology",
            r"engineer",
            r"developer",
        ],
        "case_sensitive": [
            r"\bIP\b",
            r"\bGDPR\b",
        ]
    },
    "legal": {
        "ignore_case": [
            r"court",
            r"hearing",
            r"jurist",
            r"counsel",
            r"law",
            r"rechtsan(walts|wälte)",
            r"volljurist",
            r"real\s+estate",
            r"notariat",
            r"liegenschaft",
            r"\bsteuer",
            r"tax",
            r"österreichisches\s+recht",
            r"steuerberatung",
            r"zivilrecht",
            r"verwaltungsrecht",
            r"strafrecht",
            r"verfahrensrecht",
        ],
        "case_sensitive": [
            r"\bHR\b",
            r"\bÖRAK\b",
            r"\bABGB\b",
            r"\bRAA\b",
        ]
    },
    "roles": {
        "ignore_case": [
            r"junior\s+associate",
            r"junior",
            r"assistant",
            r"associate",
            r"attorney",
            r"senior",
        ]
    },

}