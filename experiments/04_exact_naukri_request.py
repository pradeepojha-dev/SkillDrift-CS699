from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

import json


url = (
    "https://www.naukri.com/jobapi/v3/search"
    "?noOfResults=20"
    "&urlType=search_by_key_loc"
    "&searchType=adv"
    "&location=mumbai"
    "&keyword=data%20engineering"
    "&pageNo=1"
    "&k=data%20engineering"
    "&l=mumbai"
    "&nignbevent_src=jobsearchDeskGNB"
    "&seoKey=data-engineering-jobs-in-mumbai"
    "&src=jobsearchDesk"
    "&latLong="
)


request = Request(
    url,
    headers={
    "User-Agent": "SkillDrift-CS699-Academic-Project/0.1",
    "Accept": "application/json",
    "Appid": "109",
    "Systemid": "Naukri"
}
)


try:

    response = urlopen(request, timeout=20)

    raw_data = response.read().decode(
        "utf-8",
        errors="ignore"
    )

    print("--------------------------------")
    print("NAUKRI JSON TEST")
    print("--------------------------------")

    print("HTTP Status:")
    print(response.status)

    print()

    print("Characters downloaded:")
    print(len(raw_data))

    print()

    data = json.loads(raw_data)

    print("JSON conversion: SUCCESS")

    print()

    print("Total jobs reported:")
    print(data.get("noOfJobs"))

    jobs = data.get("jobDetails", [])

    print()

    print("Jobs received:")
    print(len(jobs))


except HTTPError as error:

    print("--------------------------------")
    print("HTTP ERROR")
    print("--------------------------------")

    print("Status:")
    print(error.code)

    print()

    print("Reason:")
    print(error.reason)

    print()

    print("Server response:")

    try:
        error_body = error.read().decode(
            "utf-8",
            errors="ignore"
        )

        print(error_body)

    except:
        print("Could not read error response.")


except URLError as error:

    print("CONNECTION ERROR")
    print(error.reason)


except Exception as error:

    print("OTHER ERROR")
    print(error)