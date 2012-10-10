#!/usr/bin/env python
# -*- coding: utf-8 -*-

import mailchecker
from statushandler import I3statusHandler

if __name__ == '__main__':

    status = I3statusHandler()

    #List the modules
    mailsettings = {
        'color': '#ff0000',
        'servers': [
            {
                'host': 'www.testhost1.com',
                'port': '993',
                'ssl' : True,
                'username': 'your_username',
                'password': 'your_password',
                'pause': 20
            },
            {
                'host': 'www.testhost2.net',
                'port': '993',
                'ssl' : True,
                'username': 'your_username',
                'password': 'your_password',
                'pause': 20
            }
        ]
    }
    mailchecker = mailchecker.MailChecker(mailsettings)
    status.register_module(mailchecker)

    # start the handler
    status.run()
