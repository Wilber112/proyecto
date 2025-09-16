from flask import Flask, render_template

from flask_mysqldb import MySQL


app = Flask(__name__)

app.config['MySQL_HOST']= 'localhost'
app.config['MySQL_USER']= 'root'
app.config['MySQL_PASSWORD']= ''
app.config['MySQL_DB']= 'bdpython'

MySQL =MySQL(app)

@app.route('/')
def index():

    return render_template('index.html')

@app.route('/login')
def login():
  
    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if 'usuario' not in session:
        flash("debes iniciar sesion para acceder al dashboard")
        return redirect(url_for('login'))


    return render_template('dashboard.html')





#Todo el codigo de python va antes de este if
if __name__ == '__main__':
    app.run(port=5500, debug=True)
