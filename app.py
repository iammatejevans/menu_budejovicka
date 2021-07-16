from flask import Flask, render_template, request

from main import get_menu

app = Flask(__name__)


@app.route("/")
def menu():
    menus = get_menu()
    return render_template('menu.html', menus=menus)


@app.route("/register", methods=['POST'])
def register():
    try:
        email = request.json.get('email', None)
        with open('emails.txt', 'a') as fle:
            fle.write(f'{email}\n')
    except:
        return '', 400
    return '', 202


@app.route("/success")
def success():
    return render_template('success.html')


@app.route("/error")
def error():
    return render_template('error.html')
