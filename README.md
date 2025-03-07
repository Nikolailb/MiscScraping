# Collection of random scraping scripts

This repository is a host for non-connected scraping scripts. It is meant to be an example for both me, and others who want to do some scraping on their own.

## Current scripts

- [kodejobb.py](kodejobb.py) for [kodejobb.no/stillinger](https://kodejobb.no/stillinger)
  - This script scrapes the currently available jobs from Kodejobb, and formats them nicely such that they could be sent elsewhere using json.
  - Example format:

    ```json
        {
            "job_title": "Fullstackutvikler - prosjektstilling",
            "company": "NTB",
            "short_description": "Skriv kode som graver etter nyheter – bli med og bygge KI-applikasjoner for automatisert journalistikk",
            "locations": [
                "Oslo"
            ],
            "deadline": "2025-04-05T22:00:00+00:00",
            "url": "https://kodejobb.no/stillinger/ntb/3c4d2b8f-2cb9-4a12-8fc9-0aea031caadc",
            "contact": {
                "name": "name here",
                "email": "email@email.email",
                "tlf": "00000000"
            },
            "long_description": "long desc here"
        },
    ```

  - Some fields, such as contact, might be missing if no such information can be found.
- [homepage.py](homepage.py) for any company homepage
  - This script is meant to scrape and collect any usefull information it can find on a company's website. Is is also trying to summarize this information
  - Since the data from this is not consistent, it is meant to be tossed into a LLM that can summarize all the finding for you
    > **Prompt:**
    >
    > You are now a sales representative for a IT consultancy firm. Your job is to figure out if a company is suited for any of your consultants, find people of interest in the firm, find available job postings and do whatever is needed to get people into jobs. In order to do this, you want to summarize the information found cleanly, such that your coworkers can easily sort through it and find fitting consultants for possible jobs and important contacts. It is also especially important for you to find out what kind of technology the company works with. This can be things like the tech stack, but also more general this like "They work in AI", but more specific is better.
  - By passing the above prompt to chatgpt, before copy pasting the data collected by the script (in `summary.txt` by default), you get some decent results.
