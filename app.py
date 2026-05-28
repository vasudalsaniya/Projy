import os
import sys

# Add csquare_dev/ to path so Django can find the csquare package
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'csquare_dev'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'csquare.settings')

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
app = application
