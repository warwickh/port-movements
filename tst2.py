"""
import cloudscraper

scraper = cloudscraper.create_scraper()  # returns a CloudScraper instance
# Or: scraper = cloudscraper.CloudScraper()  # CloudScraper inherits from requests.Session
print(scraper.get("https://www.hapag-lloyd.com/en/online-business/track/track-by-container-solution.html?container=FCIU7037660").text)
"""

import cfscrape

scraper = cfscrape.create_scraper()  # returns a CloudflareScraper instance
# Or: scraper = cfscrape.CloudflareScraper()  # CloudflareScraper inherits from requests.Session
output = scraper.get("https://www.hapag-lloyd.com/en/online-business/track/track-by-container-solution.html?container=FCIU7037660") # => "<!DOCTYPE html><html><head>..."
print(output)
print(output.content)
with open("test.html", "w") as f:
    f.write(str(output.content))