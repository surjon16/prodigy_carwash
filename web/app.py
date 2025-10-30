from application import app
from data import db

app.secret_key = 'prodigy_carwash_app'

if __name__ == '__main__':
    # db.drop_all()
    # db.create_all()
    app.run(debug=True, host='localhost', port='8080')
