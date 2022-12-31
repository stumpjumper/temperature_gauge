#!/usr/bin/env python

import yagmail
import ast
import time

home_dir = os.environ['HOME']
app_password_file = home_dir + '/.ssh/temp_warning_email'

with open(app_password_file) as f:
    data = f.read()

app_password_dict = ast.literal_eval(data)
user = app_password_dict["user"]
app_password = app_password_dict["app_password"]
to = app_password_dict["to"]

warning_temp = 37

subject = 'WARNING: Refrig temp too high"'
message_list = []
message_list.append(subject)
message_list.append(time.asctime())
message_list.append("Temp is above %s degrees" % warning_temp)
message = "\n".join(message_list)

content = [message]

with yagmail.SMTP(user, app_password) as yag:
    yag.send(to, subject, content)
    print('Sent email successfully')
