import os
import sys
import json
import sqlite3
import datetime
import requests
import tornado.web
import tornado.ioloop
from multiprocessing import Pool
from multiprocessing import Process

URL = "http://wthrcdn.etouch.cn/weather_mini?citykey="


def cache_local(today):
    SQL = []
    file = open("HiCity/citycode.txt", encoding='utf-8')
    lines = file.readlines()
    for line in lines:
        line = line.strip()
        if line:
            list = line.split(",")
            site = URL + list[1]
            data = requests.get(site).text
            data_dict = json.loads(data)
            if 'data' not in data_dict.keys():
                continue
            weather_info = data_dict['data']['forecast']
            for index, item in enumerate(weather_info):
                if index >= 5:  # Only cache weather information for 5 days
                    break
                date = today + datetime.timedelta(days=index)
                citycode = int(list[1])
                tup = (citycode, list[0], str(
                    date), item['type'], item['low'], item['high'], item['fengli'], item['fengxiang'])
                SQL.append(tup)
                # SQL = SQL + "INSERT INTO Weather VALUES ('%d', '%s', '%s', '%s', '%s', '%s', '%s', '%s');" % (
                #     citycode, list[0], str(date), item['type'], item['low'], item['high'], item['fengli'], item['fengxiang'])
    con = sqlite3.connect("HiCity/Weather.db")
    cur = con.cursor()
    cur.executemany("INSERT INTO Weather VALUES (?, ?, ?, ?, ?, ?, ?, ?)", SQL)
    con.commit()
    cur.close()
    con.close()


def cache_data(date):
    con = sqlite3.connect("HiCity/Weather.db")
    cur = con.cursor()
    SQL = "SELECT * FROM Weather WHERE Weather.Date = ('%s');" % (date)
    ret = cur.execute(SQL)
    result = ret.fetchall()
    cur.close()
    con.commit()
    con.close()
    return result


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("<h1>Welcome to HiCity service!</h1>")


class WeatherHandler(tornado.web.RequestHandler):
    def get(self):
        DB_name = "HiCity/Weather.db"
        today = datetime.date.today()
        if os.path.isfile(DB_name):
            pass
        else:
            con = sqlite3.connect(DB_name)
            cur = con.cursor()
            SQL = "CREATE TABLE Weather (Citycode INTEGER, Cityname TEXT, Date TEXT, Weather TEXT, Low_temperature TEXT, High_temperature TEXT, Wind_power TEXT, Wind_direction TEXT, PRIMARY KEY(Citycode, Date));"
            cur.execute(SQL)
            cache_local(today)
            cur.close()
            con.commit()
            con.close()
        data = cache_data(today)
        if data:
            self.write(json.dumps(data))
        else:
            #self.write("Today's weather data is not cached")
            # Uncomment when caching data, otherwise the webserver cannot respond:
            pro = Process(target=cache_local, args=(today,))
            pro.start()


def start_webservice():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/weather", WeatherHandler),
    ])


def func(port):
    port += 8080
    webserver = start_webservice()
    webserver.listen(port)
    tornado.ioloop.IOLoop.current().start()


def run_webserver():
    pool = Pool(5)
    for i in range(5):
        pool.apply_async(func, args=(i, ))  # 启功五个进程，端口从8080~8084
    pool.close()
    pool.join()


if __name__ == "__main__":
    run_webserver()
