from application import app
from data import db

if __name__ == '__main__':
    # db.drop_all()
    # db.create_all()
    app.run(debug=True, host='localhost', port='8080')
    # app.run(debug=True, host='192.168.254.103', port='8080')
