"""Vocabulary used by the résumé parser and the match scorer.

A curated set of skills and a subset flagged as "tooling", plus seniority and
title keywords. Kept deliberately small and editable — extend it for your
domain. Each entry maps a canonical display name to the lowercase aliases that
should match it in free text.
"""
from __future__ import annotations

# canonical name -> list of lowercase aliases (word-boundary matched)
SKILLS: dict[str, list[str]] = {
    "SQL": ["sql"],
    "Python": ["python"],
    "R": [r"\br\b"],
    "Java": ["java"],
    "JavaScript": ["javascript", "js"],
    "TypeScript": ["typescript"],
    "Scala": ["scala"],
    "Go": ["golang", r"\bgo\b"],
    "dbt": ["dbt"],
    "Airflow": ["airflow"],
    "Spark": ["spark", "pyspark"],
    "Kafka": ["kafka"],
    "Snowflake": ["snowflake"],
    "BigQuery": ["bigquery", "big query"],
    "Redshift": ["redshift"],
    "Databricks": ["databricks"],
    "Tableau": ["tableau"],
    "Power BI": ["power bi", "powerbi"],
    "Looker": ["looker", "lookml"],
    "Excel": ["excel"],
    "Pandas": ["pandas"],
    "NumPy": ["numpy"],
    "scikit-learn": ["scikit-learn", "sklearn", "scikit learn"],
    "TensorFlow": ["tensorflow"],
    "PyTorch": ["pytorch"],
    "Docker": ["docker"],
    "Kubernetes": ["kubernetes", "k8s"],
    "AWS": ["aws", "amazon web services"],
    "GCP": ["gcp", "google cloud"],
    "Azure": ["azure"],
    "Terraform": ["terraform"],
    "Git": ["git", "github", "gitlab"],
    "ETL": ["etl", "elt"],
    "Data Modeling": ["data modeling", "data modelling", "dimensional model"],
    "Data Warehousing": ["data warehouse", "data warehousing", "warehousing"],
    "Analytics": ["analytics", "analysis"],
    "Statistics": ["statistics", "statistical"],
    "Machine Learning": ["machine learning", r"\bml\b"],
    "A/B Testing": ["a/b testing", "ab testing", "experimentation"],
    "React": ["react"],
    "Node.js": ["node.js", "nodejs", "node"],
}

# skills that count toward the "tooling" match factor
TOOLING = {
    "dbt", "Airflow", "Spark", "Kafka", "Snowflake", "BigQuery", "Redshift",
    "Databricks", "Tableau", "Power BI", "Looker", "Docker", "Kubernetes",
    "AWS", "GCP", "Azure", "Terraform", "Git", "TensorFlow", "PyTorch",
    "Pandas", "NumPy", "scikit-learn",
}

# seniority rank (higher = more senior)
SENIORITY = {
    "intern": 0, "junior": 1, "associate": 1, "mid": 2, "mid-level": 2,
    "intermediate": 2, "senior": 3, "staff": 4, "lead": 4, "principal": 5,
    "head": 5, "director": 6, "vp": 7, "chief": 8,
}

# words that mark a line as a job title
TITLE_WORDS = [
    "engineer", "analyst", "scientist", "developer", "manager", "designer",
    "architect", "consultant", "administrator", "specialist", "lead",
    "director", "researcher", "programmer",
]

SECTION_HEADERS = {
    "skills": ["skills", "technical skills", "core skills", "competencies",
               "technologies", "tech stack"],
    "experience": ["experience", "work experience", "employment",
                   "professional experience"],
    "education": ["education", "academic"],
    "summary": ["summary", "profile", "objective", "about"],
}

# ---- location gazetteer (used by the résumé location detector) ------------
COUNTRIES = {
    "nigeria", "ghana", "kenya", "south africa", "egypt", "morocco", "ethiopia",
    "united states", "usa", "u.s.", "u.s.a.", "united kingdom", "uk", "u.k.",
    "canada", "ireland", "germany", "france", "spain", "portugal", "italy",
    "netherlands", "belgium", "switzerland", "austria", "sweden", "norway",
    "denmark", "finland", "poland", "ukraine", "romania", "greece", "turkey",
    "india", "pakistan", "bangladesh", "china", "japan", "south korea",
    "singapore", "malaysia", "indonesia", "philippines", "vietnam", "thailand",
    "australia", "new zealand", "brazil", "argentina", "chile", "colombia",
    "mexico", "peru", "united arab emirates", "uae", "saudi arabia", "qatar",
    "israel", "estonia", "lithuania", "latvia", "czechia", "czech republic",
    "hungary", "bulgaria", "croatia", "serbia", "slovakia", "slovenia",
}

# major cities (lowercase). Not exhaustive — extend for your market.
CITIES = {
    "lagos", "abuja", "ibadan", "port harcourt", "kano", "accra", "nairobi",
    "mombasa", "johannesburg", "cape town", "pretoria", "durban", "cairo",
    "casablanca", "addis ababa", "london", "manchester", "birmingham", "leeds",
    "edinburgh", "glasgow", "dublin", "new york", "san francisco", "los angeles",
    "seattle", "boston", "chicago", "austin", "denver", "atlanta", "miami",
    "washington", "toronto", "vancouver", "montreal", "ottawa", "berlin",
    "munich", "hamburg", "frankfurt", "cologne", "paris", "lyon", "marseille",
    "madrid", "barcelona", "lisbon", "porto", "rome", "milan", "amsterdam",
    "rotterdam", "brussels", "zurich", "geneva", "vienna", "stockholm", "oslo",
    "copenhagen", "helsinki", "warsaw", "krakow", "kyiv", "bucharest", "athens",
    "istanbul", "dubai", "abu dhabi", "riyadh", "doha", "tel aviv", "mumbai",
    "delhi", "new delhi", "bangalore", "bengaluru", "hyderabad", "chennai",
    "pune", "kolkata", "karachi", "lahore", "islamabad", "dhaka", "beijing",
    "shanghai", "shenzhen", "tokyo", "osaka", "seoul", "singapore",
    "kuala lumpur", "jakarta", "manila", "bangkok", "hanoi", "ho chi minh city",
    "sydney", "melbourne", "brisbane", "perth", "auckland", "wellington",
    "sao paulo", "rio de janeiro", "buenos aires", "santiago", "bogota",
    "mexico city", "guadalajara", "lima", "tallinn", "vilnius", "riga",
    "prague", "budapest", "sofia", "zagreb", "belgrade",
}

US_STATES = {
    "al", "ak", "az", "ar", "ca", "co", "ct", "de", "fl", "ga", "hi", "id",
    "il", "in", "ia", "ks", "ky", "la", "me", "md", "ma", "mi", "mn", "ms",
    "mo", "mt", "ne", "nv", "nh", "nj", "nm", "ny", "nc", "nd", "oh", "ok",
    "or", "pa", "ri", "sc", "sd", "tn", "tx", "ut", "vt", "va", "wa", "wv",
    "wi", "wy", "dc",
}
