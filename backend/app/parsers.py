from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import requests
import re
import time
from app.models import PropertyCreate


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
        self.driver = webdriver.Chrome()  # Or webdriver.Firefox() etc.
        self.driver.get(self.url)
        # Wait for the page to load and JavaScript to execute
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "title"))
        )
        time.sleep(2)  # wait for javascript to load
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
        for el in sqft_elements:
            text = el.get_text()
            if "sqft" in text:
                sqft = int(extract_numbers(text))
                
            elif "bath" in text:
                bath = int(extract_numbers(text))

            elif "bed" in text:
                bed = int(extract_numbers(text))
        return {"sqft": sqft, "bathrooms": bath, "bedrooms": bed}
            
    def get_at_a_glance(self):
        soup=self.soup
        at_a_glance_elements= soup.find(attrs={'aria-label': 'At a glance facts'})
        year_built=None
        for el in at_a_glance_elements:
            if "built in" in el.text.lower():
                year_built=int(re.findall(r'\d{4}',el.text)[0])
            print(el.text)
        print(year_built)

        return {"year_built":year_built}

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

            details=bed_bath_sqft|price|address_dict|high_school|at_a_glance
        self.driver.quit()
        return details

    





