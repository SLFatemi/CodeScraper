import time
from bs4 import BeautifulSoup as bs
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pika
import json

class RawData:
    def __init__(self,url):
        self.driver = webdriver.Chrome()
        self.url = url
        self.html = None
    def get_data(self):
        self.driver.get(self.url)
        time.sleep(3)
    def parse_html(self):
        self.html = bs(self.driver.page_source, 'html.parser')
        return self.html
    def get_parsed(self):
        return self.html

class MaskanData(RawData):
    def __init__(self, url):
        super().__init__(url)
        self.houses = []
    def get_all_houses(self):
        for house in self.html.select_one("#Div_Grv").find_all('div',recursive=False):
            # .find() is there to go one level deeper, First div is useless
            self.houses.append(house.find())
        return self.houses

    def show_more_btn(self):
        more_btn = WebDriverWait(self.driver, 3).until(
            EC.element_to_be_clickable((By.ID, "lnkmore"))
        )
        more_btn.click()
        time.sleep(3)

class MaskanHouse:
    def __init__(self,div):
        self.div = div
        self.html = None
        self.url = 'NO_LINK'

    def get_ad_link(self):
        links = self.div.find_all('div', onclick=lambda link: link is not None and link.startswith("window.open("))
        # Getting the link, no regex needed ;)
        self.url = links[0].get('onclick').split('(')[1][1:-2]

def rabbit_publish(data):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='detector_queue')
    channel.basic_publish(
        exchange='',
        routing_key='detector_queue',
        body=json.dumps(data)
    )
    connection.close()

if __name__ == '__main__':
    maskan_file_data = MaskanData("https://maskan-file.ir/Site/Default.aspx")
    maskan_file_data.get_data()

    for i in range(10):
        maskan_file_data.show_more_btn()

    maskan_file_data.parse_html()
    maskan_houses = []
    maskan_houses_links = []

    for house in maskan_file_data.get_all_houses():
        # Make each house an object
        if(house.parent.get('id')):
            # Take the ads out
            maskan_houses.append(MaskanHouse(house))
    for house in maskan_houses:
        house.get_ad_link()
        maskan_houses_links.append(house.url)
    # print('\n'.join(maskan_houses_links),'\n',len(maskan_houses_links))
    rabbit_publish(maskan_houses_links)
