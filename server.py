# server.py — versão reforçada CORS + OPTIONS + porta do Render
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import json, os, sys, traceback

app = Flask(__name__)

# Configurações CORS explícitas
CORS(app,
     resources={r"/*": {"origins": "*"}},
     supports_credentials=False,
     allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept"],
     expose_headers=["Content-Type"],
     methods=["GET", "POST", "OPTIONS", "PUT", "DELETE"]
)

DATA_FILE = "dados_ranked.json"

def log(*args, **kwargs):
    print(*args, **kwargs, flush=True)

# rota principal (html leve)
@app.route("/", methods=["GET"])
def home():
    return """
<!doctype html>
<html lang="pt-BR">
<head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>GeoGuessr Tracker</title>
<style>body{font-family:system-ui,Arial;margin:0;background:#f7fafc;color:#111}header{background:#16a34a;color:#fff;padding:1.5rem;text-align:center}main{max-width:960px;margin:2rem auto;background:#fff;padding:1.6rem;border-radius:12px;box-shadow:0 6px 24px rgba(2,6,23,0.06)}a.btn{display:inline-block;background:#16a34a;color:#fff;padding:.6rem 1rem;border-radius:8px;text-decoration:none;font-weight:600}</style>
</head>
<body>
<header><h1>🌍 GeoGuessr Tracker</h1></header>
<main>
<h2>Servidor ativo ✅</h2>
<p>Endpoint <code>/upload</code> pronto para receber replays via Tampermonkey (CORS habilitado).</p>
<p><a class="btn" href="/dados">Ver dados armazenados</a></p>
</main>
</body>
</html>
"""

# OPTIONS handler genérico (garante resposta à preflight)
@app.route("/upload", methods=["OPTIONS"])
def upload_options():
    resp = make_response("")
    # cabeçalhos CORS já aplicados por flask_cors, mas garantimos explicitamente:
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return resp

# endpoint principal
@app.route("/upload", methods=["POST"])
def upload():
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"status":"erro","msg":"JSON vazio"}), 400

        # cria arquivo se não existir
        if not os.path.exists(DATA_FILE):
            with open(DATA_FILE, "w", encoding="utf-8") as _:
                pass

        # salva cada objeto em uma linha (JSON Lines)
        with open(DATA_FILE, "a", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
            f.write("\n")

        log("✅ Replay salvo:", data.get("gameId","(sem id)"))
        return jsonify({"status":"ok","msg":"Replay salvo"}), 201

    except Exception as e:
        tb = traceback.format_exc()
        log("❌ Erro ao processar upload:", str(e))
        log(tb)
        return jsonify({"status":"erro","msg":str(e)}), 500

@app.route("/dados", methods=["GET"])
def dados():
    try:
        if not os.path.exists(DATA_FILE):
            return jsonify([])

        with open(DATA_FILE, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
            parsed = [json.loads(l) for l in lines]
        return jsonify(parsed)
    except Exception as e:
        log("Erro ao ler dados:", e)
        return jsonify({"status":"erro","msg":str(e)}), 500

if __name__ == "__main__":
    # usa porta do Render (variável de ambiente PORT) ou 5000 local
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
