import requests
from bs4 import BeautifulSoup
import time
import json
import random
from models import Perfume, PerfumeNotes
from dotenv import load_dotenv
import os

load_dotenv()

class FragranceScraper:
    """
    A class for scraping fragrance data from a perfume website.
    Handles pagination, rate limiting, and data extraction.
    """
    BASE_URL = os.getenv("BASE_URL")    

    # Rotating User-Agent Pool to Avoid Detection
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    ]

    def __init__(self):
        """Initialize the scraper with empty data and starting position."""
        self.all_brands_data = []
        self.current_designer_index = 0
        self.current_designer_url = None

    def get_headers(self):
        """
        Generate random headers with different user agents to avoid detection.
        Returns:
            dict: Headers with a randomly selected user agent.
        """
        return {"User-Agent": random.choice(self.USER_AGENTS)}

    def request_with_retry(self, url, retries=3):
        """
        Make HTTP requests with retry logic and exponential backoff.
        
        Args:
            url (str): The URL to request.
            retries (int): Number of retry attempts.
            
        Returns:
            Response object or None if all retries fail.
        """
        for attempt in range(retries):
            response = requests.get(url, headers=self.get_headers())

            if response.status_code == 200:
                return response
            elif response.status_code == 429:
                wait_time = random.randint(20, 30)
                print(f"Rate limited! Waiting {wait_time} seconds before retrying...")
                time.sleep(wait_time)
                if attempt == retries - 1:  # If this was the last attempt
                    return None
            else:
                print(f"Failed to fetch {url} (Status: {response.status_code})")
                return None
        return None

    def save_progress(self):
        """
        Save current scraping progress to a JSON file.
        Allows resuming the scraping process later.
        """
        progress_data = {
            "all_brands_data": self.all_brands_data,
            "current_designer_index": self.current_designer_index,
            "current_designer_url": self.current_designer_url
        }
        with open("../../data/scraping_progress.json", "w") as f:
            json.dump(progress_data, f, indent=2)
        print(f"\nProgress saved! You can resume from designer index {self.current_designer_index}")
        print(f"Current designer URL: {self.current_designer_url}")
        print("To resume, run the script again and it will continue from where it left off.")

    def load_progress(self):
        """
        Load previously saved scraping progress.
        
        Returns:
            bool: True if progress was loaded, False otherwise.
        """
        try:
            with open("../../data/scraping_progress.json", "r") as f:
                progress_data = json.load(f)
                self.all_brands_data = progress_data["all_brands_data"]
                self.current_designer_index = progress_data["current_designer_index"]
                self.current_designer_url = progress_data["current_designer_url"]
                print(f"Resuming from designer index {self.current_designer_index}")
                print(f"Current designer URL: {self.current_designer_url}")
                return True
        except FileNotFoundError:
            return False

    def get_all_designer_links(self):
        """
        Scrape all designer/brand links from the main designers page.
        
        Returns:
            list: List of URLs for all perfume designers/brands.
        """
        response = self.request_with_retry(self.BASE_URL + "/designers/")
        if not response:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        designer_links = []

        for link in soup.select('a[href^="/designers/"]'):
            full_url = self.BASE_URL + link['href']
            if full_url not in designer_links and link['href'] != "":
                designer_links.append(full_url)

        print(f"Found {len(designer_links)} designer links")
        return designer_links

    def scrape_perfume_details(self, url):
        """
        Scrape all perfume links for a specific designer/brand.
        
        Args:
            url (str): URL of the designer's page.
            
        Returns:
            tuple: (designer_name, list_of_perfume_links)
        """
        response = self.request_with_retry(url)
        if not response:
            return None, []

        soup = BeautifulSoup(response.text, 'html.parser')
        perfume_links = []

        designer_name = url.split("/")[-1].replace(".html", "")

        # Find all perfume links for this designer
        for link in soup.select(f'a[href*="/{designer_name}/"]'):
            full_url = self.BASE_URL + link['href'] if link['href'].startswith('/') else link['href']

            if full_url not in perfume_links:
                perfume_links.append(full_url)

        print(f"Found {len(perfume_links)} perfume links for {designer_name}")
        time.sleep(random.randint(2, 7))  # Randomized delay (2-7 seconds)
        return designer_name, perfume_links

    def scrape_perfume_data(self, url: str) -> Perfume:
        """
        Scrapes detailed information about a specific perfume from its URL.
        
        Args:
            url (str): URL of the perfume page.
            
        Returns:
            Perfume: A Perfume model instance with the scraped data.
        """
        response = self.request_with_retry(url)
        if not response:
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        # Track missing fields
        missing_fields = []

        brand = url.split("/")[-2].replace("-", " ").title()
        
        # Extract Perfume Name
        name_tag = soup.select_one("h1[itemprop='name']")
        name = name_tag.text.strip() if name_tag else "Unknown"
        if not name_tag:
            missing_fields.append("name")

        # Extract Brand Name
        brand_tag = soup.select_one("p[itemprop='brand'] a span[itemprop='name']")
        brand = brand_tag.text.strip() if brand_tag else "Unknown"
        if not brand_tag:
            missing_fields.append("brand")

        # Extract Perfume Image
        image_tag = soup.select_one("img[itemprop='image']")
        photo_url = image_tag["src"] if image_tag else None
        if not image_tag:
            missing_fields.append("photo_url")

        # Extract Accords
        accords = []
        for accord_tag in soup.select(".accord-box .accord-bar"):
            accord_name = accord_tag.text.strip()
            accord_width = accord_tag["style"].split("width:")[-1].split("%")[0]  # Extract percentage
            try:
                accords.append({accord_name: float(accord_width)})
            except:
                missing_fields.append(f"accords: {accord_name}")

        if not accords:
            missing_fields.append("accords")

        # Extract Notes (Top, Middle, Base)
        notes = {"top": [], "middle": [], "base": []}
        
        pyramid_sections = {
            "top": "pyramid_top",
            "middle": "pyramid_middle",
            "base": "pyramid_base"
        }
        
        for note_type, class_name in pyramid_sections.items():
            notes_list = soup.select(f"div#{class_name} a")
            if notes_list:
                notes[note_type] = [note.text.strip() for note in notes_list]
            else:
                missing_fields.append(f"notes_{note_type}")

        perfume_notes = PerfumeNotes(**notes)

        # Extract Gender Description
        gender_tag = soup.select_one("h1[itemprop='name'] small")
        gender = gender_tag.text.strip() if gender_tag else "Unknown"
        if not gender_tag:
            missing_fields.append("gender")

        # Extract Longevity and Sillage Ratings
        longevity_tag = soup.select_one("longevity-rating p span")
        longevity = longevity_tag.text.strip() if longevity_tag else None
        if not longevity_tag:
            missing_fields.append("longevity")

        sillage_tag = soup.select_one("sillage-rating p span")
        sillage = sillage_tag.text.strip() if sillage_tag else None
        if not sillage_tag:
            missing_fields.append("sillage")

        # Extract Price Value Rating
        price_value_tag = soup.select_one("price-value-widget p span")
        price_value = price_value_tag.text.strip() if price_value_tag else None
        if not price_value_tag:
            missing_fields.append("price_value")

        # Extract "This perfume reminds me of" section
        smells_like = []
        for similar_perfume in soup.select("similar-perfumes .carousel-cell a span.brand"):
            smells_like.append(similar_perfume.text.strip())

        if not smells_like:
            missing_fields.append("smells_like")

        # Construct the Perfume object
        perfume_data = Perfume(
            url=url,
            name=name,
            brand=brand,
            photo_url=photo_url,
            accords=accords,
            notes=perfume_notes,
            smells_like=smells_like,
            gender=gender,
            longevity=longevity,
            sillage=sillage,
            price_value=price_value,
            missing_fields=missing_fields
        )

        # Log missing fields
        if missing_fields:
            with open("missing_fields.log", "a") as log_file:
                log_file.write(f"URL: {url} - Missing: {', '.join(missing_fields)}\n")

        return perfume_data

    def scrape_all_designers(self):
        """
        Main method to scrape all designers and their perfumes.
        Loads previous progress if available and saves progress regularly.
        """
        # Try to load previous progress
        if not self.load_progress():
            print("No previous progress found. Starting fresh.")

        # Step 2: Scrape Perfume Links for Each Designer
        with open("../../data/website_designer_links.txt", "r") as f:
            designer_links = f.readlines()
            for i in range(self.current_designer_index, len(designer_links)):
                link = designer_links[i].strip()
                self.current_designer_url = link
                self.current_designer_index = i
                
                try:
                    brand_name, perfume_links = self.scrape_perfume_details(link)
                    if perfume_links:
                        self.all_brands_data.append({"brand": brand_name, "perfumes": perfume_links})
                    
                    # Save progress after each successful designer
                    self.save_progress()
                    
                    print(f"Processed {i + 1}/{len(designer_links)} designers")
                    time.sleep(random.randint(1,5))  # Longer delay between requests
                    
                except Exception as e:
                    print(f"Error processing designer {link}: {str(e)}")
                    self.save_progress()
                    print("Progress saved. You can resume later.")
                    break

        # Step 3: Write Final Data to JSON
        with open("../../data/website_perfumes_by_designer.json", "w") as f:
            json.dump(self.all_brands_data, f, indent=2)
        
        print(f"Scraped data for {len(self.all_brands_data)} designers.")

    def scrape_all_perfumes(self):
        """
        Scrape detailed data for all perfumes from all designers.
        Uses the previously collected perfume URLs.
        """
        all_perfumes_data = []
        with open("../../data/website_perfumes_by_designer.json", "r") as f:
            perfumes_data = json.load(f)

        for designer_data in perfumes_data:
            for perfume_url in designer_data["perfumes"]:
                perfume_data = self.scrape_perfume_data(perfume_url)
                if perfume_data:
                    all_perfumes_data.append(perfume_data)

        # Save all perfumes data to a single JSON file
        with open("../../data/website_all_perfumes.json", "w") as f:
            json.dump(all_perfumes_data, f, indent=2)

    def generate_designer_links(self):
        """
        Generate and save a list of all designer/brand URLs.
        This is typically the first step in the scraping process.
        """
        links = self.get_all_designer_links()
        with open("../../data/website_designer_links.txt", "w") as f:
            for link in links:
                f.write(link + "\n")
        print(f"Saved {len(links)} designer links to file.")


# Main Execution
if __name__ == "__main__":
    scraper = FragranceScraper()
    scraper.scrape_all_designers()
    
    # Uncomment to generate designer links
    # scraper.generate_designer_links()
    
    # Uncomment to scrape all perfume details
    # scraper.scrape_all_perfumes()
