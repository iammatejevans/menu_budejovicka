import json
import os
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup


def get_menu():
    os.environ['SCRAPERAPI_KEY'] = '1fe57d709a9593808bb9e9f229260d4c'
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
        return results
    with open('results.json', 'r') as fle:
        return json.load(fle)


#os.environ['SCRAPERAPI_KEY'] = '1fe57d709a9593808bb9e9f229260d4c'
#URL = f'http://api.scraperapi.com?api_key={os.getenv("SCRAPERAPI_KEY")}&url='
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
        today = datetime.strftime(datetime.now(), '%#d.%-m.%Y')  # change '#' to '-' on linux
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


def antal():
    result = {}
    url = URL + 'https://www.restauraceantal.cz/aktualne'
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:81.0) Gecko/20100101 Firefox/81.0'}
    response = requests.get(url, headers=headers)
    response.encoding = 'utf-8'
    menu_soup = BeautifulSoup(response.text, 'html.parser')

    menu = menu_soup.findAll('div', attrs={'class': 'title-box'})
    for meal in menu:
        name = meal.find('h3').text
        price = meal.find('span').text
        if name:
            result[name] = price

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
    result = {}
    url = URL + 'https://www.prague-catering.cz/provozovny/kantyna-ceska-sporitelna-olbrachtova/Denni-menu-Olbrachtova/'
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:81.0) Gecko/20100101 Firefox/81.0'}
    response = requests.get(url, headers=headers)
    response.encoding = 'utf-8'
    menu_soup = BeautifulSoup(response.text, 'html.parser')

    menu = menu_soup.findAll('td')
    price = ''
    for i in range(len(menu)):
        if not menu[i].find('h3'):
            if menu[i].text.replace('\xa0', ''):
                if '100/200 g' in menu[i].text or 'váhu' in menu[i].text:
                    continue
                if 'Kč' in menu[i].text:
                    price = menu[i].text
                else:
                    name = menu[i].text
                    try:
                        if 'Kč' in menu[i+1].text:
                            price = menu[i+1].text
                    except IndexError:
                        pass
                    result[name] = price
    result = dict(list(result.items())[:-1])
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
    print(kopecek())
    # print(antal())
    # print(kolkovna())
    # print(kantyna_olbrachtova())
