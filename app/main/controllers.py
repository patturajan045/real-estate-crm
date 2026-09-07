from flask import render_template, redirect
from jinja2 import TemplateNotFound

VALID_PAGES = {'login', 'register', 'dashboard', 'leads', 'properties', 'bookings', 'users', 'settings'}

def render_main_page():
    """Handles logic for the root endpoint."""
    return render_template('login.html')

def render_dynamic_page(page):
    """Handles logic for dynamically loading pages."""
    if page in VALID_PAGES:
        try:
            return render_template(f"{page}.html", active_page=page)
        except TemplateNotFound:
            return redirect('/')
    return redirect('/')