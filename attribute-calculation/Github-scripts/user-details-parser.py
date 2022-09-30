from github import Github, UnknownObjectException  # PyGithub
import time
import  mysql.connector as mysql


g1 = Github(login_or_token="ghp_") 
g2 = Github(login_or_token="ghp_") 
g3 = Github(login_or_token="ghp_") 
g4 = Github(login_or_token="ghp_") 
g5= Github(login_or_token="ghp_") 

def getClient(sequence):
    if sequence ==0:
        return g1
    if sequence ==1:
        return g2
    if sequence ==2:
        return g3
    if sequence ==3:
        return g4
    if sequence ==4:
        return g5


class GithubUser:
  def __init__(self, id,username, userobj):
      self.full_name = userobj.name
      self.id=id
      self.login=username
      self.avatar_url = userobj.avatar_url
      self.email = userobj.email
      self.location = userobj.location
      self.bio = userobj.bio
      self.blog = userobj.blog
      self.twitter = userobj.twitter_username
      self.company = userobj.company
      self.gid = userobj.id


def store_user_to_db(user,db):
    cursor2=db.cursor()
    mySql_insert_query = """INSERT INTO user_details (id, github_id,login,full_name,avatar_url,
                                email,location,bio,blog,twitter)    
                                    VALUES (%s, %s, %s, %s,%s, %s, %s, %s,%s, %s) """

    record = (user.id,user.gid,user.login,user.full_name,user.avatar_url,user.email,user.location,
              user.bio,user.blog,user.twitter)
    #print(mySql_insert_query)
    print(record)
    cursor2.execute(mySql_insert_query, record)

    data=(1, user.id)
    query="""UPDATE selected_users SET is_mined = %s WHERE id = %s"""
    cursor2.execute(query, data)
    db.commit()

def mark_notfound(id, db):
    cursor2 = db.cursor()
    data = (-1, id)
    query = """UPDATE selected_users SET is_mined = %s WHERE id = %s"""
    cursor2.execute(query, data)
    db.commit()


def get_user_details(user_login,api):
    print(user_login)
    try:
        client=getClient(api)
        user = client.get_user(user_login)
        #store_user_to_db(user)
        return user
    except UnknownObjectException:
        print("Error: "+user_login)
        return None

db = mysql.connect(
    host = "localhost",
    user = "bosu",
    passwd = "admin",
    database="ghtorrent"
)

cursor=db.cursor()
cursor.execute("select id, login from selected_users where is_mined=0")
records = cursor.fetchall()

count=0
for row in records:
    count = (count + 1)%5

    rawdata=get_user_details(row[1].lower(), count )

    if rawdata is not None:
        userobject = GithubUser(row[0], row[1], rawdata)
        store_user_to_db(userobject,db)
    else:
        mark_notfound(row[0],db)
    if count ==0:
        time.sleep(1)