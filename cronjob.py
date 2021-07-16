import yagmail
import os
import json
from datetime import datetime, timedelta

from main import kopecek, kolkovna, antal, kantyna_olbrachtova


def send_mail():

    yag = yagmail.SMTP('menu.budejovicka@gmail.com', 'sQW15uebG')
    subject = 'Denní menu Budějovická'

    timestamp = datetime.timestamp(datetime.now() - timedelta(days=1))
    if os.path.exists('timestamp.txt'):
        with open('timestamp.txt', 'r') as fle:
            timestamp = fle.read()
    if datetime.now().date() > datetime.fromtimestamp(float(timestamp)).date():
        results = {'Restaurace na Kopečku': kopecek(),
                   'Kolkovna': kolkovna(),
                   'Antal': antal(),
                   'Kantýna České Spořitalny Olbrachtova': kantyna_olbrachtova()}
        with open('results.json', 'w') as fle:
            json.dump(results, fle)
        with open('timestamp.txt', 'w') as fle:
            fle.write(str(datetime.timestamp(datetime.now())))
    else:
        with open('results.json', 'r') as fle:
            results = json.load(fle)

    html = [
        '<!DOCTYPE html>',
        '<html><head> <title>Polední menu Budějovická</title>',
        '</head> <body>',
        '<div>',
        '<h1>Polední menu</h1>'
    ]

    for restaurant, menu in results.items():
        html.append(f'<h3> {restaurant}</h3>')
        html.append('<table><tbody>')

        for meal, price in menu.items():
            html.append(f'<tr><td>{meal}</td><td>{price}</td></tr>')
        
        html.append('</tbody></table>')
    html.append('</div></body></html>')

    with open('emails.txt', 'a') as fle:
        recipients = fle.read().split('\n')

    for email in recipients:
        try:
            yag.send(email, subject, ''.join(html))
        except:
            pass


if __name__ == '__main__':
    send_mail()
