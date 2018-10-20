from flask import Flask
from AIB import save_transactions
from database import db_session


app = Flask(__name__)

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

@app.route('/import_transactions')
def import_transactions():
    return save_transactions()


if __name__ == '__main__':
    app.run(debug=True)


