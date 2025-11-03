from flask import Flask, request, jsonify
import os, json, datetime

app = Flask(__name__)

# Cria uma pasta para armazenar os dados, se ainda não existir
os.makedirs("dados", exist_ok=True)

@app.route("/")
def home():
    return "<h2>Servidor GeoGuessr Tracker ativo ✅</h2><p>Envie seus replays via Tampermonkey.</p>"

@app.route("/upload", methods=["POST"])
def upload():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"erro": "Nenhum dado recebido"}), 400

        # Salva o arquivo com timestamp
        nome_arquivo = f"dados/replay_{datetime.datetime.now().isoformat()}.json"
        with open(nome_arquivo, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return jsonify({"status": "sucesso", "arquivo": nome_arquivo})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route("/dados", methods=["GET"])
def listar_dados():
    arquivos = os.listdir("dados")
    return jsonify({"total": len(arquivos), "arquivos": arquivos})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
