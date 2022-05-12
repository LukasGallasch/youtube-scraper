import requests
import json
from tqdm import tqdm
from db_connect import DB
import datetime

class YT_stats:
    def __init__(self, api_key, channel_id,db=None):
        if db is None:
            i = input("You have no database selected. Do you really want to continue? (Y/N)")
            if i.lower() != "y":
                exit()
        self.db = db
        self.api_key = api_key
        self.channel_id = channel_id
        self.channel_statistics = None
        self.video_data = None

    def get_channel_stats(self):
        url = f"https://www.googleapis.com/youtube/v3/channels?part=statistics&id={self.channel_id}&key={self.api_key}"
        json_url = requests.get(url)
        data = json.loads(json_url.text)
        try:
            data = data["items"][0]["statistics"]
        except:
            data = None

        self.channel_statistics = data
        return data

    def get_channel_video_data(self):
        channel_videos = self._get_channel_videos()
        print(channel_videos)
        print(len(channel_videos))
        parts = ["snippet","statistics","contentDetails"]
        for video_id in tqdm(channel_videos):
            for part in parts:
                data = self._get_video_data(video_id, part)
                channel_videos[video_id].update(data)
        self.video_data =channel_videos
        return channel_videos

    def get_channel_video_ids(self):
        ids = []
        channel_videos = self._get_channel_videos()
        print(channel_videos)
        print(len(channel_videos))
        for video_id in tqdm(channel_videos):
            ids.append(video_id)
        return ids


    def _get_video_data(self, video_id, part):
        url = f"https://www.googleapis.com/youtube/v3/videos?part={part}&id={video_id}&key={self.api_key}"
        json_url = requests.get(url)
        data = json.loads(json_url.text)
        try:
            data = data["items"][0][part]
        except:
            print("error")
            data =dict()
        return data



    def dump(self, path):
        if self.channel_statistics is None or self.video_data is None:
            print("data is none")
            return

        fused_data = {self.channel_id : {"channel_statistics" : self.channel_statistics, "video_data": self.video_data}}
        
        channel_title = self.video_data.popitem()[1].get("channelTitle", self.channel_id)
        channel_title = channel_title.replace(" ", "_").lower()
        file_name = channel_title + ".json"
        full_path=f"{path}/{file_name}"
        with open(full_path, mode="w", encoding="utf-8") as json_f:
            json.dump(fused_data, json_f, indent=4)
            print("Dumped data in: "+full_path)

    def _get_channel_videos(self, limit=None):
        url = f"https://www.googleapis.com/youtube/v3/search?key={self.api_key}&channelId={self.channel_id}&part=id&order=date"
        if limit is not None and isinstance(limit, int):
            url+=f"&maxResults={str(limit)}"
        vid, npt = self._get_channel_videos_per_page(url)
        while(npt is not None):
            nexturl = url + "&pageToken=" + npt
            next_vid, npt = self._get_channel_videos_per_page(nexturl)
            vid.update(next_vid)
        return vid

    def _get_channel_videos_per_page(self, url):
        json_url = requests.get(url)
        data = json.loads(json_url.text)
        channel_videos = dict()
        if "items" not in data:
            return channel_videos, None
        item_data = data["items"]
        nextPageToken = data.get("nextPageToken", None)
        for item in item_data:
            try:
                kind = item["id"]["kind"]
                if kind == "youtube#video":
                    video_id = item["id"]["videoId"]
                    channel_videos[video_id] = dict()
            except KeyError as e:
                print(e)

        return channel_videos, nextPageToken

    def extract_videos(self):
        channel_id = "UCm3_j4RLEzgMovQTRPx47MQ"
        db = DB(self.db)
        x = open("results/drachen_lord.json", mode="r")
        vids = json.load(x)

        c = 0
        for vid in vids[channel_id]["video_data"].values():

            vid_id = list(vids[channel_id]["video_data"].keys())[c]
            title = vid["title"]
            date = datetime.datetime.strptime(vid["publishedAt"], "%Y-%m-%dT%H:%M:%S%z")
            likes = vid["likeCount"]
            views = vid["viewCount"]
            try:
                comment_int = vid["commentCount"]
            except KeyError:
                comment_int = "NULL"
            sql = "INSERT INTO `videos` (`video_id`, `publishedAt`, `title`, `viewCount`, `likeCount`, `commentCount`) VALUES (%s, %s, %s, %s, %s, %s)"
            val = vid_id, date, title, views, likes, comment_int
            db.db_insert(sql, val)
            print(val)
            c += 1

class YT_Comments:
    def __init__(self, api_key, db=None):
        if db is None:
            i = input("You have no database selected. Do you really want to continue? (Y/N)")
            if i.lower() != "y":
                exit()
        self.db = DB(db)
        self.api_key = api_key
        self.comment_int = 0
        self.reply_int = 0


    def get_video_comments(self, video_id, limit=100, status="published", optional_requests=None):
        url = f"https://youtube.googleapis.com/youtube/v3/commentThreads?part=replies%2C%20snippet&order=relevance&videoId={video_id}&key={self.api_key}"
        print(url)
        vid_comments = []
        pc, npt = self._get_comments_per_page(url)

        if limit is not None and isinstance(limit, int):
            url += f"&maxResults={str(limit)}"
        if status is not None and isinstance(status, str):
            url+=f"&moderationStatus={status}"
        if optional_requests is not None and isinstance(status, str):
            url+=optional_requests

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
                    if self.db is not None:
                        self.db.db_insert(sql,val, mute=False)
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
                            if self.db is not None:
                                self.db.db_insert(sql,val, mute=False)
                            self.reply_int +=1

                    except KeyError:
                        pass

            except KeyError:
                print("No Comments")

        return page_comments, nextPageToken