import requests
from bs4 import BeautifulSoup
import time
import json
import random
from models import Perfume, PerfumeNotes
from dotenv import load_dotenv
import os

load_dotenv()

BASE_URL = os.getenv("BASE_URL")    


# Rotating User-Agent Pool to Avoid Detection
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
]

# Function to Randomize Headers
def get_headers():
    return {"User-Agent": random.choice(USER_AGENTS)}

# Function to Handle 429 Errors with Retry & Exponential Backoff
def request_with_retry(url, retries=3):
    for attempt in range(retries):
        response = requests.get(url, headers=get_headers())

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

# Function to Save Progress
def save_progress(all_brands_data, current_designer_index, current_designer_url):
    progress_data = {
        "all_brands_data": all_brands_data,
        "current_designer_index": current_designer_index,
        "current_designer_url": current_designer_url
    }
    with open("../../data/scraping_progress.json", "w") as f:
        json.dump(progress_data, f, indent=2)
    print(f"\nProgress saved! You can resume from designer index {current_designer_index}")
    print(f"Current designer URL: {current_designer_url}")
    print("To resume, run the script again and it will continue from where it left off.")

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
def scrape_perfume_details(url):
    response = request_with_retry(url)
    if not response:
        return None, []


    soup = BeautifulSoup(response.text, 'html.parser')
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

def scrape_perfume_data(url: str) -> Perfume:
    """
    Scrapes detailed information about a specific perfume from its URL.
    Returns a Perfume model instance with the scraped data.
    """
    response = request_with_retry(url)
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

# Main Execution
if __name__ == "__main__":
    all_brands_data = []
    current_designer_index = 0
    current_designer_url = None

    # Try to load previous progress
    progress = load_progress()
    if progress:
        all_brands_data = progress["all_brands_data"]
        current_designer_index = progress["current_designer_index"]
        current_designer_url = progress["current_designer_url"]
        print(f"Resuming from designer index {current_designer_index}")
        print(f"Current designer URL: {current_designer_url}")

    # Step 1: Get All Designer Links (Uncomment if running fresh)
    # links = get_all_designer_links()
    # with open("../../data/website_designer_links.txt", "w") as f:
    #     for link in links:
    #         f.write(link + "\n")

    # Step 2: Scrape Perfume Links for Each Designer
    with open("../../data/website_designer_links.txt", "r") as f:
        designer_links = f.readlines()
        for i in range(current_designer_index, len(designer_links)):
            link = designer_links[i].strip()
            current_designer_url = link
            current_designer_index = i
            
            try:
                brand_name, perfume_links = scrape_perfume_details(link)
                if perfume_links:
                    all_brands_data.append({"brand": brand_name, "perfumes": perfume_links})
                
                # Save progress after each successful designer
                save_progress(all_brands_data, current_designer_index, current_designer_url)
                
                print(f"Processed {i + 1}/{len(designer_links)} designers")
                time.sleep(random.randint(1,5))  # Longer delay between requests
                
            except Exception as e:
                print(f"Error processing designer {link}: {str(e)}")
                save_progress(all_brands_data, current_designer_index, current_designer_url)
                print("Progress saved. You can resume later.")
                break

    # Step 3: Write Final Data to JSON
    with open("../../data/website_perfumes_by_designer.json", "w") as f:
        json.dump(all_brands_data, f, indent=2)
    
    print(f"Scraped data for {len(all_brands_data)} designers.")

    # Step 4: Scrape Perfume Data for Each Perfume Link
    # all_perfumes_data = []
    # with open("../../data/website_perfumes_by_designer.json", "r") as f:
    #     perfumes_data = json.load(f)

    # for designer_data in perfumes_data:
    #     for perfume_url in designer_data["perfumes"]:
    #         perfume_data = scrape_perfume_data(perfume_url)
    #         if perfume_data:
    #             all_perfumes_data.append(perfume_data)

    # # Save all perfumes data to a single JSON file
    # with open("../../data/website_all_perfumes.json", "w") as f:
    #     json.dump(all_perfumes_data, f, indent=2)
