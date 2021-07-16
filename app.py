from flask import Flask, render_template

from main import get_menu

app = Flask(__name__)


@app.route("/")
def menu():
    menus = get_menu()
    return render_template('menu.html', menus=menus)
