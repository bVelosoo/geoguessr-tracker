from flask import Flask, request, jsonify
import os, json, datetime

app = Flask(__name__)

# Cria uma pasta para armazenar os dados, se ainda não existir
os.makedirs("dados", exist_ok=True)

@app.route("/")
def home():
    return """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>GeoGuessr Tracker</title>
<style>
  body {font-family:system-ui,Arial,sans-serif; margin:0; background:#f9fafb; color:#111;}
  header {background:#16a34a; color:#fff; padding:1rem 2rem; text-align:center;}
  main {max-width:900px; margin:2rem auto; background:#fff; padding:2rem; border-radius:1rem;
        box-shadow:0 2px 10px rgba(0,0,0,.1);}
  h1 {margin-top:0;}
  button {background:#16a34a; color:#fff; border:none; border-radius:6px; padding:.7rem 1.2rem;
          font-size:1rem; cursor:pointer;}
  button:hover {background:#15803d;}
  footer {text-align:center; color:#666; padding:1rem;}
</style>
</head>
<body>
<header>
  <h1>🌍 GeoGuessr Tracker</h1>
</header>
<main>
  <h2>Servidor ativo ✅</h2>
  <p>O rastreador está pronto para receber replays enviados pelo Tampermonkey.</p>
  <p>Use o botão abaixo para ver os dados coletados.</p>
  <a href="/dados"><button>Ver dados armazenados</button></a>
</main>
<footer>
  <p>Feito com ❤️ em Flask</p>
</footer>
</body>
</html>
    """
