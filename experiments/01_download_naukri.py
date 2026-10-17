from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


# Paste the Naukri search-result URL copied from Chrome here.
url = "https://www.naukri.com/data-engineering-jobs-in-mumbai?k=data%20engineering&l=mumbai"


request = Request(
    url,
    headers={
        "User-Agent": "SkillDrift-CS699-Academic-Project/0.1"
    }
)


try:
    response = urlopen(request, timeout=20)

    html = response.read().decode(
        "utf-8",
        errors="ignore"
    )

    print("--------------------------------")
    print("NAUKRI ACCESS TEST")
    print("--------------------------------")

    print("HTTP Status:")
    print(response.status)

    print()

    print("HTML characters downloaded:")
    print(len(html))

    print()

    print("Content type:")
    print(response.headers.get("Content-Type"))

    print()

    print("First 500 characters:")
    print(html[:500])


    with open(
        "naukri_page.html",
        "w",
        encoding="utf-8"
    ) as file:
        file.write(html)


    print()
    print("HTML saved as:")
    print("naukri_page.html")


except HTTPError as error:

    print("--------------------------------")
    print("HTTP ERROR")
    print("--------------------------------")

    print("Status code:")
    print(error.code)

    print("Message:")
    print(error.reason)


except URLError as error:

    print("--------------------------------")
    print("CONNECTION ERROR")
    print("--------------------------------")

    print(error.reason)


except Exception as error:

    print("--------------------------------")
    print("OTHER ERROR")
    print("--------------------------------")

    print(error)