# -*- coding: utf-8 -*-
"""
Housing Market Trends - Flask Web Application
Embeds Tableau Dashboard and Story into UI
"""

import os
from flask import Flask, render_template

app = Flask(__name__)


@app.route('/')
def home():
    return render_template('index.html', page='home')


@app.route('/about')
def about():
    return render_template('index.html', page='about')


@app.route('/dashboard')
def dashboard():
    return render_template('index.html', page='dashboard')


@app.route('/story')
def story():
    return render_template('index.html', page='story')


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
