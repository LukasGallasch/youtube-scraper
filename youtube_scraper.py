import mysql.connector
import requests
import json
from tqdm import tqdm
from db_connect import DB
import datetime


class YT_stats:
    def __init__(self, api_key, channel_id, database=None):
        if isinstance(database, mysql.connector.connection.MySQLConnection):
            self.db = DB(database)
        else:
            self.db = None
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
        except KeyError:
            data = None

        self.channel_statistics = data
        return data

    def get_channel_video_data(self):
        channel_videos = self._get_channel_videos()
        print(channel_videos)
        print(len(channel_videos))
        parts = ["snippet", "statistics", "contentDetails"]
        for video_id in tqdm(channel_videos):
            for part in parts:
                data = self._get_video_data(video_id, part)
                channel_videos[video_id].update(data)
        self.video_data = channel_videos
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
            print("Error!")
            data = dict()
        return data

    def dump(self, path):
        if self.channel_statistics is None or self.video_data is None:
            print("data is none")
            return

        fused_data = {
            self.channel_id: {
                "channel_statistics": self.channel_statistics,
                "video_data": self.video_data,
            }
        }

        channel_title = self.video_data.popitem()[1].get(
            "channelTitle", self.channel_id
        )
        channel_title = channel_title.replace(" ", "_").lower()
        file_name = channel_title + ".json"
        full_path = f"{path}/{file_name}"
        with open(full_path, mode="w", encoding="utf-8") as output_json:
            json.dump(fused_data, output_json, indent=4)
            print("Dumped data in: " + full_path)

    def _get_channel_videos(self, limit=None):
        url = f"https://www.googleapis.com/youtube/v3/search?key={self.api_key}&channelId={self.channel_id}&part=id&order=date"
        if limit is not None and isinstance(limit, int):
            url += f"&maxResults={str(limit)}"
        video, nextPageToken = self._get_channel_videos_per_page(url)
        while nextPageToken is not None:
            nexturl = url + "&pageToken=" + nextPageToken
            next_vid, nextPageToken = self._get_channel_videos_per_page(nexturl)
            video.update(next_vid)
        return video

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


class YT_Comments:
    def __init__(self, api_key: str, database=None):
        if isinstance(database, mysql.connector.connection.MySQLConnection):
            self.db = DB(database)
        else:
            self.db = None
        self.api_key = api_key
        self.commentCount = 0
        self.replyCount = 0
        self.insertedComments = 0
        self.insertedReplies = 0

    def get_video_comments(
        self,
        video_id: str,
        limit: int = 100,
        status: str = "published",
        optional_requests: str = None,
    ):
        url = f"https://youtube.googleapis.com/youtube/v3/commentThreads?part=replies%2C%20snippet&order=relevance&videoId={video_id}&key={self.api_key}"
        print(url)
        vid_comments = []
        pageComments, nextPageToken = self._get_comments_per_page(url)

        if limit is not None and isinstance(limit, int):
            url += f"&maxResults={str(limit)}"
        if status is not None and isinstance(status, str):
            url += f"&moderationStatus={status}"
        if optional_requests is not None and isinstance(status, str):
            url += optional_requests

        while nextPageToken is not None:
            nexturl = url + "&pageToken=" + nextPageToken
            pageComments, nextPageToken = self._get_comments_per_page(nexturl)
            vid_comments.append(pageComments)
        print(
            f"""
///////////////////////////////////////////////////////////////////////////////////
The scraper has handled and added so many replies and comments:
Comments: Handled {self.commentCount}, Inserted: {self.insertedComments}
Replies: Handled: {self.replyCount}, Inserted: {self.insertedReplies}
Comments + Replies: Handled: {self.commentCount+self.replyCount}, Inserted: {self.insertedComments+self.insertedReplies}
///////////////////////////////////////////////////////////////////////////////////         
            """
        )
        return vid_comments

    def _get_comments_per_page(self, url):
        json_url = requests.get(url)
        data = json.loads(json_url.text)
        pageComments = []
        if "items" not in data:
            return pageComments, None
        itemData = data["items"]
        nextPageToken = data.get("nextPageToken", None)
        for item in itemData:
            try:
                kind = item["kind"]
                if kind == "youtube#comment" or "youtube#commentThread":
                    commentText = item["snippet"]["topLevelComment"]["snippet"][
                        "textDisplay"
                    ]
                    commentAuthor = item["snippet"]["topLevelComment"]["snippet"][
                        "authorDisplayName"
                    ]
                    commentAuthorId = item["snippet"]["topLevelComment"]["snippet"][
                        "authorChannelId"
                    ]["value"]
                    commentLikeCount = item["snippet"]["topLevelComment"]["snippet"][
                        "likeCount"
                    ]
                    commentId = item["snippet"]["topLevelComment"]["id"]
                    commentDate = datetime.datetime.strptime(
                        item["snippet"]["topLevelComment"]["snippet"]["publishedAt"],
                        "%Y-%m-%dT%H:%M:%S%z",
                    )
                    videoId = item["snippet"]["videoId"]
                    sql = "INSERT IGNORE INTO `comments` (`comment_id`, `comment_author`, `comment_text`, `comment_date`, `comment_like_count`, `author_id`, `video_id`) VALUES (%s, %s, %s, %s, %s, %s,%s)"
                    val = (
                        commentId,
                        commentAuthor,
                        str(commentText),
                        commentDate,
                        commentLikeCount,
                        commentAuthorId,
                        videoId,
                    )
                    if self.db is not None:
                        self.insertedComments += self.db.db_insert(sql, val)

                    self.commentCount += 1
                    try:
                        replies = item["replies"]["comments"]
                        replies_list = []
                        replies_dict_list = []
                        for reply in replies:
                            parentComment = commentId
                            replyText = reply["snippet"]["textDisplay"]
                            replyAuthor = reply["snippet"]["authorDisplayName"]
                            replyAuthorId = reply["snippet"]["authorChannelId"]["value"]
                            replyLikeCount = reply["snippet"]["likeCount"]
                            replyDate = datetime.datetime.strptime(
                                reply["snippet"]["publishedAt"], "%Y-%m-%dT%H:%M:%S%z"
                            )
                            replyId = reply["id"]

                            sql = "INSERT IGNORE INTO `replies` (`reply_id`, `reply_author`, `reply_author_id`, `reply_date`, `reply_like_count`, `reply_parent`, `reply_text`, `video_id`) VALUES (%s, %s, %s, %s, %s, %s, %s,%s)"  # SQL-Query
                            val = (
                                replyId,
                                replyAuthor,
                                replyAuthorId,
                                replyDate,
                                replyLikeCount,
                                parentComment,
                                str(replyText),
                                videoId,
                            )
                            replies_list.append(val)
                            reply_dict = {
                                "replyID": replyId,
                                "replyAuthor": replyId,
                                "replyAuthorID": replyAuthorId,
                                "replyText": replyText,
                                "replyDate": str(replyDate),
                                "replyLikes": replyLikeCount,
                            }
                            replies_dict_list.append(reply_dict)
                        self.replyCount += len(replies_list)
                        if self.db is not None:
                            self.insertedReplies += self.db.db_insertmany(
                                sql, replies_list
                            )

                        pageComments.append(
                            {
                                "commentID": commentId,
                                "commentAuthor": commentAuthor,
                                "commentAuthorID": commentAuthorId,
                                "commentText": commentText,
                                "commentDate": str(commentDate),
                                "commentLikes": commentLikeCount,
                                "replies": replies_dict_list,
                            }
                        )

                    except KeyError:  # Except Comment has no public replies
                        pass

            except KeyError:  # Except Video has no public comments
                print("No Comments")

        return pageComments, nextPageToken
