import pika
import json
import time
import pymysql


def rabbit_consume__MelkRadar():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='scrapper_queue__MelkRadar')
    while True:
        # method_frame: metadata about the message (e.g., delivery tag, etc.) (is None if there aren't any messages received)
        #
        # header_frame: headers and properties (Not needed here)
        #
        # body: the actual message you sent from the detector
        method_frame, header_frame, body = channel.basic_get(queue='scrapper_queue__MelkRadar', auto_ack=True)
        if (method_frame):
            data = json.loads(body)
            database_publish(data)
        else:
            print("NO_READY_DATA_AVAILABLE")
            time.sleep(10)


def rabbit_consume__MaskanFile():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='scrapper_queue__MaskanFile')
    while True:
        # method_frame: metadata about the message (e.g., delivery tag, etc.) (is None if there aren't any messages received)
        #
        # header_frame: headers and properties (Not needed here)
        #
        # body: the actual message you sent from the detector
        method_frame, header_frame, body = channel.basic_get(queue='scrapper_queue__MaskanFile', auto_ack=True)
        if (method_frame):
            data = json.loads(body)
            database_publish(data)
        else:
            print("NO_READY_DATA_AVAILABLE")
            time.sleep(10)


def database_publish(data):
    db = pymysql.connect(
        host='sahand.liara.cloud',
        port=30896,
        user='root',
        password='3gsc2mpq4mY217f04ccMxncb',
        database='upbeat_hodgkin',
        charset='utf8mb4'
    )
    cursor = db.cursor()
    successful_imports = 0
    for listing in data:
        listing = json.loads(listing)
        sql = """
         INSERT INTO listings (id, url, name, address, price, area, room_count, year, feats, images)
         VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
         """
        feats_json = json.dumps(listing['feats'], ensure_ascii=False)
        images_json = json.dumps(listing['images'], ensure_ascii=False)
        values = (
            listing['id'],
            listing['url'],
            listing['name'],
            listing['address'],
            f'{int(listing["price"]):,}' if str(listing['price']).isnumeric() else listing['price'],
            int(listing['area']) if listing['area'] else listing['area'],
            int(listing['room_count']) if listing['room_count'] else listing['room_count'],
            int(listing['year']) if listing['year'] else listing['year'],
            feats_json,
            images_json
        )
        try:
            cursor.execute(sql, values)
            successful_imports += 1
        except Exception as e:
            print("ERROR sql_script.py: ", e)
    db.commit()
    cursor.close()
    db.close()
    print(f"Data got transfered! , {successful_imports} were successful")


if __name__ == '__main__':
    rabbit_consume__MelkRadar()
    # rabbit_consume__MaskanFile()
