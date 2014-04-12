#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from i3pystatus.mail import Backend
import subprocess

class MaildirMail(Backend):
    """
    Checks for local mail in Maildir
    """

    settings = (
            "mailbox",
            )
    required = ("mailbox",)

    mailbox=""

    @property
    def unread(self):
        p = subprocess.Popen(['ls','-l',self.mailbox+'/new'], stdout=subprocess.PIPE)
        stdout, stderr = p.communicate()
        stdout=stdout.decode('utf8')
        return len(stdout.split('\n'))-2

Backend = MaildirMail
