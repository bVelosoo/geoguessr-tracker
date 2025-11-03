from flask import Flask, request, jsonify, make_response
import json, os

app = Flask(__name__)

DATA_FILE = "dados_ranked.json"

def cors_response(data, status=200):
    resp = make_response(json.dumps(data, ensure_ascii=False), status)
    resp.headers["Content-Type"] = "application/json"
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return resp

@app.route("/", methods=["GET"])
def home():
    return """
<h1>✅ GeoGuessr Tracker Online</h1>
<p>API funcionando e pronta para receber dados.</p>
<p><a href='/dados'>Ver dados</a></p>
"""

@app.route("/upload", methods=["OPTIONS"])
def upload_options():
    return cors_response({"ok": True})

@app.route("/upload", methods=["POST"])
def upload_data():
    try:
        data = request.get_json(force=True)
        if not data:
            return cors_response({"error":"JSON vazio"}, 400)

        with open(DATA_FILE, "a", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
            f.write("\n")

        return cors_response({"status":"ok", "msg":"salvo"})
    except Exception as e:
        return cors_response({"error": str(e)}, 500)

@app.route("/dados", methods=["GET"])
def dados():
    if not os.path.exists(DATA_FILE):
        return cors_response([])
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
        data = [json.loads(x) for x in lines if x.strip()]
    return cors_response(data)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
