import os
import django
from django.template import loader
from django.test import RequestFactory

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
req = RequestFactory().get('/')
t = loader.get_template('index.html')
html = t.render({'TWO_GIS_TILE_URL': '', 'TWO_GIS_API_KEY': ''}, request=req)
print('rendered', len(html))
