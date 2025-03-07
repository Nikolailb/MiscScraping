from urllib.parse import urljoin
import requests, json
from bs4 import BeautifulSoup
from datetime import datetime
import pytz

base_url = "https://kodejobb.no/stillinger"
def get_openings():
    """Finds the available openings at kodejobb.no and organizes the data neatly in a dictionary.
        
    Raises:
        requests.HTTPError: If not able to retrieve the data.

    Returns:
        list[dict]: A list of dicts representing the available openings.
    """
    response = requests.get(base_url)
    if response.status_code != 200:
        raise requests.HTTPError("Failed to access the site!")
    soup = BeautifulSoup(response.content, 'html.parser')
    for tag in soup(["svg", "script"]):
        tag.decompose()
    job_list = soup.find(id="job-list").find_all("a")
    job_objects = []
    for job in job_list:
        title = job.find("div", class_="job-title-from-customer").get_text(strip=True)
        company = job.find("div", class_="job-company-name").get_text(strip=True)
        short_description = job.find("div", class_="job-title").get_text(strip=True)
        locations = list({span.get_text(strip=True) for span in job.select(".job-location span") if span.get_text(strip=True)})
        deadline = job.select_one(".job-due-date").get_text(strip=True)
        job_objects.append({
            "job_title": title,
            "company": company,
            "short_description": short_description,
            "locations": locations,
            "deadline": deadline,
            "url": urljoin(base_url, job.get("href", ""))
        })
    return job_objects

def get_job_details(job: dict):
    if not job.get("url", None):
        raise ValueError("Missing url for job!")
    
    response = requests.get(job["url"])
    if response.status_code != 200:
        raise requests.HTTPError("Failed to access the site!")
    
    soup = BeautifulSoup(response.content, 'html.parser')
    for tag in soup(["svg", "script"]):
        tag.decompose()
    
    new_job = {**job}
    
    aside = soup.find("aside", class_="job-aside")
    
    deadline = aside.select_one(".company-application").find("span", string=lambda x: "Frist" in x).parent.get_text(strip=True).replace("Frist:", "")
    if deadline:
        deadline = datetime.strptime(deadline, "%d.%m.%Y")
        local_tz = pytz.timezone('Europe/Oslo')
        localized_date = local_tz.localize(deadline)
        utc_date = localized_date.astimezone(pytz.utc)
        new_job["deadline"] = utc_date.isoformat()
    
    contact_html = aside.select_one(".company-contacts")
    if contact_html:
        contact_info = contact_html.find_all("a")
        email = [c.get("href", "") for c in contact_info if "mailto:" in c.get("href", "")]
        tlf = [c.get("href", "") for c in contact_info if "tel:" in c.get("href", "")]
        contact = {
            "name": contact_html.find("h4").get_text(strip=True),
            "email": email[0].replace("mailto:", "").strip() if len(email) > 0 else "",
            "tlf": tlf[0].replace("tel:", "").strip() if len(tlf) > 0 else "",
        }
        new_job["contact"] = contact
    
    long_description = soup.select_one(".job-content").find_all("div")
    if long_description:
        long_description = long_description[-1]
        new_job["long_description"] = long_description.get_text(strip=True)
    
    return new_job
    
with open('jobs.json', 'w', encoding='utf-8') as file:
    json.dump([get_job_details(job) for job in get_openings()], file, indent=4, ensure_ascii=False)