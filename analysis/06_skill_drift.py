import pandas as pd

from pathlib import Path


# --------------------------------------------------
# STEP 1: FIND ALL SNAPSHOT FILES
# --------------------------------------------------

project_folder = Path.cwd()

snapshot_files = sorted(
    project_folder.glob(
        "skill_snapshot_*.csv"
    )
)


print("--------------------------------------------")
print("SKILLDRIFT - TIME ANALYSIS")
print("--------------------------------------------")

print(
    "Snapshots found:",
    len(snapshot_files)
)


for file in snapshot_files:
    print(file.name)


# --------------------------------------------------
# STEP 2: CHECK IF WE HAVE ENOUGH SNAPSHOTS
# --------------------------------------------------

if len(snapshot_files) < 2:

    print()
    print("--------------------------------------------")
    print("NOT ENOUGH DATA YET")
    print("--------------------------------------------")

    print(
        "At least 2 different dated snapshots are needed"
    )

    print(
        "Current snapshot:",
        snapshot_files[-1].name
        if snapshot_files
        else "None"
    )

    print()
    print(
        "Collect the same cities again on another date."
    )

    raise SystemExit


# --------------------------------------------------
# STEP 3: SELECT THE LATEST TWO SNAPSHOTS
# --------------------------------------------------

old_file = snapshot_files[-2]

new_file = snapshot_files[-1]


print()
print("--------------------------------------------")
print("COMPARING")
print("--------------------------------------------")

print(
    "Old:",
    old_file.name
)

print(
    "New:",
    new_file.name
)


# --------------------------------------------------
# STEP 4: READ SNAPSHOTS
# --------------------------------------------------

old_data = pd.read_csv(
    old_file
)

new_data = pd.read_csv(
    new_file
)


# --------------------------------------------------
# STEP 5: JOIN THE TWO SNAPSHOTS
# --------------------------------------------------

comparison = old_data.merge(
    new_data,
    on="Skill",
    suffixes=(
        "_Old",
        "_New"
    )
)


# --------------------------------------------------
# STEP 6: CALCULATE CHANGE
# --------------------------------------------------

cities = [
    "Mumbai",
    "Pune",
    "Bengaluru"
]


for city in cities:

    comparison[
        f"{city} Change"
    ] = (

        comparison[
            f"{city} %_New"
        ]

        -

        comparison[
            f"{city} %_Old"
        ]
    )


# --------------------------------------------------
# STEP 7: CLASSIFY THE CHANGE
# --------------------------------------------------

def classify_change(change):

    if change >= 5:
        return "RISING"

    elif change <= -5:
        return "DECLINING"

    else:
        return "STABLE"


for city in cities:

    comparison[
        f"{city} Trend"
    ] = comparison[
        f"{city} Change"
    ].apply(
        classify_change
    )


# --------------------------------------------------
# STEP 8: PRINT RESULTS
# --------------------------------------------------

print()
print("--------------------------------------------")
print("SKILL DRIFT RESULTS")
print("--------------------------------------------")


for _, row in comparison.iterrows():

    print()
    print(
        "Skill:",
        row["Skill"]
    )

    for city in cities:

        print(
            city,
            ":",
            row[f"{city} %_Old"],
            "%",
            "->",
            row[f"{city} %_New"],
            "%",
            "| Change:",
            round(
                row[f"{city} Change"],
                1
            ),
            "percentage points",
            "|",
            row[f"{city} Trend"]
        )


# --------------------------------------------------
# STEP 9: SAVE RESULT
# --------------------------------------------------

comparison.to_csv(
    "skill_drift_latest.csv",
    index=False
)


print()
print("--------------------------------------------")
print(
    "Saved: skill_drift_latest.csv"
)
print("--------------------------------------------")