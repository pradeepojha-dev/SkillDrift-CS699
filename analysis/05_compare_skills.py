import pandas as pd
import matplotlib.pyplot as plt

from collections import Counter
from pathlib import Path


# --------------------------------------------------
# PROJECT FOLDERS
# --------------------------------------------------

# Current file:
# SkillDrift-CS699-Abhay/analysis/05_compare_skills.py

# Project root:
# SkillDrift-CS699-Abhay/

project_folder = Path(__file__).resolve().parent.parent

data_folder = project_folder / "data" / "raw"
output_folder = project_folder / "outputs"

output_folder.mkdir(exist_ok=True)


# --------------------------------------------------
# FIND LATEST DATASET FOR EACH CITY
# --------------------------------------------------

def find_latest_file(city):

    pattern = f"naukri_data_engineering_{city}_*.csv"

    files = list(data_folder.glob(pattern))

    if len(files) == 0:

        # Fallback to older non-dated file
        old_file = (
            data_folder
            / f"naukri_data_engineering_{city}.csv"
        )

        if old_file.exists():
            return old_file

        print()
        print("--------------------------------------------")
        print("ERROR")
        print("--------------------------------------------")
        print("No dataset found for:", city)
        print("Checked folder:")
        print(data_folder)

        raise FileNotFoundError(
            f"No CSV found for {city}"
        )

    latest_file = max(
        files,
        key=lambda file: file.stat().st_mtime
    )

    return latest_file


mumbai_file = find_latest_file("mumbai")
pune_file = find_latest_file("pune")
bengaluru_file = find_latest_file("bengaluru")


# --------------------------------------------------
# SHOW SELECTED FILES
# --------------------------------------------------

print()
print("--------------------------------------------")
print("FILES SELECTED")
print("--------------------------------------------")

print("Mumbai:", mumbai_file.name)
print("Pune:", pune_file.name)
print("Bengaluru:", bengaluru_file.name)


# --------------------------------------------------
# READ DATA
# --------------------------------------------------

mumbai = pd.read_csv(
    mumbai_file,
    encoding="utf-8-sig"
)

pune = pd.read_csv(
    pune_file,
    encoding="utf-8-sig"
)

bengaluru = pd.read_csv(
    bengaluru_file,
    encoding="utf-8-sig"
)


print()
print("--------------------------------------------")
print("DATA CHECK")
print("--------------------------------------------")

print("Mumbai jobs:", len(mumbai))
print("Pune jobs:", len(pune))
print("Bengaluru jobs:", len(bengaluru))


# --------------------------------------------------
# BASIC NOISE FILTER
# --------------------------------------------------

noise_words = {
    "data",
    "senior",
    "data engineer",
    "data engineering"
}


# --------------------------------------------------
# COUNT HOW MANY JOBS MENTION EACH SKILL
# --------------------------------------------------

def get_skill_job_counts(dataframe):

    counts = Counter()

    for skills_text in dataframe["skills"].fillna(""):

        job_skills = set()

        for skill in skills_text.split(","):

            clean_skill = skill.strip().lower()

            if (
                clean_skill != ""
                and clean_skill not in noise_words
            ):
                job_skills.add(clean_skill)

        counts.update(job_skills)

    return counts


mumbai_counts = get_skill_job_counts(mumbai)
pune_counts = get_skill_job_counts(pune)
bengaluru_counts = get_skill_job_counts(bengaluru)


# --------------------------------------------------
# PRINT TOP SKILLS FOR EACH CITY
# --------------------------------------------------

def print_skill_demand(
    city,
    dataframe,
    counts
):

    print()
    print("--------------------------------------------")
    print(city, "- JOB DEMAND %")
    print("--------------------------------------------")

    for skill, count in counts.most_common(10):

        percentage = (
            count
            / len(dataframe)
            * 100
        )

        print(
            skill,
            ":",
            count,
            "jobs |",
            round(percentage, 1),
            "%"
        )


print_skill_demand(
    "MUMBAI",
    mumbai,
    mumbai_counts
)

print_skill_demand(
    "PUNE",
    pune,
    pune_counts
)

print_skill_demand(
    "BENGALURU",
    bengaluru,
    bengaluru_counts
)


# --------------------------------------------------
# REGIONAL COMPARISON
# --------------------------------------------------

skills_to_compare = [
    "python",
    "sql",
    "pyspark",
    "snowflake",
    "aws",
    "airflow",
    "azure data factory",
    "gcp",
    "etl",
    "data pipelines"
]


comparison_rows = []


for skill in skills_to_compare:

    mumbai_percent = (
        mumbai_counts.get(skill, 0)
        / len(mumbai)
        * 100
    )

    pune_percent = (
        pune_counts.get(skill, 0)
        / len(pune)
        * 100
    )

    bengaluru_percent = (
        bengaluru_counts.get(skill, 0)
        / len(bengaluru)
        * 100
    )

    comparison_rows.append({
        "Skill": skill,
        "Mumbai %": round(
            mumbai_percent,
            1
        ),
        "Pune %": round(
            pune_percent,
            1
        ),
        "Bengaluru %": round(
            bengaluru_percent,
            1
        )
    })


comparison_table = pd.DataFrame(
    comparison_rows
)


print()
print("--------------------------------------------")
print("REGIONAL SKILL COMPARISON")
print("--------------------------------------------")

print(
    comparison_table.to_string(
        index=False
    )
)


# --------------------------------------------------
# SAVE REGIONAL COMPARISON CSV
# --------------------------------------------------

comparison_csv = (
    output_folder
    / "regional_skill_comparison.csv"
)

comparison_table.to_csv(
    comparison_csv,
    index=False
)

print()
print(
    "Saved:",
    comparison_csv
)


# --------------------------------------------------
# CREATE GRAPH
# --------------------------------------------------

graph_data = comparison_table.set_index(
    "Skill"
)

graph_data.plot(
    kind="bar",
    figsize=(12, 6)
)

plt.title(
    "Regional Skill Demand - Data Engineering Jobs"
)

plt.xlabel(
    "Skill"
)

plt.ylabel(
    "Jobs Mentioning Skill (%)"
)

plt.xticks(
    rotation=45,
    ha="right"
)

plt.tight_layout()


# --------------------------------------------------
# SAVE GRAPH
# --------------------------------------------------

graph_file = (
    output_folder
    / "regional_skill_comparison.png"
)

plt.savefig(
    graph_file,
    dpi=300
)

plt.close()


print(
    "Saved:",
    graph_file
)


# --------------------------------------------------
# FINISHED
# --------------------------------------------------

print()
print("--------------------------------------------")
print("REGIONAL ANALYSIS COMPLETED SUCCESSFULLY")
print("--------------------------------------------")