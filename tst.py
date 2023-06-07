import requests
import re
import html

import cloudscraper
"""
scraper = cloudscraper.create_scraper()  # returns a CloudScraper instance
# Or: scraper = cloudscraper.CloudScraper()  # CloudScraper inherits from requests.Session
#print(scraper.get("https://www.hapag-lloyd.com/en/online-business/track/track-by-container-solution.html?container=FCIU7037660").text)
print(scraper.get("https://www.hapag-lloyd.cn/en/online-business/track/track-by-container-solution.html?__cf_chl_tk=kRCAyRTVYmXZxuuqO6UVdRaXKK.VAiitVuKyENcS2xM-1685671798-0-gaNycGzNCvs").text)
"""
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36 Edg/108.0.1462.46"

base_url = "https://www.hapag-lloyd.cn"

session = requests.Session()
session.headers.update({'user-agent' : user_agent})
url = "https://www.hapag-lloyd.com/en/online-business/track/track-by-container-solution.html"
res = session.get(url)
print(res)
print(res.text)
print(session.cookies)
print(res.headers)
with open("test.html", "w") as f:
    f.write(html.unescape(res.text))
"""
url = "https://www.hapag-lloyd.cn/cdn-cgi/challenge-platform/scripts/invisible.js"

res = session.get(url)
print(res)
print(res.headers)
print(res.text)
print(session.cookies)
with open("test.html", "w") as f:
    f.write(str(res.text))
"""
ch1_regex = "cpo.src = '(.*?)'"
chash_regex = "cHash: '(.*?)'"
ch1_url = "%s%s"%(base_url,re.findall(ch1_regex,res.text)[0])
chash_url = "%s%s"%(base_url,re.findall(chash_regex,res.text)[0])
print(ch1_url)
res = session.get(ch1_url)
print(res)
print(res.text)
print(session.cookies)
print(res.headers)
with open("test.html", "w") as f:
    f.write(html.unescape(res.text))