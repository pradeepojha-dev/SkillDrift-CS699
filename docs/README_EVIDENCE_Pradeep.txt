PRadeep Ojha - 26M0817
SkillDrift - Data Collection and Scraping Evidence

Role:
Job Data Collection and Scraping

Work completed:

1. Initial static HTML experiment
   File: experiments/01_download_naukri.py

   The first approach used Python urllib to download the Naukri
   search-result page. The HTTP request succeeded and the downloaded
   page was saved as naukri_page.html.

   However, the actual job cards were not present in the initial HTML
   because the search results were dynamically rendered in the browser.

2. Job data / JSON investigation
   File: experiments/03_naukri_json_test.py

   Browser Developer Tools and Network requests were studied to
   understand how Naukri was loading the job information.

3. Direct request experiment
   File: experiments/04_exact_naukri_request.py

   Direct access to the identified job-data request was tested.
   The initial request failed because required request headers were
   missing. After identifying the required Appid and Systemid headers,
   the request reached the service but required reCAPTCHA.

   No attempt was made to bypass reCAPTCHA or other access restrictions.

4. Improved data collection approach
   File: scraper/naukri_exporter.js

   The approach was changed to browser-side DOM extraction. The script
   reads only job cards already rendered normally on the Naukri page.

   It extracts:
   - Job title
   - Company
   - Experience
   - Salary
   - Location
   - Description
   - Posting time
   - Skills
   - Job URL

   It also removes duplicate jobs, detects the selected city and
   downloads the extracted data as a dated CSV file.

5. Data generated

   Initial exports:
   - naukri_data_engineering_mumbai.csv
   - naukri_data_engineering_pune.csv
   - naukri_data_engineering_bengaluru.csv

   Improved dated exports:
   - naukri_data_engineering_mumbai_2026-10-15.csv
   - naukri_data_engineering_pune_2026-10-15.csv
   - naukri_data_engineering_bengaluru_2026-10-15.csv

Main learning:
The experiments helped in understanding the difference between static
HTML and dynamically rendered web content, browser Network inspection,
DOM-based extraction, and changing the implementation when direct
programmatic access was restricted.