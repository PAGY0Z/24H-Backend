# passenger_wsgi.py
import sys
import os

# Add the application root directory to the Python path
# This is important so that Python can find your app.py file
# The path needs to be the absolute path to your application root directory
# Replace '/home/qwerteam/my_flask_app' with the actual path you set in Cpanel
sys.path.insert(0, os.path.dirname(__file__))

# Import the Flask application instance from your app.py file
# 'app' here refers to the 'app = Flask(__name__)' line in your app.py
from app import app as application

# The 'application' variable is the WSGI callable that Passenger looks for.
# It is defined by Flask automatically when you create the app instance.
# No further code is typically needed here for a basic Flask app.
