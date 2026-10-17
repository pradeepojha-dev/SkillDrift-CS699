Abhay Patle - 26M0840
SkillDrift - Skill Analysis Evidence

Role:
Data Cleaning, Skill Analysis and Visualisation

Work completed:

1. Processed Data Engineering job datasets collected for Mumbai, Pune and Bengaluru.

2. Initial skill analysis showed problems such as:
   - repeated skill occurrences,
   - uppercase/lowercase variations,
   - generic terms such as data, senior, data engineer and data engineering being counted as useful skills.

3. Improved the processing by:
   - converting skill names to lowercase,
   - filtering obvious noise terms,
   - counting each skill only once per job.

4. Changed the analysis metric from raw skill frequency to the percentage of jobs mentioning each skill.

5. Compared regional demand for selected skills including:
   Python, SQL, PySpark, Snowflake, AWS, Airflow,
   Azure Data Factory, GCP, ETL and Data Pipelines.

6. Generated:
   - outputs/regional_skill_comparison.csv
   - outputs/regional_skill_comparison.png

7. Updated the script to work with the shared team repository structure:
   - input datasets are read from data/raw/
   - analysis outputs are saved into outputs/

8. Verified the complete analysis by running:
   python analysis\05_compare_skills.py

   The program completed successfully and produced the regional comparison outputs.

Main learning:
Raw frequency alone is not sufficient for meaningful job-market analysis.
Data cleaning, normalization, duplicate handling and the correct demand metric
are necessary before comparing skill demand across regions.