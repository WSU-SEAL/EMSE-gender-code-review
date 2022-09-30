import csv, requests


import argparse
import requests
import  mysql.connector as mysql
import  os
import glob
import mysql.connector
from mysql.connector import Error

headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/60.0",
           "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
           "Accept-Language": "en-US,en;q=0.9"
           }



def download_avatar(url, dir_name, id):
    print(url)
    img_data = requests.get(url=url, headers=headers).content
    image_name=dir_name + "/"+ str(id) + '.jpg'
    with open(image_name, 'wb') as handler:
        handler.write(img_data)

def mark_mined(id, db):
    cursor2 = db.cursor()
    data = (1, id)
    query = """UPDATE people SET is_mined = %s WHERE gerrit_id = %s"""
    cursor2.execute(query, data)
    db.commit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Gerrit file downloader')

    parser.add_argument('--project', type=str, help='Project name', default="libreoffice")


    args = parser.parse_args()
    project_name = args.project
    database ="gerrit_"+ project_name

    dir_name ="./avatars/"+project_name

if not os.path.exists(dir_name):
    os.mkdir(dir_name)


try:
    connection = mysql.connector.connect(user='wsuseal', password='password', host='localhost', database=database,
                                             auth_plugin='mysql_native_password')
    if connection.is_connected():
        db_Info = connection.get_server_info()
        print("Connected to MySQL Server version ", db_Info)
        cursor = connection.cursor()
        cursor.execute("select database();")
        record = cursor.fetchone()
        print("You're connected to database: ", record)

        sql_reviews = """SELECT gerrit_id, avatar from people where avatar is NOT NULL"""
        cursor.execute(sql_reviews,)
        all_folks = cursor.fetchall()
        cursor.close()

        for row in all_folks:
            gerrit_id = row[0]
            url = row[1]
            download_avatar(url,dir_name,gerrit_id)
            mark_mined(gerrit_id,connection)



except Error as e:
    print("Error while connecting to MySQL", e)
else:
    connection.close()
    print("MySQL connection is closed")
