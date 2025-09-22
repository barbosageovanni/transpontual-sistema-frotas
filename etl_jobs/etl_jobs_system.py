"""
Sistema de ETL e Jobs - Transpontual
Processamento de dados, agregações e tarefas em background
"""
import os
import sys
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import requests
import json
import time

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('etl_jobs.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class JobConfig:
    """Configuração para jobs"""
    database_url: str
    api_base_url: str
    smtp_server: str = ""
    smtp_port: int = 587
    email_user: str = ""
    email_password: str = ""
    notification_emails: List[str] = None
    whatsapp_api_url: str = ""
    whatsapp_token: str = ""
    
    def __post_init__(self):
        if self.notification_emails is None:
            self.notification_emails = []

class DatabaseManager:
    """Gerenciador de conexão com banco de dados"""
    
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url, pool_pre_ping=True)
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def get_session(self):
        """Obter sessão do banco"""
        return self.SessionLocal()
    
    def execute_query(self, query: str, params: Dict = None) -> List[Dict]:
        """Executar query e retornar resultados"""
        with self.get_session() as session:
            result = session.execute(text(query), params or {})
            return [dict(row) for row in result.mappings().all()]
    
    def execute_update(self, query: str, params: Dict = None) -> int:
        """Executar update/insert e retornar linhas afetadas"""
        with self.get_session() as session:
            result = session.execute(text(query), params or {})
            session.commit()
            return result.rowcount

class NotificationService:
    """Serviço de notificações"""
    
    def __init__(self, config: JobConfig):
        self.config = config
    
    async def send_email(self, subject: str, body: str, recipients: List[str] = None):
        """Enviar email"""
        if not self.config.email_user or not recipients:
            return
        
        try:
            recipients = recipients or self.config.notification_emails
            
            msg = MimeMultipart()
            msg['From'] = self.config.email_user
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = subject
            
            msg.attach(MimeText(body, 'html'))
            
            server = smtplib.SMTP(self.config.smtp_server, self.config.smtp_port)
            server.starttls()
            server.login(self.config.email_user, self.config.email_password)
            
            text = msg.as_string()
            server.sendmail(self.config.email_user, recipients, text)
            server.quit()
            
            logger.info(f"Email enviado para {len(recipients)} destinatários")
            
        except Exception as e:
            logger.error(f"Erro ao enviar email: {e}")
    
    async def send_whatsapp(self, message: str, phone_numbers: List[str]):
        """Enviar mensagem WhatsApp (via API externa)"""
        if not self.config.whatsapp_api_url or not self.config.whatsapp_token:
            return
        
        try:
            for phone in phone_numbers:
                payload = {
                    'token': self.config.whatsapp_token,
                    'to': phone,
                    'body': message
                }
                
                response = requests.post(
                    self.config.whatsapp_api_url,
                    json=payload,
                    timeout=10
                )
                
                if response.status_code == 200:
                    logger.info(f"WhatsApp enviado para {phone}")
                else:
                    logger.error(f"Erro WhatsApp para {phone}: {response.text}")
                    
                time.sleep(1)  # Rate limiting
                
        except Exception as e:
            logger.error(f"Erro ao enviar WhatsApp: {e}")

class ChecklistAggregatorJob:
    """Job para agregações diárias de checklist"""
    
    def __init__(self, db_manager: DatabaseManager, notification_service: NotificationService):
        self.db = db_manager
        self.notification = notification_service
    
    async def run_daily_aggregation(self, target_date: datetime = None):
        """Executar agregações diárias"""
        if target_date is None:
            target_date = datetime.now() - timedelta(days=1)  # Ontem
        
        logger.info(f"Iniciando agregações para {target_date.date()}")
        
        try:
            # 1. Agregar estatísticas diárias de checklist
            await self._aggregate_daily_checklist_stats(target_date)
            
            # 2. Atualizar performance de motoristas
            await self._update_driver_performance_metrics()
            
            # 3. Agregar dados de defeitos e OS
            await self._aggregate_defects_and_service_orders()
            
            # 4. Calcular KPIs de veículos
            await self._calculate_vehicle_kpis()
            
            # 5. Refresh das views materializadas
            await self._refresh_materialized_views()
            
            # 6. Gerar relatório de resumo
            summary = await self._generate_daily_summary(target_date)
            
            # Enviar notificação de sucesso
            await self._send_success_notification(target_date, summary)
            
            logger.info(f"Agregações concluídas para {target_date.date()}")
            
        except Exception as e:
            logger.error(f"Erro nas agregações diárias: {e}")
            await self._send_error_notification(str(e))
            raise
    
    async def _aggregate_daily_checklist_stats(self, target_date: datetime):
        """Agregar estatísticas diárias de checklist"""
        
        # Criar tabela de agregação se não existir
        create_table_query = """
        CREATE TABLE IF NOT EXISTS checklist_daily_stats (
            id SERIAL PRIMARY KEY,
            data DATE NOT NULL UNIQUE,
            total_checklists INT DEFAULT 0,
            aprovados INT DEFAULT 0,
            reprovados INT DEFAULT 0,
            pendentes INT DEFAULT 0,
            taxa_aprovacao DECIMAL(5,2) DEFAULT 0,
            tempo_medio_minutos DECIMAL(8,2) DEFAULT 0,
            total_defeitos INT DEFAULT 0,
            defeitos_criticos INT DEFAULT 0,
            total_os_abertas INT DEFAULT 0,
            veiculos_com_problema INT DEFAULT 0,
            motoristas_ativos INT DEFAULT 0,
            criado_em TIMESTAMP DEFAULT NOW(),
            atualizado_em TIMESTAMP DEFAULT NOW()
        );
        """
        
        self.db.execute_update(create_table_query)
        
        # Calcular estatísticas do dia
        date_str = target_date.strftime('%Y-%m-%d')
        
        stats_query = """
        WITH checklist_stats AS (
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE status = 'aprovado') as aprovados,
                COUNT(*) FILTER (WHERE status = 'reprovado') as reprovados,
                COUNT(*) FILTER (WHERE status IN ('pendente', 'em_andamento')) as pendentes,
                ROUND(AVG(duracao_minutos), 2) as tempo_medio,
                COUNT(DISTINCT veiculo_id) as veiculos_distintos,
                COUNT(DISTINCT motorista_id) as motoristas_distintos
            FROM checklists 
            WHERE DATE(dt_inicio) = :target_date
        ),
        defeito_stats AS (
            SELECT 
                COUNT(*) as total_defeitos,
                COUNT(*) FILTER (WHERE severidade = 'critica') as defeitos_criticos
            FROM defeitos d
            JOIN checklists c ON c.id = d.checklist_id
            WHERE DATE(c.dt_inicio) = :target_date
        ),
        os_stats AS (
            SELECT COUNT(*) as total_os_abertas
            FROM ordens_servico os
            WHERE DATE(os.abertura_dt) = :target_date
        )
        INSERT INTO checklist_daily_stats (
            data, total_checklists, aprovados, reprovados, pendentes,
            taxa_aprovacao, tempo_medio_minutos, total_defeitos, defeitos_criticos,
            total_os_abertas, veiculos_com_problema, motoristas_ativos
        )
        SELECT 
            :target_date::DATE,
            cs.total,
            cs.aprovados,
            cs.reprovados,
            cs.pendentes,
            CASE WHEN cs.total > 0 THEN ROUND(cs.aprovados * 100.0 / cs.total, 2) ELSE 0 END,
            COALESCE(cs.tempo_medio, 0),
            COALESCE(ds.total_defeitos, 0),
            COALESCE(ds.defeitos_criticos, 0),
            COALESCE(os.total_os_abertas, 0),
            cs.veiculos_distintos,
            cs.motoristas_distintos
        FROM checklist_stats cs
        CROSS JOIN defeito_stats ds
        CROSS JOIN os_stats os
        ON CONFLICT (data) DO UPDATE SET
            total_checklists = EXCLUDED.total_checklists,
            aprovados = EXCLUDED.aprovados,
            reprovados = EXCLUDED.reprovados,
            pendentes = EXCLUDED.pendentes,
            taxa_aprovacao = EXCLUDED.taxa_aprovacao,
            tempo_medio_minutos = EXCLUDED.tempo_medio_minutos,
            total_defeitos = EXCLUDED.total_defeitos,
            defeitos_criticos = EXCLUDED.defeitos_criticos,
            total_os_abertas = EXCLUDED.total_os_abertas,
            veiculos_com_problema = EXCLUDED.veiculos_com_problema,
            motoristas_ativos = EXCLUDED.motoristas_ativos,
            atualizado_em = NOW();
        """
        
        rows_affected = self.db.execute_update(stats_query, {"target_date": date_str})
        logger.info(f"Estatísticas diárias atualizadas: {rows_affected} registros")
    
    async def _update_driver_performance_metrics(self):
        """Atualizar métricas de performance dos motoristas"""
        
        # Criar tabela de performance se não existir
        create_table_query = """
        CREATE TABLE IF NOT EXISTS motorista_performance (
            id SERIAL PRIMARY KEY,
            motorista_id INT NOT NULL REFERENCES motoristas(id),
            periodo_inicio DATE NOT NULL,
            periodo_fim DATE NOT NULL,
            total_checklists INT DEFAULT 0,
            checklists_aprovados INT DEFAULT 0,
            taxa_aprovacao DECIMAL(5,2) DEFAULT 0,
            tempo_medio_minutos DECIMAL(8,2) DEFAULT 0,
            total_defeitos_identificados INT DEFAULT 0,
            pontuacao_qualidade DECIMAL(5,2) DEFAULT 0,
            ranking_posicao INT,
            criado_em TIMESTAMP DEFAULT NOW(),
            atualizado_em TIMESTAMP DEFAULT NOW(),
            UNIQUE(motorista_id, periodo_inicio, periodo_fim)
        );
        """
        
        self.db.execute_update(create_table_query)
        
        # Calcular performance dos últimos 30 dias
        periodo_fim = datetime.now().date()
        periodo_inicio = periodo_fim - timedelta(days=30)
        
        performance_query = """
        WITH performance_data AS (
            SELECT 
                m.id as motorista_id,
                COUNT(c.id) as total_checklists,
                COUNT(*) FILTER (WHERE c.status = 'aprovado') as aprovados,
                ROUND(AVG(c.duracao_minutos), 2) as tempo_medio,
                COUNT(d.id) as total_defeitos,
                CASE 
                    WHEN COUNT(c.id) > 0 THEN
                        ROUND(COUNT(*) FILTER (WHERE c.status = 'aprovado') * 100.0 / COUNT(c.id), 2)
                    ELSE 0 
                END as taxa_aprovacao
            FROM motoristas m
            LEFT JOIN checklists c ON c.motorista_id = m.id 
                AND c.dt_inicio >= :periodo_inicio 
                AND c.dt_inicio < :periodo_fim + INTERVAL '1 day'
            LEFT JOIN defeitos d ON d.checklist_id = c.id
            WHERE m.ativo = true
            GROUP BY m.id
            HAVING COUNT(c.id) > 0
        ),
        performance_with_score AS (
            SELECT *,
                -- Pontuação baseada em taxa de aprovação (60%) + tempo médio (40%)
                ROUND(
                    (taxa_aprovacao * 0.6) + 
                    (CASE 
                        WHEN tempo_medio <= 15 THEN 40
                        WHEN tempo_medio <= 25 THEN 30
                        WHEN tempo_medio <= 35 THEN 20
                        ELSE 10
                    END), 2
                ) as pontuacao_qualidade
            FROM performance_data
        ),
        ranked_performance AS (
            SELECT *,
                ROW_NUMBER() OVER (ORDER BY pontuacao_qualidade DESC, taxa_aprovacao DESC) as ranking_posicao
            FROM performance_with_score
        )
        INSERT INTO motorista_performance (
            motorista_id, periodo_inicio, periodo_fim, total_checklists,
            checklists_aprovados, taxa_aprovacao, tempo_medio_minutos,
            total_defeitos_identificados, pontuacao_qualidade, ranking_posicao
        )
        SELECT 
            motorista_id, :periodo_inicio, :periodo_fim, total_checklists,
            aprovados, taxa_aprovacao, tempo_medio, total_defeitos,
            pontuacao_qualidade, ranking_posicao
        FROM ranked_performance
        ON CONFLICT (motorista_id, periodo_inicio, periodo_fim) DO UPDATE SET
            total_checklists = EXCLUDED.total_checklists,
            checklists_aprovados = EXCLUDED.checklists_aprovados,
            taxa_aprovacao = EXCLUDED.taxa_aprovacao,
            tempo_medio_minutos = EXCLUDED.tempo_medio_minutos,
            total_defeitos_identificados = EXCLUDED.total_defeitos_identificados,
            pontuacao_qualidade = EXCLUDED.pontuacao_qualidade,
            ranking_posicao = EXCLUDED.ranking_posicao,
            atualizado_em = NOW();
        """
        
        params = {
            "periodo_inicio": periodo_inicio.strftime('%Y-%m-%d'),
            "periodo_fim": periodo_fim.strftime('%Y-%m-%d')
        }
        
        rows_affected = self.db.execute_update(performance_query, params)
        logger.info(f"Performance de motoristas atualizada: {rows_affected} registros")
    
    async def _aggregate_defects_and_service_orders(self):
        """Agregar dados de defeitos e ordens de serviço"""
        
        # Criar tabela de agregação de defeitos
        create_defects_table = """
        CREATE TABLE IF NOT EXISTS defeitos_summary (
            id SERIAL PRIMARY KEY,
            data DATE NOT NULL UNIQUE,
            total_defeitos INT DEFAULT 0,
            defeitos_por_severidade JSONB DEFAULT '{}',
            defeitos_por_categoria JSONB DEFAULT '{}',
            tempo_medio_resolucao_horas DECIMAL(8,2),
            taxa_resolucao DECIMAL(5,2),
            custo_total_estimado DECIMAL(12,2),
            criado_em TIMESTAMP DEFAULT NOW(),
            atualizado_em TIMESTAMP DEFAULT NOW()
        );
        """
        
        self.db.execute_update(create_defects_table)
        
        # Agregar dados de defeitos dos últimos 7 dias
        for i in range(7):
            target_date = (datetime.now() - timedelta(days=i+1)).date()
            
            defects_query = """
            WITH defect_stats AS (
                SELECT 
                    COUNT(*) as total,
                    AVG(EXTRACT(EPOCH FROM (COALESCE(resolvido_em, NOW()) - criado_em)) / 3600) as tempo_medio_horas,
                    COUNT(*) FILTER (WHERE status = 'resolvido') * 100.0 / COUNT(*) as taxa_resolucao,
                    SUM(COALESCE(custo_estimado, 0)) as custo_total
                FROM defeitos d
                JOIN checklists c ON c.id = d.checklist_id
                WHERE DATE(c.dt_inicio) = :target_date
            ),
            severity_stats AS (
                SELECT jsonb_object_agg(severidade, cnt) as por_severidade
                FROM (
                    SELECT severidade, COUNT(*) as cnt
                    FROM defeitos d
                    JOIN checklists c ON c.id = d.checklist_id
                    WHERE DATE(c.dt_inicio) = :target_date
                    GROUP BY severidade
                ) s
            ),
            category_stats AS (
                SELECT jsonb_object_agg(categoria, cnt) as por_categoria
                FROM (
                    SELECT categoria, COUNT(*) as cnt
                    FROM defeitos d
                    JOIN checklists c ON c.id = d.checklist_id
                    WHERE DATE(c.dt_inicio) = :target_date
                    GROUP BY categoria
                ) cat
            )
            INSERT INTO defeitos_summary (
                data, total_defeitos, defeitos_por_severidade, defeitos_por_categoria,
                tempo_medio_resolucao_horas, taxa_resolucao, custo_total_estimado
            )
            SELECT 
                :target_date::DATE,
                COALESCE(ds.total, 0),
                COALESCE(ss.por_severidade, '{}'::jsonb),
                COALESCE(cs.por_categoria, '{}'::jsonb),
                ROUND(COALESCE(ds.tempo_medio_horas, 0), 2),
                ROUND(COALESCE(ds.taxa_resolucao, 0), 2),
                COALESCE(ds.custo_total, 0)
            FROM defect_stats ds
            CROSS JOIN severity_stats ss
            CROSS JOIN category_stats cs
            ON CONFLICT (data) DO UPDATE SET
                total_defeitos = EXCLUDED.total_defeitos,
                defeitos_por_severidade = EXCLUDED.defeitos_por_severidade,
                defeitos_por_categoria = EXCLUDED.defeitos_por_categoria,
                tempo_medio_resolucao_horas = EXCLUDED.tempo_medio_resolucao_horas,
                taxa_resolucao = EXCLUDED.taxa_resolucao,
                custo_total_estimado = EXCLUDED.custo_total_estimado,
                atualizado_em = NOW();
            """
            
            self.db.execute_update(defects_query, {"target_date": target_date.strftime('%Y-%m-%d')})
        
        logger.info("Agregações de defeitos concluídas")
    
    async def _calculate_vehicle_kpis(self):
        """Calcular KPIs por veículo"""
        
        # Criar tabela de KPIs de veículos
        create_vehicle_kpis_table = """
        CREATE TABLE IF NOT EXISTS veiculo_kpis (
            id SERIAL PRIMARY KEY,
            veiculo_id INT NOT NULL REFERENCES veiculos(id),
            mes_referencia DATE NOT NULL,
            total_checklists INT DEFAULT 0,
            taxa_aprovacao DECIMAL(5,2) DEFAULT 0,
            total_defeitos INT DEFAULT 0,
            custo_manutencao DECIMAL(12,2) DEFAULT 0,
            km_rodados INT DEFAULT 0,
            disponibilidade_percentual DECIMAL(5,2) DEFAULT 100,
            tempo_imobilizado_horas DECIMAL(8,2) DEFAULT 0,
            score_geral DECIMAL(5,2) DEFAULT 0,
            criado_em TIMESTAMP DEFAULT NOW(),
            atualizado_em TIMESTAMP DEFAULT NOW(),
            UNIQUE(veiculo_id, mes_referencia)
        );
        """
        
        self.db.execute_update(create_vehicle_kpis_table)
        
        # Calcular KPIs do mês atual
        mes_atual = datetime.now().replace(day=1).date()
        
        vehicle_kpis_query = """
        WITH vehicle_checklist_stats AS (
            SELECT 
                v.id as veiculo_id,
                COUNT(c.id) as total_checklists,
                COUNT(*) FILTER (WHERE c.status = 'aprovado') * 100.0 / COUNT(c.id) as taxa_aprovacao,
                COUNT(d.id) as total_defeitos,
                MAX(c.odometro_fim) - MIN(c.odometro_ini) as km_rodados
            FROM veiculos v
            LEFT JOIN checklists c ON c.veiculo_id = v.id 
                AND c.dt_inicio >= :mes_referencia
                AND c.dt_inicio < :mes_referencia + INTERVAL '1 month'
            LEFT JOIN defeitos d ON d.checklist_id = c.id
            WHERE v.ativo = true
            GROUP BY v.id
        ),
        vehicle_maintenance_stats AS (
            SELECT 
                os.veiculo_id,
                SUM(os.custo_peca + os.custo_mo + os.custo_terceiros) as custo_manutencao,
                SUM(EXTRACT(EPOCH FROM (COALESCE(os.conclusao_dt, NOW()) - os.abertura_dt)) / 3600) as tempo_imobilizado
            FROM ordens_servico os
            WHERE os.abertura_dt >= :mes_referencia
              AND os.abertura_dt < :mes_referencia + INTERVAL '1 month'
            GROUP BY os.veiculo_id
        ),
        vehicle_kpis_calculated AS (
            SELECT 
                vcs.veiculo_id,
                COALESCE(vcs.total_checklists, 0) as total_checklists,
                ROUND(COALESCE(vcs.taxa_aprovacao, 100), 2) as taxa_aprovacao,
                COALESCE(vcs.total_defeitos, 0) as total_defeitos,
                COALESCE(vms.custo_manutencao, 0) as custo_manutencao,
                COALESCE(vcs.km_rodados, 0) as km_rodados,
                ROUND(COALESCE(vms.tempo_imobilizado, 0), 2) as tempo_imobilizado,
                -- Calcular disponibilidade (assumindo 24h/dia * 30 dias = 720h)
                ROUND(100 - (COALESCE(vms.tempo_imobilizado, 0) / 720 * 100), 2) as disponibilidade,
                -- Score geral baseado em múltiplos fatores
                ROUND((
                    COALESCE(vcs.taxa_aprovacao, 100) * 0.4 +
                    (100 - LEAST(COALESCE(vcs.total_defeitos, 0) * 10, 100)) * 0.3 +
                    (100 - (COALESCE(vms.tempo_imobilizado, 0) / 720 * 100)) * 0.3
                ), 2) as score_geral
            FROM vehicle_checklist_stats vcs
            FULL OUTER JOIN vehicle_maintenance_stats vms ON vms.veiculo_id = vcs.veiculo_id
            WHERE vcs.veiculo_id IS NOT NULL OR vms.veiculo_id IS NOT NULL
        )
        INSERT INTO veiculo_kpis (
            veiculo_id, mes_referencia, total_checklists, taxa_aprovacao,
            total_defeitos, custo_manutencao, km_rodados, disponibilidade_percentual,
            tempo_imobilizado_horas, score_geral
        )
        SELECT 
            veiculo_id, :mes_referencia, total_checklists, taxa_aprovacao,
            total_defeitos, custo_manutencao, km_rodados, disponibilidade,
            tempo_imobilizado, score_geral
        FROM vehicle_kpis_calculated
        ON CONFLICT (veiculo_id, mes_referencia) DO UPDATE SET
            total_checklists = EXCLUDED.total_checklists,
            taxa_aprovacao = EXCLUDED.taxa_aprovacao,
            total_defeitos = EXCLUDED.total_defeitos,
            custo_manutencao = EXCLUDED.custo_manutencao,
            km_rodados = EXCLUDED.km_rodados,
            disponibilidade_percentual = EXCLUDED.disponibilidade_percentual,
            tempo_imobilizado_horas = EXCLUDED.tempo_imobilizado_horas,
            score_geral = EXCLUDED.score_geral,
            atualizado_em = NOW();
        """
        
        rows_affected = self.db.execute_update(vehicle_kpis_query, {"mes_referencia": mes_atual.strftime('%Y-%m-%d')})
        logger.info(f"KPIs de veículos calculados: {rows_affected} registros")
    
    async def _refresh_materialized_views(self):
        """Refresh das views materializadas"""
        
        views_to_refresh = [
            'vw_checklist_summary',
            'vw_top_itens_reprovados',
            'vw_motorista_performance'
        ]
        
        for view_name in views_to_refresh:
            try:
                self.db.execute_update(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view_name}")
                logger.info(f"View materializada atualizada: {view_name}")
            except Exception as e:
                logger.warning(f"Erro ao atualizar view {view_name}: {e}")
    
    async def _generate_daily_summary(self, target_date: datetime) -> Dict[str, Any]:
        """Gerar resumo diário"""
        
        date_str = target_date.strftime('%Y-%m-%d')
        
        summary_data = self.db.execute_query("""
            SELECT 
                cds.*,
                ds.total_defeitos as defeitos_identificados,
                ds.taxa_resolucao as taxa_resolucao_defeitos
            FROM checklist_daily_stats cds
            LEFT JOIN defeitos_summary ds ON ds.data = cds.data
            WHERE cds.data = :target_date
        """, {"target_date": date_str})
        
        if not summary_data:
            return {"error": "Não há dados para o dia especificado"}
        
        data = summary_data[0]
        
        # Buscar alertas e problemas críticos
        critical_issues = self.db.execute_query("""
            SELECT 
                v.placa,
                d.descricao,
                d.severidade,
                d.status
            FROM defeitos d
            JOIN checklists c ON c.id = d.checklist_id
            JOIN veiculos v ON v.id = d.veiculo_id
            WHERE DATE(c.dt_inicio) = :target_date
              AND d.severidade = 'critica'
              AND d.status IN ('identificado', 'aberto')
            ORDER BY d.criado_em DESC
            LIMIT 10
        """, {"target_date": date_str})
        
        return {
            "data": target_date.strftime('%d/%m/%Y'),
            "estatisticas": data,
            "problemas_criticos": critical_issues,
            "processado_em": datetime.now().isoformat()
        }
    
    async def _send_success_notification(self, target_date: datetime, summary: Dict[str, Any]):
        """Enviar notificação de sucesso"""
        
        if "error" in summary:
            return
        
        stats = summary["estatisticas"]
        critical_count = len(summary["problemas_criticos"])
        
        subject = f"Relatório Diário de Checklist - {target_date.strftime('%d/%m/%Y')}"
        
        body = f"""
        <html>
        <body>
            <h2>Resumo Diário de Checklists - {target_date.strftime('%d/%m/%Y')}</h2>
            
            <h3>📊 Estatísticas Gerais</h3>
            <ul>
                <li><strong>Total de Checklists:</strong> {stats.get('total_checklists', 0)}</li>
                <li><strong>Aprovados:</strong> {stats.get('aprovados', 0)} ({stats.get('taxa_aprovacao', 0)}%)</li>
                <li><strong>Reprovados:</strong> {stats.get('reprovados', 0)}</li>
                <li><strong>Tempo Médio:</strong> {stats.get('tempo_medio_minutos', 0)} minutos</li>
                <li><strong>Defeitos Identificados:</strong> {stats.get('total_defeitos', 0)}</li>
                <li><strong>OS Abertas:</strong> {stats.get('total_os_abertas', 0)}</li>
            </ul>
            
            <h3>⚠️ Problemas Críticos</h3>
            {f'<p style="color: red;"><strong>{critical_count} problemas críticos identificados!</strong></p>' if critical_count > 0 else '<p style="color: green;">Nenhum problema crítico identificado.</p>'}
            
            <h3>📈 Performance</h3>
            <ul>
                <li><strong>Veículos com Atividade:</strong> {stats.get('veiculos_com_problema', 0)}</li>
                <li><strong>Motoristas Ativos:</strong> {stats.get('motoristas_ativos', 0)}</li>
            </ul>
            
            <hr>
            <small>Processado automaticamente pelo sistema Transpontual em {datetime.now().strftime('%d/%m/%Y %H:%M')}</small>
        </body>
        </html>
        """
        
        await self.notification.send_email(subject, body)
        
        # Enviar WhatsApp se houver problemas críticos
        if critical_count > 0:
            whatsapp_msg = f"🚨 ALERTA TRANSPONTUAL\n{critical_count} problemas críticos identificados em {target_date.strftime('%d/%m/%Y')}!\nVerifique o dashboard para mais detalhes."
            await self.notification.send_whatsapp(whatsapp_msg, [])  # Lista de telefones configurada
    
    async def _send_error_notification(self, error_message: str):
        """Enviar notificação de erro"""
        
        subject = "ERRO - Processamento de Agregações Transpontual"
        
        body = f"""
        <html>
        <body>
            <h2 style="color: red;">❌ Erro no Processamento de Agregações</h2>
            
            <p><strong>Data/Hora:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
            
            <h3>Detalhes do Erro:</h3>
            <pre style="background: #f5f5f5; padding: 10px; border-radius: 5px;">{error_message}</pre>
            
            <p>Por favor, verifique os logs do sistema e execute a correção necessária.</p>
            
            <hr>
            <small>Sistema de monitoramento Transpontual</small>
        </body>
        </html>
        """
        
        await self.notification.send_email(subject, body)

class AlertService:
    """Serviço de alertas e monitoramento"""
    
    def __init__(self, db_manager: DatabaseManager, notification_service: NotificationService):
        self.db = db_manager
        self.notification = notification_service
    
    async def check_critical_alerts(self):
        """Verificar alertas críticos"""
        
        logger.info("Verificando alertas críticos...")
        
        alerts = []
        
        # 1. Checklists pendentes há mais de 2 horas
        pending_checklists = self.db.execute_query("""
            SELECT 
                c.id,
                c.codigo,
                v.placa,
                m.nome as motorista_nome,
                c.dt_inicio,
                EXTRACT(EPOCH FROM (NOW() - c.dt_inicio)) / 3600 as horas_pendente
            FROM checklists c
            JOIN veiculos v ON v.id = c.veiculo_id
            JOIN motoristas m ON m.id = c.motorista_id
            WHERE c.status IN ('pendente', 'em_andamento')
              AND c.dt_inicio < NOW() - INTERVAL '2 hours'
            ORDER BY c.dt_inicio
        """)
        
        if pending_checklists:
            alerts.append({
                "tipo": "checklists_pendentes",
                "severidade": "warning",
                "mensagem": f"{len(pending_checklists)} checklists pendentes há mais de 2 horas",
                "dados": pending_checklists
            })
        
        # 2. Defeitos críticos não resolvidos
        critical_defects = self.db.execute_query("""
            SELECT 
                d.id,
                d.codigo,
                v.placa,
                d.descricao,
                d.criado_em,
                EXTRACT(EPOCH FROM (NOW() - d.criado_em)) / 3600 as horas_aberto
            FROM defeitos d
            JOIN veiculos v ON v.id = d.veiculo_id
            WHERE d.severidade = 'critica'
              AND d.status IN ('identificado', 'aberto')
              AND d.criado_em < NOW() - INTERVAL '4 hours'
            ORDER BY d.criado_em
        """)
        
        if critical_defects:
            alerts.append({
                "tipo": "defeitos_criticos",
                "severidade": "critical",
                "mensagem": f"{len(critical_defects)} defeitos críticos sem resolução há mais de 4 horas",
                "dados": critical_defects
            })
        
        # 3. Veículos com taxa de reprovação alta
        problematic_vehicles = self.db.execute_query("""
            SELECT 
                v.placa,
                COUNT(c.id) as total_checklists,
                COUNT(*) FILTER (WHERE c.status = 'reprovado') as reprovados,
                ROUND(COUNT(*) FILTER (WHERE c.status = 'reprovado') * 100.0 / COUNT(c.id), 2) as taxa_reprovacao
            FROM veiculos v
            JOIN checklists c ON c.veiculo_id = v.id
            WHERE c.dt_inicio >= NOW() - INTERVAL '7 days'
              AND v.ativo = true
            GROUP BY v.id, v.placa
            HAVING COUNT(c.id) >= 3
               AND COUNT(*) FILTER (WHERE c.status = 'reprovado') * 100.0 / COUNT(c.id) > 50
            ORDER BY taxa_reprovacao DESC
        """)
        
        if problematic_vehicles:
            alerts.append({
                "tipo": "veiculos_problema",
                "severidade": "warning",
                "mensagem": f"{len(problematic_vehicles)} veículos com alta taxa de reprovação (>50%)",
                "dados": problematic_vehicles
            })
        
        # 4. CNH de motoristas vencendo em 30 dias
        expiring_cnh = self.db.execute_query("""
            SELECT 
                m.nome,
                m.cnh,
                m.validade_cnh,
                m.telefone,
                DATE(m.validade_cnh) - CURRENT_DATE as dias_para_vencer
            FROM motoristas m
            WHERE m.ativo = true
              AND m.validade_cnh IS NOT NULL
              AND m.validade_cnh BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '30 days'
            ORDER BY m.validade_cnh
        """)
        
        if expiring_cnh:
            alerts.append({
                "tipo": "cnh_vencimento",
                "severidade": "warning", 
                "mensagem": f"{len(expiring_cnh)} motoristas com CNH vencendo em até 30 dias",
                "dados": expiring_cnh
            })
        
        # Processar alertas
        if alerts:
            await self._process_alerts(alerts)
        else:
            logger.info("Nenhum alerta crítico identificado")
    
    async def _process_alerts(self, alerts: List[Dict[str, Any]]):
        """Processar lista de alertas"""
        
        critical_alerts = [a for a in alerts if a["severidade"] == "critical"]
        warning_alerts = [a for a in alerts if a["severidade"] == "warning"]
        
        # Enviar alertas críticos imediatamente
        if critical_alerts:
            await self._send_critical_alert_notification(critical_alerts)
        
        # Agrupar warnings em um relatório
        if warning_alerts:
            await self._send_warning_alert_notification(warning_alerts)
        
        logger.info(f"Processados {len(alerts)} alertas ({len(critical_alerts)} críticos, {len(warning_alerts)} avisos)")
    
    async def _send_critical_alert_notification(self, alerts: List[Dict[str, Any]]):
        """Enviar notificação de alertas críticos"""
        
        subject = "🚨 ALERTA CRÍTICO - Sistema Transpontual"
        
        body = "<html><body><h2 style='color: red;'>🚨 ALERTAS CRÍTICOS</h2>"
        
        for alert in alerts:
            body += f"<h3>{alert['mensagem']}</h3><ul>"
            for item in alert['dados'][:5]:  # Limitar a 5 itens por alerta
                if alert['tipo'] == 'defeitos_criticos':
                    body += f"<li><strong>{item['placa']}</strong>: {item['descricao']} (há {item['horas_aberto']:.1f}h)</li>"
            body += "</ul>"
        
        body += f"<p><strong>⏰ Requer ação imediata!</strong></p>"
        body += f"<small>Enviado em {datetime.now().strftime('%d/%m/%Y %H:%M')}</small></body></html>"
        
        await self.notification.send_email(subject, body)
        
        # WhatsApp para alertas críticos
        whatsapp_msg = "🚨 ALERTA CRÍTICO TRANSPONTUAL!\n"
        whatsapp_msg += f"{len(alerts)} problemas críticos identificados.\n"
        whatsapp_msg += "Verifique seu email para detalhes."
        
        await self.notification.send_whatsapp(whatsapp_msg, [])
    
    async def _send_warning_alert_notification(self, alerts: List[Dict[str, Any]]):
        """Enviar notificação de alertas de aviso"""
        
        subject = "⚠️ Alertas de Monitoramento - Sistema Transpontual"
        
        body = "<html><body><h2 style='color: orange;'>⚠️ ALERTAS DE MONITORAMENTO</h2>"
        
        for alert in alerts:
            body += f"<h3>{alert['mensagem']}</h3>"
            if alert['tipo'] == 'checklists_pendentes':
                body += "<ul>"
                for item in alert['dados'][:10]:
                    body += f"<li><strong>{item['placa']}</strong> ({item['motorista_nome']}) - há {item['horas_pendente']:.1f}h</li>"
                body += "</ul>"
            elif alert['tipo'] == 'veiculos_problema':
                body += "<ul>"
                for item in alert['dados'][:5]:
                    body += f"<li><strong>{item['placa']}</strong>: {item['taxa_reprovacao']}% de reprovação ({item['reprovados']}/{item['total_checklists']})</li>"
                body += "</ul>"
            elif alert['tipo'] == 'cnh_vencimento':
                body += "<ul>"
                for item in alert['dados']:
                    body += f"<li><strong>{item['nome']}</strong>: CNH {item['cnh']} vence em {item['dias_para_vencer']} dias</li>"
                body += "</ul>"
        
        body += f"<small>Enviado em {datetime.now().strftime('%d/%m/%Y %H:%M')}</small></body></html>"
        
        await self.notification.send_email(subject, body)

# ==============================
# SCRIPT PRINCIPAL
# ==============================

async def main():
    """Função principal para executar jobs"""
    
    # Carregar configuração
    config = JobConfig(
        database_url=os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/frotadb"),
        api_base_url=os.getenv("API_BASE_URL", "http://localhost:8005"),
        smtp_server=os.getenv("SMTP_SERVER", ""),
        smtp_port=int(os.getenv("SMTP_PORT", "587")),
        email_user=os.getenv("EMAIL_USER", ""),
        email_password=os.getenv("EMAIL_PASSWORD", ""),
        notification_emails=os.getenv("NOTIFICATION_EMAILS", "").split(",") if os.getenv("NOTIFICATION_EMAILS") else [],
        whatsapp_api_url=os.getenv("WHATSAPP_API_URL", ""),
        whatsapp_token=os.getenv("WHATSAPP_TOKEN", "")
    )
    
    # Inicializar serviços
    db_manager = DatabaseManager(config.database_url)
    notification_service = NotificationService(config)
    
    # Determinar qual job executar
    job_type = os.getenv("JOB_TYPE", "daily_aggregation")
    
    if job_type == "daily_aggregation":
        aggregator = ChecklistAggregatorJob(db_manager, notification_service)
        await aggregator.run_daily_aggregation()
        
    elif job_type == "check_alerts":
        alert_service = AlertService(db_manager, notification_service)
        await alert_service.check_critical_alerts()
        
    elif job_type == "refresh_views":
        aggregator = ChecklistAggregatorJob(db_manager, notification_service)
        await aggregator._refresh_materialized_views()
        
    else:
        logger.error(f"Tipo de job desconhecido: {job_type}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())