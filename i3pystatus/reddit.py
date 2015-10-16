#!/usr/bin/env python

from i3pystatus import IntervalModule
from i3pystatus.core.util import internet, require, user_open

import praw


class Reddit(IntervalModule):
    """
    This module fetches and displays posts and/or user mail/messages from
    reddit.com. Left-clicking on the display text opens the permalink/comments
    page using webbrowser.open() while right-clicking opens the URL of the
    submission directly. Depends on the Python Reddit API Wrapper (PRAW)
    <https://github.com/praw-dev/praw>.

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
        ("password", "Reddit password."),
        ('keyring_backend', 'alternative keyring backend for retrieving credentials'),
        ("subreddit", "Subreddit to monitor. Uses frontpage if unspecified."),
        ("sort_by", "'hot', 'new', 'rising', 'controversial', or 'top'."),
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
    password = ""
    keyring_backend = None
    subreddit = ""
    sort_by = "hot"
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

    @require(internet)
    def run(self):
        r = praw.Reddit(user_agent='i3pystatus')

        if self.password:
            r.login(self.username, self.password, disable_warning=True)
            unread_messages = sum(1 for i in r.get_unread())
            if unread_messages:
                d = vars(next(r.get_unread()))
                fdict = {
                    "message_unread": unread_messages,
                    "message_author": d["author"],
                    "message_subject": d["subject"],
                    "message_body": d["body"].replace("\n", " "),
                    "status": self.status["new_mail"]
                }
            else:
                fdict = {
                    "message_unread": "",
                    "status": self.status["no_mail"]
                }

        if self.subreddit:
            s = r.get_subreddit(self.subreddit)
        else:
            s = r
        if self.sort_by == 'hot':
            if not self.subreddit:
                d = vars(next(s.get_front_page(limit=1)))
            else:
                d = vars(next(s.get_hot(limit=1)))
        elif self.sort_by == 'new':
            d = vars(next(s.get_new(limit=1)))
        elif self.sort_by == 'rising':
            d = vars(next(s.get_rising(limit=1)))
        elif self.sort_by == 'controversial':
            d = vars(next(s.get_controversial(limit=1)))
        elif self.sort_by == 'top':
            d = vars(next(s.get_top(limit=1)))

        fdict["submission_title"] = d["title"]
        fdict["submission_author"] = d["author"]
        fdict["submission_points"] = d["ups"]
        fdict["submission_comments"] = d["num_comments"]
        fdict["submission_permalink"] = d["permalink"]
        fdict["submission_url"] = d["url"]
        fdict["submission_domain"] = d["domain"]
        fdict["submission_subreddit"] = d["subreddit"]

        self._permalink = fdict["submission_permalink"]
        self._url = fdict["submission_url"]

        if self.colorize and fdict["message_unread"]:
            color = self.color_orangered
            if self.mail_brackets:
                fdict["message_unread"] = "[{}]".format(unread_messages)
        else:
            color = self.color

        if len(fdict["submission_title"]) > self.title_maxlen:
            title = fdict["submission_title"][:(self.title_maxlen - 3)] + "..."
            fdict["submission_title"] = title

        if self.username:
            u = r.get_redditor(self.username)
            fdict["link_karma"] = u.link_karma
            fdict["comment_karma"] = u.comment_karma
        else:
            fdict["link_karma"] = ""
            fdict["comment_karma"] = ""

        full_text = self.format.format(**fdict)
        self.output = {
            "full_text": full_text,
            "color": color,
        }

    def open_mail(self):
        user_open('https://www.reddit.com/message/unread/')

    def open_permalink(self):
        user_open(self._permalink)

    def open_link(self):
        user_open(self._url)
