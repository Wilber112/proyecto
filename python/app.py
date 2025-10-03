from flask import Flask, render_template, request, url_for, flash, redirect, session

from flask_mysqldb import MySQL, MySQLdb
import MySQLdb.cursors

from werkzeug.security import generate_password_hash
import secrets
from datetime import datetime,timedelta
import smtplib
from email.mime.text import MIMEText

def generar_token(email):
    token=secrets.token_urlsafe(32)
    expiry=datetime.now() + timedelta(hours=1)
    cur =mysql.connection.cursor()
    cur.execute("UPDATE usuarios SET reset_token=%s, token_expiry=%s WHERE email=%s",(token,expiry,email))
    mysql.connection.commit()
    cur.close()
    return token 


def enviar_correo_reset(email,token):
    enlace = url_for('reset', token=token,_external=True)
    cuerpo =f""""Hola,solicitaste recuperar tu contraseña . Haz click en el siguiente enlace:
    {enlace}
    este enlace expira en 1 hora.
    si no lo solicitaste, ignora este mensaje. """

    remitente='pythoncontrasenas@gmail.com'
    clave='yqqp dtpo zmwv yuin'
    mensaje =MIMEText(cuerpo)
    mensaje['Subject']='Recuperar comtraseña' 
    mensaje['from']='pythoncontrasenas@gmail.com'
    mensaje['to']=email

    server =smtplib.SMTP('smtp.gmail.com',587)
    server.starttls()
    server.login(remitente,clave)
    server.sendmail(remitente,email,mensaje.as_string())
    server.quit()


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
@app.route('/registro',  methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form ['nombre']
        apellido = request.form ['apellido']
        username = request.form ['username']
        password = request.form ['password']
        hash = generate_password_hash(password)
   
        cur = mysql.connection.cursor()
        try:
            cur.execute("""INSERT INTO usuarios(nombre, apellido, username, password) VALUES (%s, %s, %s, %s)
                        """, (nombre, apellido, username, hash))
            mysql.connection.commit()

            cur.execute("SELECT idUsuario FROM usuarios WHERE username =%s", (username,))
            nuevo_usuario = cur.fetchone()

            cur.execute("INSERT INTO usuario_rol(idUsuario, idRol) VALUES (%s, %s)", (nuevo_usuario[0], 2))
            mysql.connection.commit()

            flash ("Usuario registrado con exito")
            return redirect(url_for('login'))
        except:
            flash("Este correo ya esta registrado")
        finally:
            cur.close()


    return render_template('registro.html')

@app.route('/dashboard')
def dashboard():
    if 'usuario' not in session:
        flash("debes iniciar sesion para acceder al dashboard")
        return redirect(url_for('login'))
    cursor = MySQLdb.connections.cursors(MySQLdb.cursors.DictCursor)
    cursor.execute("select idusuario, nombre, apellido, username, FROM usuarios")
    usuarios = cursor.fetchall()
    cursor.close
    return render_template('dashboard.html', usuarios=usuarios )

#ruta para recuperar contraseña

@app.route('/forgot', methods=['GET','POST'])
def forgot():
    if request.method=='POST':
        email=request.form['email']

        cur = mysql.connection.cursor()
        cur.execute("SELECT idUsuario FROM usuarios WHERE username=%s",(email))
        existe =cur.fetchome()
        cur.close()

        if not existe:
            flash("este correo no esta registrado")
            return redirect(url_for('forgot'))
            

        token = generar_token(email)
        enviar_correo_reset(email,token)

        flash("Te enviamos un correo para restablecer tu contraseña")
        return redirect(url_for('login'))
    return render_template('forgot.html')



@app.route('/reset/<token>', methods =['GET','POST'])
def reset(token):
    cur = mysql.connection.cursor()
    cur.execute("SELECT idUsuario, token_expiry FROM usuarios WHERE reset_token = %s", (token,))
    usuario = cur.fetchone()
    cur.close()

    if not usuario or datetime.now() > usuario[1]:
        flash("Token inválido o expirado.")
        return redirect(url_for('forgot'))

    if request.method == 'POST':
        nuevo_password = request.form['password']
        hash_nueva = generate_password_hash(nuevo_password)

        cur = mysql.connection.cursor()
        cur.execute("UPDATE usuarios SET password=%s, reset_token=NULL, token_expiry=NULL WHERE idUsuario=%s", (hash_nueva, usuario[0]))
        mysql.connection.commit()
        cur.close()

        flash("Contraseña actualizada correctamente.")
        return redirect(url_for('login'))
    
    return render_template('reset.html')

#Todo el codigo de python va antes de este if
if __name__ == '__main__':
    app.run(port=5500, debug=True)
