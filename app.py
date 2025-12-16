from flask import Flask, render_template

app = Flask(__name__)

# Rota principal
@app.route("/")
def EcoH():
    return render_template("EcoH.html")


@app.route("/menu")
def EcoMenu():
    return render_template("EcoMenu.html")

@app.route("/perfil")
def Perfil():
    return render_template("Perfil.html")

@app.route("/guia")
def Guia():
    return render_template("Guia.html")


@app.route("/artigos_1")
def ecoartigosReciclagem():
    return render_template("ecoartigosReciclagem.html")

@app.route("/artigos_2")
def ecoartigosAlimentSus():
    return render_template("ecoartigosAlimentSus.html")

@app.route("/ecoartigos")
def ecoartigos():
    return render_template("ecoartigos.html")

@app.route("/desafios")
def Desafios():
    return render_template("Desafios.html")

@app.route("/calc")
def Calculadora():
    return render_template("Calc.html")

@app.route("/pdfs")
def ecoartigospdfs():
    return render_template("ecoartigospdfs.html")

@app.route("/ecoartigosEnergia")
def ecoartigosEnergiaRen():
    return render_template("ecoartigosEnergiaRen.html")


if __name__ == "__main__":
    # Rodar servidor no host 0.0.0.0 para Codespaces
    app.run(debug=True, host="0.0.0.0", port=5000)


'''
# @app.route("/nome-na-url")
# def NomeDaFuncao():
#     return render_template("nome-do-arquivo.html")
'''