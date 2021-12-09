import json
import os
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup


def get_menu():
    timestamp = datetime.timestamp(datetime.now() - timedelta(days=1))
    if os.path.exists('timestamp.txt'):
        with open('timestamp.txt', 'r') as fle:
            timestamp = fle.read()
    if datetime.now().date() > datetime.fromtimestamp(float(timestamp)).date() or not os.path.exists('results.json'):
        results = {'Restaurace na Kopečku': kopecek(),
                   'Červená Cibule': cibule(),
                   'Na Zelené Lišce': zelena_liska(),
                   'U Kubíka': kubik(),
                   'Kolkovna': kolkovna(),
                   'Antal': antal(),
                   'Kantýna České Spořitalny Olbrachtova': kantyna_olbrachtova()}
        with open('results.json', 'w') as fle:
            json.dump(results, fle)
        with open('timestamp.txt', 'w') as fle:
            fle.write(str(datetime.timestamp(datetime.now())))
        return results
    with open('results.json', 'r') as fle:
        return json.load(fle)


URL = ''


def kopecek():
    result = {}
    url = URL + 'https://www.restaurace-nakopecku.cz/tydenni-poledni-nabidka/'
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:81.0) Gecko/20100101 Firefox/81.0'}
    response = requests.get(url, headers=headers)
    response.encoding = 'utf-8'
    menu_soup = BeautifulSoup(response.text, 'html.parser')

    days = menu_soup.findAll('span', attrs={'class': 'dm-name'})
    today = datetime.strftime(datetime.now(), '%#d.%#m.%Y')  # change '#' to '-' on linux

    for day in days:
        if today in day.parent.text.strip().split():
            menu = day.find_parent('div', attrs={'class': 'dailyMenu'}).findAll('tr')

            for item in menu:
                if len(item.findAll('td')) == 1:  # jedna se o nadpis
                    if item.findAll('td')[0].next_element.text.strip() == 'Menu':
                        break
                else:
                    meal = item.findAll('td')
                    name = meal[1].find('span', attrs={'class': 'td-jidlo-obsah'}).text
                    price = meal[2].text
                    result[name] = price

    if not result:
        today = datetime.strftime(datetime.now(), '%-d.%-m.%Y')  # change '#' to '-' on linux
        for day in days:
            if today in day.parent.text.strip().split():
                menu = day.find_parent('div', attrs={'class': 'dailyMenu'}).findAll('tr')

                for item in menu:
                    if len(item.findAll('td')) == 1:  # jedna se o nadpis
                        if item.findAll('td')[0].next_element.text.strip() == 'Menu':
                            break
                    else:
                        try:
                            meal = item.findAll('td')
                            name = meal[1].find('span', attrs={'class': 'td-jidlo-obsah'}).text
                            price = meal[2].text
                            result[name] = price
                        except:
                            pass
    return result


def cibule():

    def is_price(text):
        name = ' '.join(text).replace("\xa0", "")
        return name, None

    result = {}
    name, price = None, None
    url = URL + 'http://www.cervena-cibule.cz/cz/poledni-menu/'
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:81.0) Gecko/20100101 Firefox/81.0'}
    response = requests.get(url, headers=headers)
    response.encoding = 'utf-8'
    menu_soup = BeautifulSoup(response.text, 'html.parser')

    menu = menu_soup.findAll('span', attrs={'style': 'font-size: medium;'})
    for meal in menu:
        if meal.text.strip():
            text = meal.text.strip().split(',-')[0].split(' ')

            if name or price:
                name = (name + ' ' + ' '.join(text[:-1]).replace("\xa0", "")).strip().replace(' , ', ', ')
                price = text[-1]
                if not price.isnumeric():
                    name, price = is_price(text)
                    continue
                else:
                    result[name] = price + ' Kč'
                    name, price = None, None

            else:
                name = ' '.join(text[:-1]).replace("\xa0", "").strip()
                price = text[-1]

                if not name:
                    continue
                if 'nápoje' in name:
                    break
                if not price.isnumeric():
                    name, price = is_price(text)
                    continue

                result[name] = price + ' Kč'
                name, price = None, None

    return result


def kubik():
    result = {}
    url = URL + 'http://www.ukubika.cz/'
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:81.0) Gecko/20100101 Firefox/81.0'}
    response = requests.get(url, headers=headers)
    response.encoding = 'utf-8'
    menu_soup = BeautifulSoup(response.text, 'html.parser')

    menu = menu_soup.findAll('div', attrs={'class': 'daily-item'})

    for meal in menu:
        name = meal.find('div', attrs={'class': 'daily-itemName'}).text
        price = meal.find('div', attrs={'class': 'daily-itemPrice'}).text
        if name:
            result[name] = price

    return result


def antal():
    result = {}
    url = URL + 'https://www.restauraceantal.cz/aktualne'
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:81.0) Gecko/20100101 Firefox/81.0'}
    response = requests.get(url, headers=headers)
    response.encoding = 'utf-8'
    menu_soup = BeautifulSoup(response.text, 'html.parser')

    menu = menu_soup.findAll('div', attrs={'class': 'menu-item-header'})

    for meal in menu:
        name = meal.find('h3', attrs={'class': 'menu-item-name'}).text
        price = meal.find('span', attrs={'class': 'menu-item-price'}).text
        if name:
            result[name] = price.replace(',-', '') + ' Kč'

    return result


def kolkovna():
    result = {}
    url = URL + 'https://www.kolkovna.cz/cs/kolkovna-budejovicka-18/denni-menu'
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:81.0) Gecko/20100101 Firefox/81.0'}
    response = requests.get(url, headers=headers)
    response.encoding = 'utf-8'
    menu_soup = BeautifulSoup(response.text, 'html.parser')

    days = menu_soup.findAll('section')
    today = datetime.strftime(datetime.now(), '%d.%m.%Y')  # change '#' to '-' on linux

    for day in days:
        if today in day.find('h2').text.strip().split():
            menu = day.findAll('tr')
            for meal in menu:
                name = meal.find('td', attrs={'class': 'name'}).text.split(' |')[0]
                price = meal.find('td', attrs={'class': 'price'}).text
                result[name] = price

    return result


def kantyna_olbrachtova():

    def get_index(menu):
        for index, item in enumerate(menu):
            if item.text == 'Polévky':
                return index
        return 100

    result = {}
    url = URL + 'https://www.prague-catering.cz/provozovny/kantyna-ceska-sporitelna-olbrachtova/Denni-menu-Olbrachtova/'
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:81.0) Gecko/20100101 Firefox/81.0'}
    response = requests.get(url, headers=headers)
    response.encoding = 'utf-8'
    menu_soup = BeautifulSoup(response.text, 'html.parser')

    menu = menu_soup.findAll('td')
    menu = menu[get_index(menu):]
    price = ''

    for idx, item in enumerate(menu):
        if not item.find('h3'):
            if item.text.replace('\xa0', ''):
                if '100/200 g' in item.text or 'váhu' in item.text:
                    continue
                if 'Kč' in item.text:
                    price = item.text
                else:
                    name = item.text
                    try:
                        if 'Kč' in menu[idx + 1].text:
                            price = menu[idx + 1].text
                    except IndexError:
                        pass
                    if price == '29 Kč' and ' ' not in result:
                        result[' '] = "Cena za sto gramů:"
                    result[name] = price

    result = dict(list(result.items())[:-1])

    return result


def zelena_liska():
    url = URL + "https://www.zelenaliska.cz/images/poledni-menu/menu_zelenaliska.pdf"
    response = requests.get(url)
    pdf_file = "menu_zelenaliska.pdf"
    xml_file = "menu_zelenaliska.xml"

    with open(pdf_file, 'wb') as f:
        f.write(response.content)

    Pdf2xml(pdf_file).run()
    result = ParseZelenaLiska(xml_file).run()
    os.remove(pdf_file)
    os.remove(xml_file)

    return result


def coolna():
    result = {}
    url = URL + 'https://en.coolna.in/menu'
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:81.0) Gecko/20100101 Firefox/81.0'}
    response = requests.get(url, headers=headers)
    response.encoding = 'utf-8'
    menu_soup = BeautifulSoup(response.text, 'html.parser')

    menu = menu_soup.findAll('ul', attrs={'class': 'classic1I4Yd'})
    for item in menu:
        name = item.findAll('span', attrs={'class': 'wixrest-menus-item-title'})
        print(x.text for x in name)


if __name__ == '__main__':
    # print(get_menu())
    print(kantyna_olbrachtova())
