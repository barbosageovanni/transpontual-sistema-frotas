from flask import Blueprint, render_template, current_app, request, redirect, url_for, flash
import requests

bp = Blueprint("main", __name__)

def api_url(path: str) -> str:
    base = current_app.config.get("API_BASE", "http://localhost:8005")
    return f"{base}{path}"

@bp.route("/")
def index():
    api = current_app.config["API_BASE"]
    try:
        health = requests.get(f"{api}/health", timeout=5).json()
    except Exception as e:
        health = {"status": "erro", "detail": str(e)}
    return render_template("index.html", health=health)

@bp.route("/models")
def models():
    r = requests.get(api_url("/checklist/modelos"), timeout=10)
    modelos = r.json()
    return render_template("models.html", modelos=modelos)

@bp.route("/start", methods=["GET", "POST"])
def start():
    if request.method == "POST":
        payload = {
            "veiculo_id": int(request.form["veiculo_id"]),
            "motorista_id": int(request.form["motorista_id"]),
            "modelo_id": int(request.form["modelo_id"]),
            "tipo": request.form.get("tipo", "pre"),
            "odometro_ini": int(request.form.get("odometro_ini", "0")),
            "geo_inicio": request.form.get("geo_inicio") or None
        }
        r = requests.post(api_url("/checklist/start"), json=payload, timeout=15)
        if r.status_code >= 400:
            flash(f"Erro ao iniciar checklist: {r.text}", "danger")
            return redirect(url_for("main.start"))
        cid = r.json()["id"]
        return redirect(url_for("main.checklist_detail", checklist_id=cid))
    modelos = requests.get(api_url("/checklist/modelos"), timeout=10).json()
    return render_template("start.html", modelos=modelos)

@bp.route("/checklist/<int:checklist_id>", methods=["GET", "POST"])
def checklist_detail(checklist_id: int):
    if request.method == "POST":
        respostas = []
        for k, v in request.form.items():
            if not k.startswith("resp_"):
                continue
            item_id = int(k.split("_", 1)[1])
            valor = v
            obs = request.form.get(f"obs_{item_id}") or None
            respostas.append({"item_id": item_id, "valor": valor, "observacao": obs})
        if respostas:
            requests.post(api_url("/checklist/answer"), json={"checklist_id": checklist_id, "respostas": respostas}, timeout=20)
        if request.form.get("finalizar") == "1":
            od = request.form.get("odometro_fim")
            payload = {"checklist_id": checklist_id}
            if od:
                payload["odometro_fim"] = int(od)
            requests.post(api_url(f"/api/v1/checklist/{checklist_id}/finish"), json={"odometro_fim": payload.get("odometro_fim")}, timeout=20)
        return redirect(url_for("main.checklist_detail", checklist_id=checklist_id))

    data = requests.get(api_url(f"/checklist/{checklist_id}"), timeout=15).json()
    itens = data["itens"]
    respostas_map = {r["item_id"]: r for r in data.get("respostas", [])}
    return render_template("checklist_detail.html", data=data, itens=itens, respostas_map=respostas_map)

@bp.route("/checklists")
def checklists():
    return render_template("checklists.html")
