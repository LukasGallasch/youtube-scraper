import requests
import json
import datetime
from db_connect import DB
import mysql.connector
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


db=DB(mydb)


class YT_Comments:
    def __init__(self, api_key):
        self.api_key = api_key
        self.comment_int = 0
        self.reply_int = 0


    def get_video_comments(self, video_id, limit, status):
        url = f"https://youtube.googleapis.com/youtube/v3/commentThreads?part=replies%2C%20snippet&order=relevance&videoId={video_id}&key={self.api_key}"
        print(url)
        vid_comments = []
        pc, npt = self._get_comments_per_page(url)

        if limit is not None and isinstance(limit, int):
            url += f"&maxResults={str(limit)}"
        if status is not None and isinstance(status, str):
            url+=f"&moderationStatus={status}"

        while (npt is not None):
            nexturl = url + "&pageToken=" + npt
            pc, npt = self._get_comments_per_page(nexturl)
            vid_comments.append(pc)
        print(self.comment_int+self.reply_int)
        return vid_comments




    def _get_comments_per_page(self, url):
        json_url = requests.get(url)
        data = json.loads(json_url.text)
        page_comments = []
        if "items" not in data:
            return page_comments, None
        item_data = data["items"]
        nextPageToken = data.get("nextPageToken", None)
        for item in (item_data):
            try:
                kind = item["kind"]
                if kind == "youtube#comment" or "youtube#commentThread":
                    comment_text = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
                    comment_author = item["snippet"]["topLevelComment"]["snippet"]["authorDisplayName"]
                    author_id = item["snippet"]["topLevelComment"]["snippet"]["authorChannelId"]["value"]
                    comment_like_count = item["snippet"]["topLevelComment"]["snippet"]["likeCount"]
                    comment_id = item["snippet"]["topLevelComment"]["id"]
                    comment_date = datetime.datetime.strptime(item["snippet"]["topLevelComment"]["snippet"]["publishedAt"], "%Y-%m-%dT%H:%M:%S%z")
                    vid_id = item["snippet"]["videoId"]
                    sql="INSERT INTO `comments` (`comment_id`, `comment_author`, `comment_text`, `comment_date`, `comment_like_count`, `author_id`, `video_id`) VALUES (%s, %s, %s, %s, %s, %s,%s)"
                    val=comment_id,comment_author,str(comment_text),comment_date,comment_like_count,author_id,vid_id
                    db.db_insert(sql,val, mute=False)
                    self.comment_int += 1
                    try:
                        replies = item["replies"]["comments"]

                        for reply in replies:
                            parent_comment = comment_id
                            reply_txt = reply["snippet"]["textDisplay"]
                            reply_author = reply["snippet"]["authorDisplayName"]
                            reply_author_id = reply["snippet"]["authorChannelId"]["value"]
                            reply_like_count = reply["snippet"]["likeCount"]
                            reply_date = datetime.datetime.strptime(reply["snippet"]["publishedAt"],"%Y-%m-%dT%H:%M:%S%z")
                            reply_id = reply["id"]

                            sql="INSERT INTO `replies` (`reply_id`, `reply_author`, `reply_author_id`, `reply_date`, `reply_like_count`, `reply_parent`, `reply_text`, `video_id`) VALUES (%s, %s, %s, %s, %s, %s, %s,%s)"
                            val=reply_id,reply_author,reply_author_id,reply_date,reply_like_count,parent_comment,str(reply_txt),vid_id
                            db.db_insert(sql,val, mute=False)
                            self.reply_int +=1


                    except KeyError:
                        pass



            except KeyError:
                print("No Comments")

        return page_comments, nextPageToken