from web_app import app
import requests

api= app.config['API_KEY']
sandbox = app.config['SANDBOX']
sender = app.config['SENDER']
request_url = 'https://api.mailgun.net/v2/{0}/messages'.format(sandbox)


def send_mail(recipient,subject,html):
    return requests.post(
        request_url,
        auth=('api',api),
        data={'from': sender,
              'to': recipient,
              'subject': subject,
              'html': html})

# print 'Status: {0}'.format(request.status_code)
# print 'Body:   {0}'.format(request.text)

