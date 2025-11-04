from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app)  # permite chamadas externas (ex: Tampermonkey)

DATA_FILE = "dados_ranked.json"


# ==============================
# Página inicial
# ==============================
@app.route("/")
def home():
    return """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>GeoGuessr Tracker 🌍</title>
<style>
  body {font-family: system-ui, Arial, sans-serif; background:#f9fafb; color:#111; margin:0; padding:0;}
  header {background:#16a34a; color:white; text-align:center; padding:1.5rem 1rem; box-shadow:0 2px 6px rgba(0,0,0,0.2);}
  main {max-width:900px; margin:2rem auto; background:white; padding:2rem; border-radius:1rem;
        box-shadow:0 4px 20px rgba(0,0,0,0.08);}
  h1 {margin:0 0 1rem;}
  p {line-height:1.6;}
  .button {display:inline-block; background:#16a34a; color:white; padding:.7rem 1.2rem;
           border-radius:6px; text-decoration:none; font-weight:bold;}
  .button:hover {background:#15803d;}
  footer {text-align:center; color:#666; margin-top:3rem; padding:1rem;}
</style>
</head>
<body>
  <header>
    <h1>🌍 GeoGuessr Tracker</h1>
    <p>Monitor de partidas Ranked e Unranked</p>
  </header>
  <main>
    <h2>Servidor ativo ✅</h2>
    <p>O rastreador está pronto para receber replays automaticamente via Tampermonkey.</p>
    <p>Assim que você jogar e o script capturar as partidas, elas aparecerão aqui:</p>
    <a href="/dados" class="button">Ver dados armazenados</a>
  </main>
  <footer>
    Feito com ❤️ em Flask – 2025
  </footer>
</body>
</html>
"""


# ==============================
# Receber dados do script
# ==============================
@app.route("/upload", methods=["POST"])
def upload():
    try:
        data = request.get_json(force=True)

        if not data:
            return jsonify({"status": "erro", "msg": "JSON vazio"}), 400

        # cria arquivo se não existir
        new_file = not os.path.exists(DATA_FILE)
        if new_file:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                pass

        # evita duplicado
        if not new_file:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        if json.loads(line).get("gameId") == data.get("gameId"):
                            return jsonify({"status": "ignored", "msg": "Partida já salva"})
                    except:
                        pass

        with open(DATA_FILE, "a", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
            f.write("\n")

        print("✅ Replay salvo:", data.get("gameId"))
        return jsonify({"status": "ok", "msg": "Replay salvo com sucesso"})

    except Exception as e:
        print("❌ Erro ao salvar replay:", e)
        return jsonify({"status": "erro", "msg": str(e)}), 500


# ==============================
# Listar dados
# ==============================
@app.route("/dados")
def dados():
    try:
        if not os.path.exists(DATA_FILE):
            return jsonify([])

        with open(DATA_FILE, "r", encoding="utf-8") as f:
            linhas = f.readlines()

        dados = [json.loads(l) for l in linhas if l.strip()]
        return jsonify(dados)

    except Exception as e:
        return jsonify({"status": "erro", "msg": str(e)}), 500


# ==============================
# Render / Gunicorn entry
# ==============================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
