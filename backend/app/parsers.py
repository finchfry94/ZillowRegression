from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import requests
import re
import datetime as dt
from urllib.parse import urljoin
import time
from app.models import PropertyCreate

class ZillowSavedSearchParser:
    """
    A parser to extract relevant information from a Zillow saved search page.
    """
    def __init__(self, url):
        self.url = url
        self.driver = webdriver.Chrome() #etc.
        self.driver.get(self.url)
        # Wait for the page to load and JavaScript to execute
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "title"))
        )

        time.sleep(3)  # wait for javascript to load
        self.html_content = self.driver.page_source
        self.soup= BeautifulSoup(self.html_content, 'html.parser')

    def get_urls(self):
        """
        Scrolls down the page to load all property cards and extracts their URLs.
        """
        found_urls = set() # Use a set to automatically handle duplicates
        scroll_attempts = 0
        max_scroll_attempts = 15 # Limit scrolls to prevent infinite loops

        print("Starting scroll process to load all properties...")

        try:
            last_height = self.driver.execute_script("return document.body.scrollHeight")

            while scroll_attempts < max_scroll_attempts:
                scroll_attempts += 1
                print(f"Scroll attempt {scroll_attempts}/{max_scroll_attempts}...")

                # --- 1. Parse current view for URLs ---
                current_html = self.driver.page_source
                soup = BeautifulSoup(current_html, 'html.parser')
                # Use the correct attribute: 'data-test' or inspect element to confirm
                property_cards = soup.find_all('a', attrs={'data-test': 'property-card-link'})
                # Fallback if the above doesn't work, inspect the element for class/structure
                if not property_cards:
                     # Example fallback: Find articles within the results list
                     results_container = soup.find('ul', class_=lambda x: x and 'photo-cards' in x) # Adjust class
                     if results_container:
                         property_cards = results_container.find_all('a', href=True, recursive=True) # Find any link with href inside

                urls_before_scroll = len(found_urls)
                new_urls_found_this_pass = 0

                for card in property_cards:
                    href = card.get('href')
                    if href:
                        # Ensure URL is absolute
                        absolute_url = urljoin(self.driver.current_url, href)
                        if absolute_url not in found_urls:
                            found_urls.add(absolute_url)
                            new_urls_found_this_pass += 1
                            # print(f"  Found new URL: {absolute_url}") # Uncomment for verbose logging

                print(f"  Found {new_urls_found_this_pass} new URLs this pass. Total unique URLs: {len(found_urls)}")

                # --- 2. Scroll down ---
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

                # --- 3. Wait for new content to load ---
                # Wait a fixed amount of time. Adjust based on network speed/site responsiveness.
                time.sleep(3) # Increase if content loads slowly

                # --- 4. Check if scroll height changed (more content loaded) ---
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    # If height didn't change, maybe wait a bit longer once?
                    print("  Scroll height didn't change. Waiting extra time...")
                    time.sleep(4)
                    new_height = self.driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        print("  Scroll height still unchanged after extra wait. Assuming end of results.")
                        break # Exit loop if height hasn't changed after extra wait

                last_height = new_height

                # --- Optional: Check if URL count stopped increasing ---
                # if len(found_urls) == urls_before_scroll and new_urls_found_this_pass == 0:
                #     print("  No new URLs found in the last pass. Assuming end of results.")
                #     break # Exit if no new URLs were added

            if scroll_attempts == max_scroll_attempts:
                print("Warning: Reached maximum scroll attempts.")

        except Exception as e:
            print(f"An error occurred during scrolling/parsing: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # --- 5. Quit driver after finishing ---
            print(f"Finished scrolling. Total unique URLs found: {len(found_urls)}")
            self.driver.quit()
            print("WebDriver closed.")

        return list(found_urls) # Return as a list


class ZillowListingParserSelenium:
    """
    A parser to extract relevant information from a Zillow listing page using Selenium.
    """

    def __init__(self, url):
        """
        Initializes the ZillowListingParserSelenium with the URL of a Zillow listing page.

        :param url: str, URL of the Zillow listing page
        """
        self.url = url
        self.driver = webdriver.Chrome() #etc.
        self.driver.get(self.url)
        # Wait for the page to load and JavaScript to execute
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "title"))
        )

        time.sleep(3)  # wait for javascript to load
        self.html_content = self.driver.page_source
        self.soup=soup = BeautifulSoup(self.html_content, 'html.parser')

    def parse_address(self):
        soup=self.soup
        title_tag = soup.find('title')
        if title_tag:
            title_text = title_tag.text
            address_from_title = title_text.split('|')[0].strip()

            # Extract address, city, state, and zip using regex
            match = re.match(r"(.+?),\s*([A-Za-z\s]+),\s*([A-Z]{2})\s*(\d{5})", address_from_title)
            if match:
                address, city, state, zip_code = match.groups()
            return {
                "address": address.strip(),
                "city": city.strip(),
                "state": state.strip(),
                "zip_code": zip_code.strip()
            }
        else:
            print("Title tag not found. Cannot extract address.")
            return None
        
    def get_price(self):
        soup=self.soup
        price = soup.find(attrs={'data-testid': 'price'})
        price={'list_price':int(price.text.replace('$','').replace(',',''))}

        return price
        
    def bed_bath_sqft(self):
        """
        Extracts the number of bedrooms, bathrooms, and square footage from the HTML.

        :param soup: BeautifulSoup object representing the parsed HTML
        :return: dict, containing bedrooms, bathrooms, and sqft, or None if not found
        """
        soup=self.soup
        def extract_numbers(text):
            return ''.join(filter(str.isdigit, text))

        sqft_elements = soup.find_all(attrs={'data-testid':'bed-bath-sqft-fact-container'})
        sqft=None
        bath=None
        bed=None
        for el in sqft_elements:
            text = el.get_text()
            try:
                if "sqft" in text:
                    sqft = int(extract_numbers(text))
                    
                elif "bath" in text:
                    bath = int(extract_numbers(text))

                elif "bed" in text:
                    bed = int(extract_numbers(text))
            except:
                pass # this is to allow the --- on zillow

        return {"sqft": sqft, "bathrooms": bath, "bedrooms": bed}
            
    def get_at_a_glance(self):
        soup=self.soup
        at_a_glance_elements= soup.find(attrs={'aria-label': 'At a glance facts'})
        year_built=None
        lot_size=None
        lot_size_unit=None
        for el in at_a_glance_elements:
            if "built in" in el.text.lower():
                try:
                    year_built=int(re.findall(r'\d{4}',el.text)[0])
                except:
                    pass #year built is still none... they can put ---- for year
            if "lot" in el.text.lower():
                try:
                    lot_size=float(re.findall(r'\d+\.\d+|\d+',el.text.lower())[0])
                    lot_size_unit=re.findall(r'\b(acres|sqft)\b',el.text.lower())[0]
                except:
                    pass #lot size is still none... they can put ---- for lot size

                
                print(lot_size,lot_size_unit)
            print(el.text)
        print(year_built)

        return {"year_built":year_built,"lot_size":lot_size,"lot_size_unit":lot_size_unit}

    def get_high_school(self):
        soup=self.soup
        print('getting high school')
        high_element=soup.find(attrs={'data-testid':'school-listing-High'})
        high_school=None
        print(high_element)
        if high_element:
            high_school=high_element.text
            pattern = r"^High:\s*(.*)$" # Look for "High:", optional space, then capture the rest
            match = re.search(pattern, high_school)
            if match:
                high_school=match.group(1).strip()
        return {"high_school":high_school}
    
    def get_price_history(self):
        """
        Finds elements containing price history information (Date, Event, Price)
        and parses them into a structured list.
        """
        soup = self.soup
        history_data = []

        # --- Strategy 1: Find elements likely containing the full string ---
        # This regex looks for the keywords in order within the text content.
        # It's flexible about the surrounding tags.
        # We capture the values between the keywords.
        history_pattern = re.compile(
            r'Date:\s*([\d/]+)\s*,\s*Event:\s*([^,]+)\s*,\s*Price:\s*([$\d,]+)',
            re.IGNORECASE # Make it case-insensitive just in case
        )

        # Find all text nodes that seem to match the pattern
        potential_texts = soup.find_all(attrs={'label':history_pattern})

        if potential_texts:
            print(f"Found {len(potential_texts)} potential history text nodes.")
            for text_node in potential_texts:
                match = history_pattern.search(str(text_node)) # Search within the specific text node
                if match:
                    date_str = match.group(1).strip()
                    event_str = match.group(2).strip()
                    price_str = match.group(3).strip()

                    try:
                        # Clean and convert data
                        # Adjust the date format '%m/%d/%Y' if needed based on actual site data
                        parsed_date = dt.datetime.strptime(date_str, '%m/%d/%Y')
                        # Remove '$' and ',' from price before converting
                        cleaned_price = re.sub(r'[$,]', '', price_str)
                        parsed_price = float(cleaned_price) # Use float for price

                        history_data.append({
                            "date": parsed_date,
                            "event": event_str,
                            "price": parsed_price
                        })
                        print(f"Parsed History Entry: Date={parsed_date}, Event='{event_str}', Price={parsed_price}")

                    except ValueError as e:
                        print(f"Skipping history entry due to parsing error: {e}. Text was: '{text_node}'")
                    except Exception as e:
                         print(f"An unexpected error occurred parsing history: {e}. Text was: '{text_node}'")

        # --- Strategy 2: (Alternative/Fallback) Find a known container ---
        # If you identify a specific container (e.g., <ul class="price-history-list">)
        # you could search within that container first.
        # Example:
        # history_container = soup.find('ul', class_='price-history-list') # Fictional class
        # if history_container:
        #     list_items = history_container.find_all('li') # Assuming history is in list items
        #     for item in list_items:
        #         text_content = item.get_text(" ", strip=True)
        #         match = history_pattern.search(text_content)
        #         if match:
        #             # ... (same parsing logic as above) ...
        #             pass # Add parsing logic here

        if not history_data:
             print("Could not find or parse any price history entries matching the pattern.")

        return history_data
            
        


    def parse(self):
        """
        Parses the HTML content of a Zillow listing and extracts relevant information.

        :return: dict, extracted information such as price, address, and other details
        """
        address_dict=self.parse_address()
        print(address_dict)
        if not address_dict:
            print("Failed to parse address.")
            self.driver.quit()
            return None
        
        else:
            bed_bath_sqft = self.bed_bath_sqft()
            print(bed_bath_sqft)
            price=self.get_price()
            at_a_glance=self.get_at_a_glance()
            
            high_school=self.get_high_school()

            property_details=bed_bath_sqft|price|address_dict|high_school|at_a_glance
        self.driver.quit()
        return property_details

    
