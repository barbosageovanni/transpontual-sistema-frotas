#!/usr/bin/env python3
"""
Adicionar veículos de teste para validação
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

try:
    sys.path.append(str(Path(__file__).parent.parent / "backend_fastapi"))
    from app.core.database import SessionLocal
    from sqlalchemy import text
except ImportError as e:
    print(f"[ERROR] Erro ao importar dependências: {e}")
    sys.exit(1)


def add_test_vehicles():
    print("[VEHICLES] Adicionando veículos de teste...")

    vehicles = [
        {
            "placa": "ABC1234",
            "marca": "Volkswagen",
            "modelo": "Delivery 8.160",
            "ano": 2020,
            "km_atual": 15000,
            "tipo": "Caminhão"
        },
        {
            "placa": "DEF5678",
            "marca": "Mercedes-Benz",
            "modelo": "Sprinter 515",
            "ano": 2021,
            "km_atual": 8000,
            "tipo": "Van"
        },
        {
            "placa": "GHI9012",
            "marca": "Ford",
            "modelo": "Transit 350",
            "ano": 2022,
            "km_atual": 5000,
            "tipo": "Van"
        }
    ]

    try:
        with SessionLocal() as session:
            for vehicle in vehicles:
                try:
                    # Verificar se já existe
                    existing = session.execute(
                        text("SELECT id FROM veiculos WHERE placa = :placa"),
                        {"placa": vehicle["placa"]}
                    ).fetchone()

                    if not existing:
                        session.execute(text("""
                            INSERT INTO veiculos
                            (placa, marca, modelo, ano, km_atual, tipo, ativo, criado_em)
                            VALUES
                            (:placa, :marca, :modelo, :ano, :km_atual, :tipo, true, NOW())
                        """), vehicle)
                        print(f"[SUCCESS] Veículo criado: {vehicle['placa']} - {vehicle['marca']} {vehicle['modelo']}")
                    else:
                        print(f"[WARNING] Veículo já existe: {vehicle['placa']}")

                except Exception as e:
                    print(f"[ERROR] Erro ao criar veículo {vehicle['placa']}: {e}")

            session.commit()
            print("\n[SUCCESS] Veículos de teste adicionados!")

    except Exception as e:
        print(f"[ERROR] Erro ao adicionar veículos: {e}")


if __name__ == "__main__":
    add_test_vehicles()