"""
Checklist Service - Sistema Transpontual
Regras de negócio e operações relacionadas ao checklist
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, or_, func

from app.models import (
    Checklist, ChecklistModelo, ChecklistItem, ChecklistResposta,
    Defeito, OrdemServico, Veiculo, Motorista, Viagem
)
from app.core.exceptions import BusinessRuleException
import logging

logger = logging.getLogger(__name__)

class ChecklistService:
    """Serviço principal para operações de checklist"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_checklist(
        self,
        veiculo_id: int,
        motorista_id: int,
        modelo_id: int,
        tipo: str,
        viagem_id: Optional[int] = None,
        odometro_ini: Optional[int] = None,
        geo_inicio: Optional[str] = None,
        dispositivo_info: Optional[Dict] = None,
        created_by: Optional[int] = None
    ) -> Checklist:
        """
        Criar novo checklist com validações de negócio
        """
        # Validações básicas
        veiculo = self.db.get(Veiculo, veiculo_id)
        if not veiculo or not veiculo.ativo:
            raise BusinessRuleException(
                "Veículo não encontrado ou inativo",
                code="VEICULO_INATIVO"
            )
        
        motorista = self.db.get(Motorista, motorista_id)
        if not motorista or not motorista.ativo:
            raise BusinessRuleException(
                "Motorista não encontrado ou inativo",
                code="MOTORISTA_INATIVO"
            )
        
        modelo = self.db.get(ChecklistModelo, modelo_id)
        if not modelo or not modelo.ativo:
            raise BusinessRuleException(
                "Modelo de checklist não encontrado ou inativo",
                code="MODELO_INATIVO"
            )
        
        # Verificar se categoria do veículo é compatível com o modelo
        if (modelo.categoria_veiculo and 
            modelo.categoria_veiculo != 'todos' and 
            veiculo.categoria != modelo.categoria_veiculo):
            raise BusinessRuleException(
                f"Modelo de checklist não compatível com veículo categoria {veiculo.categoria}",
                code="CATEGORIA_INCOMPATIVEL"
            )
        
        # Verificar checklist pendente para mesmo veículo e tipo
        existing = self.db.query(Checklist).filter(
            Checklist.veiculo_id == veiculo_id,
            Checklist.tipo == tipo,
            Checklist.status.in_(['pendente', 'em_andamento'])
        ).first()
        
        if existing:
            raise BusinessRuleException(
                f"Já existe checklist {tipo} pendente para este veículo (ID: {existing.id})",
                code="CHECKLIST_PENDENTE"
            )
        
        # Validações específicas por tipo
        if tipo == "pre":
            # Para pré-viagem, verificar se há checklist pós-viagem pendente
            pos_pendente = self.db.query(Checklist).filter(
                Checklist.veiculo_id == veiculo_id,
                Checklist.tipo == 'pos',
                Checklist.status.in_(['pendente', 'em_andamento'])
            ).first()
            
            if pos_pendente:
                raise BusinessRuleException(
                    "Existe checklist pós-viagem pendente. Finalize-o antes de iniciar pré-viagem",
                    code="POS_VIAGEM_PENDENTE"
                )
                
        elif tipo == "pos":
            # Para pós-viagem, deve existir pré-viagem aprovado recente
            pre_recente = self.db.query(Checklist).filter(
                Checklist.veiculo_id == veiculo_id,
                Checklist.tipo == 'pre',
                Checklist.status == 'aprovado',
                Checklist.dt_inicio >= datetime.utcnow() - timedelta(days=1)
            ).first()
            
            if not pre_recente:
                logger.warning(f"Checklist pós-viagem sem pré-viagem aprovado recente - Veículo: {veiculo.placa}")
        
        # Validar viagem se fornecida
        if viagem_id:
            viagem = self.db.get(Viagem, viagem_id)
            if not viagem:
                raise BusinessRuleException(
                    "Viagem não encontrada",
                    code="VIAGEM_NAO_ENCONTRADA"
                )
            
            if viagem.veiculo_id != veiculo_id:
                raise BusinessRuleException(
                    "Viagem não pertence ao veículo selecionado",
                    code="VIAGEM_VEICULO_INCOMPATIVEL"
                )
            
            if viagem.status == 'bloqueada':
                raise BusinessRuleException(
                    "Não é possível iniciar checklist para viagem bloqueada",
                    code="VIAGEM_BLOQUEADA"
                )
        
        # Validar odômetro
        if odometro_ini is not None and odometro_ini < veiculo.km_atual:
            logger.warning(f"Odômetro inicial ({odometro_ini}) menor que atual do veículo ({veiculo.km_atual})")
        
        # Criar checklist
        checklist = Checklist(
            veiculo_id=veiculo_id,
            motorista_id=motorista_id,
            modelo_id=modelo_id,
            viagem_id=viagem_id,
            tipo=tipo,
            odometro_ini=odometro_ini,
            geo_inicio=geo_inicio,
            dispositivo_info=dispositivo_info,
            criado_por=created_by
        )
        
        self.db.add(checklist)
        self.db.flush()
        
        logger.info(f"Checklist criado: {checklist.id} - Veículo: {veiculo.placa} - Tipo: {tipo}")
        
        return checklist
    
    def update_responses(
        self,
        checklist_id: int,
        respostas: List[Dict[str, Any]],
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Atualizar respostas do checklist
        """
        checklist = self.db.get(Checklist, checklist_id)
        if not checklist:
            raise BusinessRuleException(
                "Checklist não encontrado",
                code="CHECKLIST_NAO_ENCONTRADO"
            )
        
        if checklist.status not in ['pendente', 'em_andamento']:
            raise BusinessRuleException(
                "Não é possível modificar checklist finalizado",
                code="CHECKLIST_FINALIZADO"
            )
        
        # Atualizar status se necessário
        if checklist.status == 'pendente':
            checklist.status = 'em_andamento'
        
        bloqueios_criados = 0
        defeitos_criados = []
        
        # Processar cada resposta
        for resp_data in respostas:
            item_id = resp_data['item_id']
            
            # Verificar se item pertence ao modelo do checklist
            item = self.db.query(ChecklistItem).filter(
                ChecklistItem.id == item_id,
                ChecklistItem.modelo_id == checklist.modelo_id,
                ChecklistItem.ativo == True
            ).first()
            
            if not item:
                logger.warning(f"Item {item_id} não encontrado ou não pertence ao modelo {checklist.modelo_id}")
                continue
            
            # Verificar se já existe resposta
            resposta_existente = self.db.query(ChecklistResposta).filter(
                ChecklistResposta.checklist_id == checklist_id,
                ChecklistResposta.item_id == item_id
            ).first()
            
            if resposta_existente:
                # Atualizar resposta existente
                resposta_existente.valor = resp_data['valor']
                resposta_existente.valor_numerico = resp_data.get('valor_numerico')
                resposta_existente.opcao_selecionada = resp_data.get('opcao_selecionada')
                resposta_existente.observacao = resp_data.get('observacao')
                resposta_existente.foto_url = resp_data.get('foto_url')
                resposta_existente.geo = resp_data.get('geo')
                resposta_existente.tempo_resposta_segundos = resp_data.get('tempo_resposta_segundos')
                resposta = resposta_existente
            else:
                # Criar nova resposta
                resposta = ChecklistResposta(
                    checklist_id=checklist_id,
                    item_id=item_id,
                    valor=resp_data['valor'],
                    valor_numerico=resp_data.get('valor_numerico'),
                    opcao_selecionada=resp_data.get('opcao_selecionada'),
                    observacao=resp_data.get('observacao'),
                    foto_url=resp_data.get('foto_url'),
                    geo=resp_data.get('geo'),
                    tempo_resposta_segundos=resp_data.get('tempo_resposta_segundos')
                )
                self.db.add(resposta)
                self.db.flush()
            
            # Processar item reprovado
            if resposta.valor == "nao_ok":
                # Verificar se já existe defeito para esta resposta
                defeito_existente = self.db.query(Defeito).filter(
                    Defeito.checklist_id == checklist_id,
                    Defeito.item_id == item_id
                ).first()
                
                if not defeito_existente:
                    # Criar defeito
                    descricao_defeito = self._build_defeito_description(item, resposta)
                    
                    defeito = Defeito(
                        checklist_id=checklist_id,
                        item_id=item_id,
                        resposta_id=resposta.id,
                        veiculo_id=checklist.veiculo_id,
                        severidade=item.severidade,
                        categoria=item.categoria,
                        descricao=descricao_defeito,
                        prioridade=self._get_priority_from_severity(item.severidade),
                        status="identificado",
                        criado_por=user_id
                    )
                    self.db.add(defeito)
                    self.db.flush()
                    defeitos_criados.append(defeito.id)
                    
                    if item.bloqueia_viagem:
                        bloqueios_criados += 1
                    
                    # Gerar OS automática se necessário
                    if item.gera_os:
                        self._create_automatic_service_order(defeito, user_id)
        
        # Atualizar métricas do checklist
        self._update_checklist_metrics(checklist)
        
        self.db.commit()
        
        logger.info(f"Respostas atualizadas - Checklist: {checklist_id}, Defeitos: {len(defeitos_criados)}, Bloqueios: {bloqueios_criados}")
        
        return {
            "success": True,
            "respostas_processadas": len(respostas),
            "defeitos_criados": len(defeitos_criados),
            "bloqueios_criados": bloqueios_criados,
            "status": checklist.status
        }
    
    def finish_checklist(
        self,
        checklist_id: int,
        odometro_fim: Optional[int] = None,
        geo_fim: Optional[str] = None,
        assinatura_motorista: Optional[str] = None,
        observacoes_gerais: Optional[str] = None
    ) -> Checklist:
        """
        Finalizar checklist com validações
        """
        checklist = self.db.get(Checklist, checklist_id)
        if not checklist:
            raise BusinessRuleException(
                "Checklist não encontrado",
                code="CHECKLIST_NAO_ENCONTRADO"
            )
        
        if checklist.status in ['aprovado', 'reprovado', 'cancelado']:
            raise BusinessRuleException(
                "Checklist já foi finalizado",
                code="CHECKLIST_JA_FINALIZADO"
            )
        
        # Validar se há respostas suficientes
        total_itens = self.db.query(ChecklistItem).filter(
            ChecklistItem.modelo_id == checklist.modelo_id,
            ChecklistItem.ativo == True
        ).count()
        
        total_respostas = self.db.query(ChecklistResposta).filter(
            ChecklistResposta.checklist_id == checklist_id
        ).count()
        
        if total_respostas < total_itens:
            raise BusinessRuleException(
                f"Checklist incompleto: {total_respostas}/{total_itens} itens respondidos",
                code="CHECKLIST_INCOMPLETO"
            )
        
        # Validar odômetro final
        if odometro_fim is not None:
            if checklist.odometro_ini and odometro_fim < checklist.odometro_ini:
                raise BusinessRuleException(
                    "Odômetro final não pode ser menor que o inicial",
                    code="ODOMETRO_INVALIDO"
                )
        
        # Calcular duração
        duracao_minutos = None
        if checklist.dt_inicio:
            duracao_minutos = int((datetime.utcnow() - checklist.dt_inicio).total_seconds() / 60)
        
        # Determinar status final baseado em bloqueios
        tem_bloqueios = self.db.query(Defeito).filter(
            Defeito.checklist_id == checklist_id,
            Defeito.status == 'identificado'
        ).join(ChecklistItem).filter(
            ChecklistItem.bloqueia_viagem == True
        ).count() > 0
        
        status_final = "reprovado" if tem_bloqueios else "aprovado"
        
        # Atualizar checklist
        checklist.odometro_fim = odometro_fim
        checklist.geo_fim = geo_fim
        checklist.assinatura_motorista = assinatura_motorista
        checklist.observacoes_gerais = observacoes_gerais
        checklist.duracao_minutos = duracao_minutos
        checklist.status = status_final
        checklist.dt_fim = datetime.utcnow()
        checklist.finalizado_em = datetime.utcnow()
        
        # Atualizar métricas finais
        self._update_checklist_metrics(checklist)
        
        # Atualizar KM do veículo se fornecido
        if odometro_fim and checklist.veiculo:
            if odometro_fim > checklist.veiculo.km_atual:
                checklist.veiculo.km_atual = odometro_fim
        
        # Atualizar status da viagem se aplicável
        if checklist.viagem_id and checklist.tipo == "pre":
            viagem = self.db.get(Viagem, checklist.viagem_id)
            if viagem:
                if status_final == "aprovado":
                    viagem.status = "liberada"
                elif status_final == "reprovado":
                    viagem.status = "bloqueada"
                    viagem.motivo_cancelamento = f"Checklist reprovado: {checklist.codigo}"
        
        self.db.commit()
        
        logger.info(f"Checklist finalizado: {checklist.codigo} - Status: {status_final} - Duração: {duracao_minutos}min")
        
        return checklist
    
    def get_checklist_with_details(self, checklist_id: int) -> Optional[Dict[str, Any]]:
        """
        Buscar checklist com todos os detalhes
        """
        checklist = self.db.query(Checklist).filter(Checklist.id == checklist_id).first()
        if not checklist:
            return None
        
        # Buscar itens do modelo
        itens = self.db.query(ChecklistItem).filter(
            ChecklistItem.modelo_id == checklist.modelo_id,
            ChecklistItem.ativo == True
        ).order_by(ChecklistItem.ordem).all()
        
        # Buscar respostas
        respostas = self.db.query(ChecklistResposta).filter(
            ChecklistResposta.checklist_id == checklist_id
        ).all()
        
        # Buscar defeitos
        defeitos = self.db.query(Defeito).filter(
            Defeito.checklist_id == checklist_id
        ).all()
        
        return {
            "checklist": checklist,
            "itens": itens,
            "respostas": respostas,
            "defeitos": defeitos
        }
    
    def get_pending_checklists(
        self,
        veiculo_id: Optional[int] = None,
        motorista_id: Optional[int] = None,
        limit: int = 50
    ) -> List[Checklist]:
        """
        Buscar checklists pendentes
        """
        query = self.db.query(Checklist).filter(
            Checklist.status.in_(['pendente', 'em_andamento'])
        )
        
        if veiculo_id:
            query = query.filter(Checklist.veiculo_id == veiculo_id)
        
        if motorista_id:
            query = query.filter(Checklist.motorista_id == motorista_id)
        
        return query.order_by(Checklist.dt_inicio).limit(limit).all()
    
    def cancel_checklist(
        self,
        checklist_id: int,
        motivo: str,
        user_id: Optional[int] = None
    ) -> Checklist:
        """
        Cancelar checklist
        """
        checklist = self.db.get(Checklist, checklist_id)
        if not checklist:
            raise BusinessRuleException(
                "Checklist não encontrado",
                code="CHECKLIST_NAO_ENCONTRADO"
            )
        
        if checklist.status in ['aprovado', 'reprovado']:
            raise BusinessRuleException(
                "Não é possível cancelar checklist já finalizado",
                code="CHECKLIST_FINALIZADO"
            )
        
        checklist.status = 'cancelado'
        checklist.observacoes_gerais = f"CANCELADO: {motivo}"
        checklist.dt_fim = datetime.utcnow()
        checklist.finalizado_em = datetime.utcnow()
        
        # Cancelar defeitos relacionados
        self.db.query(Defeito).filter(
            Defeito.checklist_id == checklist_id,
            Defeito.status == 'identificado'
        ).update({"status": "nao_procede"})
        
        self.db.commit()
        
        logger.info(f"Checklist cancelado: {checklist.codigo} - Motivo: {motivo}")
        
        return checklist
    
    # ==============================
    # MÉTODOS PRIVADOS/AUXILIARES
    # ==============================
    
    def _update_checklist_metrics(self, checklist: Checklist):
        """Atualizar métricas calculadas do checklist"""
        stats = self.db.execute(text("""
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE valor = 'ok') as ok_count,
                COUNT(*) FILTER (WHERE valor = 'nao_ok') as nok_count,
                COUNT(*) FILTER (WHERE valor = 'na') as na_count
            FROM checklist_respostas cr
            WHERE cr.checklist_id = :checklist_id
        """), {"checklist_id": checklist.id}).mappings().first()
        
        if stats:
            checklist.total_itens = stats['total']
            checklist.itens_ok = stats['ok_count']
            checklist.itens_nok = stats['nok_count'] 
            checklist.itens_na = stats['na_count']
            
            if stats['total'] > 0:
                checklist.score_aprovacao = round(stats['ok_count'] * 100.0 / stats['total'], 2)
            else:
                checklist.score_aprovacao = 0.0
        
        # Verificar se tem bloqueios
        tem_bloqueios = self.db.execute(text("""
            SELECT COUNT(*) > 0 as tem_bloqueios
            FROM checklist_respostas cr
            JOIN checklist_itens ci ON ci.id = cr.item_id
            WHERE cr.checklist_id = :checklist_id 
              AND ci.bloqueia_viagem = true 
              AND cr.valor = 'nao_ok'
        """), {"checklist_id": checklist.id}).scalar()
        
        checklist.tem_bloqueios = bool(tem_bloqueios)
    
    def _build_defeito_description(self, item: ChecklistItem, resposta: ChecklistResposta) -> str:
        """Construir descrição do defeito baseada na resposta"""
        descricao = f"{item.descricao}"
        
        if resposta.opcao_selecionada:
            descricao += f" - {resposta.opcao_selecionada}"
        
        if resposta.observacao:
            descricao += f" - {resposta.observacao}"
        
        return descricao[:500]  # Limitar tamanho
    
    def _get_priority_from_severity(self, severidade: str) -> str:
        """Converter severidade em prioridade"""
        mapping = {
            'critica': 'urgente',
            'alta': 'alta',
            'media': 'normal',
            'baixa': 'baixa'
        }
        return mapping.get(severidade, 'normal')
    
    def _create_automatic_service_order(self, defeito: Defeito, user_id: Optional[int] = None):
        """Criar ordem de serviço automática para defeito"""
        try:
            # Verificar se já existe OS para este defeito
            existing_os = self.db.query(OrdemServico).filter(
                OrdemServico.defeito_id == defeito.id
            ).first()
            
            if existing_os:
                logger.info(f"OS já existe para defeito {defeito.id}")
                return
            
            # Determinar tipo de serviço baseado na severidade
            tipo_servico = "emergencial" if defeito.severidade == "critica" else "corretiva"
            
            # Criar OS
            os = OrdemServico(
                veiculo_id=defeito.veiculo_id,
                defeito_id=defeito.id,
                tipo_servico=tipo_servico,
                descricao=f"Serviço automático - {defeito.descricao}",
                status="aberta",
                criado_por=user_id
            )
            
            self.db.add(os)
            self.db.flush()
            
            # Atualizar status do defeito
            defeito.status = "aberto"
            
            logger.info(f"OS automática criada: {os.numero_os} para defeito {defeito.id}")
            
        except Exception as e:
            logger.error(f"Erro ao criar OS automática: {e}")
            # Não propagar o erro para não impactar o fluxo principal

class ChecklistAnalyticsService:
    """Serviço para análises e relatórios de checklist"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_summary_metrics(
        self,
        days: int = 30,
        veiculo_id: Optional[int] = None,
        motorista_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Buscar métricas resumidas de checklist"""
        
        params = {"days": days}
        filters = ["c.dt_inicio >= NOW() - make_interval(days => :days)"]
        
        if veiculo_id:
            filters.append("c.veiculo_id = :veiculo_id")
            params["veiculo_id"] = veiculo_id
            
        if motorista_id:
            filters.append("c.motorista_id = :motorista_id")
            params["motorista_id"] = motorista_id
        
        where_clause = " AND ".join(filters)
        
        # Métricas principais
        resumo = self.db.execute(text(f"""
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE status = 'aprovado') as aprovados,
                COUNT(*) FILTER (WHERE status = 'reprovado') as reprovados,
                COUNT(*) FILTER (WHERE status IN ('pendente', 'em_andamento')) as pendentes,
                COUNT(*) FILTER (WHERE tem_bloqueios = true) as com_bloqueios,
                ROUND(AVG(score_aprovacao), 2) as score_medio,
                ROUND(AVG(duracao_minutos), 1) as duracao_media,
                COUNT(DISTINCT veiculo_id) as veiculos_distintos,
                COUNT(DISTINCT motorista_id) as motoristas_distintos
            FROM checklists c
            WHERE {where_clause}
        """), params).mappings().first()
        
        # Evolução temporal (últimos 7 dias dentro do período)
        evolucao = self.db.execute(text(f"""
            SELECT 
                DATE_TRUNC('day', dt_inicio) as data,
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE status = 'aprovado') as aprovados,
                COUNT(*) FILTER (WHERE status = 'reprovado') as reprovados
            FROM checklists c
            WHERE {where_clause}
              AND c.dt_inicio >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY DATE_TRUNC('day', dt_inicio)
            ORDER BY data
        """), params).mappings().all()
        
        return {
            "resumo": dict(resumo) if resumo else {},
            "evolucao_semanal": [dict(row) for row in evolucao]
        }
    
    def get_top_rejected_items(
        self,
        days: int = 30,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Buscar itens com maior taxa de reprovação"""
        
        result = self.db.execute(text("""
            SELECT 
                i.categoria,
                i.descricao,
                COUNT(*) as total_respostas,
                COUNT(*) FILTER (WHERE r.valor = 'nao_ok') as reprovacoes,
                ROUND(COUNT(*) FILTER (WHERE r.valor = 'nao_ok') * 100.0 / COUNT(*), 2) as taxa_reprovacao
            FROM checklist_respostas r
            JOIN checklist_itens i ON i.id = r.item_id  
            JOIN checklists c ON c.id = r.checklist_id
            WHERE c.dt_inicio >= NOW() - make_interval(days => :days)
            GROUP BY i.categoria, i.descricao, i.id
            HAVING COUNT(*) >= 5
            ORDER BY taxa_reprovacao DESC, reprovacoes DESC
            LIMIT :limit
        """), {"days": days, "limit": limit}).mappings().all()
        
        return [dict(row) for row in result]
    
    def get_driver_performance(
        self,
        days: int = 90,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Performance dos motoristas"""
        
        result = self.db.execute(text("""
            SELECT 
                m.id as motorista_id,
                m.nome,
                COUNT(c.id) as total_checklists,
                COUNT(*) FILTER (WHERE c.status = 'aprovado') as aprovados,
                COUNT(*) FILTER (WHERE c.status = 'reprovado') as reprovados,
                ROUND(COUNT(*) FILTER (WHERE c.status = 'aprovado') * 100.0 / COUNT(c.id), 2) as taxa_aprovacao,
                ROUND(AVG(c.duracao_minutos), 1) as tempo_medio_minutos,
                COUNT(*) FILTER (WHERE c.tem_bloqueios) as checklists_com_bloqueio
            FROM motoristas m
            JOIN checklists c ON c.motorista_id = m.id
            WHERE m.ativo = TRUE 
              AND c.dt_inicio >= NOW() - make_interval(days => :days)
            GROUP BY m.id, m.nome
            HAVING COUNT(c.id) >= 3
            ORDER BY taxa_aprovacao DESC, total_checklists DESC
            LIMIT :limit
        """), {"days": days, "limit": limit}).mappings().all()
        
        return [dict(row) for row in result]