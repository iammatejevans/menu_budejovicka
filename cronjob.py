import yagmail
import os
import json
from datetime import datetime, timedelta

from main import kopecek, kolkovna, antal, kantyna_olbrachtova

def send_mail():

    yag = yagmail.SMTP('menu.budejovicka@gmail.com', 'sQW15uebG')
    recipients = ['iam.matejevans@gmail.com']
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
        '<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css"', 
        'rel="stylesheet" integrity="sha384-EVSTQN3/azprG1Anm3QDgpJLIm9Nao0Yz1ztcQTwFspd3yD65VohhpuuCOmLASjC"', 
        'crossorigin="anonymous">',
        '<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/js/bootstrap.bundle.min.js"',
        'integrity="sha384-MrcW6ZMFYlzcLA8Nl+NtUVF0sA7MsXsP1UyJoMp4YLEuNSfAP+JcXn/tWtIaxVXM"', 
        'crossorigin="anonymous"></script>',
        '</head> <body>',
        '<div class="container mb-5">',
        '<h1 class="mt-5">Polední menu</h1>'
    ]

    for restaurant, menu in results.items():
        html.append(f'<h3 class="mt-5"> {restaurant}</h3>')
        html.append('<table class="table mb-3 table-hover"><tbody>')

        for meal, price in menu.items():
            html.append(f'<tr><td>{meal}</td><td>{price}</td></tr>')
        
        html.append('</tbody></table>')
    html.append('</div></body></html>')

    for email in recipients:
        yag.send(email, subject, ''.join(html))


if __name__ == '__main__':
    send_mail()
