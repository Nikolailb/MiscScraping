import requests, re, concurrent.futures
from typing import Any, Callable, Dict, Iterable, List, Set
from bs4 import BeautifulSoup
from collections import defaultdict
from urllib.parse import urljoin
from transformers import pipeline, BartTokenizer

from crawler import WebCrawler

IRRELEVANT_TAGS = ["script", "style", "footer", "header", "nav", "aside", "form", "button", "svg"]
IGNORED_ASSETS = [
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', 
    '.svg', '.css', '.js', '.mp4', '.mp3', '.avi', 
    '.mov', '.webm', '.pdf', '.woff', '.woff2', '.ttf'
]
KEYWORDS_EN = ["about", "news", "team", "contact", "vacancie", "career", "event", "blog"]
KEYWORDS_NO = ["om oss", "nyheter", "kontakt", "stillinger", "karriere"]
KEYWORDS = KEYWORDS_EN + KEYWORDS_NO
def filtr(value: str):
    value = value.lower()
    return any(keyword in value for keyword in KEYWORDS)

summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
tokenizer = BartTokenizer.from_pretrained('facebook/bart-large-cnn')

def summarize_text(text):    
    if not text: return ""
    inputs = tokenizer(text, return_tensors='pt', truncation=True, max_length=1024)
    if len(inputs['input_ids'][0]) < 512:
        return text
    text = tokenizer.decode(inputs['input_ids'][0], skip_special_tokens=True)
    summary = summarizer(text, max_length=256, min_length=50, do_sample=False)
    return summary[0]['summary_text']

def extract_text_from_html(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    
    for tag in soup(IRRELEVANT_TAGS):
        tag.decompose()
    
    for repeated_content in soup.find_all(["div", "span", "section"]):
        if any('advertis' in c for c in repeated_content.get('class', [])):
            repeated_content.decompose()
    
    text = soup.get_text(strip=True, separator=" ")
    text = re.sub(r'\n+', '\n', text).strip()
    
    return text

def get_html_content(url):
    response = requests.get(url)
    if response.status_code != 200: return None
    return response.content

def find_relevant_links(soup, keywords=KEYWORDS):
    """Simplified crawler, just looks at the homepage to find relevant links"""
    links = defaultdict(set)
    for link in soup.find_all("a", href=True):
        for keyword in keywords:
            if keyword in link["href"].lower():
                links[keyword].add(link["href"])
    return links

def is_ignored_asset(url: str):
    """Check if the URL points to a static asset based on its extension."""
    return any(url.lower().endswith(ext) for ext in IGNORED_ASSETS)

def categorize_links(
        links: Iterable[str], 
        max_count: int = 4, 
        ordering: Callable[[str], Any] = len, 
        categories: Iterable[str] = KEYWORDS) -> Dict[str, List[str]]:
    """Categorizes the provided links based on a set of categories. Each category has a max count,
      and what url to cut is determined by the ordering.

    Args:
        links (Iterable): _description_
        max_count (int, optional): _description_. Defaults to 4.
        ordering (Callable[[str], Any], optional): Importance ordering of the links. Defaults to len.
        categories (Iterable[str], optional): The categories to sort the links into. Defaults to KEYWORDS.

    Returns:
        Dict[str, List[str]]: The categorized strings.
    """
    categorized_links  = {}
    visited_links = set()
    for category in categories:
        filtered_links = [
            link for link in links 
            if category in link and link not in visited_links and not is_ignored_asset(link)
        ]
        categorized_links[category] = sorted(filtered_links, key=ordering)[:max_count]
        visited_links.update(categorized_links[category])
    return categorized_links 

handlers: dict[str, Callable[[bytes], str]] = {
    
}

def process_link(
    link: str, 
    url: str, 
    category: str, 
    handlers: Dict[str, Callable], 
    verbose: bool, 
    checked_links: Set[str], 
    text_collections: Set[str]
):
    """Process a single link: fetch content, extract text, and handle errors."""
    full_link = urljoin(url, link)
    if full_link in checked_links:
        return
    
    if verbose:
        print("Checking out:", link)
    
    html_content = get_html_content(full_link)
    if html_content is None:
        print("Failed to fetch website:", full_link)
    else:
        handler = handlers.get(category, extract_text_from_html)
        try:
            text_collections.add(handler(html_content))
        except Exception as e:
            print(f"Error processing {full_link}: {e}")
    
    checked_links.add(full_link)

def get_company_information(url, verbose = False, max_workers = 5) -> List[str]:
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    if response.status_code != 200:
        raise requests.HTTPError("Failed to fetch website")
    
    crawler = WebCrawler(max_workers=5, depth_limit=4)
    links = categorize_links(crawler.start(url, filtr))

    checked_links = set() 
    text_collections = set()
    text_collections.add(extract_text_from_html(response.content))

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit tasks to the thread pool for each link in all categories
        futures = []
        for category in links:
            for link in links[category]:
                futures.append(executor.submit(
                    process_link, link, url, category, handlers, verbose, checked_links, text_collections
                ))

        # Wait for all tasks to complete
        concurrent.futures.wait(futures)
    return text_collections

test_url = "https://www.kongsberg.com/"
with open("summary.txt", "w", encoding='utf-8') as file:
    information = get_company_information(test_url, verbose=True)
    print("Found information from: ", test_url)
    file.write("\n".join(summarize_text(text) for text in information))