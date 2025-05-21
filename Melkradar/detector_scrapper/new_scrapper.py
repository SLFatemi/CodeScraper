import json
import time
import pika
import requests


class Data:
    def __init__(self, url, estate, count):
        self.url = url
        self.header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
            "Accept": "application/json;q=0.9, */*;q=0.1",
            "Accept-Language": "en-US,en;q=0.9,fa-IR;q=0.8,fa;q=0.7",
            "Content-Type": "application/json; charset=utf-8; odata.metadata=minimal"
        }
        self.payload = {
            "SearchInfo": {
                "EstateTypeGroup": f"{estate}",
                "EstateTypeList": [],
                "AdvertTypeGroup": None,
                "AdvertTypeList": [],
                "CityAreaGroups": [],
                "City_Id": None,
                "AreaSizeFrom": None,
                "AreaSizeTo": None,
                "SellTotalPriceMin": None,
                "SellTotalPriceMax": None,
                "RentMortgagePriceMin": None,
                "RentMortgagePriceMax": None,
                "RentMonthlyPriceMin": None,
                "RentMonthlyPriceMax": None,
                "Bedrooms": [],
                "IsFullMortgage": False,
                "BuildingAgeMax": None,
                "BuildingAgeMin": None
            },
            "PageNo": 1,
            "PageSize": count
        }

    def get_data(self):
        try:
            return requests.post(self.url, headers=self.header, json=self.payload).json()["value"]
        except:
            print("there was an error")


class MelkRadarAd:
    def __init__(self, data_json):
        self.id = data_json["EasyKey"]
        self.url = data_json["Url"]
        self.name = data_json["Summary"].split('\n')[0].split('-')[0]
        self.address = data_json['VendorCityAreaTitle']
        self.price = data_json["SellTotalPrice"] if data_json[
                                                        "AdvertType"] == "Sale" else f'{data_json["RentMortgagePrice"]} ,{data_json["RentMonthlyPrice"]}'
        self.area = data_json["AreaSize"]
        self.room_count = data_json["BedroomCount"]
        self.year = data_json["BuiltDateStr"]
        self.feats = None
        self.images = data_json["VendorImageUrls"].split(',') if data_json["VendorImageUrls"] else None

    def get_final_json(self):
        return {
            "id": self.id,
            "url": self.url,
            "name": self.name,
            "address": self.address,
            "price": self.price,
            "area": self.area,
            "room_count": self.room_count,
            "year": self.year if self.year else None,
            "feats": self.feats,
            "images": self.images
        }


def rabbit_publish(data):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='scrapper_queue__MelkRadar')
    channel.basic_publish(
        exchange='',
        routing_key='scrapper_queue__MelkRadar',
        body=json.dumps(data)
    )
    connection.close()


def get_new_data():
    try:
        url = "https://melkradar.com/p/odata/PeoplePanel/estateMarker/getAdvers"
        final_data_list = []
        apartment_data = Data(url, "Apartment", 10)
        office_data = Data(url, "Office", 10)
        for apartment in apartment_data.get_data():
            apartment_json = MelkRadarAd(apartment).get_final_json()
            final_data_list.append(json.dumps(apartment_json, indent=4))
        for office in office_data.get_data():
            office_json = MelkRadarAd(office).get_final_json()
            final_data_list.append(json.dumps(office_json, indent=4))
        # EVERY 1 MINUTE
        rabbit_publish(final_data_list)
        time.sleep(60)
    except Exception as e:
        print("ERROR new_scrapper.py: ",e)
        time.sleep(10)


if __name__ == '__main__':
    while True:
        get_new_data()
