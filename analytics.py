import json
import os
from tqdm import tqdm
import emoji
from collections import Counter

class analytics:
    def __init__(self, dir):
        self.dir=dir
        self.words = ""


    def get_words(self, replies=True):
        str = ""
        files = os.listdir(self.dir)
        for file in tqdm(files):
            path = f"{self.dir}/{file}"
            with open(path, mode="r", encoding="utf-8") as f:
                j = json.load(f)
                for parts in j:
                    for page in parts:
                        comment = page["comment"]
                        txt = comment["comment_text"]
                        str+=txt
                        if replies is True:
                            try:
                                for reply in page["replies"]:
                                    reply = reply["text"]
                                    str += reply
                            except KeyError:
                                pass
                            except TypeError:
                                str += " "

        str = str.replace("\n", " ")
        str = str.replace(".", " ")
        str = str.replace("!", " ")
        str = str.replace(",", " ")
        str = str.replace("?", " ")         #TODO: summarize replaces
        str = str.replace('"', " ")
        str = str.lower()
        str = str.replace("@", " ")
        str = str.replace("/", " ")
        str = str.replace(":", " ")
        str = str.replace("(", " ")
        str = str.replace(")", " ")
        emoji.demojize(str, use_aliases=False, delimiters=("",""))
        str = ' '.join(str.split())
        self.words += str
        return str

    def count_ranking(self):
        words = str(self.words).split(" ")
        count = Counter(words)
        count = count.most_common()
        return count

    def most_popular_comments(self, replies = True):
        from operator import itemgetter
        com = []
        files = os.listdir(self.dir)
        for file in tqdm(files):
            path = f"{self.dir}/{file}"
            with open(path, mode="r", encoding="utf-8") as f:
                j = json.load(f)
                for parts in j:
                    for page in parts:
                        comment = page["comment"]
                        txt = comment["comment_text"]
                        c_l = comment["comment_like_count"]
                        com.append([int(c_l),txt])
                        if replies is True:
                            try:
                                for reply in page["replies"]:
                                    reply = reply["text"]
                                    r_l = reply["likes"]
                                    com.append([int(r_l),reply])
                            except KeyError:
                                pass
                            except TypeError:
                                pass
        #print(com)
        com = (sorted(com, key=lambda x:x[0], reverse=True)) #TODO: Ints = 0?
        print(com)
