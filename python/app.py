from flask import Flask, render_template

from flask_mysqldb import MySQL


app = Flask(__name__)

app.config['MySQL_HOST']= 'localhost'
app.config['MySQL_USER']= 'ROOT'
app.config['MySQL_PASSWORD']= ''
app.config['MySQL_DB']= ''

@app.route('/')
def index():

    return render_template('index.html')


if __name__ == '__main__':
    app.run(port=5500, debug=True)
