# This is just a simple wrapper for gunicorn to find your app.
# If you want to change the application, simply change "app.py" above to the
# new file.


import main

server = main.server
