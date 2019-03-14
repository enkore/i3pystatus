#!/usr/bin/env python

import re
import praw

from i3pystatus import IntervalModule
from i3pystatus.core.util import internet, require, user_open


class Reddit(IntervalModule):
    """
    This module fetches and displays posts and/or user mail/messages from
    reddit.com. Left-clicking on the display text opens the permalink/comments
    page using webbrowser.open() while right-clicking opens the URL of the
    submission directly. Depends on the Python Reddit API Wrapper (PRAW)
    <https://github.com/praw-dev/praw>.

    PRAW must be configured for this module to work.
    https://praw.readthedocs.io/en/latest/

    .. rubric:: Available formatters

    * {submission_title}
    * {submission_author}
    * {submission_points}
    * {submission_comments}
    * {submission_permalink}
    * {submission_url}
    * {submission_domain}
    * {submission_subreddit}
    * {message_unread}
    * {message_author}
    * {message_subject}
    * {message_body}
    * {link_karma}
    * {comment_karma}

    """

    settings = (
        ("format", "Format string used for output."),
        ("username", "Reddit username."),
        ('keyring_backend', 'alternative keyring backend for retrieving \
                            credentials'),
        ("subreddit", "Subreddit to monitor. Uses frontpage if unspecified."),
        ("sort_by", "'hot', 'new', 'rising', 'controversial', or 'top'."),
        ("time_filter", "'all', 'day','hour', 'month', 'week', 'year'"),
        ("color", "Standard color."),
        ("colorize", "Enable color change on new message."),
        ("color_orangered", "Color for new messages."),
        ("mail_brackets", "Display unread message count in square-brackets."),
        ("title_maxlen", "Maximum number of characters to display in title."),
        ("interval", "Update interval."),
        ("status", "New message indicator."),
    )
    format = "[{submission_subreddit}] {submission_title} ({submission_domain})"
    username = ""
    keyring_backend = None
    subreddit = ""
    sort_by = "hot"
    time_filter = "all"
    color = "#FFFFFF"
    colorize = True
    color_orangered = "#FF4500"
    mail_brackets = False
    title_maxlen = 80
    interval = 300
    status = {
        "new_mail": "✉",
        "no_mail": "",
    }

    on_leftclick = "open_permalink"

    _permalink = ""
    _url = ""

    subreddit_pattern = re.compile(r"{submission_\w+}")
    message_pattern = re.compile(r"{message_\w+\}")
    user_pattern = re.compile(r"{comment_karma}|{link_karma}")

    reddit_session = None

    @require(internet)
    def run(self):
        reddit = self.connect()
        fdict = {}

        if self.message_pattern.search(self.format):
            fdict.update(self.get_messages(reddit))
        if self.subreddit_pattern.search(self.format):
            fdict.update(self.get_subreddit(reddit))
        if self.user_pattern.search(self.format):
            fdict.update(self.get_redditor(reddit))

        if self.colorize and fdict.get("message_unread", False):
            color = self.color_orangered
            if self.mail_brackets:
                fdict["message_unread"] = "[{}]".format(fdict["message_unread"])
        else:
            color = self.color

        self.data = fdict
        full_text = self.format.format(**fdict)
        self.output = {
            "full_text": full_text,
            "color": color,
        }

    def connect(self):
        if not self.reddit_session:
            self.reddit_session = praw.Reddit(user_agent='i3pystatus',
                                              disable_update_check=True)
        return self.reddit_session

    def get_redditor(self, reddit):
        redditor_info = {}
        u = reddit.redditor(self.username)
        redditor_info["link_karma"] = u.link_karma
        redditor_info["comment_karma"] = u.comment_karma
        return redditor_info

    def get_messages(self, reddit):
        message_info = {
            "message_unread": "",
            "status": self.status["no_mail"],
            "message_author": "",
            "message_subject": "",
            "message_body": ""
        }
        unread_messages = sum(1 for i in reddit.inbox.unread())
        if unread_messages:
            d = vars(next(reddit.inbox.unread()))
            message_info = {
                "message_unread": unread_messages,
                "message_author": d["author"],
                "message_subject": d["subject"],
                "message_body": d["body"].replace("\n", " "),
                "status": self.status["new_mail"]
            }
        return message_info

    def get_subreddit(self, reddit):
        fdict = {}
        subreddit_dict = {}
        if self.subreddit:
            s = reddit.subreddit(self.subreddit)
        else:
            s = reddit.front

        if self.sort_by == 'hot':
            subreddit_dict = vars(next(s.hot(limit=1)))
        elif self.sort_by == 'new':
            subreddit_dict = vars(next(s.new(limit=1)))
        elif self.sort_by == 'rising':
            try:
                subreddit_dict = vars(next(s.rising(limit=1)))
            except StopIteration:
                return
        elif self.sort_by == 'controversial':
            subreddit_dict = vars(next(s.controversial(
                time_filter=self.time_filter,
                limit=1))
            )
        elif self.sort_by == 'top':
            subreddit_dict = vars(next(s.top(limit=1)))
        fdict["submission_title"] = subreddit_dict["title"]
        fdict["submission_author"] = subreddit_dict["author"]
        fdict["submission_points"] = subreddit_dict["ups"]
        fdict["submission_comments"] = subreddit_dict["num_comments"]
        fdict["submission_permalink"] = subreddit_dict["permalink"]
        fdict["submission_url"] = subreddit_dict["url"]
        fdict["submission_domain"] = subreddit_dict["domain"]
        fdict["submission_subreddit"] = subreddit_dict["subreddit"]

        if len(fdict["submission_title"]) > self.title_maxlen:
            title = fdict["submission_title"][:(self.title_maxlen - 3)] + "..."
            fdict["submission_title"] = title

        self._permalink = fdict["submission_permalink"]
        self._url = fdict["submission_url"]

        return fdict

    def open_mail(self):
        user_open('https://www.reddit.com/message/unread/')

    def open_permalink(self):
        user_open(self._permalink)

    def open_link(self):
        user_open(self._url)
