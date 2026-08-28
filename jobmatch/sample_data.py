"""Placeholder sample content.

Per the handoff, all of this is demo copy and must not ship as real data. It
stands in for the resume parser + job-source search while the app is developed.
"""
from __future__ import annotations

from .models import Apply, Factors, Job, Profile, SavedJob, Skill


def sample_profile() -> Profile:
    return Profile(
        name="Amara Okafor",
        current_title="Senior Data Analyst",
        target_title="Analytics Engineer",
        years="6 years",
        years_span="2019 – present",
        location="Lagos, Nigeria · open to remote",
        remote_ok=True,
        confidence="high",
        skills=[
            Skill("SQL"), Skill("dbt"), Skill("Python"), Skill("Analytics"),
            Skill("Data Modeling"), Skill("Airflow"), Skill("Tableau"),
            Skill("Snowflake"), Skill("ETL"), Skill("Statistics"),
            Skill("BigQuery", "low"), Skill("Looker", "low"),
        ],
    )


def _job(**kw) -> Job:
    return Job(**kw)


def sample_jobs() -> list[Job]:
    return [
        _job(
            id="j1", title="Analytics Engineer", company="Flutterwave",
            location="Lagos, NG", mode="Remote", type="Full-time",
            salary_min=70000, salary_max=88000, score=91,
            factors=Factors(("9/12", 75), ("Match", 92), ("Remote ok", 100), ("2/5", 40)),
            posted="2 days ago",
            apply=Apply("website", "https://flutterwave.com/careers/analytics-engineer"),
            description=(
                "Own the analytics layer end to end — model raw event and "
                "transactional data into clean, well-tested marts the whole "
                "company trusts. You'll partner with data scientists and product "
                "teams to turn ambiguous questions into reliable metrics."
            ),
            requirements=[
                (True, "4+ years in analytics or data engineering"),
                (True, "Strong SQL and dimensional modeling"),
                (True, "Experience with dbt"),
                (False, "Production Airflow or Dagster orchestration"),
                (False, "Looker or LookML modeling"),
            ],
            benefits="Remote-first, learning budget, home-office stipend, private health cover.",
            matched_skills=["SQL", "dbt", "Python"], extra_skill_count=4,
            source="company careers page",
        ),
        _job(
            id="j2", title="Senior Data Analyst", company="Paystack",
            location="Lagos, NG", mode="Hybrid", type="Full-time",
            salary_min=60000, salary_max=80000, score=84,
            factors=Factors(("10/12", 83), ("Match", 90), ("Hybrid", 70), ("3/5", 60)),
            posted="4 days ago",
            apply=Apply("email", "careers@paystack.com"),
            description=(
                "Drive decisions across payments and growth. Build dashboards, "
                "run deep-dive analyses, and define the metrics leadership steers by."
            ),
            requirements=[
                (True, "5+ years in analytics"),
                (True, "Expert SQL"),
                (True, "Stakeholder communication"),
                (False, "Experiment design / causal inference"),
            ],
            benefits="Competitive pay, equity, hybrid Lagos office, annual retreat.",
            matched_skills=["SQL", "Tableau", "Statistics"], extra_skill_count=5,
            source="company careers page",
        ),
        _job(
            id="j3", title="Data Platform Engineer", company="Kobo360",
            location="Remote (Africa)", mode="Remote", type="Contract",
            salary_min=None, salary_max=None, score=68,
            factors=Factors(("7/12", 58), ("Close", 74), ("Remote ok", 100), ("2/5", 40)),
            posted="1 week ago",
            apply=Apply("form", "https://forms.gle/kobo360-data-platform"),
            description=(
                "Help scale our logistics data platform. Build ingestion "
                "pipelines and keep the warehouse fast and dependable."
            ),
            requirements=[
                (True, "Python and SQL"),
                (True, "ETL pipeline experience"),
                (False, "Kafka / streaming"),
                (False, "Kubernetes"),
            ],
            benefits="Fully remote, flexible hours, 6-month renewable contract.",
            matched_skills=["Python", "ETL"], extra_skill_count=3,
            source="job board",
        ),
        _job(
            id="j4", title="BI Developer", company="Andela",
            location="Nairobi, KE", mode="Remote", type="Full-time",
            salary_min=52000, salary_max=72000, score=61,
            factors=Factors(("6/12", 50), ("Below", 60), ("Remote ok", 100), ("1/5", 20)),
            posted="3 days ago",
            apply=Apply("none", ""),
            description=(
                "Build and maintain BI dashboards for internal teams and turn "
                "raw data into clear visual stories."
            ),
            requirements=[
                (True, "SQL and a BI tool"),
                (False, "Power BI / DAX"),
                (False, "Data warehouse modeling"),
            ],
            benefits="Remote, global team, generous PTO.",
            matched_skills=["SQL", "Tableau"], extra_skill_count=2,
            source="job board",
        ),
        _job(
            id="j5", title="Machine Learning Engineer", company="Moniepoint",
            location="Lagos, NG", mode="On-site", type="Full-time",
            salary_min=75000, salary_max=95000, score=44,
            factors=Factors(("4/12", 33), ("Below", 55), ("On-site", 20), ("1/5", 20)),
            posted="5 days ago",
            apply=Apply("website", "https://moniepoint.com/careers/ml-engineer"),
            description=(
                "Ship ML models to production for fraud and credit risk. Strong "
                "engineering fundamentals required."
            ),
            requirements=[
                (True, "Python"),
                (False, "PyTorch / TensorFlow"),
                (False, "MLOps and model serving"),
                (False, "On-site in Lagos"),
            ],
            benefits="On-site Lagos HQ, meals, health cover, equity.",
            matched_skills=["Python"], extra_skill_count=1,
            source="company careers page",
        ),
    ]


def sample_saved(jobs: list[Job]) -> list[SavedJob]:
    by_id = {j.id: j for j in jobs}
    return [
        SavedJob(by_id["j1"], saved_at="2h ago", deadline="Closes in 3 days"),
        SavedJob(by_id["j2"], saved_at="yesterday", applied_at="Applied 12 Aug",
                 channel_note="Email application"),
        SavedJob(by_id["j3"], saved_at="2 days ago", channel_note="Form application"),
        SavedJob(by_id["j4"], saved_at="4 days ago"),
        SavedJob(by_id["j5"], saved_at="1 week ago", expired=True),
    ]
