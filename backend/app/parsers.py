from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import re
import time

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
        time.sleep(2) #wait for javascript to load
        self.html_content = self.driver.page_source

    def parse(self):
        """
        Parses the HTML content of a Zillow listing and extracts relevant information.

        :return: dict, extracted information such as price, address, and other details
        """
        soup = BeautifulSoup(self.html_content, 'html.parser')
        title_tag = soup.find('title')
        if title_tag:
            title_text = title_tag.text
            address_from_title = title_text.split('|')[0].strip()
            print(f"Address from title tag: {address_from_title}")

            # Extract address, city, state, and zip using regex
            match = re.match(r"(.+?),\s*([A-Za-z\s]+),\s*([A-Z]{2})\s*(\d{5})", address_from_title)
            if match:
                address, city, state, zip_code = match.groups()
                print(f"Address: {address}")
                print(f"City: {city}")
                print(f"State: {state}")
                print(f"Zip Code: {zip_code}")
                return {
                    "address": address,
                    "city": city,
                    "state": state,
                    "zip_code": zip_code,
                }
            else:
                print("Could not parse address components.")
                return None
        self.driver.quit()
        return None

url='https://www.zillow.com/homedetails/126-Fancy-Trl-Anderson-SC-29621/441715185_zpid/'
listing=ZillowListingParserSelenium(url)

listing.parse()
