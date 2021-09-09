import requests
import time
import re
import random
from lxml import etree

from src.data import ctx
from src.utils.log_tools import get_logger
from src.demo import log_demo

log = get_logger('main', 'spider')

for i in range(1400001, 1500007):
    time.sleep(random.random() + 2)
    url = 'https://movie.douban.com/celebrity/' + str(i)
    log.info(url)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 '
                      'Safari/537.36',
    }
    html = requests.get(url, headers=headers).content
    selector = etree.HTML(html)

    # 影人页面
    name = selector.xpath(".//div[@id='content']/h1/text()")
    print(i, name)
    # gender = selector.xpath(".//div[@class='info']//li[1]/text()")[1].replace(":", '').strip()
    # # birthday = selector.xpath(".//div[@class='info']//li[2]/text()")
    # birthday = selector.xpath(".//div[@class='info']//li[3]/text()")[1].replace(":", '').strip()

    # 合作关系演员目录（页数）
    # pages = selector.xpath(".//div[@class='paginator']/a[last()]/text()")
    # if pages:
    #     pages = eval(pages[0])
    #
    # print(i, pages)
