from youtube_scraper import YT_Comments, YT_stats
import json
import mysql.connector

mydb = mysql.connector.connect(
    buffered=True,
    host="",
    user="",
    password="",
    database="",
    auth_plugin="mysql_native_password",
    charset="utf8mb4",  # utf8mb4 recommended
    use_unicode=True,
)
api_key = ""  # Here goes your Google API Key
channel_id = ""  # Here goes the Youtube-Channel ID

comments = YT_Comments(api_key, mydb)
with open("comments.txt", mode="w") as co:
    json.dump(comments.get_video_comments(""), co, indent=4)
stats = YT_stats(api_key, channel_id, mydb)
stats.get_channel_video_data()
stats.dump("some/path")
