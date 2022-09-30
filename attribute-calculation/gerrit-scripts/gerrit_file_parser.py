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

encoding = 'utf-8'

src_extensions=['.c','.cpp','.h','.java','.kt','.py','.s','.jsp','.gcode','.json','.aspx','.xml','.rdf''.jsf','.jad',
                '.jsf','.asm','.cc','.r','.bas','.js','.lua','.m','.go','.bat','.cs','.rss','.dtd','.script','.f',
                '.tcl','.perl','.yaml','.inc','.php','.sh','.d','.csproj','.cgi','.conf','.cxx','.cmake','.tcl',
                '.gradle','.ini','.pom' '.tk','.asp','.swift','.mm','.vb', '.rb','.scala','.md','.html',
                '.properties','.in','.x','.txt','.css','.yml','.jl','.ipynb','.sln', '.tpl','.as', '.sql',
                '.src','.erl','.tex', '.tmpl','.config', '.mod', '.xsd','.cfg', '.scss','.ac']

gerrit_URL ={"wikimedia": "https://gerrit.wikimedia.org/r/",
             "qt": "https://codereview.qt-project.org/",
             "ovirt": "https://gerrit.ovirt.org/",
             "android": "https://android-review.googlesource.com/",
             "whamcloud": "https://review.whamcloud.com/",
             "typo3":"https://review.typo3.org/",
             "couchbase":"https://review.couchbase.org/",
             "go":"https://go-review.googlesource.com/",
              "chromiumos":"https://chromium-review.googlesource.com/",
             "libreoffice":"https://gerrit.libreoffice.org/",
             }

def get_file_download_url(gerrit,change_id,file, patchid, requestid, project,branch):
    #print(file)
    file_encoded=file.replace("/", "%2F")
    project_encoded=project.replace("/", "%2F")
    branch=branch.replace("/", "%2F")
    mychangeid= project_encoded+"~" +branch +"~" +str(change_id)
    download_url = gerrit +"changes/"+mychangeid+ "/revisions/" + str(patchid) +"/files/"+file_encoded+"/download"
    #print(download_url)
    return  download_url


def downloadFile(url, request_id):
    try:
        myfile = requests.get(url, allow_redirects=True)
        rand_value = randint(1, 10000)
        location = './tmp/' + str(request_id) + "-"+ str(rand_value) + '.zip'
        file = open(location, 'wb')
        file.write(myfile.content)
        file.close()
        return location
    except:
        return None


def get_src_from_zip(ziplocation):
    try:
        zip = ZipFile(ziplocation)
        src_file = zip.open(zip.namelist()[0])
        contents = src_file.read().decode('windows-1252',errors='replace')
        src_file.close()
        return contents
    except BadZipFile:
        return ''

def extractZIP(ziplocation):
    try:
        dir_name = ziplocation.rsplit(".", 1)[0].rsplit("/", 1)[1]
        os.mkdir(ziplocation.rsplit(".", 1)[0].rsplit("/", 1)[0] + "/" + dir_name)
        with ZipFile(ziplocation, 'r') as zipref:
            zipref.extractall(ziplocation.rsplit(".", 1)[0])
        file_path = glob.glob(ziplocation.rsplit(".", 1)[0] + "/*")
        source_file = file_path[0].replace("\\\\", "/").replace("\\", "/")
        return source_file
    except BadZipFile as bz:
        return  None
    except Error as  err:
        print(err)
        return None



def get_gerrit_url(project):
    return gerrit_URL[project]


def get_files(connection,request_id, patchset_id):
    try:
        cursor=connection.cursor()
        sql_files = """SELECT file_name FROM `patch_details` 
            WHERE request_id=%s and patchset_id=%s"""
        cursor.execute(sql_files, (request_id,patchset_id,))
        files=cursor.fetchall()
        cursor.close()
        return files
    except:
        return None


def isSourceFile(source_file_name):
    file_extension = Path(source_file_name).suffix.lower()
    if file_extension in src_extensions:
        return True
    return False



def calculateComplexity(source_file):
    try:
        complexity_analysis = lizard.analyze_file(source_file)
        avg_complexity=complexity_analysis.average_cyclomatic_complexity
        num_methods= len(complexity_analysis.function_list)

        nLOC=complexity_analysis.nloc
        return (avg_complexity, num_methods, nLOC)
    except:
        print("Analysis failed for: " + source_file)
        return (0, 0, 0)

def downloadBaseFile(url):
    myfile = requests.get(url, allow_redirects=True)
    file_bytes=base64.b64decode(myfile.content)
    message = file_bytes.decode('ascii')
    return message



def save_file_details(connection,request_id, patch_id, file, num_methods, LOC_count, SRC_count, complexity):
    try:
        cursor=connection.cursor()
        sql_insert = """INSERT INTO file_details (request_id, patch_id, file_name,num_methods, LOC_count, SRC_count,complexity )
                        VALUES (%s,%s,%s,%s,%s,%s,%s)"""

        cursor.execute(sql_insert, (request_id, patch_id, file, num_methods, LOC_count, SRC_count, complexity,))
        connection.commit()
    except mysql.connector.Error as err:
        print(err)
        print("Error Code:", err.errno)
        print("SQLSTATE", err.sqlstate)
        print("Message", err.msg)


def mark_pull_finished(request_id, connection):
    cursor = connection.cursor()
    sql_project = "UPDATE request_detail SET is_mined =1 WHERE request_id=%s"
    cursor.execute(sql_project, (request_id,))
    connection.commit()





if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Gerrit file downloader')

    parser.add_argument('--project', type=str, help='Project name', default="libreoffice")


    args = parser.parse_args()
    project_name = args.project
    gerrit=get_gerrit_url(project_name)
    database ="gerrit_"+ project_name
    if not os.path.exists("tmp/"+project_name):
        os.mkdir("tmp/"+project_name)



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

        sql_reviews = """SELECT request_id, gerrit_id, project, branch, current_patch_id  
        from request_detail where is_mined=0 ORDER BY request_id DESC"""
        cursor.execute(sql_reviews,)
        all_reviews = cursor.fetchall()
        cursor.close()

        for row in all_reviews:
            request_id = row[0]
            change_id = row[1]
            project = row[2]
            branch = row[3]
            patch_id = row[4]
            print(request_id)
            files =get_files(connection,request_id,patch_id)

            for file in files:
                rand=randint(1,9999)
                file_path =file[0]
                file_name =Path(file_path).name
                if not isSourceFile(file_name):
                    continue
                file_url=get_file_download_url(gerrit,change_id,file_path,patch_id, request_id,project, branch)
                ziplocation = downloadFile(file_url, request_id)
                if ziplocation is None:
                    continue
                try:
                    file_contents =get_src_from_zip(ziplocation)
                except OSError as error:
                    continue
                LOC_count = len(file_contents.splitlines())
                tmp_location = "tmp/" + str(project_name) + "/" +str(rand) + Path(file_name).name
                file_to_write = open(tmp_location, 'w')
                file_to_write.write(file_contents)
                file_to_write.close()
                try:
                    (complexity, num_methods, src_count) = calculateComplexity(tmp_location)
                except Error as e:
                    print(e)
                    complexity = 0
                    num_methods = 0
                    LOC_count = 0
                    src_count=0
                os.remove(tmp_location)
                os.remove(ziplocation)
                save_file_details(connection,request_id, patch_id, file[0], num_methods, LOC_count, src_count, complexity)
            mark_pull_finished(request_id,connection)


except Error as e:
    print("Error while connecting to MySQL", e)
else:
    connection.close()
    print("MySQL connection is closed")
