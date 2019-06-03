from app import app

@app.route('/')
@app.route('/home/api/v1.0/energy')
@app.route('/home/api/v1.0/energy/start_date=')

def index():
    return "Hello, World!"


# https://stackoverflow.com/questions/9637297/proper-rest-formatted-url-with-date-ranges