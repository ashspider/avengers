import os
UPLOAD_FOLDER = '/tmp/'
WTF_CSRF_ENABLED = True
SECRET_KEY = os.urandom(50)
MONGO_URI = "mongodb://admin:admin123@ds149134.mlab.com:49134/heroku_2g2nnp30"


#Arvind's config (used in send_mail.py)
API_KEY='eaaa281772bb987593385c3af8fbc4a0-b6183ad4-429ef9c8'
SANDBOX='sandbox9f44f4a447194480a2f069d7d4a53297.mailgun.org'
SENDER='postmaster@sandbox9f44f4a447194480a2f069d7d4a53297.mailgun.org'
