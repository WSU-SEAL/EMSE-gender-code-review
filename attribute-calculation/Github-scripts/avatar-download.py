import requests
import  mysql.connector as mysql
import cv2

headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:60.0) Gecko/20100101 Firefox/60.0",
           "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
           "Accept-Language": "en-US,en;q=0.9"
           }



def download_avatar(url, gid):
    img_data = requests.get(url=url, headers=headers).content
    image_name="avatars2/" + str(gid) + '.jpg'
    with open(image_name, 'wb') as handler:
        handler.write(img_data)

    image = cv2.imread(image_name)

    try:
        dummy = image.shape  # this line will throw the exception
    except:
        raise Exception("Invalid image")


def mark_mined(id, db):
    cursor2 = db.cursor()
    data = (1, id)
    query = """UPDATE user_details SET is_mined = %s WHERE id = %s"""
    cursor2.execute(query, data)
    db.commit()

db = mysql.connect(
    host = "localhost",
    user = "wsuseal",
    passwd = "password",
    database="ghtorrent"
)

cursor=db.cursor()
cursor.execute("select id, github_id, avatar_url from user_details where is_mined=0")
records = cursor.fetchall()

count=0
for row in records:
    try:
        print("Downloading: " + row[2])
        download_avatar(row[2], row[1])
        mark_mined(row[0],db)
    except:
        print("Error: "+row[1])
        exit(1)