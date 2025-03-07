import requests
from bs4 import BeautifulSoup
import time
import json
import random
from models import Perfume
from dotenv import load_dotenv
import os
import re

load_dotenv()

class PerfumeDataScraper:
    # Rotating User-Agent Pool to Avoid Detection
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 OPR/104.0.0.0",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/120.0.6099.119 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (iPad; CPU OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Vivaldi/6.2.3105.58",
    ]


    def __init__(self):
        self.base_url = os.getenv("BASE_URL")

        # Load all perfume URLs from the file
        with open("../../data/website_perfumes_by_designer.json", "r") as f:
            self.perfumes_by_designer = json.load(f)

        # Load already scraped perfumes to avoid duplicates
        self.scraped_perfumes = self.load_scraped_perfumes()

        print(f"Starting to scrape perfume data... Already scraped: {len(self.scraped_perfumes)} perfumes.")

    def get_headers(self):
        """
        Generate random headers with different user agents to avoid detection.
        Returns:
            dict: Headers with a randomly selected user agent.
        """
        return {"User-Agent": random.choice(self.USER_AGENTS)}

    def load_scraped_perfumes(self):
        """Load previously scraped perfume data to avoid duplicate scraping."""
        try:
            with open("../../data/website_all_perfumes.json", "r") as f:
                return {p['url'] for p in json.load(f)}
        except (FileNotFoundError, json.JSONDecodeError):
            return set()  # Return an empty set if file doesn't exist or is empty

    def remove_leading_digits(self, text: str) -> str:
        """
        Removes any leading digits (and optional whitespace) from the start of `text`.
        Example: '201Good for everyday wear' -> 'Good for everyday wear'
        """
        return re.sub(r'^[0-9]+\s*', '', text).strip()

    def save_progress(self, all_perfumes_data):
        """Save progress after scraping each perfume, converting non-serializable objects."""
        
        # Convert all Perfume objects to dictionaries before saving
        perfumes_dict = []
        for perfume in all_perfumes_data:
            # Handle both Perfume objects and dictionaries/strings
            if hasattr(perfume, '__dict__'):
                # It's a Perfume object
                perfume_dict = {
                    **perfume.__dict__,
                    "notes": perfume.notes
                }
            elif isinstance(perfume, dict):
                # It's already a dictionary
                perfume_dict = perfume
            else:
                # Skip if it's a string or other non-compatible type
                continue
                
            perfumes_dict.append(perfume_dict)

        with open("../../data/website_all_perfumes.json", "w") as f:
            json.dump(perfumes_dict, f, indent=2)
        
        print(f"✅ Progress saved! {len(perfumes_dict)} perfumes stored.")

    def request_with_retry(self, url, max_retries=10):
        """Handles rate limits (429 errors), retries intelligently, and logs failures."""
        attempt = 0
        base_wait_time = 20
        max_wait_time = 120

        while attempt < max_retries:
            try:
                response = requests.get(url, headers=self.get_headers(), timeout=15)

                if response.status_code == 200:
                    return response

                elif response.status_code == 429:  # Rate limit handling
                    wait_time = min(base_wait_time * (2 ** attempt), max_wait_time)
                    print(f"⚠️ Rate limited! Waiting {wait_time} seconds before retrying...")
                    time.sleep(wait_time)
                    attempt += 1

                else:
                    with open("error.log", "a") as log_file:
                        log_file.write(f"❌ Failed to fetch {url} - Status {response.status_code}\n")
                    print(f"❌ Error {response.status_code} for {url}. Logging and skipping.")
                    return None  # Move to next URL

            except requests.exceptions.RequestException as e:
                with open("error.log", "a") as log_file:
                    log_file.write(f"❌ Network error: {str(e)} for {url}. Retrying...\n")
                print(f"⚠️ Network error: {str(e)}. Retrying after 60 seconds...")
                time.sleep(60)  # Avoid infinite failure loops

        # If we reach max_retries, log and move on
        with open("failed_urls.log", "a") as log_file:
            log_file.write(f"❌ Max retries reached for {url}. Skipping.\n")
        print(f"🚨 Max retries reached for {url}, skipping.")
        return None

    def scrape_perfume_data(self, url: str) -> Perfume:
        """Scrapes perfume data, handling errors and missing fields."""
        if url in self.scraped_perfumes:
            print(f"✅ Skipping already scraped perfume: {url}")
            return None  # Skip if already scraped

        response = self.request_with_retry(url)
        if not response:
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        missing_fields = []

        try:
            brand = url.split("/")[-2].replace("-", " ").title()

            name_tag = soup.select_one("h1[itemprop='name']")
            name = name_tag.text.strip() if name_tag else "Unknown"
            if not name_tag:
                missing_fields.append("name")

            brand_tag = soup.select_one("p[itemprop='brand'] a span[itemprop='name']")
            brand = brand_tag.text.strip() if brand_tag else "Unknown"
            if not brand_tag:
                missing_fields.append("brand")

            image_tag = soup.select_one("img[itemprop='image']")
            photo_url = image_tag["src"] if image_tag else None
            if not image_tag:
                missing_fields.append("photo_url")

            # Extract Accords
            accords = []
            for accord_tag in soup.select(".accord-box .accord-bar"):
                try:
                    accord_name = accord_tag.text.strip()
                    accord_width = accord_tag["style"].split("width:")[-1].split("%")[0]
                    accords.append({accord_name: float(accord_width)})
                except:
                    missing_fields.append(f"accords: {accord_name}")

            # Extract Notes
            all_notes = set()

            # 1) Find all <pyramid-level> nodes that have a [notes] attribute, e.g. notes="ingredients" or notes="top"
            pyramid_levels = soup.select('pyramid-level[notes]')

            for level in pyramid_levels:
                # 2) For each anchor (<a>) inside, get the text from next_sibling 
                # (because the note text typically appears after the <a>).
                for anchor in level.select('a'):
                    note_text = anchor.next_sibling
                    if note_text:
                        note_text = note_text.strip()
                        if note_text:
                            all_notes.add(note_text)

            notes_list = list(all_notes)

            smells_like = [perfume.text.strip() for perfume in soup.select("similar-perfumes .carousel-cell a span.brand")]

            reviews = []
            for review_box in soup.select(".fragrance-review-box"):
                body_el = review_box.select_one('[itemprop="reviewBody"]')
                if body_el:
                    reviews.append(body_el.text.strip())

            pros_container = None
            cons_container = None

            for column in soup.select('.grid-x .cell.small-6'):
                header_el = column.select_one('h4.header')
                if header_el and 'Pros' in header_el.get_text():
                    pros_container = column
                elif header_el and 'Cons' in header_el.get_text():
                    cons_container = column
            pros = []
            cons = []

            if pros_container:
                for pro_div in pros_container.select('.cell.small-12'):
                    line = pro_div.get_text(strip=True)
                    # Clean up leading digits
                    line = self.remove_leading_digits(line)
                    if line:
                        pros.append(line)

            if cons_container:
                for con_div in cons_container.select('.cell.small-12'):
                    line = con_div.get_text(strip=True)
                    # Clean up leading digits
                    line = self.remove_leading_digits(line)
                    if line:
                        cons.append(line)

            # Construct Perfume object
            perfume_data = Perfume(
                url=url, name=name, brand=brand, photo_url=photo_url, accords=accords,
                notes=notes_list, smells_like=smells_like,
                missing_fields=missing_fields, reviews=reviews, pros=pros, cons=cons
            )

            # Log missing fields
            if missing_fields:
                with open("missing_fields.log", "a") as log_file:
                    log_file.write(f"URL: {url} - Missing: {', '.join(missing_fields)}\n")

            return perfume_data

        except Exception as e:
            with open("error.log", "a") as log_file:
                log_file.write(f"❌ Error parsing {url}: {str(e)}\n")
            print(f"⚠️ Error parsing {url}, logged.")
            return None
    def scrape_all_perfumes(self):
        """Scrapes only 2 perfumes for testing purposes and saves progress."""
        all_perfumes_data = list(self.scraped_perfumes)  # Load existing data
        count = 0  # Track the number of perfumes scraped

        for designer_data in self.perfumes_by_designer:
            for perfume_url in designer_data["perfumes"]:
                perfume_data = self.scrape_perfume_data(perfume_url)
                if perfume_data:
                    all_perfumes_data.append(perfume_data)
                    self.save_progress(all_perfumes_data)  # Save after each perfume
                    count += 1

        
        print(f"✅ Finished scraping {count} perfumes!")

if __name__ == "__main__":
    scraper = PerfumeDataScraper()
    scraper.scrape_all_perfumes()