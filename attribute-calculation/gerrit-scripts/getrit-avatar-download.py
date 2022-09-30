import csv, requests
import urllib.request
from random import randint
import json
import base64
from zipfile import ZipFile, BadZipFile

import argparse
import lizard
from pathlib import  Path
import  os
import glob
import mysql.connector
from mysql.connector import Error


gerrit_URL ={"wikimedia": "https://gerrit.wikimedia.org/r/", #not -available
             "qt": "https://codereview.qt-project.org/", #not -available
             "ovirt": "https://gerrit.ovirt.org/",
             "android": "https://android-review.googlesource.com/",
             "whamcloud": "https://review.whamcloud.com/", #not -available
             "typo3":"https://review.typo3.org/",
             "couchbase":"https://review.couchbase.org/",
             "go":"https://go-review.googlesource.com/",
              "chromiumos":"https://chromium-review.googlesource.com/",
             "libreoffice":"https://gerrit.libreoffice.org/", #not -available
             }

def get_gerrit_url(project):
    return gerrit_URL[project]


def get_file_download_url(gerrit,people_id):
    #print(file)
    download_url = gerrit +"accounts/"+str(people_id)
    #print(download_url)
    return  download_url

def get_json_response(url):
    try:
        contents = urllib.request.urlopen(url).read()
        data = json.loads(contents[4:])
        print(data)
        return  data
    except urllib.error.HTTPError:
        print("Not found user")
        return None

def updateUserAvatarURL(gerrit_id,avatarurl, connection):
    try:
        cursor = connection.cursor()
        sql_insert = """UPDATE people  SET avatar =%s WHERE gerrit_id =%s"""

        cursor.execute(sql_insert, ( avatarurl,gerrit_id, ))
        connection.commit()

    except mysql.connector.Error as err:
        print(err)
        print("Error Code:", err.errno)
        print("SQLSTATE", err.sqlstate)
        print("Message", err.msg)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Gerrit file downloader')

    parser.add_argument('--project', type=str, help='Project name', default="libreoffice")


    args = parser.parse_args()
    project_name = args.project
    gerrit=get_gerrit_url(project_name)
    database ="gerrit_"+ project_name




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

        sql_reviews = """SELECT gerrit_id, preferred_email from people"""
        cursor.execute(sql_reviews,)
        all_folks = cursor.fetchall()
        cursor.close()

        for row in all_folks:
            gerrit_id = row[0]
            email = row[1]
            url1 =get_file_download_url(gerrit, gerrit_id)
            url2 = get_file_download_url(gerrit, email)

            userdata =get_json_response(url1)
            if userdata is None:
                userdata =get_json_response(url2)
            if userdata is not None:
                avatars =userdata['avatars']
                if len(avatars)>0:
                    avatarurl =avatars[len(avatars)-1]
                    updateUserAvatarURL(gerrit_id,avatarurl['url'], connection)



except Error as e:
    print("Error while connecting to MySQL", e)
else:
    connection.close()
    print("MySQL connection is closed")
