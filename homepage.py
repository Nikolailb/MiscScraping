import os, requests, re, nltk
from typing import Callable, List
from bs4 import BeautifulSoup
from collections import defaultdict
from urllib.parse import urljoin
from transformers import pipeline, BartTokenizer
from nltk.tokenize import sent_tokenize

IRRELEVANT_TAGS = ["script", "style", "footer", "header", "nav", "aside", "form", "button", "svg"]
KEYWORDS_EN = ["about", "news", "team", "contact", "vacancie", "career", "event", "blog"]
KEYWORDS_NO = ["om oss", "nyheter", "kontakt", "stillinger", "karriere"]
KEYWORDS = KEYWORDS_EN + KEYWORDS_NO

summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
tokenizer = BartTokenizer.from_pretrained('facebook/bart-large-cnn')

def preprocess_text(text):
    sentences = sent_tokenize(text)
    return sentences

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
    links = defaultdict(set)
    for link in soup.find_all("a", href=True):
        for keyword in keywords:
            if keyword in link["href"].lower():
                links[keyword].add(link["href"])
    return links


handlers: dict[str, Callable[[bytes], str]] = {
    
}

def get_company_information(url, verbose = False) -> List[str]:
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    if response.status_code != 200:
        raise requests.HTTPError("Failed to fetch website")
    
    soup = BeautifulSoup(response.content, "html.parser")
    links = find_relevant_links(soup)
    text_collections = set()
    text_collections.add(extract_text_from_html(response.content))
    checked_links = []
    for category in links:
        for link in sorted(links[category], key=len):
            full_link = urljoin(url, link)
            if full_link in checked_links: continue
            if verbose:
                print("Checking out: ", link)
            html_content = get_html_content(full_link)
            if html_content is None:
                print("Failed to fetch website:", full_link)
            else:
                handler = handlers.get(category, extract_text_from_html)
                text_collections.add(handler(html_content))
            checked_links.append(full_link)
    return text_collections

test_url = "https://www.kongsberg.com/"
with open("summary.txt", "w", encoding='utf-8') as file:
    information = get_company_information(test_url, verbose=True)
    
    file.write("\n".join(summarize_text(text) for text in information))