# -*- coding: utf-8 -*-
"""
Housing Market Trends - Flask Web Application
Embeds Tableau Dashboard and Story into UI
"""

import os
from flask import Flask, abort, render_template

app = Flask(__name__)


ALLOWED_PAGES = {'home', 'about', 'dashboard', 'story'}


@app.route('/', defaults={'page': 'home'})
@app.route('/<page>')
@app.route('/<page>/')
def render_page(page):
    if page not in ALLOWED_PAGES:
        abort(404)
    return render_template('index.html', page=page)


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
