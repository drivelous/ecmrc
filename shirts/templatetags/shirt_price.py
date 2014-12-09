from django import template

from all_products.queryutil import ShirtQuery

register = template.Library()

@register.filter
def shirt_price(shirt):
    shirt_query = ShirtQuery(shirt)
    for size in shirt_query.sizes:
    	stock = shirt_query.get_stock(size)
    	if stock > 0:
    		return shirt_query.get_price(size)