import os
import sys
import json
import sqlite3
import datetime
import keyboard
import requests
import threading
import webbrowser
import tornado.web
import tornado.ioloop
import tkinter as tk
import tkinter.messagebox
from os import startfile
from openpyxl import Workbook
from tkinter import filedialog
from tkinter import scrolledtext
from multiprocessing import Process


global_text = None
URL = "http://wthrcdn.etouch.cn/weather_mini?citykey="
LOCAL_WEB = "http://localhost:8080"


class myThread(threading.Thread):
    def __init__(self, city):
        threading.Thread.__init__(self)
        self.city = city
        self.matchResult = []

    def run(self):
        while True:
            def callback():
                try:
                    self.matchResult = auto_complete(
                        self.city, self.matchResult)
                except tkinter.TclError:
                    print("Warning: 'Tab' completion cannot find the target!")
            keyboard.add_hotkey('tab', callback)
            keyboard.wait()


def auto_complete(city, matchResult):
    global global_text
    word = global_text.get()
    if word in matchResult:
        item = matchResult.index(word)
        global_text.delete(0, tk.END)
        if item + 1 >= len(matchResult):
            global_text.insert(tk.END, matchResult[0])
        else:
            global_text.insert(tk.END, matchResult[item+1])
    else:
        matchResult = fuzzy_matching(word, city)
        if len(matchResult) > 0:
            global_text.delete(0, tk.END)
            global_text.insert(tk.END, matchResult[0])
    return matchResult


def use_interface():
    window = tk.Tk()
    window.title('HiCity program')
    window.geometry('825x475')

    menubar = tk.Menu(window)
    filemenu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label='File', menu=filemenu)

    submenu = tk.Menu(filemenu)
    filemenu.add_cascade(label='Manage DB', menu=submenu)
    submenu.add_command(label='Insert data', command=lambda: insert_data(city))
    submenu.add_command(label='Delete data', command=lambda: delete_data(city))
    submenu.add_command(label='Update data', command=lambda: update(city))
    submenu.add_command(label='Select data', command=(
        lambda: select_data(feedback, city)))

    filemenu.add_separator()
    filemenu.add_command(label='Backup to database',
                         command=(lambda: backup_DB(city)))
    filemenu.add_command(label='Export to execl',
                         command=(lambda: backup_execl(city)))
    filemenu.add_separator()
    filemenu.add_command(label='Exit', command=(lambda: sys.exit()))

    viewmenu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label='View', menu=viewmenu)

    viewmenu.add_command(label='Search', command=(
        lambda: search(city, feedback)))
    viewmenu.add_command(label='View log', command=openInstruktion)

    helpmenu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label='Help', menu=helpmenu)
    helpmenu.add_command(label='HiCity webserver',
                         command=(lambda: webbrowser.open(LOCAL_WEB)))
    helpmenu.add_separator()
    helpmenu.add_command(label='Welcome', command=welcome)
    helpmenu.add_command(label='About', command=about)

    window.resizable(0, 0)
    window.config(menu=menubar)

    tk.Label(window, text='City information:',).place(x=30, y=10)
    info = scrolledtext.ScrolledText(
        window, relief="solid", width=30, height=15, font=('微软雅黑', 10))
    info.place(x=30, y=35)
    info.config(state='disabled')

    tk.Label(window, text='feedback information:',).place(x=410, y=10)
    feedback = scrolledtext.ScrolledText(
        window, relief="solid", width=37, height=15, font=('微软雅黑', 10))
    feedback.place(x=410, y=35)
    feedback.config(state='disabled')

    search_button = tk.Button(
        window, text='Inquire weather', command=(lambda: search(city, feedback)))
    search_button.place(x=225, y=400)
    clear_button = tk.Button(window, text='Clear message',
                             command=(lambda: clear(feedback)))
    clear_button.place(x=575, y=400)

    city = load_data(info)
    window.wm_attributes('-topmost', 1)
    window.wm_attributes('-topmost', 0)

    window.mainloop()


def load_data(info):
    window = tk.Tk()
    window.title('Loading data!')
    window.geometry('650x125')
    window.wm_attributes('-topmost', 1)

    tk.Label(window, text='Current progress: ',).place(x=25, y=55)
    canvas = tk.Canvas(window, width=400, height=22, bg="white")
    canvas.place(x=165, y=55)
    percent = tk.Label(window, text='0%',)
    percent.place(x=575, y=55)

    if os.path.isfile("HiCity/City.db"):
        city = read_fromDB(window, canvas, percent, info)
        window.destroy()
        return city
    else:
        city = read_file(window, canvas, percent, info)
        dialog_backup_DB(city, window)
        return city

    window.resizable(0, 0)
    window.mainloop()


def dialog_backup_DB(city, window):
    ret = tk.messagebox.askquestion(
        "tips", '   Do you need to back up your data to the database?\nThe system will automatically merge conflict information.')
    if ret == "yes":
        importDB(city, "HiCity/City")
        tk.messagebox.showinfo(
            "info", "Already imported into the database!")
        window.destroy()

        return city
    else:
        window.destroy()
        return city


def read_file(window, canvas, percent, info):
    file = None
    city = {}
    city_info = ""
    try:
        file = open("HiCity/citycode.txt", encoding='utf-8')
        lines = file.readlines()
        total = len(lines)
        fill_line = canvas.create_rectangle(0, 0, 0, 0, width=0, fill="green")
        num = 1
        for cur, line in enumerate(lines):
            line = line.strip()
            if line:
                list = line.split(",")
                if cur % 25 == 0:
                    info.config(state='normal')
                    info.insert(tk.END, city_info)
                    info.see(tk.END)
                    info.config(state='disabled')
                if list[0] != "":
                    if list[0] in city:
                        lis = []
                        lis.append(city[list[0]])
                        lis.append(list[1])
                        city[list[0]] = lis
                    else:
                        city[list[0]] = list[1]
                    city_info += str(num) + ". " + \
                        list[0] + ": " + list[1] + "\n"
                    num += 1
                ratio = float(cur) / total
                canvas.coords(fill_line, (0, 0, 400*ratio, 55))
                percent.config(text="{0}%".format(int(ratio * 100)))
                window.update()
        canvas.coords(fill_line, (0, 0, 400, 55))
        percent.config(text="100%")
        log_record("Load data from file: citycode.txt")
    except FileNotFoundError:
        log_record("No such file or directory: citycode.txt")
        print("No such file or directory: citycode.txt\n")
    except UnicodeDecodeError:
        log_record("File encoding format error.")
        print("File encoding format error.")
    finally:
        if file:
            file.close()
    return city


def read_fromDB(window, canvas, percent, info):
    city = {}
    con = sqlite3.connect("HiCity/City.db")
    cur = con.cursor()
    SQL = "SELECT COUNT() FROM City"
    ret = cur.execute(SQL)
    num = ret.fetchall()
    total = num[0][0]
    fill_line = canvas.create_rectangle(0, 0, 0, 0, width=0, fill="green")
    city_info = ""
    for item in range(1, num[0][0] + 1):
        ret = cur.execute(
            "SELECT CityName, Code FROM City WHERE ID = '%d'" % (item))
        result = ret.fetchall()
        city[result[0][0]] = result[0][1]
        city_info += str(item) + ". " + \
            result[0][0] + ": " + result[0][1] + "\n"
        if item % 25 == 0:
            info.config(state='normal')
            info.insert(tk.END, city_info)
            info.see(tk.END)
            info.config(state='disabled')

        ratio = float(item) / total
        canvas.coords(fill_line, (0, 0, 400*ratio, 55))
        percent.config(text="{0}%".format(int(ratio * 100)))
        window.update()

    info.config(state='normal')
    info.insert(tk.END, city_info)
    info.see(tk.END)
    info.config(state='disabled')

    canvas.coords(fill_line, (0, 0, 400, 55))
    percent.config(text="100%")
    cur.close()
    con.close()
    tk.messagebox.showinfo("Complete", "All information imported successfully")
    log_record("Load data from the database.")
    return city


def clear(feedback):
    feedback.config(state='normal')
    feedback.delete('1.0', 'end')
    feedback.config(state='disabled')


def insert_data(city):
    window = tk.Tk()
    window.title('Insert')
    window.geometry('335x150')
    window.wm_attributes('-topmost', 1)

    city_name = tk.Label(window, text='cityname: ')
    city_name.place(x=30, y=25)
    name_box = tk.Entry(window, relief="solid",)
    name_box.place(x=110, y=25)
    code = tk.Label(window, text='citycode: ')
    code.place(x=30, y=65)
    code_box = tk.Entry(window, relief="solid",)
    code_box.place(x=110, y=65)

    def insert():
        city_name = name_box.get()
        city_code = code_box.get()
        if city_name == "" or city_code == "":
            tk.messagebox.showwarning("Warning", "Input cannot be empty!")
            return
        SQL = "INSERT INTO City (CityName, Code) VALUES ('%s', '%s');" % (
            city_name, city_code)
        carryOutSQL(SQL, "HiCity/City.db")
        log_record("Insert data: '%s' '%s'" % (city_name, city_code))
        tk.messagebox.showinfo("information", "Finished!")

    insert_button = tk.Button(window, text="insert", command=insert)
    insert_button.place(x=110, y=100)

    cancel_button = tk.Button(window, text="cancel", command=window.destroy)
    cancel_button.place(x=225, y=100)

    global global_text
    global_text = name_box
    thread = myThread(city)
    thread.setDaemon(True)
    thread.start()

    window.mainloop()


def delete_data(city):
    window = tk.Tk()
    window.title('Delete')
    window.geometry('330x125')
    window.wm_attributes('-topmost', 1)

    city_name = tk.Label(window, text='cityname: ')
    city_name.place(x=30, y=25)
    name_box = tk.Entry(window, relief="solid",)
    name_box.place(x=110, y=25)

    def delete():
        city_name = name_box.get()
        if city_name == "":
            tk.messagebox.showwarning("Warning", "Input cannot be empty!")
            return
        SQL = "DELETE FROM City WHERE CityName = ('%s');" % (city_name)
        carryOutSQL(SQL, "HiCity/City.db")
        log_record("Delete data: '%s'" % (city_name))
        tk.messagebox.showinfo("information", "Finished!")
    insert_button = tk.Button(window, text="delete", command=delete)
    insert_button.place(x=110, y=65)

    cancel_button = tk.Button(window, text="cancel", command=window.destroy)
    cancel_button.place(x=225, y=65)

    global global_text
    global_text = name_box
    thread = myThread(city)
    thread.setDaemon(True)
    thread.start()

    window.mainloop()


def update(city):
    window = tk.Tk()
    window.title('Update')
    window.geometry('335x150')
    window.wm_attributes('-topmost', 1)

    city_name = tk.Label(window, text='cityname: ')
    city_name.place(x=30, y=25)
    name_box = tk.Entry(window, relief="solid",)
    name_box.place(x=110, y=25)
    code = tk.Label(window, text='citycode: ')
    code.place(x=30, y=65)
    code_box = tk.Entry(window, relief="solid",)
    code_box.place(x=110, y=65)

    def update():
        city_name = name_box.get()
        city_code = code_box.get()
        if city_name == "" or city_code == "":
            tk.messagebox.showwarning("Warning", "Input cannot be empty!")
            return
        SQL = "UPDATE City SET Code = ('%s') WHERE CityName = ('%s');" % (
            city_code, city_name)
        carryOutSQL(SQL, "HiCity/City.db")
        log_record("Update data: '%s' '%s'" % (city_name, city_code))
        tk.messagebox.showinfo("information", "Finished!")

    insert_button = tk.Button(window, text="update", command=update)
    insert_button.place(x=110, y=100)

    cancel_button = tk.Button(window, text="cancel", command=window.destroy)
    cancel_button.place(x=225, y=100)

    global global_text
    global_text = name_box
    thread = myThread(city)
    thread.setDaemon(True)
    thread.start()

    window.mainloop()


def select_data(feedback, city):
    window = tk.Tk()
    window.title('Select')
    window.geometry('330x125')
    window.wm_attributes('-topmost', 1)

    city_name = tk.Label(window, text='cityname: ')
    city_name.place(x=30, y=25)
    name_box = tk.Entry(window, relief="solid",)
    name_box.place(x=110, y=25)

    def select(feedback):
        city_name = name_box.get()
        if city_name == "":
            tk.messagebox.showwarning("Warning", "Input cannot be empty!")
            return
        SQL = "SELECT * FROM City WHERE CityName = ('%s');" % (city_name)
        ret = carryOutSQL(SQL, "HiCity/City.db")
        if len(ret) == 0:
            tk.messagebox.showwarning(
                "Warning", "The query result does not exist!")
            return
        else:
            feedback.config(state='normal')
            feedback.insert(tk.END, "Search result: " + city_name +
                            " " + ret[0][2] + "\n")
            feedback.see(tk.END)
            feedback.config(state='disabled')

            tk.messagebox.showinfo("information", "Finished!")

    insert_button = tk.Button(window, text="select",
                              command=(lambda: select(feedback)))
    insert_button.place(x=110, y=65)

    cancel_button = tk.Button(window, text="cancel", command=window.destroy)
    cancel_button.place(x=225, y=65)

    global global_text
    global_text = name_box
    thread = myThread(city)
    thread.setDaemon(True)
    thread.start()

    window.mainloop()


def carryOutSQL(SQL, DB_name):
    con = sqlite3.connect(DB_name)
    cur = con.cursor()
    ret = cur.execute(SQL)
    result = ret.fetchall()
    cur.close()
    con.commit()
    con.close()
    return result


def backup_DB(city):
    DB_name = tk.filedialog.asksaveasfilename(
        filetypes=[("sqlite sorce file", ".db")])
    if DB_name == "":
        return
    importDB(city, DB_name)


def importDB(city, DB_name):
    DB_name += ".db"
    if os.path.isfile(DB_name):
        return
    con = sqlite3.connect(DB_name)
    cur = con.cursor()
    SQL = "CREATE TABLE City (ID INTEGER PRIMARY KEY, CityName TEXT, Code TEXT);"
    cur.execute(SQL)
    i = 0
    for key, value in city.items():
        i += 1
        if type(value) == list:
            list_merge = ""
            for element in value:
                list_merge = list_merge + " " + element
            list_merge.strip(" ")
            cur.execute("INSERT INTO City VALUES ('%d', '%s', '%s')" %
                        (i, key, list_merge))
        else:
            cur.execute("INSERT INTO City VALUES ('%s', '%s', '%s')" %
                        (i, key, value))
    cur.close()
    con.commit()
    con.close()
    log_record("Backup to database")


def backup_execl(city):
    filename = tk.filedialog.asksaveasfilename(
        filetypes=[("Execl sorce file", ".xlsx")])
    if filename == "":
        return
    filename = filename + ".xlsx"
    workbook = Workbook()
    sheet = workbook.active
    for key, value in city.items():
        if type(value) == list:
            values = ""
            values = value[0] + " " + value[1]
            sheet.append([key, str(values)])
        else:
            sheet.append([key, value])
    workbook.save(filename)
    log_record("Backup to execl-table")


def search(city, feedback):
    window = tk.Tk()
    window.title('Search')
    window.geometry('315x125')
    window.wm_attributes('-topmost', 1)

    entry_box = tk.Entry(window, width='28', relief="solid", show=None)
    entry_box.place(x=35, y=25)

    def find():
        cityname = entry_box.get()

        if cityname in city:
            feedback.config(state='normal')
            feedback.insert(tk.END, cityname + ": " + city[cityname] + "\n")
            feedback.see(tk.END)
            feedback.config(state='disabled')
            log_record("Search success")
        else:
            dictList = []
            for key in city:
                dictList.append(key)
            ret = filter(lambda x: str(x).count(cityname), dictList)
            matchResult = list(ret)
            if len(matchResult) != 0:
                feedback.config(state='normal')
                feedback.insert(
                    tk.END, "No matching results. Do you want to find the following cities?\n")
                feedback.insert(tk.END, matchResult)
                feedback.insert(tk.END, "\n")
                feedback.see(tk.END)
                feedback.config(state='disabled')
                log_record("Fuzzy search result matching")
            else:
                log_record("Find results are empty")
                tk.messagebox.showwarning(
                    "Warning", "Invalid city name, please input again!")

    def inquire_weather():
        cityname = entry_box.get()
        if cityname in city:
            result = city[cityname]
            city_list = result.strip().split(" ")
            for elem in city_list:
                webserver_return = False
                try:
                    website = LOCAL_WEB + "/weather"
                    data = requests.get(website).text
                    print(data)
                    info = json.loads(data)
                    for item in info:
                        if item[0] == int(elem):
                            webserver_return = True
                            feedback.config(state='normal')
                            feedback.insert(tk.END, "--------------------\n")
                            feedback.insert(tk.END, cityname +
                                            ": "+str(elem)+"\n")
                            feedback.insert(tk.END, "日期: "+item[2]+"\n")
                            feedback.insert(tk.END, "天气: "+item[3]+"\n")
                            feedback.insert(tk.END, "最低温: "+item[4]+"\n")
                            feedback.insert(tk.END, "最高温: "+item[5]+"\n")
                            feedback.insert(tk.END, "风力: "+item[6]+"\n")
                            feedback.insert(tk.END, "风向: "+item[7]+"\n")
                            feedback.insert(
                                tk.END, "website: " + LOCAL_WEB + "\n")
                            feedback.see(tk.END)
                            feedback.config(state='disabled')
                            break
                except requests.exceptions.RequestException:
                    tk.messagebox.showwarning(
                        "Warning", "The local server is down!")
                except json.decoder.JSONDecodeError:
                    answer = tk.messagebox.askokcancel(
                        "Tip", "Today's weather data is not cached, do you need to cache the data?")
                    if answer == True:
                        website = LOCAL_WEB + "/cache"
                        requests.get(website)
                if not webserver_return:
                    site = URL + str(elem)
                    data = requests.get(site).text
                    data_dict = json.loads(data)
                    feedback.config(state='normal')
                    if 'data' not in data_dict.keys():
                        feedback.insert(
                            tk.END, "\nUnable to find weather information for this city: \n"+str(elem)+"\n")
                        feedback.see(tk.END)
                        feedback.config(state='disabled')
                        continue
                    weather_info = data_dict['data']['forecast'][1]
                    feedback.insert(tk.END, "--------------------\n")
                    feedback.insert(tk.END, cityname+": "+str(elem)+"\n")
                    feedback.insert(tk.END, "日期: "+weather_info['date']+"\n")
                    feedback.insert(tk.END, "天气: "+weather_info['type']+"\n")
                    feedback.insert(tk.END, "最低温: "+weather_info['low']+"\n")
                    feedback.insert(tk.END, "最高温: "+weather_info['high']+"\n")
                    feedback.insert(tk.END, "风力: "+weather_info['fengli']+"\n")
                    feedback.insert(
                        tk.END, "风向: "+weather_info['fengxiang']+"\n")
                    feedback.see(tk.END)
                    feedback.config(state='disabled')
        else:
            tk.messagebox.showwarning(
                "Warning", "Please enter an accurate city name!")
    search_button = tk.Button(window, text="search", command=find)
    search_button.place(x=35, y=65)

    inquire_button = tk.Button(window, text="weather", command=inquire_weather)
    inquire_button.place(x=118, y=65)

    cancel_button = tk.Button(window, text="cancel", command=window.destroy)
    cancel_button.place(x=215, y=65)

    global global_text
    global_text = entry_box
    thread = myThread(city)
    thread.setDaemon(True)
    thread.start()

    window.mainloop()


def openInstruktion():
    os.system('notepad HiCity/log.txt')


def welcome():
    tk.messagebox.showinfo(
        "Welcome", "Welcome to the HiCity program.")


def about():
    tk.messagebox.showinfo(
        "About", "\tversion 1.0\nThe webserver can be parallelized!")


def fuzzy_matching(word, city):
    dictList = []
    for key in city:
        dictList.append(key)
    ret = filter(lambda x: str(x).startswith(word), dictList)
    matchResult = list(ret)
    return matchResult


def log_record(info):
    with open("HiCity/log.txt", 'a+') as filename:
        filename.write("[%s] %s\n" %
                       (str(datetime.datetime.now()), info))


if __name__ == "__main__":
    #os.system(r"start server.exe")
    log_record("Enter the system")
    use_interface()
