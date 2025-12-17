from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
from flask import jsonify
import os

app = Flask(__name__)
app.secret_key = 'chave_secreta_eco' 

# --- CONFIGURAÇÃO DO BANCO DE DADOS ---
basedir = os.path.abspath(os.path.dirname(__file__))
import os
os.makedirs(app.instance_path, exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'ecowise.db')

db = SQLAlchemy(app)

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)
    telefone = db.Column(db.String(20))
    nascimento = db.Column(db.String(20))
    semana_atual = db.Column(db.Integer, default=0)

class DesafioConcluido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    semana = db.Column(db.Integer, nullable=False)
    desafio_index = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

# --- ROTAS DE NAVEGAÇÃO ---

@app.route('/api/desafios/<int:semana>', methods=['GET'])
def get_desafios_semana(semana):
    if 'usuario_id' not in session:
        return jsonify({'error':'unauthorized'}), 401
    user_id = session['usuario_id']
    entries = DesafioConcluido.query.filter_by(user_id=user_id, semana=semana).all()
    indices = [e.desafio_index for e in entries]
    return jsonify({'feitos': indices})

@app.route('/api/desafios', methods=['POST'])
def salvar_desafios():
    if 'usuario_id' not in session:
        return jsonify({'error':'unauthorized'}), 401
    data = request.get_json()
    semana = int(data.get('semana'))
    feitos = data.get('feitos', [])
    user_id = session['usuario_id']
    DesafioConcluido.query.filter_by(user_id=user_id, semana=semana).delete()
    for idx in feitos:
        db.session.add(DesafioConcluido(user_id=user_id, semana=semana, desafio_index=int(idx)))
    db.session.commit()
    return jsonify({'status':'ok'})


@app.route("/pdfs/<filename>")
def download_pdf(filename):
    pdf_path = os.path.join(basedir, 'Ecoartigos')
    return send_from_directory(pdf_path, filename)


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
    idade = None
    try:
        dt = datetime.strptime(user.nascimento, "%Y-%m-%d").date()
        hoje = date.today()
        idade = hoje.year - dt.year - ((hoje.month, hoje.day) < (dt.month, dt.day))
    except:
        idade = None
    desafios_concluidos = DesafioConcluido.query.filter_by(user_id=user.id).count()
    progresso_percent = round((user.semana_atual / 24) * 100) if user.semana_atual else 0
    return render_template("Perfil.html", usuario=user, idade=idade, desafios_concluidos=desafios_concluidos, progresso_percent=progresso_percent)

@app.route("/atualizar-perfil", methods=['POST'])
def atualizar_perfil():
    if 'usuario_id' not in session:
        return jsonify({'error': 'unauthorized'}), 401
    user = Usuario.query.get(session['usuario_id'])
    data = request.get_json()
    nome = data.get('nome', '').strip()
    if nome:
        user.nome = nome
    db.session.commit()
    return jsonify({'status': 'ok', 'nome': user.nome})

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