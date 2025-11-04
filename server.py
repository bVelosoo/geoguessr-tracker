# server.py
from flask import Flask, request, jsonify, make_response
import json, os, time
from collections import defaultdict, Counter

app = Flask(__name__)

DATA_FILE = "dados_ranked.json"

# --------------------------
# Helpers
# --------------------------
def cors_json(data, status=200):
    resp = make_response(json.dumps(data, ensure_ascii=False), status)
    resp.headers["Content-Type"] = "application/json; charset=utf-8"
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return resp

def append_line(obj):
    with open(DATA_FILE, "a", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)
        f.write("\n")

def read_all():
    if not os.path.exists(DATA_FILE):
        return []
    out = []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                continue
    return out

# --------------------------
# Root & status
# --------------------------
@app.route("/", methods=["GET"])
def home():
    return """
<!doctype html><html lang="pt-BR"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>GeoGuessr Tracker</title>
<style>
body{background:#0b1220;color:#dbeafe;font-family:system-ui,Arial;padding:2rem}
.container{max-width:980px;margin:0 auto}
.card{background:#07122b;padding:1.2rem;border-radius:10px;box-shadow:0 8px 30px rgba(2,6,23,0.6)}
a.button{display:inline-block;background:#10b981;color:#fff;padding:.5rem .9rem;border-radius:8px;text-decoration:none;font-weight:600}
small{color:#94a3b8}
</style>
</head><body>
<div class="container">
  <div class="card">
    <h1>GeoGuessr Tracker</h1>
    <p>Servidor ativo. Use o Tampermonkey para enviar replays para <code>/upload</code>.</p>
    <p><a class="button" href="/dashboard">Abrir Dashboard</a> <small> (abre o painel analítico)</small></p>
    <p style="margin-top:.5rem;color:#94a3b8">Dados salvos em <code>{}</code></p>
  </div>
</div>
</body></html>
""".format(DATA_FILE)

# --------------------------
# Upload endpoint (Tampermonkey)
# --------------------------
@app.route("/upload", methods=["OPTIONS", "POST"])
def upload():
    if request.method == "OPTIONS":
        return cors_json({"ok": True})
    try:
        data = request.get_json(force=True)
    except Exception as e:
        return cors_json({"status":"error","msg":"invalid json","detail":str(e)}, 400)

    if not data:
        return cors_json({"status":"error","msg":"empty payload"}, 400)

    # add server-side metadata
    record = {
        "receivedAt": int(time.time()),
        "payload": data
    }
    try:
        append_line(record)
        return cors_json({"status":"ok","msg":"saved"})
    except Exception as e:
        return cors_json({"status":"error","msg":str(e)}, 500)

# --------------------------
# Raw data viewer
# --------------------------
@app.route("/dados", methods=["GET"])
def dados():
    allr = read_all()
    return cors_json(allr)

# --------------------------
# Analytics endpoints
# --------------------------
@app.route("/analytics/countries", methods=["GET"])
def analytics_countries():
    allr = read_all()
    cnt = Counter()
    # count country occurrences by round panorama countryCode
    for rec in allr:
        payload = rec.get("payload") or {}
        game = payload.get("game") or payload.get("pageProps", {}).get("game") or payload
        rounds = game.get("rounds") or []
        for r in rounds:
            cc = r.get("panorama", {}).get("countryCode") or r.get("country") or None
            if cc:
                cnt[cc.lower()] += 1
    out = [{"country": k, "count": v} for k, v in cnt.most_common()]
    return cors_json(out)

@app.route("/analytics/heatmap", methods=["GET"])
def analytics_heatmap():
    allr = read_all()
    points = defaultdict(int)
    for rec in allr:
        payload = rec.get("payload") or {}
        game = payload.get("game") or payload.get("pageProps", {}).get("game") or payload
        rounds = game.get("rounds") or []
        for r in rounds:
            pano = r.get("panorama", {})
            lat = pano.get("lat")
            lng = pano.get("lng")
            if lat is None or lng is None:
                continue
            key = f"{round(lat,5)}|{round(lng,5)}"
            points[key] += 1
    arr = []
    for k, v in points.items():
        lat, lng = k.split("|")
        arr.append({"lat": float(lat), "lng": float(lng), "count": v})
    return cors_json(arr)

@app.route("/analytics/mode", methods=["GET"])
def analytics_mode():
    allr = read_all()
    cnt = Counter()
    for rec in allr:
        payload = rec.get("payload") or {}
        game = payload.get("game") or payload.get("pageProps", {}).get("game") or payload
        # attempt multiple fields
        mode = game.get("competitiveGameMode") or game.get("mode") or ("rated" if game.get("isRated") else "casual")
        if mode is None:
            mode = "unknown"
        cnt[mode] += 1
    out = [{"mode": k, "count": v} for k, v in cnt.items()]
    return cors_json(out)

@app.route("/analytics/rating", methods=["GET"])
def analytics_rating():
    allr = read_all()
    # build timeline per player nick
    series = defaultdict(list)
    for rec in allr:
        ts = rec.get("receivedAt", int(time.time()))
        payload = rec.get("payload") or {}
        game = payload.get("game") or payload.get("pageProps", {}).get("game") or payload
        teams = game.get("teams") or []
        for t in teams:
            for p in t.get("players", []) if isinstance(t.get("players", []), list) else []:
                nick = p.get("nick") or p.get("playerId") or "unknown"
                rating = p.get("rating") or p.get("competitive", {}).get("rating")
                if rating is not None:
                    series[nick].append({"ts": ts, "rating": rating})
    out = [{"nick": nick, "points": sorted(points, key=lambda x: x["ts"])} for nick, points in series.items()]
    return cors_json(out)

# --------------------------
# Dashboard page (dark theme)
# --------------------------
@app.route("/dashboard", methods=["GET"])
def dashboard():
    return """
<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>GeoGuessr Tracker — Dashboard</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<style>
:root{--bg:#07122b;--panel:#07122b;--muted:#94a3b8;--accent:#10b981}
body{margin:0;background:linear-gradient(180deg,#041025 0%, #07122b 100%);color:#e6eef8;font-family:Inter,system-ui,Arial;min-height:100vh}
.header{padding:18px 28px;border-bottom:1px solid rgba(255,255,255,0.03);display:flex;align-items:center;gap:16px}
.container{max-width:1200px;margin:18px auto;padding:0 18px}
.grid{display:grid;grid-template-columns:1fr 420px;gap:18px}
.card{background:var(--panel);padding:14px;border-radius:12px;box-shadow:0 6px 30px rgba(2,6,23,0.6)}
.row{display:flex;gap:12px}
h1{margin:0;font-size:20px}
.small{color:var(--muted);font-size:13px}
#map{height:420px;border-radius:8px;border:1px solid rgba(255,255,255,0.04)}
.list{max-height:420px;overflow:auto;padding-right:6px}
.country-item{display:flex;justify-content:space-between;padding:8px;border-bottom:1px dashed rgba(255,255,255,0.02)}
.footer{padding:18px;text-align:center;color:var(--muted);font-size:13px}
.button{background:var(--accent);color:#041025;padding:8px 10px;border-radius:8px;font-weight:700;text-decoration:none}
.chart{height:320px}
</style>
</head>
<body>
  <div class="header">
    <div style="flex:1">
      <h1>GeoGuessr Tracker — Dashboard</h1>
      <div class="small">Visão geral dos replays coletados</div>
    </div>
    <div>
      <a class="button" href="/dados" target="_blank">Ver JSON cru</a>
    </div>
  </div>

  <div class="container">
    <div class="grid">
      <div>
        <div class="card" style="margin-bottom:18px">
          <div style="display:flex;justify-content:space-between;align-items:center">
            <div>
              <strong>Painel global</strong><div class="small">Últimas partidas e mapa de calor</div>
            </div>
            <div class="small" id="stats-summary">Carregando…</div>
          </div>
          <div style="margin-top:12px" id="map" ></div>
        </div>

        <div class="row">
          <div class="card" style="flex:1">
            <strong>Países mais frequentes</strong>
            <div id="countries-list" class="list" style="margin-top:8px">carregando…</div>
          </div>
          <div class="card" style="width:360px">
            <strong>Modos</strong>
            <div id="mode-chart" class="chart"></div>
          </div>
        </div>

        <div style="height:18px"></div>

        <div class="row">
          <div class="card" style="flex:1">
            <strong>Evolução de rating (jogadores detectados)</strong>
            <div id="rating-chart" class="chart"></div>
          </div>
          <div class="card" style="width:360px">
            <strong>Heatmap pontos</strong>
            <div class="small" style="margin-top:6px;color:var(--muted)">Pontos onde as partidas caíram (agregados)</div>
            <div id="heat-list" style="margin-top:8px;max-height:200px;overflow:auto"></div>
          </div>
        </div>

      </div>

      <div>
        <div class="card" style="margin-bottom:18px">
          <strong>Filtros</strong>
          <div class="small">Filtre por modo / período (em próximas versões)</div>
          <div style="margin-top:12px;display:flex;gap:8px">
            <button onclick="refreshAll()" class="button" style="background:#3b82f6">Atualizar</button>
          </div>
        </div>

        <div class="card">
          <strong>Últimas capturas</strong>
          <div id="recent-list" style="margin-top:8px;max-height:380px;overflow:auto"></div>
        </div>
      </div>

    </div>

    <div class="footer">Dados privados — hospedado em seu servidor. Sem login (opção futura disponível).</div>
  </div>

<script src="https://cdn.plot.ly/plotly-2.24.1.min.js"></script>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
async function fetchJson(path){ const r = await fetch(path); if(!r.ok) throw new Error('fetch err '+r.status); return r.json(); }

async function refreshAll(){
  try{
    const [countries, heat, mode, rating, raw] = await Promise.all([
      fetchJson('/analytics/countries'),
      fetchJson('/analytics/heatmap'),
      fetchJson('/analytics/mode'),
      fetchJson('/analytics/rating'),
      fetchJson('/dados')
    ]);

    document.getElementById('stats-summary').textContent = raw.length + ' partidas';

    // countries list
    const cl = document.getElementById('countries-list');
    cl.innerHTML = '';
    (countries.slice(0,50)).forEach(c=>{
      const el = document.createElement('div'); el.className='country-item';
      el.innerHTML = `<div style="text-transform:uppercase">${c.country}</div><div class="small">${c.count}</div>`;
      cl.appendChild(el);
    });

    // mode chart
    const modes = mode.map(m=>m.mode); const mcounts = mode.map(m=>m.count);
    Plotly.newPlot('mode-chart', [{ labels: modes, values: mcounts, type:'pie' }], {margin:{t:0,b:0}});

    // rating chart
    const ratingDiv = document.getElementById('rating-chart');
    const traces = rating.map(s=>{
      return { x: s.points.map(p=>new Date(p.ts*1000)), y: s.points.map(p=>p.rating), type:'scatter', name:s.nick };
    });
    Plotly.newPlot(ratingDiv, traces, {margin:{t:10}});

    // heat list
    const hl = document.getElementById('heat-list'); hl.innerHTML='';
    heat.slice(0,200).forEach(p=>{
      const r = document.createElement('div'); r.style.padding='6px 0'; r.textContent = `${p.count}x — ${p.lat.toFixed(4)}, ${p.lng.toFixed(4)}`; hl.appendChild(r);
    });

    // recent list
    const recent = document.getElementById('recent-list'); recent.innerHTML='';
    raw.slice(-120).reverse().forEach(rec=>{
      const d = new Date((rec.receivedAt||0)*1000);
      const item = document.createElement('div'); item.style.padding='8px;border-bottom':'1px solid rgba(255,255,255,0.03)';
      item.innerHTML = `<div style="font-size:13px"><b>${rec.payload?.game?.gameId || rec.payload?.gameId || 'sem-id'}</b></div>
        <div class="small">${d.toLocaleString()} • rounds: ${ (rec.payload?.game?.rounds || []).length }</div>`;
      recent.appendChild(item);
    });

    // map with circle markers
    renderMap(heat);

  }catch(err){
    console.error(err);
    alert('Erro ao carregar dados: '+err.message);
  }
}

let mapObj = null;
function renderMap(points){
  if(!mapObj){
    mapObj = L.map('map').setView([20,0], 2);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '&copy; OpenStreetMap contributors' }).addTo(mapObj);
  } else {
    mapObj.eachLayer(layer => { if(layer && layer.options && layer.options.pane === 'markerPane') mapObj.removeLayer(layer); });
  }
  points.forEach(p=>{
    const r = Math.min(40, 4 + Math.log(1 + p.count)*6);
    L.circleMarker([p.lat, p.lng], {radius: r, fillColor:'#ff7b00', color:'#ffb78c', weight:1, fillOpacity:0.8}).addTo(mapObj)
      .bindPopup(`${p.count} partidas<br>${p.lat.toFixed(4)}, ${p.lng.toFixed(4)}`);
  });
}

window.onload = function(){ refreshAll(); setInterval(refreshAll, 60*1000); };
</script>
</body></html>
"""

# --------------------------
# Run
# --------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
