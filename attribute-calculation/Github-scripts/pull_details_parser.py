from datetime import timezone, datetime
import time
from pprint import pprint

import argparse
from github.GithubException import UnknownObjectException, RateLimitExceededException, GithubException

"""
Created on Mon Mar  7 16:39:55 2022

@author: Sayma, Amiangshu
"""

from github import Github

import mysql.connector
import pathlib
from mysql.connector import Error
import requests, csv, os

src_extensions=['.c','.cpp','.h','.java','.kt','.py','.s','.jsp','.gcode','.json','.aspx','.xml','.rdf''.jsf','.jad',
                '.jsf','.asm','.cc','.r','.bas','.js','.lua','.m','.go','.bat','.cs','.rss','.dtd','.script','.f',
                '.tcl','.perl','.yaml','.inc','.php','.sh','.d','.csproj','.cgi','.conf','.pm','.cmake','.tcl',
                '.gradle','.ini','.pom' '.tk','.asp','.swift','.mm','.vb', '.rb','.scala','.md','.html',
                '.properties','.in','.x','.txt','.css','.yml','.jl','.ipynb','.sln', '.tpl','.as', '.sql', 
                '.src','.erl','.tex', '.tmpl','.config', '.mod', '.xsd','.cfg', '.scss','.ac']

log_in_tokens =["ghp_", 
                "ghp_", 
                "ghp_", 
                "ghp_", 
                "ghp_", 
                "ghp_", 
                "ghp_", 
                "ghp_", 
                "ghp_", 
                "ghp_", 
                "ghp_", 
                "ghp_", 
                "ghp_", 
                "ghp_", 
                "ghp_", 
                "ghp_", 
                ]


import lizard
from pathlib import  Path

encoding = 'utf-8'

def getClient(sequence):
    login_token =log_in_tokens[sequence]
    github =Github(login_or_token=login_token)
    return  github


def get_pull_requests(project_id, connection):
    cursor = connection.cursor()
    sql_pulls = "SELECT id, pullreq_id from pull_requests where base_repo_id=%s and is_mined=0"
    cursor.execute(sql_pulls, (project_id,))
    pulls =cursor.fetchall()
    cursor.close()
    return  pulls

def mark_project_finished(project_id, connection):
    cursor = connection.cursor()
    sql_project = "UPDATE projects SET is_mined =1 WHERE project_id=%s"
    cursor.execute(sql_project, (project_id,))
    connection.commit()

def mark_pull_finished(pull_id, connection):
    cursor = connection.cursor()
    sql_project = "UPDATE pull_requests SET is_mined =1 WHERE id=%s"
    cursor.execute(sql_project, (pull_id,))
    connection.commit()

def wait_rate_limit_expiration(gitclient):
    rate = gitclient.get_rate_limit()
    remaining = rate.core.remaining
    if remaining < 10:
        reset = rate.core.reset.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        seconds = (reset - now).total_seconds()
        print(f"Rate limit exceeded")
        print(f"Reset is in {seconds:.3g} seconds.")
        print(f"Waiting for {seconds:.3g} seconds...")
        time.sleep(seconds + 10)
        print("Done waiting - resume!")

def get_pull_detail(pull_number, repo, gitclient, retrying=False):
    try:
        pull_obj =repo.get_pull(pull_number)
    except UnknownObjectException as err:
        return None
    except GithubException as ghe:
        return None
    except requests.exceptions.ConnectionError as cee:
        time.sleep(300)
        if not retrying:
            return get_pull_detail(pull_number,repo,gitclient,retrying=True)
        else:
            return None
    except RateLimitExceededException as ree:
        wait_rate_limit_expiration(gitclient)
        if retrying is True:
            return None #send retry failed

        return  get_pull_detail(pull_number,repo, gitclient, retrying=True)
    return  pull_obj

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



def save_file_details(connection,project_id, pull_id, file_name, LOC_count, srcLOC, complexity, num_methods,
                      file_add, file_delete, total_churn, file_status):
    try:
        cursor=connection.cursor()
        sql_insert = """INSERT INTO pull_files (pull_id, project_id, file_name,LOC_count, SRC_count, complexity,
                        num_methods, additions, deletions, total_churn, file_status )
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s, %s, %s,%s)"""

        cursor.execute(sql_insert, (pull_id, project_id, file_name, LOC_count, srcLOC,
                                    complexity, num_methods, file_add, file_delete, total_churn, file_status,))
        connection.commit()
    except mysql.connector.Error as err:
        print(err)
        print("Error Code:", err.errno)
        print("SQLSTATE", err.sqlstate)
        print("Message", err.msg)

def save_pull_details(connection,project_id, pull_id, p_commit_count,p_changed_files, p_additions,
                                      p_deletions, p_created_at, p_merged_At, p_closed_at, p_num_comments,
                                      p_num_review_comments, p_state, p_merge_sha ):
    try:
        cursor=connection.cursor()
        sql_insert = """INSERT INTO pull_details (pull_id, project_id, commit_count, num_changed_files,
                        additions, deletions, created_at, merged_at, closed_at, total_comments, 
                        review_comments, current_state, merge_sha  )
                        VALUES (%s,%s,%s,%s,%s,%s,%s, %s, %s,%s, %s, %s, %s)"""

        cursor.execute(sql_insert, (pull_id, project_id, p_commit_count, p_changed_files,
                                    p_additions, p_deletions, p_created_at, p_merged_At, p_closed_at, p_num_comments,
                                    p_num_review_comments, p_state, p_merge_sha))
        connection.commit()
        return True
    except mysql.connector.Error as err:
        print(err)
        print("Error Code:", err.errno)
        print("SQLSTATE", err.sqlstate)
        print("Message", err.msg)

    return  False

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Github pull request downloader')

    parser.add_argument('--seq', type=int, help='Client ID', default=0)
    parser.add_argument('--part', type=int, help='Partition', default=2)

    args = parser.parse_args()
    clientID = args.seq
    PART = args.part


def analyze_files(pull_files):
    try:
        for file in pull_files:
            file_name = str(file.filename)
            file_add = file.additions
            file_delete = file.deletions
            total_churn = file.changes
            file_status = file.status
            if isSourceFile(file_name):
                try:
                    file_detail = requests.get(file.raw_url, allow_redirects=True, timeout=120)
                    source_code_lines = file_detail.content
                    tmp_location = "tmp/" + str(PART) + "/" + Path(file_name).name
                    file_to_write = open(tmp_location, 'wb')
                    file_to_write.write(file_detail.content)
                    file_to_write.close()
                    (complexity, num_methods, src_count) = calculateComplexity(tmp_location)
                    LOC_count = len(source_code_lines.splitlines())
                    os.remove(tmp_location)
                except requests.exceptions.ReadTimeout as rto:
                    print(rto)
                    time.sleep(300)
                    complexity = 0
                    num_methods = 0
                    src_count = 0
                    LOC_count = 0
                except requests.exceptions.ConnectionError as rec:
                    print(rec)
                    time.sleep(300)
                    complexity = 0
                    num_methods = 0
                    src_count = 0
                    LOC_count = 0
            else:
                complexity = 0
                num_methods = 0
                src_count = 0
                LOC_count = 0

            save_file_details(connection, project_id, pull_id, file_name, LOC_count, src_count, complexity,
                              num_methods, file_add, file_delete, total_churn, file_status)
    except RateLimitExceededException as ree:
        wait_rate_limit_expiration(gitclient)
    except GithubException as gec:
        return None
    #except requests.exceptions.ConnectionError:
    #    return  None


try:
    connection = mysql.connector.connect(user='wsuseal', password='password', host='localhost', database='ghtorrent',
                                         auth_plugin='mysql_native_password')
    if connection.is_connected():
        db_Info = connection.get_server_info()
        print("Connected to MySQL Server version ", db_Info)
        cursor = connection.cursor()
        cursor.execute("select database();")
        record = cursor.fetchone()
        print("You're connected to database: ", record)


        sql_projects = "SELECT project_id, url from projects where is_mined=%s"
        cursor.execute(sql_projects, (PART,))
        all_projects = cursor.fetchall()
        cursor.close()
        #print(all_projects)
        num_projects=len(all_projects)

        for row in all_projects:
            project_id =row[0]
            url =row[1]
            name_parts = url.split("/", 6)
            repo_name = name_parts[4] + "/" + name_parts[5]
            print(repo_name)
            try:
                gitclient=getClient(clientID)

                try:
                    repo =gitclient.get_repo(repo_name, lazy=False)
                except RateLimitExceededException as REE:
                    wait_rate_limit_expiration(gitclient)
                    repo = gitclient.get_repo(repo_name, lazy=False)

                all_pulls=get_pull_requests(project_id, connection)
                for pull_request in all_pulls:
                    pull_id=pull_request[0]
                    print("parsing: "+ str(pull_request[0]))
                    pull_detail = get_pull_detail(pull_request[1], repo, gitclient)
                    if pull_detail is None:
                        mark_pull_finished(pull_id, connection)
                        continue

                    p_commit_count=pull_detail.commits
                    p_changed_files=pull_detail.changed_files
                    p_closed_at=pull_detail.closed_at
                    p_created_at =pull_detail.created_at
                    p_merged_At=pull_detail.merged_at
                    p_num_comments=pull_detail.comments
                    p_additions=pull_detail.additions
                    p_deletions=pull_detail.deletions
                    p_merge_sha=pull_detail.merge_commit_sha
                    p_num_review_comments =pull_detail.review_comments
                    p_state=pull_detail.state
                    saved=save_pull_details(connection, project_id, pull_id,p_commit_count,p_changed_files, p_additions,
                                      p_deletions, p_created_at, p_merged_At, p_closed_at, p_num_comments,
                                      p_num_review_comments, p_state, p_merge_sha  )

                    if saved is False:
                        mark_pull_finished(pull_id, connection)
                        continue

                    try:
                        pull_files=pull_detail.get_files()
                    except RateLimitExceededException as ree:
                        wait_rate_limit_expiration(gitclient)
                        pull_files = pull_detail.get_files()
                    analyze_files(pull_files)
                    mark_pull_finished(pull_id, connection)

                mark_project_finished(project_id, connection)

            except UnknownObjectException as pe:
                print(pe)
                print("Project not found")
                mark_project_finished(project_id, connection)


except Error as e:
    print("Error while connecting to MySQL", e)
else:
    connection.close()
    print("MySQL connection is closed")

