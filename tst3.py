from bs4 import BeautifulSoup
import cfscrape

valid = True
cnt = 0
url = 'https://www.cdp.net/en/responses?queries%5Bname%5D=nike'

# send requests until the scraper protection kicks in
while valid:
    cnt += 1
    print(cnt)

    # scrape
    scraper = cfscrape.create_scraper()
    res = scraper.get(url) 
    soup = BeautifulSoup(res.content, 'html.parser')
    table = soup.find('table', class_='sortable_table')
    
    # if protection is activated, the table will not be found. Exit loop.
    # takes approx. 40 requests
    if table == None:
        valid = False
        print('scraper protection kicked in')