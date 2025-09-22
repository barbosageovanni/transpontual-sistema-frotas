# backend_fastapi/app/routers/kpis.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..db import get_db

router = APIRouter()

@router.get("/summary")
def summary(days: int = 30, db: Session = Depends(get_db)):
    s = db.execute(text("""
        SELECT
          COUNT(*) AS total,
          COUNT(*) FILTER (WHERE status='aprovado') AS aprovados,
          COUNT(*) FILTER (WHERE status='reprovado') AS reprovados
        FROM checklist
        WHERE dt_inicio >= NOW() - make_interval(days => :d)
    """), {"d": days}).mappings().first() or {}

    itens = db.execute(text("""
        SELECT i.descricao, COUNT(*) qtd
        FROM checklist_respostas r
        JOIN checklist_itens i ON i.id = r.item_id
        JOIN checklist c ON c.id = r.checklist_id
        WHERE r.valor='nao_ok' AND c.dt_inicio >= NOW() - make_interval(days => :d)
        GROUP BY i.descricao
        ORDER BY qtd DESC
        LIMIT 10
    """), {"d": days}).mappings().all()

    motoristas = db.execute(text("""
        SELECT COALESCE(m.nome, CONCAT('ID ', c.motorista_id)) AS nome, COUNT(*) qtd
        FROM checklist c
        LEFT JOIN motoristas m ON m.id = c.motorista_id
        WHERE c.status='reprovado' AND c.dt_inicio >= NOW() - make_interval(days => :d)
        GROUP BY nome
        ORDER BY qtd DESC
        LIMIT 10
    """), {"d": days}).mappings().all()

    veiculos = db.execute(text("""
        SELECT COALESCE(v.placa, CONCAT('ID ', c.veiculo_id)) AS placa, COUNT(*) qtd
        FROM checklist c
        LEFT JOIN veiculos v ON v.id = c.veiculo_id
        WHERE c.status='reprovado' AND c.dt_inicio >= NOW() - make_interval(days => :d)
        GROUP BY placa
        ORDER BY qtd DESC
        LIMIT 10
    """), {"d": days}).mappings().all()

    total = s.get("total", 0) or 0
    aprovados = s.get("aprovados", 0) or 0
    reprovados = s.get("reprovados", 0) or 0
    taxa = (aprovados / total * 100.0) if total else 0.0

    return {
        "total": total,
        "aprovados": aprovados,
        "reprovados": reprovados,
        "taxa_aprovacao": round(taxa, 2),
        "top_itens_reprovados": list(itens),
        "top_motoristas": list(motoristas),
        "top_veiculos": list(veiculos),
    }
