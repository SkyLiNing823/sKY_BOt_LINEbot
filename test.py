import requests
from bs4 import BeautifulSoup

send_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36",
    "Connection": "keep-alive",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.8"}

money = 'jpy'
money = money.lower()
data = ['usd', 'hkd', 'gbp', 'aud', 'cad', 'sgd', 'chf', 'jpy', 'zar',
        'sek', 'nzd', 'thb', 'php', 'idr', 'eur', 'krw', 'vnd', 'myr', 'cny']
num = data.index(money)
URL = 'https://rate.bot.com.tw/xrt?Lang=zh-TW'
request = requests.get(URL, headers=send_headers)
html = request.content
bsObj = BeautifulSoup(html, 'html.parser')
rate_table = bsObj.find('table', attrs={'title': '牌告匯率'}).find(
    'tbody').find_all('tr')
buyin_rate = rate_table[num].find(
    'td', attrs={'data-table': '本行即期買入'})
sellout_rate = rate_table[num].find(
    'td', attrs={'data-table': '本行即期賣出'})
words = money.upper()+"\n即時即期買入: {}\n即時即期賣出: {}".format(buyin_rate.get_text().strip(),
                                                        sellout_rate.get_text().strip())
print(words)