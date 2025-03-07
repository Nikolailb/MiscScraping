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
