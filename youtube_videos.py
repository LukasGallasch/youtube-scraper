from db_connect import *
def extract_videos():
    import json
    import mysql.connector
    import datetime
    channel_id = "UCm3_j4RLEzgMovQTRPx47MQ"

    mydb = mysql.connector.connect(
          buffered=True,
          host="localhost",
          user="Desktop-HDK",
          password="pgw6t9v6xTTQCPgH",
          database="drachenlord_analyse",
          auth_plugin="mysql_native_password",
          charset="utf8mb4",
          use_unicode=True
        )
    db = DB(mydb)
    x= open("results/drachen_lord.json", mode="r")
    vids = json.load(x)

    c = 0
    for vid in vids[channel_id]["video_data"].values():

            vid_id = list(vids[channel_id]["video_data"].keys())[c]
            title = vid["title"]
            date = datetime.datetime.strptime(vid["publishedAt"],"%Y-%m-%dT%H:%M:%S%z")
            likes = vid["likeCount"]
            views = vid["viewCount"]
            try:
                comment_int =vid["commentCount"]
            except KeyError:
                comment_int = "NULL"
            sql = "INSERT INTO `videos` (`video_id`, `publishedAt`, `title`, `viewCount`, `likeCount`, `commentCount`) VALUES (%s, %s, %s, %s, %s, %s)"
            val = vid_id, date, title,views,likes, comment_int
            db.db_insert(sql,val)
            print(val)
            c+=1
