Rohit Sapkale - 26M2132
SkillDrift - Time-Based Skill Drift Evidence
Role:
Time-Based Skill Drift and Pipeline Integration
Work completed:
1. Extended the regional analysis toward time-based skill analysis.
2. Identified that one collection date can show current demand
but cannot determine whether a skill is rising or declining.
3. Introduced dated snapshots of regional skill-demand percentages.
4. Generated the first genuine baseline snapshot:
skill_snapshot_2026-10-15.csv
5. Developed 06_skill_drift.py to:
- identify dated snapshots,
- compare different collection dates,
- calculate percentage-point changes,
- classify skills as Rising, Stable or Declining.
6. Current testing contains only one genuine snapshot.
The system correctly reports "NOT ENOUGH DATA YET"
instead of generating an unsupported trend.
7. Worked on integrating the snapshot workflow with the
regional analysis pipeline.
Main learning:
Temporal analysis requires genuine observations from multiple
dates. Insufficient data should be reported rather than used
to generate a false trend.
