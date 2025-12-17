from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = 'chave_secreta_eco' 

# --- CONFIGURAÇÃO DO BANCO DE DADOS ---
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'ecowise.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)
    telefone = db.Column(db.String(20))
    nascimento = db.Column(db.String(20))
    semana_atual = db.Column(db.Integer, default=0)

with app.app_context():
    db.create_all()

# --- ROTAS DE NAVEGAÇÃO ---

@app.route("/")
def EcoH():
    return render_template("EcoH.html")

@app.route("/menu")
def EcoMenu():
    if 'usuario_id' not in session:
        return redirect(url_for('EcoH'))
    return render_template("EcoMenu.html")

@app.route("/perfil")
def Perfil():
    if 'usuario_id' not in session:
        return redirect(url_for('EcoH'))
    user = Usuario.query.get(session['usuario_id'])
    return render_template("Perfil.html", usuario=user)

# --- REINSERINDO AS ROTAS QUE CAUSARAM O ERRO ---

@app.route("/ecoartigos")
def ecoartigos():
    return render_template("ecoartigos.html")

@app.route("/artigos_1")
def ecoartigosReciclagem():
    return render_template("ecoartigosReciclagem.html")

@app.route("/artigos_2")
def ecoartigosAlimentSus():
    return render_template("ecoartigosAlimentSus.html")

@app.route("/ecoartigosEnergia")
def ecoartigosEnergiaRen():
    return render_template("ecoartigosEnergiaRen.html")

@app.route("/guia")
def Guia():
    return render_template("Guia.html")

@app.route("/desafios")
def Desafios():
    return render_template("Desafios.html")

@app.route("/calc")
def Calculadora():
    return render_template("Calculadora.html")

@app.route("/pdfs")
def ecoartigospdfs():
    return render_template("ecoartigospdfs.html")

# --- ROTAS DE AUTENTICAÇÃO ---

@app.route("/cadastro", methods=['POST'])
def cadastro():
    nome = request.form.get('nome')
    email = request.form.get('email')
    senha = request.form.get('senha')
    telefone = request.form.get('telefone')
    nascimento = request.form.get('nascimento')

    usuario_existente = Usuario.query.filter_by(email=email).first()
    if usuario_existente:
        return "Email já cadastrado!", 400

    hash_senha = generate_password_hash(senha, method='pbkdf2:sha256')
    novo_usuario = Usuario(nome=nome, email=email, senha=hash_senha, telefone=telefone, nascimento=nascimento)

    db.session.add(novo_usuario)
    db.session.commit()

    session['usuario_id'] = novo_usuario.id
    return redirect(url_for('EcoMenu'))

@app.route("/login", methods=['POST'])
def login():
    email = request.form.get('email')
    senha = request.form.get('senha')
    usuario = Usuario.query.filter_by(email=email).first()

    if usuario and check_password_hash(usuario.senha, senha):
        session['usuario_id'] = usuario.id
        return redirect(url_for('EcoMenu'))
    else:
        return "Login inválido!", 401

@app.route("/sair")
def sair():
    session.pop('usuario_id', None)
    return redirect(url_for('EcoH'))

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)