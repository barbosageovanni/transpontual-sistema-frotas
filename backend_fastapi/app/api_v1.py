# backend_fastapi/app/api_v1.py
"""
Router principal da API v1 - Vers?o simplificada com SSO
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.sql import func
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db, is_database_available
from app import models, schemas
from app.routers import checklist as checklist_router
from app.routers import fornecedores
from app.core.security import (
    create_access_token,
    verify_password,
    get_current_user,
    authenticate_via_sso_token,
    create_sso_login_url
)

# Router principal
api_router = APIRouter()

# Health check
@api_router.get("/health")
async def api_health():
    return {"status": "ok", "api": "v1"}

# Debug: informa??es r?pidas do banco
@api_router.get("/debug/db/info")
def debug_db_info(db: Session = Depends(get_db)):
    try:
        # Tenta impor um statement timeout baixo (pode n?o ter efeito dependendo do driver)
        try:
            db.execute(text("SET LOCAL statement_timeout = 2000"))
        except Exception:
            pass
        veiculos = db.query(models.Veiculo).count()
        motoristas = db.query(models.Motorista).count()
        usuarios = db.query(models.Usuario).count()
        return {
            "database": "connected",
            "counts": {
                "veiculos": veiculos,
                "motoristas": motoristas,
                "usuarios": usuarios,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"DB error: {e}")

# Auth b?sico
@api_router.post("/auth/login", response_model=schemas.Token)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    # Check if database is available
    if not is_database_available() or db is None:
        print("[WARN] Database offline - using demo login")
        # Demo login for offline mode
        if payload.email == "admin@transpontual.com" and payload.senha in ["admin123", "123456", "admin"]:
            # Create demo user object matching UsuarioResponse schema
            from datetime import datetime
            demo_user = {
                "id": 1,
                "nome": "Admin Demo",  # Changed from nome_completo to nome
                "email": "admin@transpontual.com",
                "papel": "gestor",
                "ativo": True,
                "criado_em": datetime.now(),  # Added required field
                "ultimo_acesso": None,
                "ultimo_ip": None,
                "tentativas_login": 0,
                "bloqueado_ate": None,
                "horario_inicio": None,
                "horario_fim": None,
                "dias_semana": None,
                "ips_permitidos": None,
                "localizacao_restrita": False,
                "data_validade": None,
                "max_sessoes": 1
            }
            token = create_access_token({"sub": "1", "email": payload.email})
            return {
                "access_token": token,
                "token_type": "bearer",
                "user": demo_user
            }
        else:
            raise HTTPException(status_code=401, detail="Credenciais inv?lidas (modo offline)")

    # Normal database operations
    try:
        user = db.query(models.Usuario).filter(models.Usuario.email == payload.email).first()

        # Dev bypass: create user if doesn't exist and using dev passwords
        if not user and payload.senha in ["123456", "admin", "test", "dev"]:
            user = models.Usuario(
                nome_completo="Dev User",
                email=payload.email,
                password_hash="dev_password",
                papel="gestor",
                ativo=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        if not user:
            raise HTTPException(status_code=401, detail="Credenciais inv?lidas")

        # Verifica senha (aceita hash bcrypt ou texto puro em DEV)
        if not verify_password(payload.senha, user.password_hash):
            raise HTTPException(status_code=401, detail="Credenciais inv?lidas")

        # JWT com subject = user.id
        token = create_access_token({"sub": str(user.id), "email": user.email}, user_obj=user)
        return {"access_token": token, "token_type": "bearer", "user": user}

    except Exception as e:
        print(f"[ERROR] Login database error: {e}")
        raise HTTPException(status_code=500, detail=f"Erro de conex?o: {str(e)[:50]}...")


# SSO Routes
@api_router.post("/auth/sso-login")
def sso_login(jwt_token: str = Query(...), db: Session = Depends(get_db)):
    """
    Login via SSO com token JWT de outro sistema Transpontual
    """
    try:
        # Autenticar via token SSO
        user = authenticate_via_sso_token(jwt_token, db)
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Token SSO inv?lido ou usu?rio n?o encontrado"
            )

        # Criar token local
        local_token = create_access_token(
            {"sub": str(user.id), "email": user.email},
            user_obj=user
        )

        return {
            "access_token": local_token,
            "token_type": "bearer",
            "user": user,
            "sso_authenticated": True
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Erro SSO login: {e}")
        raise HTTPException(status_code=500, detail="Erro interno no SSO")


@api_router.get("/auth/sso-links")
def get_sso_links(current_user: models.Usuario = Depends(get_current_user)):
    """
    Retorna links para outros sistemas com SSO
    """
    try:
        # URLs dos outros sistemas
        baker_url = "https://dashboard.transpontual.app.br/auth/sso-login"
        financial_url = "https://financeiro.transpontual.app.br/auth/sso-login"

        # Criar URLs com tokens SSO
        baker_sso_url = create_sso_login_url("baker", baker_url, current_user)
        financial_sso_url = create_sso_login_url("financeiro", financial_url, current_user)

        links = []

        if baker_sso_url:
            links.append({
                "system": "baker",
                "name": "Dashboard Baker",
                "url": baker_sso_url,
                "description": "Painel administrativo e financeiro"
            })

        if financial_sso_url:
            links.append({
                "system": "financeiro",
                "name": "Sistema Financeiro",
                "url": financial_sso_url,
                "description": "Gest?o financeira e cont?bil"
            })

        return {"links": links}

    except Exception as e:
        print(f"[ERROR] Erro gerando links SSO: {e}")
        return {"links": []}


# Usu?rio atual (prot?gido)
@api_router.get("/users/me", response_model=schemas.UsuarioResponse)
def get_me(current_user: models.Usuario = Depends(get_current_user)):
    return current_user

# Gerenciamento de usu?rios
@api_router.get("/users")
def list_users(
    papel: Optional[str] = Query(None, description="Filtrar por papel"),
    status: Optional[str] = Query(None, description="Filtrar por status (ativo/inativo/bloqueado)"),
    busca: Optional[str] = Query(None, description="Buscar por nome ou email"),
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    """Lista todos os usu?rios com filtros opcionais - apenas admin/gestor"""
    if current_user.papel not in ["admin", "gestor"]:
        raise HTTPException(status_code=403, detail="Sem permiss?o para listar usu?rios")

    # Check if database is available
    if not is_database_available() or db is None:
        print("?? Database offline - using demo user list")
        from datetime import datetime
        # Return demo users list
        demo_users = [
            {
                "id": 1,
                "nome": "Administrador do Sistema",
                "email": "admin@transpontual.com",
                "papel": "admin",
                "ativo": True,
                "criado_em": datetime.now(),
                "ultimo_acesso": None,
                "ultimo_ip": None,
                "tentativas_login": 0,
                "bloqueado_ate": None,
                "horario_inicio": None,
                "horario_fim": None,
                "dias_semana": None,
                "ips_permitidos": None,
                "localizacao_restrita": False,
                "data_validade": None,
                "max_sessoes": 1
            }
        ]
        return demo_users

    try:
        query = db.query(models.Usuario)

        # Filtro por papel
        if papel:
            query = query.filter(models.Usuario.tipo_usuario == papel)

        # Filtro por status
        if status:
            if status == "ativo":
                query = query.filter(models.Usuario.ativo == True)
            elif status == "inativo":
                query = query.filter(models.Usuario.ativo == False)

        # Filtro por busca (nome ou email)
        if busca:
            busca_pattern = f"%{busca}%"
            query = query.filter(
                (models.Usuario.nome_completo.ilike(busca_pattern)) |
                (models.Usuario.email.ilike(busca_pattern))
            )

        usuarios = query.all()

        # Converter para formato compat?vel
        result = []
        for user in usuarios:
            result.append({
                "id": user.id,
                "nome": user.nome_completo or user.username,
                "email": user.email,
                "papel": user.tipo_usuario or ("admin" if user.is_admin else "gestor"),
                "ativo": user.ativo and user.is_active,
                "criado_em": user.created_at.isoformat() if user.created_at else None,
                "ultimo_acesso": user.last_login.isoformat() if user.last_login else None,
                "tentativas_login": user.login_count or 0
            })

        return result

    except Exception as e:
        print(f"Erro ao listar usu?rios: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@api_router.get("/users/{user_id}", response_model=schemas.UsuarioResponse)
def get_user(user_id: int, db: Session = Depends(get_db), current_user: models.Usuario = Depends(get_current_user)):
    """Obter usu?rio por ID"""
    if current_user.papel not in ["admin", "gestor"]:
        raise HTTPException(status_code=403, detail="Sem permiss?o para ver usu?rios")

    user = db.query(models.Usuario).filter(models.Usuario.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usu?rio n?o encontrado")
    return user

# Duplicate endpoints removed - using comprehensive versions below

# Ve?culos
@api_router.get("/vehicles", response_model=List[schemas.VeiculoResponse])
def list_vehicles(db: Session = Depends(get_db)):
    if not is_database_available() or db is None:
        # Return demo vehicles for offline mode
        return [
            {
                "id": 1,
                "placa": "ABC-1234",
                "modelo": "Caminh?o Demo",
                "ano": 2020,
                "km_atual": 50000,
                "status": "ativo",
                "combustivel": "diesel"
            },
            {
                "id": 2,
                "placa": "DEF-5678",
                "modelo": "Van Demo",
                "ano": 2021,
                "km_atual": 30000,
                "status": "ativo",
                "combustivel": "flex"
            }
        ]
    return db.query(models.Veiculo).all()

@api_router.get("/vehicles/{vehicle_id}", response_model=schemas.VeiculoResponse)
def get_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    if not is_database_available() or db is None:
        # Return demo vehicle for offline mode
        return {
            "id": vehicle_id,
            "placa": f"DEMO-{vehicle_id:04d}",
            "modelo": "Ve?culo Demo",
            "ano": 2020,
            "km_atual": 50000,
            "status": "ativo",
            "combustivel": "diesel"
        }
    veiculo = db.query(models.Veiculo).filter(models.Veiculo.id == vehicle_id).first()
    if not veiculo:
        raise HTTPException(status_code=404, detail="Ve?culo n?o encontrado")
    return veiculo

@api_router.post("/vehicles", response_model=schemas.VeiculoResponse, status_code=201)
def create_vehicle(body: schemas.VeiculoCreate, db: Session = Depends(get_db)):
    veiculo = models.Veiculo(**body.model_dump())
    db.add(veiculo)
    db.commit()
    db.refresh(veiculo)
    return veiculo

@api_router.put("/vehicles/{vehicle_id}", response_model=schemas.VeiculoResponse)
def update_vehicle(vehicle_id: int, body: dict, db: Session = Depends(get_db)):
    veiculo = db.query(models.Veiculo).filter(models.Veiculo.id == vehicle_id).first()
    if not veiculo:
        raise HTTPException(status_code=404, detail="Ve?culo n?o encontrado")

    try:
        # Atualizar campos b?sicos
        for field in ['placa', 'modelo', 'ano', 'km_atual', 'renavam', 'observacoes_manutencao']:
            if field in body and body[field] is not None:
                if field == 'ano' and body[field]:
                    setattr(veiculo, field, int(body[field]))
                elif field == 'km_atual' and body[field]:
                    setattr(veiculo, field, int(body[field]))
                else:
                    setattr(veiculo, field, body[field])

        # Processar campos boolean
        if 'ativo' in body:
            value = body['ativo']
            if isinstance(value, str):
                value = value.lower() in ('true', '1', 'on', 'yes')
            veiculo.ativo = bool(value)

        if 'em_manutencao' in body:
            value = body['em_manutencao']
            if isinstance(value, str):
                value = value.lower() in ('true', '1', 'on', 'yes')
            veiculo.em_manutencao = bool(value)

        db.commit()
        db.refresh(veiculo)
        return veiculo

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao atualizar ve?culo: {str(e)}")

# Motoristas
@api_router.get("/drivers", response_model=List[schemas.MotoristaResponse])
def list_drivers(db: Session = Depends(get_db)):
    if not is_database_available() or db is None:
        return [
            {
                "id": 1,
                "nome": "Jo?o Silva - Demo",
                "email": "joao@demo.com",
                "telefone": "(11) 99999-9999",
                "cnh": "12345678901",
                "validade_cnh": "2025-12-31",
                "ativo": True,
                "usuario_id": None
            },
            {
                "id": 2,
                "nome": "Maria Santos - Demo",
                "email": "maria@demo.com",
                "telefone": "(11) 88888-8888",
                "cnh": "10987654321",
                "validade_cnh": "2026-06-30",
                "ativo": True,
                "usuario_id": None
            }
        ]

    try:
        return db.query(models.Motorista).all()
    except Exception as e:
        print(f"Database error in list_drivers: {e}")
        return []

@api_router.post("/drivers", response_model=schemas.MotoristaResponse, status_code=201)
def create_driver(body: schemas.MotoristaCreate, db: Session = Depends(get_db)):
    """Criar novo motorista"""
    try:
        # Primeiro criar o usu?rio se email e senha foram fornecidos
        usuario = None
        if body.email and body.senha:
            # Verificar se j? existe usu?rio com este email
            existing_user = db.query(models.Usuario).filter(models.Usuario.email == body.email).first()
            if existing_user:
                raise HTTPException(status_code=400, detail="Email j? est? em uso")
            
            # Criar usu?rio (usar nome do motorista para o usu?rio tamb?m)
            usuario = models.Usuario(
                nome=body.nome,  # Usar nome do motorista
                email=body.email,
                senha_hash=body.senha,  # Em produ??o deveria usar hash
                papel="motorista",
                ativo=True
            )
            db.add(usuario)
            db.flush()  # Para obter o ID

        # Criar motorista
        motorista_data = body.model_dump(exclude=['email', 'senha', 'usuario_id'])
        motorista = models.Motorista(
            usuario_id=usuario.id if usuario else None,
            **motorista_data
        )
        
        db.add(motorista)
        db.commit()
        db.refresh(motorista)
        
        return motorista
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao criar motorista: {str(e)}")

@api_router.put("/drivers/{driver_id}", response_model=schemas.MotoristaResponse)
def update_driver(driver_id: int, body: dict, db: Session = Depends(get_db)):
    """Atualizar motorista"""
    try:
        from datetime import datetime

        motorista = db.query(models.Motorista).filter(models.Motorista.id == driver_id).first()
        if not motorista:
            raise HTTPException(status_code=404, detail="Motorista n?o encontrado")

        # Atualizar campos b?sicos do motorista
        for field in ['nome', 'cnh', 'categoria', 'observacoes']:
            if field in body and body[field] is not None:
                setattr(motorista, field, body[field])

        # Processar data de validade da CNH
        if 'validade_cnh' in body and body['validade_cnh']:
            if isinstance(body['validade_cnh'], str):
                try:
                    motorista.validade_cnh = datetime.strptime(body['validade_cnh'], '%Y-%m-%d').date()
                except ValueError:
                    # Tentar outros formatos de data
                    try:
                        motorista.validade_cnh = datetime.strptime(body['validade_cnh'], '%d/%m/%Y').date()
                    except ValueError:
                        pass  # Manter valor atual se n?o conseguir converter
            else:
                motorista.validade_cnh = body['validade_cnh']
        elif 'validade_cnh' in body and not body['validade_cnh']:
            motorista.validade_cnh = None

        # Processar campo ativo
        if 'ativo' in body:
            value = body['ativo']
            if isinstance(value, str):
                value = value.lower() in ('true', '1', 'on', 'yes')
            motorista.ativo = bool(value)

        # Atualizar email do usu?rio se fornecido
        if 'email' in body and body['email'] and motorista.usuario:
            existing_user = db.query(models.Usuario).filter(
                models.Usuario.email == body['email'],
                models.Usuario.id != motorista.usuario.id
            ).first()
            if existing_user:
                raise HTTPException(status_code=400, detail="Email j? est? em uso")

            motorista.usuario.email = body['email']

        db.commit()
        db.refresh(motorista)

        return motorista

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar motorista: {str(e)}")

@api_router.get("/drivers/{driver_id}", response_model=schemas.MotoristaResponse)
def get_driver(driver_id: int, db: Session = Depends(get_db)):
    """Obter motorista por ID"""
    motorista = db.query(models.Motorista).filter(models.Motorista.id == driver_id).first()
    if not motorista:
        raise HTTPException(status_code=404, detail="Motorista n?o encontrado")
    return motorista

# Checklists
@api_router.get("/checklist")
def list_checklists(
    page: int = 1,
    per_page: int = 12,
    veiculo_id: Optional[int] = Query(None),
    motorista_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    tipo: Optional[str] = Query(None),
    data_inicio: Optional[str] = Query(None),
    data_fim: Optional[str] = Query(None),
    limit: Optional[int] = Query(None),
    offset: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    # Check database availability first
    if not is_database_available() or db is None:
        return {
            "total": 0,
            "checklists": [],
            "page": page,
            "per_page": per_page,
            "offline_mode": True,
            "message": "Banco de dados n?o dispon?vel - modo offline"
        }

    try:
        from datetime import datetime

        # Usar limit e offset se fornecidos, sen?o usar page e per_page
        if limit is not None and offset is not None:
            actual_limit = limit
            actual_offset = offset
        else:
            actual_limit = per_page
            actual_offset = (page - 1) * per_page

        # Double-check database session is valid before querying
        if db is None:
            return {
                "total": 0,
                "checklists": [],
                "page": page,
                "per_page": per_page,
                "offline_mode": True,
                "message": "Database session is None"
            }

        # Construir query com filtros
        query = db.query(models.Checklist)

        # Aplicar filtros
        if veiculo_id:
            query = query.filter(models.Checklist.veiculo_id == veiculo_id)

        if motorista_id:
            query = query.filter(models.Checklist.motorista_id == motorista_id)

        if status:
            query = query.filter(models.Checklist.status == status)

        if tipo:
            query = query.filter(models.Checklist.tipo == tipo)

        if data_inicio:
            try:
                data_inicio_dt = datetime.strptime(data_inicio, '%Y-%m-%d')
                query = query.filter(models.Checklist.dt_inicio >= data_inicio_dt)
            except ValueError:
                pass  # Ignorar se formato de data inv?lido

        if data_fim:
            try:
                data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d')
                # Adicionar 23:59:59 para incluir todo o dia
                from datetime import timedelta
                data_fim_dt = data_fim_dt + timedelta(days=1) - timedelta(seconds=1)
                query = query.filter(models.Checklist.dt_inicio <= data_fim_dt)
            except ValueError:
                pass  # Ignorar se formato de data inv?lido

        # Buscar dados com filtros e pagina??o
        total = query.count()
        checklists = query.offset(actual_offset).limit(actual_limit).all()

        # Load related data
        veiculo_ids = {c.veiculo_id for c in checklists if c.veiculo_id}
        motorista_ids = {c.motorista_id for c in checklists if c.motorista_id}
        modelo_ids = {c.modelo_id for c in checklists if c.modelo_id}

        # Get vehicles
        veiculos = {}
        if veiculo_ids:
            for v in db.query(models.Veiculo).filter(models.Veiculo.id.in_(veiculo_ids)).all():
                veiculos[v.id] = {"placa": v.placa, "modelo": v.modelo}

        # Get drivers
        motoristas = {}
        if motorista_ids:
            for m in db.query(models.Motorista).filter(models.Motorista.id.in_(motorista_ids)).all():
                motoristas[m.id] = {"nome": m.nome}

        # Get models
        modelos = {}
        if modelo_ids:
            for mod in db.query(models.ChecklistModelo).filter(models.ChecklistModelo.id.in_(modelo_ids)).all():
                modelos[mod.id] = {"nome": mod.nome, "tipo": mod.tipo}

        # Build response with related data
        checklist_data = []
        for c in checklists:
            v = veiculos.get(c.veiculo_id, {})
            m = motoristas.get(c.motorista_id, {})
            mod = modelos.get(c.modelo_id, {})

            checklist_data.append({
                "id": c.id,
                "veiculo_id": c.veiculo_id,
                "veiculo_placa": v.get("placa"),
                "veiculo_modelo": v.get("modelo"),
                "motorista_id": c.motorista_id,
                "motorista_nome": m.get("nome"),
                "modelo_id": c.modelo_id,
                "modelo_nome": mod.get("nome"),
                "modelo_tipo": mod.get("tipo"),
                "tipo": c.tipo,
                "status": c.status,
                "dt_inicio": c.dt_inicio.isoformat() if c.dt_inicio else None,
                "dt_fim": c.dt_fim.isoformat() if c.dt_fim else None,
                "odometro_ini": c.odometro_ini,
                "odometro_fim": c.odometro_fim,
            })

        return {
            "checklists": checklist_data,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "pages": (total + per_page - 1) // per_page
            }
        }
    except Exception as e:
        print(f"Error listing checklists: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/checklist/complete")
def complete_checklist(checklist_data: dict, db: Session = Depends(get_db)):
    """Endpoint para finalizar um checklist com respostas"""
    try:
        # Rollback any previous failed transaction
        db.rollback()

        # Buscar ou criar ve?culo
        vehicle = db.query(models.Veiculo).filter(models.Veiculo.placa == checklist_data['vehicle']).first()
        if not vehicle:
            vehicle = models.Veiculo(
                placa=checklist_data['vehicle'],
                ativo=True,
                km_atual=0
            )
            db.add(vehicle)
            db.flush()

        # Buscar ou criar motorista padr?o
        motorista = db.query(models.Motorista).first()
        if not motorista:
            # Criar motorista padr?o
            usuario = models.Usuario(
                nome="Motorista Padr?o",
                email="motorista@transpontual.com",
                senha_hash="default",
                papel="motorista"
            )
            db.add(usuario)
            db.flush()

            motorista = models.Motorista(
                nome="Motorista Padr?o",
                usuario_id=usuario.id,
                ativo=True
            )
            db.add(motorista)
            db.flush()

        # Buscar ou criar modelo de checklist padr?o
        modelo = db.query(models.ChecklistModelo).first()
        if not modelo:
            modelo = models.ChecklistModelo(
                nome="Checklist Padr?o",
                tipo="saida",
                ativo=True
            )
            db.add(modelo)
            db.flush()

        # Criar checklist
        checklist = models.Checklist(
            veiculo_id=vehicle.id,
            motorista_id=motorista.id,
            modelo_id=modelo.id,
            tipo=checklist_data.get('type', 'saida').lower(),
            status="concluido",
            dt_fim=func.now()
        )
        db.add(checklist)
        db.flush()

        # Salvar respostas
        item_counter = 1
        for item_id, response_data in checklist_data.get('responses', {}).items():
            # Criar ou buscar item do checklist
            item = db.query(models.ChecklistItem).filter(
                models.ChecklistItem.modelo_id == modelo.id,
                models.ChecklistItem.ordem == item_counter
            ).first()

            if not item:
                item = models.ChecklistItem(
                    modelo_id=modelo.id,
                    ordem=item_counter,
                    descricao=f"Item {item_counter}",
                    categoria="verificacao",
                    tipo_resposta="multipla_escolha",
                    severidade="baixa"
                )
                db.add(item)
                db.flush()

            # Salvar respostas selecionadas
            selected_options = response_data.get('selected', [])
            others_text = response_data.get('others', '')

            if selected_options or others_text:
                response_value = {
                    'selected': selected_options,
                    'others': others_text,
                    'has_photos': len(response_data.get('photos', [])) > 0
                }

                checklist_response = models.ChecklistResposta(
                    checklist_id=checklist.id,
                    item_id=item.id,
                    valor=str(response_value),
                    observacao=others_text if others_text else None
                )
                db.add(checklist_response)

            item_counter += 1

        db.commit()
        return {"message": "Checklist salvo com sucesso", "checklist_id": checklist.id}

    except Exception as e:
        db.rollback()
        print(f"Error completing checklist: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Upload b?sico
@api_router.post("/uploads/image", response_model=schemas.UploadResponse)
async def upload_image():
    # Implementa??o b?sica
    return {"filename": "test.jpg"}

# KPIs b?sicos
@api_router.get("/kpis/summary")
def kpi_summary(db: Session = Depends(get_db)):
    if not is_database_available() or db is None:
        return {
            "total_checklists": 150,
            "aprovados": 120,
            "reprovados": 30,
            "taxa_aprovacao": 80.0,
            "offline_mode": True
        }

    try:
        total = db.query(models.Checklist).count()
        aprovados = db.query(models.Checklist).filter(models.Checklist.status == "aprovado").count()
        return {
            "total": total,
            "aprovados": aprovados,
            "reprovados": total - aprovados,
            "taxa_aprovacao": (aprovados / total * 100) if total > 0 else 0,
        }
    except Exception as e:
        print(f"Database error in kpi_summary: {e}")
        return {
            "total_checklists": 150,
            "aprovados": 120,
            "reprovados": 30,
            "taxa_aprovacao": 80.0,
            "offline_mode": True
        }

# Checklist stats para testes
@api_router.get("/checklist/stats/summary")
def checklist_stats_summary(db: Session = Depends(get_db)):
    if not is_database_available() or db is None:
        # Return demo stats for offline mode
        return {
            "total_checklists": 150,
            "aprovados": 120,
            "reprovados": 30,
            "taxa_aprovacao": 80.0,
            "offline_mode": True
        }

    try:
        total = db.query(models.Checklist).count()
        aprovados = db.query(models.Checklist).filter(models.Checklist.status == "aprovado").count()
        reprovados = db.query(models.Checklist).filter(models.Checklist.status == "reprovado").count()
        return {
            "total_checklists": total,
            "aprovados": aprovados,
            "reprovados": reprovados,
            "taxa_aprovacao": (aprovados / total * 100) if total > 0 else 0,
        }
    except Exception as e:
        print(f"Database error in checklist_stats_summary: {e}")
        return {
            "total_checklists": 150,
            "aprovados": 120,
            "reprovados": 30,
            "taxa_aprovacao": 80.0,
            "offline_mode": True
        }

# Additional endpoints for dashboard compatibility
@api_router.get("/checklist/stats/resumo")
def checklist_stats_resumo(dias: int = 30, db: Session = Depends(get_db)):
    """Resumo de estat?sticas de checklist (compatibilidade)"""
    if not is_database_available() or db is None:
        # Return demo stats for offline mode
        return {
            "total_checklists": 150,
            "aprovados": 120,
            "reprovados": 30,
            "taxa_aprovacao": 80.0,
            "offline_mode": True
        }
    return checklist_stats_summary(db)

@api_router.get("/metrics/top-itens-reprovados")
def metrics_top_itens_reprovados(dias: int = 30, db: Session = Depends(get_db)):
    """Top itens reprovados nos ?ltimos dias"""
    return {"itens_reprovados": [], "message": "Feature em desenvolvimento"}

@api_router.get("/metrics/performance-motoristas")
def metrics_performance_motoristas(dias: int = 30, db: Session = Depends(get_db)):
    """Performance dos motoristas nos ?ltimos dias"""
    return {"motoristas": [], "message": "Feature em desenvolvimento"}

@api_router.get("/checklist/bloqueios")
def checklist_bloqueios(dias: int = 7, db: Session = Depends(get_db)):
    """Checklists com bloqueios nos ?ltimos dias"""
    return {"bloqueios": [], "message": "Feature em desenvolvimento"}

@api_router.get("/checklist/pending")
def checklist_pending(db: Session = Depends(get_db)):
    """Checklists pendentes de aprova??o"""
    if not is_database_available() or db is None:
        return {
            "pending_checklists": [],
            "total": 0,
            "offline_mode": True,
            "message": "Banco de dados n?o dispon?vel - modo offline"
        }

    try:
        checklists = db.query(models.Checklist).filter(
            models.Checklist.status == "aguardando_aprovacao"
        ).outerjoin(models.Veiculo).outerjoin(models.Motorista).all()

        result = []
        for checklist in checklists:
            result.append({
                "id": checklist.id,
                "veiculo_placa": checklist.veiculo.placa if checklist.veiculo else None,
                "motorista_nome": checklist.motorista.nome if checklist.motorista else None,
                "data_criacao": checklist.dt_inicio.isoformat() if checklist.dt_inicio else None,
                "status": checklist.status
            })

        return result
    except Exception as e:
        return []

# ===============================
# M?DULO DE ABASTECIMENTO
# ===============================

@api_router.post("/abastecimentos/upload-cupom")
async def upload_cupom_fiscal(request: Request):
    """
    Processa upload de cupom fiscal e extrai dados usando OCR
    """
    import logging
    logger = logging.getLogger(__name__)

    try:
        from app.services.cupom_extractor import extract_cupom_data

        # Receber arquivo da requisição
        form = await request.form()
        file_upload = form.get('file')

        if not file_upload:
            raise HTTPException(status_code=400, detail="Nenhum arquivo enviado")

        # Ler conteúdo do arquivo
        file_content = await file_upload.read()

        # Extrair dados do cupom
        data = extract_cupom_data(file_content)

        # Log para debug
        logger.info(f"OCR extraction completed")
        logger.info(f"Extracted data keys: {list(data.keys())}")
        logger.info(f"Posto: {data.get('posto')}")
        logger.info(f"Litros: {data.get('litros')}")
        logger.info(f"Valor litro: {data.get('valor_litro')}")
        logger.info(f"Valor total: {data.get('valor_total')}")
        logger.info(f"Has raw_text: {bool(data.get('raw_text'))}")
        if data.get('raw_text'):
            logger.info(f"Raw text length: {len(data.get('raw_text', ''))}")
            logger.info(f"Raw text preview (first 200 chars): {data.get('raw_text', '')[:200]}")

        # Verificar qualidade da extração
        campos_importantes = ['litros', 'valor_litro', 'valor_total', 'data_abastecimento']
        campos_extraidos = sum(1 for campo in campos_importantes if data.get(campo))

        message = "Cupom processado com sucesso"
        warning = None

        if campos_extraidos == 0:
            warning = "Não foi possível extrair dados importantes do cupom. Verifique a qualidade da imagem e tente novamente com uma foto mais nítida e bem iluminada."
        elif campos_extraidos < len(campos_importantes):
            warning = f"Apenas {campos_extraidos} de {len(campos_importantes)} campos foram extraídos. Revise os dados e preencha os campos faltantes manualmente."

        return {
            "success": True,
            "data": data,
            "message": message,
            "warning": warning,
            "campos_extraidos": campos_extraidos,
            "total_campos": len(campos_importantes)
        }

    except ImportError as e:
        logger.error(f"Erro de importação OCR: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail="OCR não disponível. Instale as dependências: pip install pytesseract pillow"
        )
    except Exception as e:
        logger.error(f"Erro ao processar cupom: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Erro ao processar cupom: {str(e)}")

@api_router.get("/abastecimentos")
def list_abastecimentos(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    veiculo_id: int = Query(None),
    motorista_id: int = Query(None),
    data_inicio: str = Query(None),
    data_fim: str = Query(None),
    db: Session = Depends(get_db)
):
    """Lista abastecimentos com filtros"""
    query = db.query(models.Abastecimento).join(models.Veiculo).join(models.Motorista)

    if veiculo_id:
        query = query.filter(models.Abastecimento.veiculo_id == veiculo_id)

    if motorista_id:
        query = query.filter(models.Abastecimento.motorista_id == motorista_id)

    if data_inicio:
        try:
            from datetime import datetime
            data_inicio_dt = datetime.fromisoformat(data_inicio)
            query = query.filter(models.Abastecimento.data_abastecimento >= data_inicio_dt)
        except:
            pass

    if data_fim:
        try:
            from datetime import datetime
            data_fim_dt = datetime.fromisoformat(data_fim)
            query = query.filter(models.Abastecimento.data_abastecimento <= data_fim_dt)
        except:
            pass

    abastecimentos = query.order_by(models.Abastecimento.data_abastecimento.desc()).offset(skip).limit(limit).all()

    result = []
    for abast in abastecimentos:
        result.append({
            "id": abast.id,
            "data_abastecimento": abast.data_abastecimento.isoformat() if abast.data_abastecimento else None,
            "veiculo_id": abast.veiculo_id,
            "motorista_id": abast.motorista_id,
            "veiculo_placa": abast.veiculo.placa if abast.veiculo else None,
            "veiculo_marca": abast.veiculo.marca if abast.veiculo else None,
            "veiculo_modelo": abast.veiculo.modelo if abast.veiculo else None,
            "motorista_nome": abast.motorista.nome if abast.motorista else None,
            "odometro": abast.odometro,
            "litros": abast.litros,
            "valor_litro": abast.valor_litro,
            "valor_total": abast.valor_total,
            "posto": abast.posto,
            "tipo_combustivel": abast.tipo_combustivel,
            "numero_cupom": abast.numero_cupom,
            "observacoes": abast.observacoes
        })

    return result

@api_router.post("/abastecimentos")
def create_abastecimento(abastecimento_data: dict, db: Session = Depends(get_db)):
    """Cria novo abastecimento"""
    try:
        from datetime import datetime

        abastecimento = models.Abastecimento(
            veiculo_id=abastecimento_data["veiculo_id"],
            motorista_id=abastecimento_data["motorista_id"],
            fornecedor_id=abastecimento_data.get("fornecedor_id"),
            data_abastecimento=datetime.fromisoformat(abastecimento_data.get("data_abastecimento", datetime.now().isoformat())),
            odometro=abastecimento_data["odometro"],
            litros=str(abastecimento_data["litros"]),
            valor_litro=str(abastecimento_data["valor_litro"]),
            valor_total=str(abastecimento_data["valor_total"]),
            posto=abastecimento_data.get("posto"),
            tipo_combustivel=abastecimento_data.get("tipo_combustivel", "Diesel"),
            numero_cupom=abastecimento_data.get("numero_cupom"),
            observacoes=abastecimento_data.get("observacoes")
        )

        db.add(abastecimento)
        db.commit()
        db.refresh(abastecimento)

        return {"id": abastecimento.id, "message": "Abastecimento criado com sucesso"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao criar abastecimento: {str(e)}")

@api_router.get("/abastecimentos/{abastecimento_id}")
def get_abastecimento(abastecimento_id: int, db: Session = Depends(get_db)):
    """Busca abastecimento por ID"""
    abast = db.query(models.Abastecimento).filter(models.Abastecimento.id == abastecimento_id).first()
    if not abast:
        raise HTTPException(status_code=404, detail="Abastecimento n?o encontrado")

    return {
        "id": abast.id,
        "veiculo_id": abast.veiculo_id,
        "motorista_id": abast.motorista_id,
        "data_abastecimento": abast.data_abastecimento.isoformat() if abast.data_abastecimento else None,
        "odometro": abast.odometro,
        "litros": abast.litros,
        "valor_litro": abast.valor_litro,
        "valor_total": abast.valor_total,
        "posto": abast.posto,
        "tipo_combustivel": abast.tipo_combustivel,
        "numero_cupom": abast.numero_cupom,
        "observacoes": abast.observacoes
    }

@api_router.put("/abastecimentos/{abastecimento_id}")
def update_abastecimento(
    abastecimento_id: int,
    abastecimento_data: dict,
    db: Session = Depends(get_db)
):
    """Atualizar abastecimento existente"""
    abastecimento = db.query(models.Abastecimento).filter(
        models.Abastecimento.id == abastecimento_id
    ).first()

    if not abastecimento:
        raise HTTPException(status_code=404, detail="Abastecimento n?o encontrado")

    try:
        from datetime import datetime

        # Atualizar campos fornecidos
        for campo, valor in abastecimento_data.items():
            if hasattr(abastecimento, campo):
                if campo == "data_abastecimento" and valor:
                    setattr(abastecimento, campo, datetime.fromisoformat(valor))
                else:
                    setattr(abastecimento, campo, valor)

        db.commit()
        db.refresh(abastecimento)

        return {
            "id": abastecimento.id,
            "veiculo_id": abastecimento.veiculo_id,
            "motorista_id": abastecimento.motorista_id,
            "data_abastecimento": abastecimento.data_abastecimento.isoformat() if abastecimento.data_abastecimento else None,
            "odometro": abastecimento.odometro,
            "litros": abastecimento.litros,
            "valor_litro": abastecimento.valor_litro,
            "valor_total": abastecimento.valor_total,
            "posto": abastecimento.posto,
            "tipo_combustivel": abastecimento.tipo_combustivel,
            "numero_cupom": abastecimento.numero_cupom,
            "observacoes": abastecimento.observacoes
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao atualizar abastecimento: {str(e)}")

@api_router.delete("/abastecimentos/{abastecimento_id}")
def delete_abastecimento(
    abastecimento_id: int,
    db: Session = Depends(get_db)
):
    """Excluir abastecimento"""
    abastecimento = db.query(models.Abastecimento).filter(
        models.Abastecimento.id == abastecimento_id
    ).first()

    if not abastecimento:
        raise HTTPException(status_code=404, detail="Abastecimento n?o encontrado")

    try:
        db.delete(abastecimento)
        db.commit()
        return {"message": "Abastecimento exclu?do com sucesso"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao excluir abastecimento: {str(e)}")

# ===============================
# M?DULO DE ORDEM DE SERVI?O
# ===============================

@api_router.get("/ordens-servico")
def list_ordens_servico(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    veiculo_id: int = Query(None),
    status: str = Query(None),
    tipo_servico: str = Query(None),
    data_inicio: str = Query(None),
    data_fim: str = Query(None),
    db: Session = Depends(get_db)
):
    """Lista ordens de servi?o com filtros"""
    try:
        # Verificar se a tabela existe tentando fazer uma consulta simples
        ordens = db.query(models.OrdemServico).limit(1).all()

        # Se chegou at? aqui, a tabela existe, fazer consulta completa
        query = db.query(models.OrdemServico)

        if veiculo_id:
            query = query.filter(models.OrdemServico.veiculo_id == veiculo_id)

        if status:
            query = query.filter(models.OrdemServico.status == status)

        if tipo_servico:
            query = query.filter(models.OrdemServico.tipo_servico == tipo_servico)

        # Filtros de data
        if data_inicio:
            from datetime import datetime
            try:
                data_inicio_dt = datetime.fromisoformat(data_inicio)
                query = query.filter(models.OrdemServico.data_abertura >= data_inicio_dt)
            except:
                pass

        if data_fim:
            from datetime import datetime
            try:
                data_fim_dt = datetime.fromisoformat(data_fim)
                query = query.filter(models.OrdemServico.data_abertura <= data_fim_dt)
            except:
                pass

        ordens = query.order_by(models.OrdemServico.data_abertura.desc()).offset(skip).limit(limit).all()

        result = []
        for ordem in ordens:
            try:
                # Buscar dados do ve?culo separadamente
                veiculo = None
                if ordem.veiculo_id:
                    try:
                        veiculo = db.query(models.Veiculo).filter(models.Veiculo.id == ordem.veiculo_id).first()
                    except:
                        pass

                result.append({
                    "id": ordem.id,
                    "numero_os": ordem.numero_os,
                    "veiculo_id": ordem.veiculo_id,
                    "veiculo_placa": veiculo.placa if veiculo else None,
                    "veiculo_marca": veiculo.marca if veiculo else None,
                    "veiculo_modelo": veiculo.modelo if veiculo else None,
                    "tipo_servico": ordem.tipo_servico,
                    "status": ordem.status,
                    "data_abertura": ordem.data_abertura.isoformat() if ordem.data_abertura else None,
                    "data_prevista": ordem.data_prevista.isoformat() if ordem.data_prevista else None,
                    "data_conclusao": ordem.data_conclusao.isoformat() if ordem.data_conclusao else None,
                    "oficina": ordem.oficina,
                    "odometro": ordem.odometro,
                    "valor_total": ordem.valor_total,
                    "descricao_problema": ordem.descricao_problema,
                    "descricao_servico": ordem.descricao_servico,
                    "observacoes": ordem.observacoes
                })
            except Exception as e:
                # Se der erro em uma ordem espec?fica, pular
                continue

        return result

    except Exception as e:
        # Se der erro (tabela n?o existe, etc), retornar lista vazia
        return []

class OrdemServicoCreate(BaseModel):
    veiculo_id: int
    tipo_servico: str
    status: Optional[str] = "Aberta"
    data_prevista: Optional[str] = None
    oficina: Optional[str] = None
    odometro: Optional[int] = None
    descricao_problema: Optional[str] = None
    descricao_servico: Optional[str] = None
    valor_total: Optional[float] = None
    observacoes: Optional[str] = None

class OrdemServicoUpdate(BaseModel):
    veiculo_id: Optional[int] = None
    tipo_servico: Optional[str] = None
    status: Optional[str] = None
    data_prevista: Optional[str] = None
    data_conclusao: Optional[str] = None
    oficina: Optional[str] = None
    odometro: Optional[int] = None
    descricao_problema: Optional[str] = None
    descricao_servico: Optional[str] = None
    valor_total: Optional[float] = None
    observacoes: Optional[str] = None

@api_router.post("/ordens-servico")
def create_ordem_servico(ordem_data: OrdemServicoCreate, db: Session = Depends(get_db)):
    """Cria nova ordem de servi?o"""
    try:
        from datetime import datetime

        # Verificar se a tabela existe primeiro
        try:
            db.query(models.OrdemServico).limit(1).all()
        except Exception:
            raise HTTPException(status_code=500, detail="Tabela ordens_servico n?o existe ou n?o est? acess?vel")

        # Criar ordem de servi?o sem numero_os para evitar erro de coluna
        ordem_dict = {
            'veiculo_id': ordem_data.veiculo_id,
            'tipo_servico': ordem_data.tipo_servico,
            'status': ordem_data.status or "Aberta",
            'data_abertura': datetime.now(),
            'data_prevista': datetime.fromisoformat(ordem_data.data_prevista) if ordem_data.data_prevista else None,
            'oficina': ordem_data.oficina,
            'odometro': ordem_data.odometro,
            'descricao_problema': ordem_data.descricao_problema,
            'descricao_servico': ordem_data.descricao_servico,
            'valor_total': str(ordem_data.valor_total) if ordem_data.valor_total else None,
            'observacoes': ordem_data.observacoes
        }

        # Filtrar campos nulos
        ordem_dict = {k: v for k, v in ordem_dict.items() if v is not None}

        ordem = models.OrdemServico(**ordem_dict)

        db.add(ordem)
        db.commit()
        db.refresh(ordem)

        return {"id": ordem.id, "message": "Ordem de servi?o criada com sucesso"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao criar ordem de servi?o: {str(e)}")

@api_router.get("/ordens-servico/{ordem_id}")
def get_ordem_servico(ordem_id: int, db: Session = Depends(get_db)):
    """Busca ordem de servi?o por ID com itens"""
    ordem = db.query(models.OrdemServico).filter(models.OrdemServico.id == ordem_id).first()
    if not ordem:
        raise HTTPException(status_code=404, detail="Ordem de servi?o n?o encontrada")

    itens = db.query(models.OrdemServicoItem).filter(models.OrdemServicoItem.ordem_servico_id == ordem_id).all()

    return {
        "id": ordem.id,
        "veiculo_id": ordem.veiculo_id,
        "veiculo_placa": ordem.veiculo.placa if ordem.veiculo else None,
        "veiculo_marca": ordem.veiculo.marca if ordem.veiculo else None,
        "veiculo_modelo": ordem.veiculo.modelo if ordem.veiculo else None,
        "tipo_servico": ordem.tipo_servico,
        "status": ordem.status,
        "data_abertura": ordem.data_abertura.isoformat() if ordem.data_abertura else None,
        "data_prevista": ordem.data_prevista.isoformat() if ordem.data_prevista else None,
        "data_conclusao": ordem.data_conclusao.isoformat() if ordem.data_conclusao else None,
        "oficina": ordem.oficina,
        "odometro": ordem.odometro,
        "descricao_problema": ordem.descricao_problema,
        "descricao_servico": ordem.descricao_servico,
        "valor_total": ordem.valor_total,
        "observacoes": ordem.observacoes,
        "itens": [{
            "id": item.id,
            "tipo_item": item.tipo_item,
            "descricao": item.descricao,
            "quantidade": item.quantidade,
            "valor_unitario": item.valor_unitario,
            "valor_total": item.valor_total,
            "observacoes": item.observacoes
        } for item in itens]
    }

@api_router.put("/ordens-servico/{ordem_id}")
def update_ordem_servico(
    ordem_id: int,
    ordem_data: dict,
    db: Session = Depends(get_db)
):
    """Atualizar ordem de servi?o existente"""
    ordem = db.query(models.OrdemServico).filter(
        models.OrdemServico.id == ordem_id
    ).first()

    if not ordem:
        raise HTTPException(status_code=404, detail="Ordem de servi?o n?o encontrada")

    try:
        from datetime import datetime

        # Filtrar campos de data vazios ANTES de processar
        clean_data = {}
        for campo, valor in ordem_data.items():
            if campo in ["data_abertura", "data_prevista", "data_conclusao"]:
                # Para campos de data: apenas incluir se n?o for string vazia
                if valor and isinstance(valor, str) and valor.strip():
                    clean_data[campo] = valor
                # Se for string vazia, n?o incluir no update (manter valor atual)
            else:
                # Para outros campos: incluir se n?o for None
                if valor is not None:
                    clean_data[campo] = valor

        # Atualizar apenas os campos filtrados
        for campo, valor in clean_data.items():
            if hasattr(ordem, campo):
                if campo in ["data_abertura", "data_prevista", "data_conclusao"]:
                    # Converter string de data para datetime
                    if isinstance(valor, str):
                        setattr(ordem, campo, datetime.fromisoformat(valor))
                    else:
                        setattr(ordem, campo, valor)
                else:
                    setattr(ordem, campo, valor)

        db.commit()
        db.refresh(ordem)

        return {
            "id": ordem.id,
            "numero_os": ordem.numero_os,
            "veiculo_id": ordem.veiculo_id,
            "tipo_servico": ordem.tipo_servico,
            "status": ordem.status,
            "data_abertura": ordem.data_abertura.isoformat() if ordem.data_abertura else None,
            "data_prevista": ordem.data_prevista.isoformat() if ordem.data_prevista else None,
            "data_conclusao": ordem.data_conclusao.isoformat() if ordem.data_conclusao else None,
            "oficina": ordem.oficina,
            "odometro": ordem.odometro,
            "descricao_problema": ordem.descricao_problema,
            "descricao_servico": ordem.descricao_servico,
            "valor_total": ordem.valor_total,
            "observacoes": ordem.observacoes
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao atualizar ordem de servi?o: {str(e)}")

@api_router.delete("/ordens-servico/{ordem_id}")
def delete_ordem_servico(
    ordem_id: int,
    db: Session = Depends(get_db)
):
    """Excluir ordem de servi?o"""
    ordem = db.query(models.OrdemServico).filter(
        models.OrdemServico.id == ordem_id
    ).first()

    if not ordem:
        raise HTTPException(status_code=404, detail="Ordem de servi?o n?o encontrada")

    try:
        # Excluir itens relacionados primeiro
        db.query(models.OrdemServicoItem).filter(
            models.OrdemServicoItem.ordem_servico_id == ordem_id
        ).delete()

        # Excluir a ordem
        db.delete(ordem)
        db.commit()
        return {"message": "Ordem de servi?o exclu?da com sucesso"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao excluir ordem de servi?o: {str(e)}")

# Debug: Populate checklist items for existing models
@api_router.post("/debug/populate-checklist-items")
def populate_checklist_items(db: Session = Depends(get_db)):
    """Populate checklist items for existing models based on form"""
    try:
        # Define checklist items based on the form model
        checklist_items = [
            # MOTOR
            {"categoria": "motor", "descricao": "Vazamento ?leo do motor", "ordem": 1},
            {"categoria": "motor", "descricao": "N?vel de ?leo do motor", "ordem": 2},
            {"categoria": "motor", "descricao": "Vazamento de ?gua", "ordem": 3},
            {"categoria": "motor", "descricao": "N?vel de ?gua", "ordem": 4},
            {"categoria": "motor", "descricao": "Correia do motor", "ordem": 5},
            {"categoria": "motor", "descricao": "Mangueiras", "ordem": 6},

            # FREIOS
            {"categoria": "freios", "descricao": "N?vel do fluido de freio", "ordem": 7},
            {"categoria": "freios", "descricao": "Vazamento nas rodas dianteiras", "ordem": 8},
            {"categoria": "freios", "descricao": "Vazamento nas rodas traseiras", "ordem": 9},
            {"categoria": "freios", "descricao": "Freio de estacionamento", "ordem": 10},

            # PNEUS
            {"categoria": "pneus", "descricao": "Condi??es dos pneus dianteiros", "ordem": 11},
            {"categoria": "pneus", "descricao": "Condi??es dos pneus traseiros", "ordem": 12},
            {"categoria": "pneus", "descricao": "Pneu sobressalente", "ordem": 13},
            {"categoria": "pneus", "descricao": "Calibragem dos pneus", "ordem": 14},

            # RODAS
            {"categoria": "rodas", "descricao": "Porcas das rodas dianteiras", "ordem": 15},
            {"categoria": "rodas", "descricao": "Porcas das rodas traseiras", "ordem": 16},

            # COMBUST?VEL
            {"categoria": "combustivel", "descricao": "N?vel de combust?vel", "ordem": 17},
            {"categoria": "combustivel", "descricao": "Vazamento de combust?vel", "ordem": 18},

            # EL?TRICA
            {"categoria": "eletrica", "descricao": "Bateria", "ordem": 19},
            {"categoria": "eletrica", "descricao": "Far?is", "ordem": 20},
            {"categoria": "eletrica", "descricao": "Lanternas", "ordem": 21},
            {"categoria": "eletrica", "descricao": "Pisca alerta", "ordem": 22},
            {"categoria": "eletrica", "descricao": "Luz de freio", "ordem": 23},
            {"categoria": "eletrica", "descricao": "Luz de r?", "ordem": 24},
            {"categoria": "eletrica", "descricao": "Buzina", "ordem": 25},

            # CABINE
            {"categoria": "cabine", "descricao": "Espelhos", "ordem": 26},
            {"categoria": "cabine", "descricao": "Limpador de para-brisa", "ordem": 27},
            {"categoria": "cabine", "descricao": "Vidros", "ordem": 28},
            {"categoria": "cabine", "descricao": "Painel de instrumentos", "ordem": 29},
            {"categoria": "cabine", "descricao": "Cinto de seguran?a", "ordem": 30},
            {"categoria": "cabine", "descricao": "Banco do motorista", "ordem": 31},

            # DOCUMENTOS
            {"categoria": "documentos", "descricao": "CNH do motorista", "ordem": 32},
            {"categoria": "documentos", "descricao": "CRLV do ve?culo", "ordem": 33},

            # EQUIPAMENTOS
            {"categoria": "equipamentos", "descricao": "Extintor", "ordem": 34},
            {"categoria": "equipamentos", "descricao": "Tri?ngulo", "ordem": 35},
            {"categoria": "equipamentos", "descricao": "Chave de roda", "ordem": 36},
            {"categoria": "equipamentos", "descricao": "Macaco", "ordem": 37},
        ]

        # Get all existing models
        models = db.query(models.ChecklistModelo).all()

        created_count = 0
        for modelo in models:
            # Check if this model already has items
            existing_items = db.query(models.ChecklistItem).filter(
                models.ChecklistItem.modelo_id == modelo.id
            ).count()

            if existing_items == 0:
                # Create items for this model
                for item_data in checklist_items:
                    checklist_item = models.ChecklistItem(
                        modelo_id=modelo.id,
                        categoria=item_data["categoria"],
                        descricao=item_data["descricao"],
                        ordem=item_data["ordem"],
                        tipo_resposta="multipla_escolha",
                        severidade="media",
                        ativo=True
                    )
                    db.add(checklist_item)
                    created_count += 1

        db.commit()
        return {
            "message": f"Created {created_count} checklist items for {len(models)} models",
            "models": [{"id": m.id, "nome": m.nome} for m in models]
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error populating items: {str(e)}")

# Checklist finish endpoint
@api_router.post("/checklist/{checklist_id}/finish")
def finish_checklist_v1(checklist_id: int, body: dict = {}, db: Session = Depends(get_db)):
    """Finalizar checklist"""
    try:
        checklist = db.get(models.Checklist, checklist_id)
        if not checklist:
            raise HTTPException(status_code=404, detail="Checklist n?o encontrado")

        checklist.status = "aguardando_aprovacao"
        from datetime import datetime
        checklist.dt_fim = datetime.utcnow()

        db.commit()
        db.refresh(checklist)

        return {
            "message": "Checklist finalizado com sucesso",
            "checklist": {
                "id": checklist.id,
                "status": checklist.status,
                "dt_fim": checklist.dt_fim.isoformat()
            }
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# Checklist delete endpoint
@api_router.delete("/checklist/{checklist_id}")
def delete_checklist_v1(checklist_id: int, db: Session = Depends(get_db)):
    """Excluir checklist"""
    try:
        checklist = db.get(models.Checklist, checklist_id)
        if not checklist:
            raise HTTPException(status_code=404, detail="Checklist n?o encontrado")

        # Delete all responses first (foreign key constraint)
        db.query(models.ChecklistResposta).filter(
            models.ChecklistResposta.checklist_id == checklist_id
        ).delete()

        # Delete the checklist
        db.delete(checklist)
        db.commit()
        return {"message": "Checklist exclu?do com sucesso"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# Include Checklist router
api_router.include_router(checklist_router.router, prefix="/checklist")

# Include Fornecedores router
api_router.include_router(fornecedores.router, prefix="/fornecedores", tags=["fornecedores"])

# ===============================
# M?DULO DE CONTROLE DE ACESSO AVAN?ADO
# ===============================

# Moved to avoid duplicate route - see line 1169

@api_router.get("/users/permissions/{modulo}/{acao}")
def check_user_permission(
    modulo: str,
    acao: str,
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verifica se o usu?rio tem permiss?o para uma a??o espec?fica em um m?dulo"""
    from app.security import verificar_permissao_modulo

    permitido = verificar_permissao_modulo(current_user, modulo, acao, db)

    return {
        "usuario_id": current_user.id,
        "modulo": modulo,
        "acao": acao,
        "permitido": permitido
    }

@api_router.post("/users/activity")
def register_user_activity(
    activity_data: dict,
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Registra atividade do usu?rio para auditoria"""
    try:
        log = models.LogAcesso(
            usuario_id=current_user.id,
            ip_acesso=activity_data.get('ip', ''),
            user_agent=activity_data.get('user_agent', ''),
            url_acessada=activity_data.get('url', ''),
            metodo_http=activity_data.get('method', ''),
            sucesso=True
        )
        db.add(log)

        # Atualizar ?ltima atividade do usu?rio
        current_user.ultimo_acesso = func.now()
        if activity_data.get('ip'):
            current_user.ultimo_ip = activity_data['ip']

        db.commit()
        return {"message": "Atividade registrada com sucesso"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao registrar atividade: {str(e)}")

@api_router.post("/users/log-action")
def log_user_action(
    action_data: dict,
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Registra a??o importante do usu?rio"""
    try:
        log = models.LogAcesso(
            usuario_id=current_user.id,
            ip_acesso=action_data.get('ip', ''),
            user_agent=action_data.get('user_agent', ''),
            url_acessada=action_data.get('url', ''),
            metodo_http=action_data.get('method', ''),
            sucesso=True,
            # Pode adicionar campo de detalhes se necess?rio
        )
        db.add(log)
        db.commit()
        return {"message": "A??o registrada com sucesso"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao registrar a??o: {str(e)}")

@api_router.get("/users/session-check")
def check_user_session(
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verifica se a sess?o do usu?rio ? v?lida"""
    try:
        # Verificar se o usu?rio n?o foi bloqueado ou desativado
        if not current_user.ativo:
            return {"valida": False, "motivo": "Usu?rio inativo"}

        if current_user.bloqueado_ate and current_user.bloqueado_ate > func.now():
            return {"valida": False, "motivo": "Usu?rio bloqueado"}

        # Verificar limite de sess?es (implementa??o simplificada)
        # Em um sistema real, voc? manteria controle das sess?es ativas
        return {"valida": True}

    except Exception as e:
        return {"valida": False, "motivo": f"Erro na verifica??o: {str(e)}"}

# Duplicate route removed - see comprehensive implementation starting at line 1284

# Duplicate route removed - see comprehensive implementation at line 82

@api_router.post("/users", response_model=schemas.UsuarioResponse, status_code=201)
def create_user(
    user_data: schemas.UsuarioCreate,
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cria novo usu?rio (apenas admins e gestores)"""
    # Verificar se ? admin ou gestor
    if current_user.papel not in ['admin', 'gestor']:
        raise HTTPException(status_code=403, detail="Sem permiss?o para criar usu?rios")

    try:
        from app.core.security import hash_password
        from datetime import datetime, time, date
        import logging

        logger = logging.getLogger(__name__)
        logger.info(f"Creating user with data: {user_data}")

        # Verificar se email j? existe
        existing_user = db.query(models.Usuario).filter(models.Usuario.email == user_data.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email j? cadastrado")

        # Processar dias da semana
        dias_semana = None
        if user_data.dias_semana:
            if isinstance(user_data.dias_semana, list):
                dias_semana = ','.join(map(str, user_data.dias_semana))
            elif isinstance(user_data.dias_semana, str):
                dias_semana = user_data.dias_semana

        user = models.Usuario(
            username=user_data.email.split('@')[0],  # Gerar username a partir do email
            nome_completo=user_data.nome,
            email=user_data.email,
            password_hash=hash_password(user_data.senha),
            tipo_usuario=user_data.papel,
            is_admin=(user_data.papel == 'admin'),
            ativo=user_data.ativo,
            is_active=user_data.ativo,
            # Campos extras que n?o existem no modelo atual ser?o ignorados
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return user

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating user: {str(e)}")
        logger.error(f"Exception type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=400, detail=f"Erro ao criar usu?rio: {str(e)}")

@api_router.put("/users/{user_id}")
def update_user(
    user_id: int,
    user_data: dict,
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Atualiza usu?rio existente (apenas admins)"""
    # Verificar se ? admin
    if current_user.papel != 'admin':
        raise HTTPException(status_code=403, detail="Acesso negado")

    user = db.query(models.Usuario).filter(models.Usuario.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usu?rio n?o encontrado")

    try:
        from datetime import datetime

        # Atualizar campos b?sicos
        for campo in ['nome', 'email', 'papel', 'ativo', 'ips_permitidos', 'localizacao_restrita', 'max_sessoes']:
            if campo in user_data and user_data[campo] is not None:
                # Convers?o de tipos quando necess?rio
                if campo == 'ativo':
                    value = user_data[campo]
                    if isinstance(value, str):
                        value = value.lower() in ('true', '1', 'on', 'yes')
                    setattr(user, campo, bool(value))
                elif campo == 'max_sessoes' and user_data[campo]:
                    setattr(user, campo, int(user_data[campo]))
                else:
                    setattr(user, campo, user_data[campo])

        # Processar hor?rios
        if 'horario_inicio' in user_data and user_data['horario_inicio']:
            if isinstance(user_data['horario_inicio'], str):
                user.horario_inicio = datetime.strptime(user_data['horario_inicio'], '%H:%M').time()
            else:
                user.horario_inicio = user_data['horario_inicio']
        elif 'horario_inicio' in user_data and not user_data['horario_inicio']:
            user.horario_inicio = None

        if 'horario_fim' in user_data and user_data['horario_fim']:
            if isinstance(user_data['horario_fim'], str):
                user.horario_fim = datetime.strptime(user_data['horario_fim'], '%H:%M').time()
            else:
                user.horario_fim = user_data['horario_fim']
        elif 'horario_fim' in user_data and not user_data['horario_fim']:
            user.horario_fim = None

        # Processar data de validade
        if 'data_validade' in user_data and user_data['data_validade']:
            if isinstance(user_data['data_validade'], str):
                user.data_validade = datetime.strptime(user_data['data_validade'], '%Y-%m-%d').date()
            else:
                user.data_validade = user_data['data_validade']
        elif 'data_validade' in user_data and not user_data['data_validade']:
            user.data_validade = None

        # Processar dias da semana
        if 'dias_semana' in user_data:
            if isinstance(user_data['dias_semana'], list):
                user.dias_semana = ','.join(map(str, user_data['dias_semana']))
            else:
                user.dias_semana = user_data['dias_semana']

        # Processar senha se fornecida
        if 'senha' in user_data and user_data['senha']:
            # Em produção, usar hash adequado
            user.password_hash = user_data['senha']

        # Salvar mudanças do usuário primeiro
        db.commit()
        db.refresh(user)

        # Processar permissões por sistema SSO se fornecidas
        permissions_updated = False
        sistemas = ['frotas', 'baker', 'financeiro']

        for sistema in sistemas:
            perm_key = f'permissoes_{sistema}'
            if perm_key in user_data and user_data[perm_key]:
                permissions_updated = True
                perm_data = user_data[perm_key]

                # Remover permissões existentes para este sistema
                db.query(models.UsuarioPermissao).filter(
                    models.UsuarioPermissao.usuario_id == user_id,
                    models.UsuarioPermissao.modulo == sistema
                ).delete()

                # Adicionar novas permissões baseadas nos checkboxes
                if isinstance(perm_data, dict):
                    if perm_data.get('acesso_leitura'):
                        db.add(models.UsuarioPermissao(
                            usuario_id=user_id, modulo=sistema,
                            acao='visualizar', permitido=True
                        ))
                    if perm_data.get('acesso_escrita'):
                        db.add(models.UsuarioPermissao(
                            usuario_id=user_id, modulo=sistema,
                            acao='editar', permitido=True
                        ))
                    if perm_data.get('acesso_exclusao'):
                        db.add(models.UsuarioPermissao(
                            usuario_id=user_id, modulo=sistema,
                            acao='excluir', permitido=True
                        ))
                    if perm_data.get('admin_completo'):
                        for acao in ['visualizar', 'criar', 'editar', 'excluir']:
                            db.add(models.UsuarioPermissao(
                                usuario_id=user_id, modulo=sistema,
                                acao=acao, permitido=True
                            ))

        if permissions_updated:
            db.commit()

        return {"id": user.id, "message": "Usu?rio atualizado com sucesso"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao atualizar usu?rio: {str(e)}")

@api_router.post("/users/{user_id}/activate")
def activate_user(
    user_id: int,
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Ativa usu?rio"""
    if current_user.papel != 'admin':
        raise HTTPException(status_code=403, detail="Acesso negado")

    user = db.query(models.Usuario).filter(models.Usuario.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usu?rio n?o encontrado")

    user.ativo = True
    user.tentativas_login = 0
    user.bloqueado_ate = None

    db.commit()
    return {"message": "Usu?rio ativado com sucesso"}

@api_router.post("/users/{user_id}/deactivate")
def deactivate_user(
    user_id: int,
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Desativa usu?rio"""
    if current_user.papel != 'admin':
        raise HTTPException(status_code=403, detail="Acesso negado")

    user = db.query(models.Usuario).filter(models.Usuario.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usu?rio n?o encontrado")

    user.ativo = False
    db.commit()
    return {"message": "Usu?rio desativado com sucesso"}

@api_router.get("/users/{user_id}/permissions")
def get_user_permissions(
    user_id: int,
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obt?m permiss?es espec?ficas do usu?rio"""
    if current_user.papel != 'admin':
        raise HTTPException(status_code=403, detail="Acesso negado")

    user = db.query(models.Usuario).filter(models.Usuario.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usu?rio n?o encontrado")

    # Buscar permiss?es espec?ficas
    permissoes = db.query(models.UsuarioPermissao).filter(
        models.UsuarioPermissao.usuario_id == user_id
    ).all()

    permissoes_dict = {}
    for perm in permissoes:
        if perm.modulo not in permissoes_dict:
            permissoes_dict[perm.modulo] = {}
        permissoes_dict[perm.modulo][perm.acao] = perm.permitido

    return {
        "usuario_id": user_id,
        "permissoes_especificas": permissoes_dict
    }

@api_router.post("/users/{user_id}/permissions")
def update_user_permissions(
    user_id: int,
    permissions_data: dict,
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Atualiza permiss?es espec?ficas do usu?rio"""
    if current_user.papel != 'admin':
        raise HTTPException(status_code=403, detail="Acesso negado")

    user = db.query(models.Usuario).filter(models.Usuario.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usu?rio n?o encontrado")

    try:
        # Remover todas as permiss?es espec?ficas existentes
        db.query(models.UsuarioPermissao).filter(
            models.UsuarioPermissao.usuario_id == user_id
        ).delete()

        # Adicionar novas permiss?es
        for key, value in permissions_data.items():
            if '_' in key:  # formato: modulo_acao
                modulo, acao = key.split('_', 1)
                if value:  # apenas criar se for True
                    permissao = models.UsuarioPermissao(
                        usuario_id=user_id,
                        modulo=modulo,
                        acao=acao,
                        permitido=True
                    )
                    db.add(permissao)

        db.commit()
        return {"message": "Permiss?es atualizadas com sucesso"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao atualizar permiss?es: {str(e)}")

@api_router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Exclui um usu?rio (apenas admins)"""
    if current_user.papel != 'admin':
        raise HTTPException(status_code=403, detail="Acesso negado")

    # Verificar se o usu?rio existe
    user = db.query(models.Usuario).filter(models.Usuario.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usu?rio n?o encontrado")

    # N?o permitir excluir a si mesmo
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="N?o ? poss?vel excluir seu pr?prio usu?rio")

    try:
        # Excluir permiss?es espec?ficas relacionadas
        db.query(models.UsuarioPermissao).filter(
            models.UsuarioPermissao.usuario_id == user_id
        ).delete()

        # Excluir logs de acesso relacionados (opcional, pode manter para auditoria)
        # db.query(models.LogAcesso).filter(
        #     models.LogAcesso.usuario_id == user_id
        # ).delete()

        # Excluir o usu?rio
        db.delete(user)
        db.commit()

        return {"message": f"Usu?rio {user.nome} exclu?do com sucesso"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao excluir usu?rio: {str(e)}")

@api_router.get("/users/{user_id}/access-log")
def get_user_access_log(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obt?m log de acesso do usu?rio"""
    if current_user.papel != 'admin':
        raise HTTPException(status_code=403, detail="Acesso negado")

    logs = db.query(models.LogAcesso).filter(
        models.LogAcesso.usuario_id == user_id
    ).order_by(models.LogAcesso.timestamp.desc()).offset(skip).limit(limit).all()

    return [{
        "id": log.id,
        "ip_acesso": log.ip_acesso,
        "url_acessada": log.url_acessada,
        "metodo_http": log.metodo_http,
        "status_resposta": log.status_resposta,
        "timestamp": log.timestamp.isoformat() if log.timestamp else None,
        "sucesso": log.sucesso,
        "motivo_falha": log.motivo_falha
    } for log in logs]

# Endpoint para inicializar perfis padr?o
@api_router.post("/admin/init-profiles")
def initialize_default_profiles(
    current_user: models.Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Inicializa os perfis de acesso padr?o"""
    if current_user.papel != 'admin':
        raise HTTPException(status_code=403, detail="Acesso negado")

    try:
        from app.security import criar_perfis_padrao
        criar_perfis_padrao(db)
        return {"message": "Perfis padr?o criados com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar perfis: {str(e)}")

# Maintenance alerts endpoint
@api_router.get("/maintenance/alerts-data")
def get_maintenance_alerts(db: Session = Depends(get_db)):
    if not is_database_available() or db is None:
        # Return demo maintenance alerts for offline mode
        return {
            "alerts": [
                {
                    "id": 1,
                    "veiculo_id": 1,
                    "veiculo_placa": "ABC-1234",
                    "tipo": "Revis?o",
                    "descricao": "Revis?o de 50.000km",
                    "vencimento": "2024-01-15",
                    "prioridade": "alta"
                },
                {
                    "id": 2,
                    "veiculo_id": 2,
                    "veiculo_placa": "DEF-5678",
                    "tipo": "Troca de ?leo",
                    "descricao": "Troca de ?leo do motor",
                    "vencimento": "2024-01-20",
                    "prioridade": "media"
                }
            ],
            "total": 2,
            "offline_mode": True
        }

    # Normal database operations would go here
    return {"alerts": [], "total": 0, "offline_mode": False}




 
