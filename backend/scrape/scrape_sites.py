import requests
from bs4 import BeautifulSoup
import time
import json
import random
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
from models import Perfume, PerfumeNotes
from dotenv import load_dotenv
import os
from typing import List, Dict, Optional
from tqdm import tqdm

load_dotenv()

BASE_URL = os.getenv("BASE_URL")    

# Rotating User-Agent Pool to Avoid Detection
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
]

# Configuration
BATCH_SIZE = 50  # Number of perfumes to process in each batch
MAX_CONCURRENT_REQUESTS = 5  # Maximum number of concurrent requests
REQUEST_TIMEOUT = 30  # Timeout for requests in seconds
MIN_DELAY = 2  # Minimum delay between requests
MAX_DELAY = 5  # Maximum delay between requests

# Function to Randomize Headers
def get_headers():
    return {"User-Agent": random.choice(USER_AGENTS)}

# Function to Handle 429 Errors with Retry & Exponential Backoff
async def request_with_retry(session, url, retries=3):
    for attempt in range(retries):
        try:
            async with session.get(url, headers=get_headers(), timeout=REQUEST_TIMEOUT) as response:
                if response.status == 200:
                    return await response.text()
                elif response.status == 429:
                    wait_time = random.randint(20, 30)
                    print(f"Rate limited! Waiting {wait_time} seconds before retrying...")
                    await asyncio.sleep(wait_time)
                    if attempt == retries - 1:
                        return None
                else:
                    print(f"Failed to fetch {url} (Status: {response.status})")
                    return None
        except Exception as e:
            print(f"Error fetching {url}: {str(e)}")
            if attempt == retries - 1:
                return None
            await asyncio.sleep(random.randint(MIN_DELAY, MAX_DELAY))
    return None

# Function to Save Progress
def save_progress(all_brands_data: List[Dict], current_designer_index: int, current_designer_url: str, processed_perfumes: List[str]):
    progress_data = {
        "all_brands_data": all_brands_data,
        "current_designer_index": current_designer_index,
        "current_designer_url": current_designer_url,
        "processed_perfumes": processed_perfumes
    }
    with open("../../data/scraping_progress.json", "w") as f:
        json.dump(progress_data, f, indent=2)
    print(f"\nProgress saved! You can resume from designer index {current_designer_index}")
    print(f"Current designer URL: {current_designer_url}")
    print(f"Processed {len(processed_perfumes)} perfumes so far")

# Function to Load Progress
def load_progress():
    try:
        with open("../../data/scraping_progress.json", "r") as f:
            progress_data = json.load(f)
            return progress_data
    except FileNotFoundError:
        return None

# Function to Get All Designer Links
def get_all_designer_links():
    response = request_with_retry(BASE_URL + "/designers/")
    if not response:
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    designer_links = []

    for link in soup.select('a[href^="/designers/"]'):
        full_url = BASE_URL + link['href']
        if full_url not in designer_links and link['href'] != "":
            designer_links.append(full_url)

    print(f"Found {len(designer_links)} designer links")
    return designer_links

# Function to Scrape Perfume Links for a Designer
async def scrape_perfume_details(session, url):
    response = await request_with_retry(session, url)
    if not response:
        return None, []

    soup = BeautifulSoup(response, 'html.parser')
    perfume_links = []

    designer_name = url.split("/")[-1].replace(".html", "")

    # Find all perfume links for this designer
    for link in soup.select(f'a[href*="/{designer_name}/"]'):
        full_url = BASE_URL + link['href'] if link['href'].startswith('/') else link['href']

        if full_url not in perfume_links:
            perfume_links.append(full_url)

    print(f"Found {len(perfume_links)} perfume links for {designer_name}")
    time.sleep(random.randint(2, 7))  # Randomized delay (5-15 seconds)
    return designer_name, perfume_links

async def scrape_perfume_data(session, url: str) -> Optional[Perfume]:
    """
    Asynchronously scrapes detailed information about a specific perfume from its URL.
    Returns a Perfume model instance with the scraped data.
    """
    html = await request_with_retry(session, url)
    if not html:
        return None

    soup = BeautifulSoup(html, 'html.parser')
    missing_fields = []

    # Extract data (same as before, but with async context)
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

    accords = []
    for accord_tag in soup.select(".accord-box .accord-bar"):
        accord_name = accord_tag.text.strip()
        accord_width = accord_tag["style"].split("width:")[-1].split("%")[0]
        try:
            accords.append({accord_name: float(accord_width)})
        except:
            missing_fields.append(f"accords: {accord_name}")

    if not accords:
        missing_fields.append("accords")

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

    gender_tag = soup.select_one("h1[itemprop='name'] small")
    gender = gender_tag.text.strip() if gender_tag else "Unknown"
    if not gender_tag:
        missing_fields.append("gender")

    longevity_tag = soup.select_one("longevity-rating p span")
    longevity = longevity_tag.text.strip() if longevity_tag else None
    if not longevity_tag:
        missing_fields.append("longevity")

    sillage_tag = soup.select_one("sillage-rating p span")
    sillage = sillage_tag.text.strip() if sillage_tag else None
    if not sillage_tag:
        missing_fields.append("sillage")

    price_value_tag = soup.select_one("price-value-widget p span")
    price_value = price_value_tag.text.strip() if price_value_tag else None
    if not price_value_tag:
        missing_fields.append("price_value")

    smells_like = []
    for similar_perfume in soup.select("similar-perfumes .carousel-cell a span.brand"):
        smells_like.append(similar_perfume.text.strip())

    if not smells_like:
        missing_fields.append("smells_like")

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

    if missing_fields:
        with open("missing_fields.log", "a") as log_file:
            log_file.write(f"URL: {url} - Missing: {', '.join(missing_fields)}\n")

    return perfume_data

async def process_batch(session, perfume_urls: List[str]) -> List[Optional[Perfume]]:
    """
    Process a batch of perfume URLs concurrently.
    """
    tasks = []
    for url in perfume_urls:
        task = asyncio.create_task(scrape_perfume_data(session, url))
        tasks.append(task)
        await asyncio.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if isinstance(r, Perfume)]

async def main():
    all_brands_data = []
    current_designer_index = 0
    current_designer_url = None
    processed_perfumes = set()

    # Try to load previous progress
    progress = load_progress()
    if progress:
        all_brands_data = progress["all_brands_data"]
        current_designer_index = progress["current_designer_index"]
        current_designer_url = progress["current_designer_url"]
        processed_perfumes = set(progress.get("processed_perfumes", []))
        print(f"Resuming from designer index {current_designer_index}")
        print(f"Current designer URL: {current_designer_url}")
        print(f"Already processed {len(processed_perfumes)} perfumes")

    async with aiohttp.ClientSession() as session:
        with open("../../data/website_designer_links.txt", "r") as f:
            designer_links = f.readlines()
            
            for i in range(current_designer_index, len(designer_links)):
                link = designer_links[i].strip()
                current_designer_url = link
                current_designer_index = i
                
                try:
                    brand_name, perfume_links = await scrape_perfume_details(session, link)
                    if perfume_links:
                        # Filter out already processed perfumes
                        new_perfume_links = [url for url in perfume_links if url not in processed_perfumes]
                        
                        # Process in batches
                        for j in range(0, len(new_perfume_links), BATCH_SIZE):
                            batch = new_perfume_links[j:j + BATCH_SIZE]
                            print(f"\nProcessing batch {j//BATCH_SIZE + 1} for {brand_name}")
                            
                            perfumes = await process_batch(session, batch)
                            processed_perfumes.update(batch)
                            
                            # Save progress after each batch
                            save_progress(all_brands_data, current_designer_index, current_designer_url, list(processed_perfumes))
                            
                            # Add to results
                            all_brands_data.append({
                                "brand": brand_name,
                                "perfumes": [p.model_dump() for p in perfumes if p]
                            })
                            
                            # Write intermediate results
                            with open("../../data/website_perfumes_by_designer.json", "w") as f:
                                json.dump(all_brands_data, f, indent=2)
                            
                            print(f"Processed {len(processed_perfumes)}/{len(perfume_links)} perfumes for {brand_name}")
                    
                    print(f"Completed {i + 1}/{len(designer_links)} designers")
                    
                except Exception as e:
                    print(f"Error processing designer {link}: {str(e)}")
                    save_progress(all_brands_data, current_designer_index, current_designer_url, list(processed_perfumes))
                    print("Progress saved. You can resume later.")
                    break

    print(f"Scraped data for {len(all_brands_data)} designers.")
    print(f"Total perfumes processed: {len(processed_perfumes)}")

if __name__ == "__main__":
    asyncio.run(main())
