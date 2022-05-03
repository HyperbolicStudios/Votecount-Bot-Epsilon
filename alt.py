import cloudscraper

scraper = cloudscraper.create_scraper()
url = "https://hypixel.net/threads/hypixel-mafia-machines-workshop-006-3f-hotel-shops.4924167/page-27#post-35535735"
response = scraper.get(url).text

import traceback

try:
    1/0
except:
    traceback.print_exc()
