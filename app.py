from flask import Flask, render_template

app = Flask(__name__)

# Rota principal
@app.route("/")
def index():
    return render_template("EcoH.html")

if __name__ == "__main__":
    # Rodar servidor no host 0.0.0.0 para Codespaces
    app.run(debug=True, host="0.0.0.0", port=5000)
    