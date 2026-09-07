from . import main_bp
from .controllers import render_main_page, render_dynamic_page

@main_bp.route('/')
def main():
    return render_main_page()

@main_bp.route('/<page>')
def load_page(page):
    return render_dynamic_page(page)