# backend_fastapi/app/main.py
"""
Transpontual - FastAPI application
"""
import os
import asyncio
from datetime import datetime
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import text
from werkzeug.security import generate_password_hash

from app.core.config import get_settings
from app.core.database import create_tables, test_connection, get_db, SessionLocal
from app.api_v1 import api_router
from app import models


settings = get_settings()

app = FastAPI(
    title="Transpontual Fleet Management API",
    description="Gestao de frotas com checklist veicular",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    import time
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    print(f"{request.method} {request.url} - {response.status_code} - {process_time:.2f}s")
    return response


@app.on_event("startup")
async def startup_event():
    print("Startup: initializing API...")

    async def _init_db():
        try:
            # Add timeout to database operations
            ok = await asyncio.wait_for(
                asyncio.to_thread(test_connection),
                timeout=10.0
            )
            if ok:
                print("Startup: DB connection OK")
                try:
                    await asyncio.wait_for(
                        asyncio.to_thread(create_tables),
                        timeout=15.0
                    )
                    print("Startup: tables checked/created")
                except asyncio.TimeoutError:
                    print("Startup: timeout creating tables")
                except Exception as e:
                    print(f"Startup: error creating tables: {e}")
            else:
                print("Startup: DB connection failed")
        except asyncio.TimeoutError:
            print("Startup: DB connection timeout")
        except Exception as e:
            print(f"Startup: DB init error: {e}")

    # Don't block startup on DB issues - run in background
    asyncio.create_task(_init_db())


@app.on_event("shutdown")
async def shutdown_event():
    print("Shutdown: API stopping...")


app.include_router(api_router, prefix="/api/v1")


uploads_dir = settings.STORAGE_DIR
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/files", StaticFiles(directory=uploads_dir), name="files")


@app.get("/")
async def root():
    return {
        "message": "Transpontual Fleet Management API",
        "version": "1.0.0",
        "status": "online",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint that's always responsive"""
    result = {"status": "healthy", "api": "online", "timestamp": datetime.now().isoformat()}

    # Test database connection with timeout
    try:
        async def test_db():
            db = SessionLocal()
            try:
                db.execute(text("SELECT 1"))
                db.close()
                return True
            except Exception:
                db.close()
                return False

        # Use asyncio timeout for DB test
        db_ok = await asyncio.wait_for(asyncio.to_thread(test_db), timeout=5.0)
        result["database"] = "connected" if db_ok else "disconnected"

    except asyncio.TimeoutError:
        result["database"] = "timeout"
    except Exception as e:
        result["database"] = f"error: {str(e)[:100]}"

    # Return 200 OK even if DB is having issues
    return result


# Compatibility endpoints for Flask dashboard (without /api/v1 prefix)
@app.get("/vehicles")
async def get_vehicles_compat(db: Session = Depends(get_db)):
    """Vehicles endpoint for dashboard compatibility"""
    try:
        vehicles = db.query(models.Veiculo).all()
        return vehicles
    except Exception as e:
        print(f"Error getting vehicles: {e}")
        return []

@app.post("/vehicles")
async def create_vehicle_compat(vehicle_data: dict, db: Session = Depends(get_db)):
    """Create vehicle endpoint for dashboard compatibility"""
    try:
        veiculo = models.Veiculo(**vehicle_data)
        db.add(veiculo)
        db.commit()
        db.refresh(veiculo)
        return veiculo
    except Exception as e:
        print(f"Error creating vehicle: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/checklist")
async def get_checklist_compat(limit: int = 25, offset: int = 0, db: Session = Depends(get_db)):
    """Checklist endpoint for dashboard compatibility"""
    try:
        checklists = db.query(models.Checklist).offset(offset).limit(limit).all()
        return checklists
    except Exception as e:
        print(f"Error getting checklists: {e}")
        return []

@app.get("/checklist/stats/resumo")
async def get_checklist_stats_compat(dias: int = 30, db: Session = Depends(get_db)):
    """Checklist stats for dashboard compatibility"""
    total = db.query(models.Checklist).count()
    aprovados = db.query(models.Checklist).filter(models.Checklist.status == "aprovado").count()
    return {
        "total_checklists": total,
        "taxa_aprovacao": (aprovados / total * 100) if total > 0 else 0,
    }

@app.get("/metrics/top-itens-reprovados")
async def get_top_itens_reprovados_compat(dias: int = 30):
    """Top rejected items for dashboard compatibility"""
    return {"itens_reprovados": [], "message": "Feature em desenvolvimento"}

@app.get("/metrics/performance-motoristas")
async def get_performance_motoristas_compat(dias: int = 30):
    """Driver performance for dashboard compatibility"""
    return {"motoristas": [], "message": "Feature em desenvolvimento"}

@app.get("/checklist/bloqueios")
async def get_checklist_bloqueios_compat(dias: int = 7):
    """Checklist blockages for dashboard compatibility"""
    return {"bloqueios": [], "message": "Feature em desenvolvimento"}

@app.get("/checklist/stats/evolucao")
async def get_checklist_evolucao_compat(dias: int = 7):
    """Checklist evolution stats for dashboard compatibility"""
    return []

@app.get("/drivers")
async def get_drivers_compat(db: Session = Depends(get_db)):
    """Drivers endpoint for dashboard compatibility"""
    try:
        motoristas = db.query(models.Motorista).all()
        result = []
        for motorista in motoristas:
            driver_data = {
                "id": motorista.id,
                "nome": motorista.nome,
                "cnh": motorista.cnh,
                "categoria": motorista.categoria,
                "validade_cnh": motorista.validade_cnh.isoformat() if motorista.validade_cnh else None,
                "observacoes": motorista.observacoes,
                "ativo": motorista.ativo,
                "criado_em": motorista.criado_em.isoformat() if motorista.criado_em else None
            }
            if motorista.usuario:
                driver_data["email"] = motorista.usuario.email
            result.append(driver_data)
        return result
    except Exception as e:
        print(f"Error getting drivers: {e}")
        return []

@app.get("/drivers/{driver_id}")
async def get_driver_compat(driver_id: int, db: Session = Depends(get_db)):
    """Get driver by ID endpoint for dashboard compatibility"""
    try:
        motorista = db.query(models.Motorista).filter(models.Motorista.id == driver_id).first()
        if not motorista:
            raise HTTPException(status_code=404, detail="Motorista não encontrado")

        driver_data = {
            "id": motorista.id,
            "nome": motorista.nome,
            "cnh": motorista.cnh,
            "categoria": motorista.categoria,
            "validade_cnh": motorista.validade_cnh.isoformat() if motorista.validade_cnh else None,
            "observacoes": motorista.observacoes,
            "ativo": motorista.ativo,
            "criado_em": motorista.criado_em.isoformat() if motorista.criado_em else None,
            "email": ""
        }
        if motorista.usuario:
            driver_data["email"] = motorista.usuario.email

        return driver_data
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting driver {driver_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/drivers/{driver_id}")
async def update_driver_compat(driver_id: int, driver_data: dict, db: Session = Depends(get_db)):
    """Update driver endpoint for dashboard compatibility"""
    try:
        motorista = db.query(models.Motorista).filter(models.Motorista.id == driver_id).first()
        if not motorista:
            raise HTTPException(status_code=404, detail="Motorista não encontrado")

        # Atualizar campos do motorista
        if 'nome' in driver_data:
            motorista.nome = driver_data['nome']
        if 'cnh' in driver_data:
            motorista.cnh = driver_data['cnh'] if driver_data['cnh'] else None
        if 'categoria' in driver_data:
            motorista.categoria = driver_data['categoria'] if driver_data['categoria'] else None
        if 'validade_cnh' in driver_data:
            validade_cnh = driver_data['validade_cnh']
            if validade_cnh and isinstance(validade_cnh, str) and validade_cnh.strip():
                try:
                    from datetime import datetime
                    motorista.validade_cnh = datetime.strptime(validade_cnh, '%Y-%m-%d').date()
                except ValueError:
                    motorista.validade_cnh = None
            else:
                motorista.validade_cnh = None
        if 'observacoes' in driver_data:
            motorista.observacoes = driver_data['observacoes']
        if 'ativo' in driver_data:
            motorista.ativo = driver_data['ativo']

        # Atualizar email do usuário se fornecido
        if 'email' in driver_data and motorista.usuario:
            existing_user = db.query(models.Usuario).filter(
                models.Usuario.email == driver_data['email'],
                models.Usuario.id != motorista.usuario.id
            ).first()
            if existing_user:
                raise HTTPException(status_code=400, detail="Email já está em uso")

            motorista.usuario.email = driver_data['email']

        db.commit()
        db.refresh(motorista)

        # Return updated data
        result = {
            "id": motorista.id,
            "nome": motorista.nome,
            "cnh": motorista.cnh,
            "categoria": motorista.categoria,
            "validade_cnh": motorista.validade_cnh.isoformat() if motorista.validade_cnh else None,
            "observacoes": motorista.observacoes,
            "ativo": motorista.ativo,
            "criado_em": motorista.criado_em.isoformat() if motorista.criado_em else None,
            "email": ""
        }
        if motorista.usuario:
            result["email"] = motorista.usuario.email

        return result

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error updating driver {driver_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/drivers")
async def create_driver_compat(driver_data: dict, db: Session = Depends(get_db)):
    """Create driver endpoint for dashboard compatibility"""
    try:
        # Create user first
        user = models.Usuario(
            nome=driver_data['nome'],
            email=driver_data.get('email', ''),
            senha_hash=generate_password_hash(driver_data.get('senha', '')),
            papel='motorista',
            ativo=driver_data.get('ativo', True)
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Convert date string to date object if needed
        validade_cnh = driver_data.get('validade_cnh')
        if validade_cnh and isinstance(validade_cnh, str) and validade_cnh.strip():
            from datetime import datetime
            try:
                validade_cnh = datetime.strptime(validade_cnh, '%Y-%m-%d').date()
            except ValueError:
                validade_cnh = None
        else:
            validade_cnh = None

        # Clean and validate fields
        cnh = driver_data.get('cnh', '').strip()
        categoria = driver_data.get('categoria', '').strip()

        # Create driver
        motorista = models.Motorista(
            nome=driver_data['nome'],
            usuario_id=user.id,
            cnh=cnh if cnh else None,
            categoria=categoria if categoria else None,
            validade_cnh=validade_cnh,
            observacoes=driver_data.get('observacoes', ''),
            ativo=driver_data.get('ativo', True)
        )
        db.add(motorista)
        db.commit()
        db.refresh(motorista)

        return {"id": motorista.id, "nome": motorista.nome, "message": "Motorista criado com sucesso"}
    except Exception as e:
        db.rollback()
        print(f"Error creating driver: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/checklist/modelos")
async def get_checklist_modelos_compat(db: Session = Depends(get_db)):
    """Checklist models endpoint for dashboard compatibility"""
    try:
        modelos = db.query(models.ChecklistModelo).filter(models.ChecklistModelo.ativo == True).all()
        result = []
        for modelo in modelos:
            result.append({
                "id": modelo.id,
                "nome": modelo.nome,
                "tipo": modelo.tipo,
                "versao": modelo.versao,
                "ativo": modelo.ativo,
                "criado_em": modelo.criado_em.isoformat() if modelo.criado_em else None
            })

        # If no models exist, create some sample ones
        if not result:
            sample_models = [
                {
                    "nome": "Checklist Pré-Viagem Caminhão",
                    "tipo": "pre",
                    "versao": 1
                },
                {
                    "nome": "Checklist Pós-Viagem Caminhão",
                    "tipo": "pos",
                    "versao": 1
                },
                {
                    "nome": "Checklist Inspeção Diária",
                    "tipo": "extra",
                    "versao": 1
                }
            ]

            for sample in sample_models:
                modelo = models.ChecklistModelo(**sample)
                db.add(modelo)

            db.commit()

            # Reload the models
            modelos = db.query(models.ChecklistModelo).filter(models.ChecklistModelo.ativo == True).all()
            result = []
            for modelo in modelos:
                result.append({
                    "id": modelo.id,
                    "nome": modelo.nome,
                    "tipo": modelo.tipo,
                    "versao": modelo.versao,
                    "ativo": modelo.ativo,
                    "criado_em": modelo.criado_em.isoformat() if modelo.criado_em else None
                })

        return result
    except Exception as e:
        print(f"Error getting checklist models: {e}")
        # Return sample data as fallback
        return [
            {
                "id": 1,
                "nome": "Checklist Pré-Viagem Caminhão",
                "tipo": "pre",
                "versao": 1,
                "ativo": True,
                "criado_em": datetime.now().isoformat()
            },
            {
                "id": 2,
                "nome": "Checklist Pós-Viagem Caminhão",
                "tipo": "pos",
                "versao": 1,
                "ativo": True,
                "criado_em": datetime.now().isoformat()
            },
            {
                "id": 3,
                "nome": "Checklist Inspeção Diária",
                "tipo": "extra",
                "versao": 1,
                "ativo": True,
                "criado_em": datetime.now().isoformat()
            }
        ]

@app.post("/checklist/start")
async def start_checklist_compat(checklist_data: dict, db: Session = Depends(get_db)):
    """Start checklist endpoint for dashboard compatibility"""
    try:
        # Create new checklist record
        checklist = models.Checklist(
            veiculo_id=checklist_data['veiculo_id'],
            motorista_id=checklist_data['motorista_id'],
            modelo_id=checklist_data['modelo_id'],
            tipo=checklist_data['tipo'],
            odometro_ini=checklist_data.get('odometro_ini', 0),
            status='em_andamento'
        )
        db.add(checklist)
        db.commit()
        db.refresh(checklist)

        # Return checklist data with id for redirect
        return {
            "id": checklist.id,
            "veiculo_id": checklist.veiculo_id,
            "motorista_id": checklist.motorista_id,
            "modelo_id": checklist.modelo_id,
            "tipo": checklist.tipo,
            "status": checklist.status,
            "dt_inicio": checklist.dt_inicio.isoformat() if checklist.dt_inicio else None,
            "message": "Checklist iniciado com sucesso"
        }
    except Exception as e:
        db.rollback()
        print(f"Error starting checklist: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/checklist/pending")
async def get_pending_checklists_compat(db: Session = Depends(get_db)):
    """Get checklists pending approval"""
    try:
        checklists = db.query(models.Checklist).filter(
            models.Checklist.status == "aguardando_aprovacao"
        ).outerjoin(models.Veiculo).outerjoin(models.Motorista).all()

        result = []
        for checklist in checklists:
            result.append({
                "id": checklist.id,
                "codigo": checklist.codigo or f"CL-{checklist.id}",
                "veiculo_placa": checklist.veiculo.placa if checklist.veiculo else "N/A",
                "veiculo_modelo": f"{checklist.veiculo.modelo} {checklist.veiculo.ano or ''}" if checklist.veiculo else "N/A",
                "motorista_nome": checklist.motorista.nome if checklist.motorista else "N/A",
                "dt_inicio": checklist.dt_inicio.isoformat() if checklist.dt_inicio else None,
                "dt_fim": checklist.dt_fim.isoformat() if checklist.dt_fim else None,
                "tipo": checklist.tipo or "pre",
                "observacoes_gerais": checklist.observacoes_gerais
            })

        return result
    except Exception as e:
        print(f"Error getting pending checklists: {e}")
        import traceback
        traceback.print_exc()
        return []

@app.get("/checklist/{checklist_id}")
async def get_checklist_compat(checklist_id: int, db: Session = Depends(get_db)):
    """Get checklist by ID for dashboard compatibility"""
    try:
        checklist = db.query(models.Checklist).filter(models.Checklist.id == checklist_id).first()
        if not checklist:
            raise HTTPException(status_code=404, detail="Checklist not found")

        # Get checklist items from the model
        items = db.query(models.ChecklistItem).filter(models.ChecklistItem.modelo_id == checklist.modelo_id).order_by(models.ChecklistItem.ordem).all()

        # Get existing responses for this checklist
        responses = db.query(models.ChecklistResposta).filter(models.ChecklistResposta.checklist_id == checklist_id).all()
        response_dict = {resp.item_id: resp for resp in responses}

        # Build items with responses
        items_data = []
        respostas_data = []
        for item in items:
            item_data = {
                "id": item.id,
                "ordem": item.ordem,
                "descricao": item.descricao,
                "categoria": item.categoria,
                "tipo_resposta": item.tipo_resposta,
                "severidade": item.severidade,
                "exige_foto": item.exige_foto,
                "bloqueia_viagem": item.bloqueia_viagem,
                "resposta": None,
                "observacao": None
            }

            # Add existing response if any
            if item.id in response_dict:
                resp = response_dict[item.id]
                item_data["resposta"] = resp.valor
                item_data["observacao"] = resp.observacao

                # Add to separate responses list for template compatibility
                respostas_data.append({
                    "item_id": item.id,
                    "valor": resp.valor,
                    "observacao": resp.observacao
                })

            items_data.append(item_data)

        # Calculate statistics
        itens_ok = sum(1 for resp in respostas_data if resp["valor"] == "ok")
        itens_nok = sum(1 for resp in respostas_data if resp["valor"] == "nao_ok")
        itens_na = sum(1 for resp in respostas_data if resp["valor"] == "na")
        itens_pendentes = len(items_data) - len(respostas_data)

        return {
            "id": checklist.id,
            "veiculo_id": checklist.veiculo_id,
            "motorista_id": checklist.motorista_id,
            "modelo_id": checklist.modelo_id,
            "tipo": checklist.tipo,
            "status": checklist.status,
            "odometro_ini": checklist.odometro_ini,
            "dt_inicio": checklist.dt_inicio.isoformat() if checklist.dt_inicio else None,
            "dt_fim": checklist.dt_fim.isoformat() if checklist.dt_fim else None,
            "veiculo": {
                "placa": checklist.veiculo.placa,
                "modelo": checklist.veiculo.modelo
            } if checklist.veiculo else None,
            "motorista": {
                "nome": checklist.motorista.nome
            } if checklist.motorista else None,
            "modelo": {
                "nome": checklist.modelo.nome,
                "tipo": checklist.modelo.tipo
            } if checklist.modelo else None,
            "itens": items_data,
            "respostas": respostas_data,
            "itens_ok": itens_ok,
            "itens_nok": itens_nok,
            "itens_na": itens_na,
            "itens_pendentes": itens_pendentes
        }
    except Exception as e:
        print(f"Error getting checklist {checklist_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/checklist/answer")
async def save_checklist_answer_compat(answer_data: dict, db: Session = Depends(get_db)):
    """Save checklist item answer for dashboard compatibility (no auth)"""
    try:
        # Expected format: { "checklist_id": 6, "item_id": 1, "valor": "ok", "observacao": "test" }
        checklist_id = answer_data['checklist_id']
        item_id = answer_data['item_id']
        valor = answer_data['valor']
        observacao = answer_data.get('observacao', '')

        # Check if response already exists
        existing = db.query(models.ChecklistResposta).filter(
            models.ChecklistResposta.checklist_id == checklist_id,
            models.ChecklistResposta.item_id == item_id
        ).first()

        if existing:
            # Update existing response
            existing.valor = valor
            existing.observacao = observacao
        else:
            # Create new response
            response = models.ChecklistResposta(
                checklist_id=checklist_id,
                item_id=item_id,
                valor=valor,
                observacao=observacao
            )
            db.add(response)

        db.commit()

        return {
            "success": True,
            "message": "Resposta salva com sucesso",
            "checklist_id": checklist_id,
            "item_id": item_id,
            "valor": valor
        }
    except Exception as e:
        db.rollback()
        print(f"Error saving checklist answer: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/checklist/finish")
async def finish_checklist_compat(finish_data: dict, db: Session = Depends(get_db)):
    """Finish checklist endpoint for dashboard compatibility"""
    try:
        checklist_id = finish_data['checklist_id']

        # Update checklist status
        checklist = db.query(models.Checklist).filter(models.Checklist.id == checklist_id).first()
        if not checklist:
            raise HTTPException(status_code=404, detail="Checklist not found")

        # Update checklist fields
        checklist.status = "aguardando_aprovacao"  # Changed from "finalizado" to pending approval
        checklist.dt_fim = datetime.now()
        if finish_data.get('odometro_fim'):
            checklist.odometro_fim = finish_data['odometro_fim']

        db.commit()

        return {
            "success": True,
            "message": "Checklist finalizado e enviado para aprovação",
            "checklist_id": checklist_id,
            "status": checklist.status,
            "redirect": "/checklists/new"
        }
    except Exception as e:
        db.rollback()
        print(f"Error finishing checklist: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/checklist/{checklist_id}")
async def delete_checklist_compat(checklist_id: int, db: Session = Depends(get_db)):
    """Delete checklist endpoint for dashboard compatibility"""
    try:
        checklist = db.query(models.Checklist).filter(models.Checklist.id == checklist_id).first()
        if not checklist:
            raise HTTPException(status_code=404, detail="Checklist not found")

        # Delete all responses first (foreign key constraint)
        db.query(models.ChecklistResposta).filter(
            models.ChecklistResposta.checklist_id == checklist_id
        ).delete()

        # Delete the checklist
        db.delete(checklist)
        db.commit()
        return {"success": True, "message": "Checklist excluído com sucesso"}
    except Exception as e:
        db.rollback()
        print(f"Error deleting checklist: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/checklist/answer")
async def save_checklist_answer(answer_data: dict, db: Session = Depends(get_db)):
    """Save checklist item answer for dashboard compatibility"""
    try:
        # Expected format: { "checklist_id": 6, "item_id": 1, "valor": "ok", "observacao": "test" }
        checklist_id = answer_data['checklist_id']
        item_id = answer_data['item_id']
        valor = answer_data['valor']
        observacao = answer_data.get('observacao', '')

        # Check if response already exists
        existing = db.query(models.ChecklistResposta).filter(
            models.ChecklistResposta.checklist_id == checklist_id,
            models.ChecklistResposta.item_id == item_id
        ).first()

        if existing:
            # Update existing response
            existing.valor = valor
            existing.observacao = observacao
        else:
            # Create new response
            response = models.ChecklistResposta(
                checklist_id=checklist_id,
                item_id=item_id,
                valor=valor,
                observacao=observacao
            )
            db.add(response)

        db.commit()

        return {
            "success": True,
            "message": "Resposta salva com sucesso",
            "checklist_id": checklist_id,
            "item_id": item_id,
            "valor": valor
        }
    except Exception as e:
        db.rollback()
        print(f"Error saving checklist answer: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/checklist-stats")
async def get_checklist_stats_api(db: Session = Depends(get_db)):
    """Checklist stats API endpoint"""
    try:
        total = db.query(models.Checklist).count()
        aprovados = db.query(models.Checklist).filter(models.Checklist.status == "aprovado").count()
        return {
            "total_checklists": total,
            "taxa_aprovacao": (aprovados / total * 100) if total > 0 else 0,
        }
    except Exception as e:
        print(f"Error getting checklist stats: {e}")
        return {"total_checklists": 0, "taxa_aprovacao": 0}


@app.post("/checklist/{checklist_id}/approve")
async def approve_checklist_compat(checklist_id: int, approval_data: dict, db: Session = Depends(get_db)):
    """Approve a checklist"""
    try:
        checklist = db.query(models.Checklist).filter(models.Checklist.id == checklist_id).first()
        if not checklist:
            raise HTTPException(status_code=404, detail="Checklist not found")

        checklist.status = "aprovado"
        checklist.aprovado_por = approval_data.get("aprovado_por", "gestor")
        checklist.dt_aprovacao = datetime.now()

        db.commit()
        return {"success": True, "message": "Checklist aprovado com sucesso"}
    except Exception as e:
        db.rollback()
        print(f"Error approving checklist: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/checklist/{checklist_id}/reject")
async def reject_checklist_compat(checklist_id: int, rejection_data: dict, db: Session = Depends(get_db)):
    """Reject a checklist"""
    try:
        checklist = db.query(models.Checklist).filter(models.Checklist.id == checklist_id).first()
        if not checklist:
            raise HTTPException(status_code=404, detail="Checklist not found")

        checklist.status = "reprovado"
        checklist.reprovado_por = rejection_data.get("reprovado_por", "gestor")
        checklist.motivo_reprovacao = rejection_data.get("motivo_reprovacao", "")
        checklist.dt_reprovacao = datetime.now()

        db.commit()
        return {"success": True, "message": "Checklist reprovado com sucesso"}
    except Exception as e:
        db.rollback()
        print(f"Error rejecting checklist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Debug endpoint to create test user
@app.post("/debug/create-test-user")
async def create_test_user(db: Session = Depends(get_db)):
    """Create test user for development"""
    try:
        from werkzeug.security import generate_password_hash

        # Check if user already exists
        existing = db.query(models.Usuario).filter(models.Usuario.email == "admin@test.com").first()
        if existing:
            return {"message": "Test user already exists", "email": "admin@test.com"}

        # Create test user
        test_user = models.Usuario(
            nome="Admin Test",
            email="admin@test.com",
            senha_hash=generate_password_hash("123456"),
            papel="gestor",
            ativo=True
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)

        return {"message": "Test user created successfully", "email": "admin@test.com", "password": "123456"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(status_code=404, content={"message": "Endpoint nao encontrado"})


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    return JSONResponse(status_code=500, content={"message": "Erro interno do servidor"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8005, reload=True)
