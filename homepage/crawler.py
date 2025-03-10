import time
import requests, re, random, threading, concurrent.futures
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
from typing import Callable, Set
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET


user_agents = [
    # Chrome
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",

    # Firefox
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0",

    # Edge
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",

    # Safari
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Version/17.0 Safari/537.36",

    # Mobile (Android & iOS)
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/537.36"
]

def get_random_user_agent():
    return random.choice(user_agents)

class WebCrawler:
    
    def __init__(self, max_workers=5, depth_limit=5, is_nice_bot = True, user_agent="JobHunterCrawler"):
        """
        Args:
            max_workers (int, optional): The number of concurrent threads to run at once. Defaults to 5.
            depth_limit (int, optional): The maximum search depth. Defaults to 5.
            is_nice_bot (bool, optional): Whether the crawler respects the websites robot.txt or not. Defaults to True.
            user_agent (str, optional): What User-Agent to provide if being nice. Defaults to "JobHunterCrawler".
        """
        self.visited_urls = set()
        self.lock = threading.Lock()
        self.max_workers = max_workers
        self.depth_limit = depth_limit
        self.is_nice_bot = is_nice_bot
        self.user_agent = user_agent
        self.robots_parsers = {}  # Cache for robots.txt rules

    def get_robots_parser(self, base_url: str) -> RobotFileParser | None:
        """Fetch and parse the site's robots.txt file."""
        domain = urlparse(base_url).netloc
        if domain in self.robots_parsers:
            return self.robots_parsers[domain]  # Return cached parser

        robots_url = urljoin(base_url, "/robots.txt")
        parser = RobotFileParser()
        try:
            response = requests.get(robots_url)
            response.raise_for_status()
            response.encoding = 'utf-8'
            parser.parse(response.text.splitlines())
            self.robots_parsers[domain] = parser  # Cache the parser
        except requests.exceptions.RequestException as e:
            print(f"Error fetching robots.txt for {base_url}: {e}")
            return None
        return parser
    
    def has_sitemap(self, parser: RobotFileParser):
        return len(parser.site_maps()) > 0

    def get_urls_from_sitemap(self, sitemap_url):
        response = requests.get(sitemap_url)
        if response.status_code != 200:
            return
        root = ET.fromstring(response.content)
        namespaces = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        urlset = root.findall(".//ns:url/ns:loc", namespaces)
        if not urlset:
            sitemaps = root.findall(".//ns:sitemap/ns:loc", namespaces)
            if not sitemaps: return
            return self.get_urls_from_sitemap(sitemaps[0].text)
        return [url.text for url in urlset]

    def is_allowed(self, url: str) -> bool:
        """Check if the URL is allowed based on robots.txt rules."""
        parser = self.get_robots_parser(url)
        if parser:
            return parser.can_fetch(self.user_agent, url)
        return True  # If no robots.txt, assume allowed

    def normalize_url(self, url: str) -> str:
        """Normalize URL by removing fragments."""
        parsed_url = urlparse(url)
        return f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"

    def crawl(
            self, 
            base_url: str, 
            fltr: Callable[[str], bool]=lambda a: True, 
            depth=0, 
            url=None):
        """ Multi-threaded web crawler. """
        if url is None:
            url = base_url

        with self.lock:
            if url in self.visited_urls:
                return
            self.visited_urls.add(url)

        if not self.is_allowed(url) and self.is_nice_bot:
            print(f"Blocked by robots.txt: {url}")
            return

        try:
            response = requests.get(url, headers={"User-Agent": get_random_user_agent() if not self.is_nice_bot else self.user_agent}, timeout=5)
            response.encoding = response.apparent_encoding
            if response.status_code != 200:
                return
            soup = BeautifulSoup(response.content, "html.parser")
        except:
            return

        links = set()
        for link in soup.find_all("a", href=True):
            link = self.normalize_url(urljoin(base_url, link["href"]))
            if link not in self.visited_urls and fltr(link):
                links.add(link)

        parser = self.get_robots_parser(base_url)
        parser.site_maps()
        if parser and self.is_nice_bot:
            crawl_delay = parser.crawl_delay(self.user_agent)
            if crawl_delay:
                time.sleep(crawl_delay) 

        # Use multithreading for recursive crawling
        if depth < self.depth_limit:
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {executor.submit(self.crawl, base_url, fltr, depth + 1, link) for link in links}
                concurrent.futures.wait(futures)  # Wait for all tasks to complete

    def start(self, base_url: str, fltr=lambda a: True) -> Set[str]:
        """ Start the crawling process and return visited URLs. """
        parser = self.get_robots_parser(base_url)
        if parser and self.has_sitemap(parser):
            print("Found sitemap! Parsing urls...")
            sitemap = parser.site_maps()[0]
            urls = self.get_urls_from_sitemap(sitemap)
            if urls:
                self.visited_urls = [url for url in urls if fltr(url)]
        
        if not self.visited_urls:
            print("No urls from sitemap, crawling...")
            self.crawl(base_url, fltr)
        return self.visited_urls
    
# a = WebCrawler(depth_limit=5)
# print(a.start("https://www.equinor.com/", filtr))
