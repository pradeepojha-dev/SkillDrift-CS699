from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError

import json


base_url = "https://www.naukri.com/jobapi/v3/search"


parameters = {
    "noOfResults": 20,
    "urlType": "search_by_key_loc",
    "searchType": "adv",
    "location": "mumbai",
    "keyword": "data engineering",
    "pageNo": 1,
    "k": "data engineering",
    "l": "mumbai"
}


query_string = urlencode(parameters)

url = base_url + "?" + query_string


print("Request URL:")
print(url)
print()


request = Request(
    url,
    headers={
        "User-Agent": "SkillDrift-CS699-Academic-Project/0.1"
    }
)


try:

    response = urlopen(request, timeout=20)

    raw_data = response.read().decode(
        "utf-8",
        errors="ignore"
    )


    print("HTTP Status:")
    print(response.status)

    print()

    print("Characters downloaded:")
    print(len(raw_data))

    print()


    data = json.loads(raw_data)


    print("JSON successfully converted to Python.")

    print()

    print("Total jobs reported:")
    print(data.get("noOfJobs"))

    print()


    jobs = data.get("jobDetails", [])


    print("Jobs received on this page:")
    print(len(jobs))


    with open(
        "naukri_jobs_raw.json",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )


    print()
    print("Saved as:")
    print("naukri_jobs_raw.json")


except HTTPError as error:

    print("HTTP ERROR")

    print(error.code)
    print(error.reason)


except URLError as error:

    print("CONNECTION ERROR")

    print(error.reason)


except Exception as error:

    print("OTHER ERROR")

    print(error)