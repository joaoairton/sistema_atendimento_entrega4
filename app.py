# app.py
# Ponto de entrada da aplicacao. Cria o Flask, registra os blueprints e sobe o servidor.
from flask import Flask, render_template
import config
from routes.api          import api_bp
from routes.pacientes    import pac_bp
from routes.atendimentos import atend_bp
from routes.prescricoes  import pres_bp

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

app.register_blueprint(api_bp)
app.register_blueprint(pac_bp)
app.register_blueprint(atend_bp)
app.register_blueprint(pres_bp)


@app.route("/")
def index():
    from services.db_service import listar_atendimentos
    return render_template("index.html",
                           atendimentos=listar_atendimentos()[:5])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
