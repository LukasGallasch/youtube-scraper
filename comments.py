import requests
import json

class YT_Comments:
    def __init__(self, api_key):
        self.api_key = api_key
        self.comment_int = 0


    def get_video_comments(self, video_id, limit):
        url = f"https://youtube.googleapis.com/youtube/v3/commentThreads?part=replies%2C%20snippet&order=relevance&videoId={video_id}&key={self.api_key}"
        vid_comments = []
        pc, npt = self._get_comments_per_page(url)

        if limit is not None and isinstance(limit, int):
            url += f"&maxResults={str(limit)}"
        while (npt is not None):
            nexturl = url + "&pageToken=" + npt
            pc, npt = self._get_comments_per_page(nexturl)
            vid_comments.append(pc)
        print(url)
        print(self.comment_int)
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
                    comment_text = item["snippet"]["topLevelComment"]["snippet"]["textOriginal"]
                    comment_author = item["snippet"]["topLevelComment"]["snippet"]["authorDisplayName"]
                    author_id = item["snippet"]["topLevelComment"]["snippet"]["authorChannelId"]["value"]
                    comment_like_count = item["snippet"]["topLevelComment"]["snippet"]["likeCount"]
                    comment_date = item["snippet"]["topLevelComment"]["snippet"]["publishedAt"]
                    comment = {"comment_text" : comment_text,
                               "comment_author" : comment_author,
                               "comment_author_id" : author_id,
                               "comment_like_count" : comment_like_count,
                               "comment_date" : comment_date}
                    replies_l = []
                    self.comment_int += 1
                    try:
                        replies = item["replies"]["comments"]

                        for reply in replies:
                            reply_txt = reply["snippet"]["textOriginal"]
                            reply_author = reply["snippet"]["authorDisplayName"]
                            reply_author_id = reply["snippet"]["authorChannelId"]["value"]
                            reply_like_count = reply["snippet"]["likeCount"]
                            reply_date = reply["snippet"]["publishedAt"]
                            reply_dict = {"text" : reply_txt,
                                          "author" : reply_author,
                                          "author_id" : reply_author_id,
                                          "likes" : reply_like_count,
                                          "date" : reply_date}
                            replies_l.append(reply_dict)
                            self.comment_int +=1


                    except KeyError:
                        replies_l.append(None)

                    comment_dict = {
                        "comment": comment,
                        "replies": replies_l,
                    }
                    page_comments.append(comment_dict)

            except KeyError:
                print("No Comments")

        return page_comments, nextPageToken