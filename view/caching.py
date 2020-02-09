from layout.block import Page
from layout.table import Table
from model.caching import cache as saved_cache


def render_detailpage():
    data = [[key, saved_cache[key]] for key in sorted(saved_cache.keys())]
    page = Page([Table(data)])
    page.render('output/details.html')
