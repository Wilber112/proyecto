from flask import Flask, render_template, request, url_for, flash, redirect, session
from flask_mysqldb import MySQL, MySQLdb
import MySQLdb.cursors
from werkzeug.security import generate_password_hash
import secrets
from datetime import datetime,timedelta
import smtplib
from email.mime.text import MIMEText
import secrets, smtplib,qrcode, os,re

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

app = Flask(__name__)
app.secret_key = 'colegiocarlosalban'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'bdpython1' 

mysql = MySQL(app)

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
    cuerpo =f"""
Hola,solicitaste recuperar tu contraseña.
Haz click en el siguiente enlace:
{enlace}

Este enlace expira en 1 hora.
Si no lo solicitaste, ignora este mensaje.
"""
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

def enviar_qr_por_correo(email,qr_path):
    remitente =  'pythoncontrasenas@gmail.com'
    clave = 'yqqp dtpo zmwv yuin'
    asunto = 'Tu código QR de registro'
    cuerpo = f"""Hola {nombre},

    
Te has registrado correctamente en el sistema
Adjunto encontraras tu codigo QR personal para registrar asistencias

por favor, guardalo o impremelo para usarlo al ingresar o salir 

Saludos,
Equipo de control de asistencias
"""
    mensaje = MIMEMultipart()
    mensaje['From'] = remitente
    mensaje['To'] = email
    mensaje['Subject'] = asunto
    mensaje.attach(MIMEText(cuerpo, 'plain'))

    if os.path.exists(qr_path):
        raise FileNotFoundError(f"QR no encontrado{qr_path}")

    with open(qr_path, 'rb') as adjunto:
        parte = MIMEBase('application', 'octet-stream')    
        parte.set_payload(adjunto.read())
        encoders.encode_base64(parte)
        parte.add_header('Content-Disposition', f'attachment; filename= {os.path.basename(qr_path)}')
        mensaje.attach(parte)

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(remitente, clave)
    server.sendmail(remitente, email, mensaje.as_string())
    server.quit()
    

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

        if not re.match(r'[^@]+@[^@]+\.[^@]+', username):
            flash("Correo electronico invalido.")
            return render_template('registro.html')
   
        cur = mysql.connection.cursor()
        try:
            cur.execute("SELECT * FROM usuarios WHERE username = %s", (username,))
            if cur.fetchone()[0]>0:
                flash("El correo ya esta registrado")
                return render_template('registro.html')
            

        cur.execute("""
            INSERT INTO usuarios(nombre, apellido, username, password)
            VALUES (%s, %s, %s, %s)
        """, (nombre, apellido, username, hash hash_pw))
        mysql.connection.commit()
        user_id = cur.lastrowid

        qr_data = f"usuario:{user_id}"
        img = qrcode.make(qr_data)
        qr_folder = os.path.join(app.root_`path,'static','qr')
        os.makedirs(qr_folder, exist_ok=True)
        qr_filename = f"qr_{user_id}.png"
        qr_path = os.path.join(qr_folder, qr_filename)
        img.save(qr_path)
        qr_web_path = f"/static/qr/{qr_filename}"

        cur.execute("UPDATE usuarios SET qr_path=%s WHERE idUsuario=%s", (qr_web_path, user_id))
        mysql.connection.commit()

        cur.execute("SELECT COUNT(*) FROM roles WHERE idRol = 2")
        if cur.fetchone()[0] >0:
            cur.execute("INSERT INTO usuario_rol(idUsuarios, idRol) VALUES (%s, %s)", (user_id, 2))
            mysql.connection.commit()

            try:
                enviar_qr_por_correo(username,nombre,qr_path)
                flash("Usuario registrado y QR enviado al correo.")
            except Exception as e:
                print(f"Error al enviar correo:",e)
                flash("Usuario creado, pero jubo un problema al enviar el QR por correo.")

                return redirect(url_for('login'))

            except Exception as e:
                print(f"Error al registrar usuario:", e)
                flash("Ocurrio un erro al registrar el usuario.")
            finally:
                 cur.close()

        return render_template('registro.html')

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
    cursor.execute("""
        SELECT u.idUsuario, u.nombre, u.apellido, u.username, r.nombrerRol, ur.idRol
        FROM usuarios u
        lEFT JOIN usuario_rol ur ON u.idUsuario = ur.idUsuario
        lEFT JOIN roles r ON ur.idRol = r.idRol
        """)
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
