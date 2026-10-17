(() => {

    console.log("=== SkillDrift Naukri Exporter ===");

    const cards = [...document.querySelectorAll(".cust-job-tuple")];

    console.log("Job cards found:", cards.length);

    if (cards.length === 0) {
        console.log("STOP: No job cards found.");
        return;
    }

    const jobs = cards.map(card => {

        const link =
            card.querySelector('a[href*="/job-listings-"]');

        const skills =
            [...card.querySelectorAll(".tags-gt .tag-li")]
            .map(el => el.innerText.trim())
            .filter(Boolean);

        return {
            title:
                card.querySelector(".title")
                ?.innerText.trim() || "",

            company:
                card.querySelector(".comp-name")
                ?.innerText.trim() || "",

            experience:
                card.querySelector(".expwdth")
                ?.innerText.trim() || "",

            salary:
                card.querySelector(".sal-wrap")
                ?.innerText.trim() || "",

            location:
                card.querySelector(".locWdth")
                ?.innerText.trim() || "",

            description:
                card.querySelector(".job-desc")
                ?.innerText.trim() || "",

            posted:
                card.querySelector(".job-post-day")
                ?.innerText.trim() || "",

            skills:
                skills.join(", "),

            url:
                link?.href || ""
        };
    });


    // Remove duplicate jobs
    const uniqueJobs = [
        ...new Map(
            jobs.map(job => [
                job.url || job.title + job.company,
                job
            ])
        ).values()
    ];


    // -------- CITY DETECTION --------

    const params =
        new URLSearchParams(window.location.search);

    let city = params.get("l");


    // If URL parameter "l" is missing,
    // read city from URL path.
    if (!city) {

        const match =
            window.location.pathname.match(
                /jobs-in-([^/?]+)/
            );

        if (match) {
            city = match[1];
        }
    }


    // Final fallback
    if (!city) {
        city = "unknown";
    }


    city = city
        .toLowerCase()
        .replaceAll(" ", "_")
        .replaceAll("-", "_");


    // -------- CHECK DATA --------

    console.log("City detected:", city);
    console.log("Jobs extracted:", uniqueJobs.length);

    console.log("First job:");
    console.log(uniqueJobs[0]);


    // -------- CSV --------

    const headers = [
        "title",
        "company",
        "experience",
        "salary",
        "location",
        "description",
        "posted",
        "skills",
        "url"
    ];


    const escapeCSV = value => {

        const text =
            String(value ?? "");

        return '"' +
            text.replaceAll('"', '""') +
            '"';
    };


    const csvRows = [

        headers.join(","),

        ...uniqueJobs.map(job =>
            headers
                .map(key =>
                    escapeCSV(job[key])
                )
                .join(",")
        )

    ];


    const csv =
        csvRows.join("\n");


    const today =
        new Date()
            .toISOString()
            .slice(0, 10);


    const filename =
        `naukri_data_engineering_${city}_${today}.csv`;


    const blob =
        new Blob(
            ["\uFEFF" + csv],
            {
                type:
                    "text/csv;charset=utf-8;"
            }
        );


    const downloadLink =
        document.createElement("a");


    downloadLink.href =
        URL.createObjectURL(blob);

    downloadLink.download =
        filename;


    document.body.appendChild(
        downloadLink
    );

    downloadLink.click();

    downloadLink.remove();


    setTimeout(() => {
        URL.revokeObjectURL(
            downloadLink.href
        );
    }, 1000);


    console.log(
        "CSV downloaded:",
        filename
    );

})();