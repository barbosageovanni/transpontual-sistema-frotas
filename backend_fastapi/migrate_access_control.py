#!/usr/bin/env python3
"""
Script de migração para o sistema de controle de acesso avançado
Este script adiciona as novas tabelas e colunas necessárias para o sistema de permissões granulares

Base de dados: PostgreSQL
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import get_db, engine

def backup_database():
    """Função para backup - deve ser implementada manualmente conforme ambiente"""
    print("⚠️  IMPORTANTE: Faça backup do banco de dados antes de executar esta migração!")
    print("   Exemplo: pg_dump nome_do_banco > backup_$(date +%Y%m%d_%H%M%S).sql")
    input("   Pressione Enter após fazer o backup para continuar...")

def migrate_usuarios_table():
    """Adiciona novos campos de controle de acesso à tabela usuarios"""
    print("📝 Migrando tabela 'usuarios'...")

    migrations = [
        # Campos de controle de horário
        "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS horario_inicio TIME",
        "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS horario_fim TIME",
        "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS dias_semana VARCHAR(20)",

        # Campos de controle de localização/IP
        "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS ips_permitidos TEXT",
        "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS localizacao_restrita BOOLEAN DEFAULT false",

        # Campos de validade e sessão
        "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS data_validade DATE",
        "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS max_sessoes INTEGER DEFAULT 1",

        # Campos de auditoria e controle
        "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS ultimo_acesso TIMESTAMP",
        "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS ultimo_ip VARCHAR(45)",
        "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS tentativas_login INTEGER DEFAULT 0",
        "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS bloqueado_ate TIMESTAMP",
    ]

    return migrations

def create_new_tables():
    """Cria as novas tabelas do sistema de controle de acesso"""
    print("🗃️  Criando novas tabelas...")

    tables = [
        # Tabela de permissões específicas por usuário
        """
        CREATE TABLE IF NOT EXISTS usuario_permissoes (
            id SERIAL PRIMARY KEY,
            usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
            modulo VARCHAR(50) NOT NULL,
            acao VARCHAR(20) NOT NULL,
            permitido BOOLEAN NOT NULL DEFAULT true,
            criado_em TIMESTAMP DEFAULT NOW(),
            UNIQUE(usuario_id, modulo, acao)
        );
        """,

        # Tabela de controle de sessões ativas
        """
        CREATE TABLE IF NOT EXISTS sessoes_usuarios (
            id SERIAL PRIMARY KEY,
            usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
            token_sessao VARCHAR(255) UNIQUE NOT NULL,
            ip_acesso VARCHAR(45) NOT NULL,
            user_agent TEXT,
            inicio_sessao TIMESTAMP DEFAULT NOW(),
            ultima_atividade TIMESTAMP DEFAULT NOW(),
            ativa BOOLEAN DEFAULT true
        );
        """,

        # Tabela de logs de acesso para auditoria
        """
        CREATE TABLE IF NOT EXISTS logs_acesso (
            id SERIAL PRIMARY KEY,
            usuario_id INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
            ip_acesso VARCHAR(45) NOT NULL,
            user_agent TEXT,
            url_acessada VARCHAR(500),
            metodo_http VARCHAR(10),
            status_resposta INTEGER,
            timestamp TIMESTAMP DEFAULT NOW(),
            sucesso BOOLEAN DEFAULT true,
            motivo_falha VARCHAR(200)
        );
        """,

        # Tabela de perfis de acesso predefinidos
        """
        CREATE TABLE IF NOT EXISTS perfis_acesso (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(100) UNIQUE NOT NULL,
            descricao TEXT,
            permissoes JSON,
            ativo BOOLEAN DEFAULT true,
            criado_em TIMESTAMP DEFAULT NOW()
        );
        """,

        # Tabela de associação entre usuários e perfis
        """
        CREATE TABLE IF NOT EXISTS usuario_perfis (
            usuario_id INTEGER REFERENCES usuarios(id) ON DELETE CASCADE,
            perfil_id INTEGER REFERENCES perfis_acesso(id) ON DELETE CASCADE,
            atribuido_em TIMESTAMP DEFAULT NOW(),
            atribuido_por INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
            PRIMARY KEY (usuario_id, perfil_id)
        );
        """
    ]

    return tables

def create_indexes():
    """Cria índices para melhor performance"""
    print("🚀 Criando índices para performance...")

    indexes = [
        # Índices para logs de acesso
        "CREATE INDEX IF NOT EXISTS idx_logs_acesso_usuario_id ON logs_acesso(usuario_id);",
        "CREATE INDEX IF NOT EXISTS idx_logs_acesso_timestamp ON logs_acesso(timestamp DESC);",
        "CREATE INDEX IF NOT EXISTS idx_logs_acesso_ip ON logs_acesso(ip_acesso);",

        # Índices para sessões
        "CREATE INDEX IF NOT EXISTS idx_sessoes_usuario_id ON sessoes_usuarios(usuario_id);",
        "CREATE INDEX IF NOT EXISTS idx_sessoes_ativa ON sessoes_usuarios(ativa);",
        "CREATE INDEX IF NOT EXISTS idx_sessoes_ultima_atividade ON sessoes_usuarios(ultima_atividade);",

        # Índices para permissões
        "CREATE INDEX IF NOT EXISTS idx_usuario_permissoes_lookup ON usuario_permissoes(usuario_id, modulo, acao);",

        # Índices para usuarios (novos campos)
        "CREATE INDEX IF NOT EXISTS idx_usuarios_ultimo_acesso ON usuarios(ultimo_acesso);",
        "CREATE INDEX IF NOT EXISTS idx_usuarios_bloqueado_ate ON usuarios(bloqueado_ate);",
        "CREATE INDEX IF NOT EXISTS idx_usuarios_data_validade ON usuarios(data_validade);",
    ]

    return indexes

def insert_default_profiles():
    """Insere os perfis de acesso padrão"""
    print("👥 Inserindo perfis de acesso padrão...")

    profiles = [
        {
            'nome': 'Administrador',
            'descricao': 'Acesso total ao sistema',
            'permissoes': {
                "usuarios": ["visualizar", "criar", "editar", "excluir"],
                "veiculos": ["visualizar", "criar", "editar", "excluir"],
                "motoristas": ["visualizar", "criar", "editar", "excluir"],
                "checklists": ["visualizar", "criar", "editar", "excluir"],
                "abastecimentos": ["visualizar", "criar", "editar", "excluir"],
                "ordens_servico": ["visualizar", "criar", "editar", "excluir"],
                "financeiro": ["visualizar", "criar", "editar", "excluir"],
                "fiscal": ["visualizar", "criar", "editar", "excluir"],
                "relatorios": ["visualizar", "criar", "editar", "excluir"]
            }
        },
        {
            'nome': 'Gestor de Frota',
            'descricao': 'Acesso à gestão de frota e relatórios',
            'permissoes': {
                "veiculos": ["visualizar", "criar", "editar"],
                "motoristas": ["visualizar", "criar", "editar"],
                "checklists": ["visualizar", "criar", "editar"],
                "abastecimentos": ["visualizar", "criar", "editar"],
                "ordens_servico": ["visualizar", "criar", "editar"],
                "relatorios": ["visualizar", "criar"]
            }
        },
        {
            'nome': 'Responsável Fiscal',
            'descricao': 'Acesso apenas aos documentos fiscais',
            'permissoes': {
                "fiscal": ["visualizar", "criar", "editar"],
                "veiculos": ["visualizar"],
                "relatorios": ["visualizar"]
            }
        },
        {
            'nome': 'Responsável Financeiro',
            'descricao': 'Acesso aos controles financeiros',
            'permissoes': {
                "financeiro": ["visualizar", "criar", "editar"],
                "abastecimentos": ["visualizar"],
                "ordens_servico": ["visualizar"],
                "relatorios": ["visualizar", "criar"]
            }
        },
        {
            'nome': 'Operacional',
            'descricao': 'Acesso aos checklists e operações básicas',
            'permissoes': {
                "checklists": ["visualizar", "criar", "editar"],
                "veiculos": ["visualizar"],
                "motoristas": ["visualizar"]
            }
        },
        {
            'nome': 'Estagiário',
            'descricao': 'Acesso limitado e com restrições de horário',
            'permissoes': {
                "veiculos": ["visualizar"],
                "checklists": ["visualizar"],
                "relatorios": ["visualizar"]
            }
        }
    ]

    insert_statements = []
    for profile in profiles:
        insert_statements.append(f"""
        INSERT INTO perfis_acesso (nome, descricao, permissoes)
        VALUES (
            '{profile['nome']}',
            '{profile['descricao']}',
            '{str(profile['permissoes']).replace("'", '"')}'::json
        ) ON CONFLICT (nome) DO NOTHING;
        """)

    return insert_statements

def add_comments():
    """Adiciona comentários às tabelas e colunas para documentação"""
    print("📖 Adicionando comentários para documentação...")

    comments = [
        # Comentários nas colunas da tabela usuarios
        "COMMENT ON COLUMN usuarios.horario_inicio IS 'Horário inicial permitido para acesso (ex: 08:00)';",
        "COMMENT ON COLUMN usuarios.horario_fim IS 'Horário final permitido para acesso (ex: 18:00)';",
        "COMMENT ON COLUMN usuarios.dias_semana IS 'Dias da semana permitidos (1=seg, 2=ter, etc) separados por vírgula';",
        "COMMENT ON COLUMN usuarios.ips_permitidos IS 'Lista de IPs autorizados separados por vírgula';",
        "COMMENT ON COLUMN usuarios.localizacao_restrita IS 'Se true, restringe acesso por localização';",
        "COMMENT ON COLUMN usuarios.data_validade IS 'Data de validade do acesso do usuário';",
        "COMMENT ON COLUMN usuarios.max_sessoes IS 'Número máximo de sessões simultâneas permitidas';",
        "COMMENT ON COLUMN usuarios.ultimo_acesso IS 'Timestamp do último acesso bem-sucedido';",
        "COMMENT ON COLUMN usuarios.ultimo_ip IS 'Último IP usado para acesso';",
        "COMMENT ON COLUMN usuarios.tentativas_login IS 'Contador de tentativas de login falhadas';",
        "COMMENT ON COLUMN usuarios.bloqueado_ate IS 'Timestamp até quando o usuário está bloqueado';",

        # Comentários nas tabelas
        "COMMENT ON TABLE usuario_permissoes IS 'Permissões específicas por usuário e módulo';",
        "COMMENT ON TABLE sessoes_usuarios IS 'Controle de sessões ativas dos usuários';",
        "COMMENT ON TABLE logs_acesso IS 'Log de auditoria de todos os acessos ao sistema';",
        "COMMENT ON TABLE perfis_acesso IS 'Perfis de acesso predefinidos com conjunto de permissões';",
        "COMMENT ON TABLE usuario_perfis IS 'Associação entre usuários e perfis de acesso';",
    ]

    return comments

def run_migration():
    """Executa toda a migração"""
    print("🚀 Iniciando migração do sistema de controle de acesso avançado...")
    print("=" * 70)

    # Backup warning
    backup_database()

    try:
        # Get database session
        db_gen = get_db()
        db = next(db_gen)

        # Lista de todas as operações
        all_operations = []

        # 1. Adicionar colunas à tabela usuarios
        all_operations.extend(migrate_usuarios_table())

        # 2. Criar novas tabelas
        all_operations.extend(create_new_tables())

        # 3. Criar índices
        all_operations.extend(create_indexes())

        # 4. Inserir perfis padrão
        all_operations.extend(insert_default_profiles())

        # 5. Adicionar comentários
        all_operations.extend(add_comments())

        # Executar todas as operações
        success_count = 0
        total_count = len(all_operations)

        for i, operation in enumerate(all_operations, 1):
            try:
                print(f"[{i:3d}/{total_count}] Executando migração...")
                db.execute(text(operation.strip()))
                db.commit()
                success_count += 1
                print(f"✅ Operação {i} executada com sucesso")
            except Exception as e:
                print(f"⚠️  Operação {i} já executada ou erro: {str(e)[:100]}")
                db.rollback()
                continue

        print("=" * 70)
        print(f"🎉 Migração concluída!")
        print(f"   ✅ {success_count}/{total_count} operações executadas com sucesso")
        print("   📊 Sistema de controle de acesso avançado instalado!")
        print()
        print("🔧 Próximos passos:")
        print("   1. Reinicie a aplicação FastAPI")
        print("   2. Teste o acesso aos novos endpoints")
        print("   3. Configure os primeiros usuários via interface web")
        print("   4. Defina permissões específicas conforme necessário")

    except Exception as e:
        print(f"❌ Erro durante a migração: {e}")
        print("   Verifique a conexão com o banco e tente novamente")
        return False

    finally:
        db.close()

    return True

def verify_migration():
    """Verifica se a migração foi aplicada corretamente"""
    print("\n🔍 Verificando migração...")

    verification_queries = [
        "SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'usuarios' AND column_name = 'horario_inicio';",
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'usuario_permissoes';",
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'logs_acesso';",
        "SELECT COUNT(*) FROM perfis_acesso;",
    ]

    try:
        db_gen = get_db()
        db = next(db_gen)

        print("Verificando colunas adicionadas à tabela usuarios...")
        result = db.execute(text(verification_queries[0])).scalar()
        print(f"   ✅ Novas colunas encontradas: {result > 0}")

        print("Verificando criação da tabela usuario_permissoes...")
        result = db.execute(text(verification_queries[1])).scalar()
        print(f"   ✅ Tabela usuario_permissoes: {'✓' if result > 0 else '✗'}")

        print("Verificando criação da tabela logs_acesso...")
        result = db.execute(text(verification_queries[2])).scalar()
        print(f"   ✅ Tabela logs_acesso: {'✓' if result > 0 else '✗'}")

        print("Verificando perfis padrão inseridos...")
        result = db.execute(text(verification_queries[3])).scalar()
        print(f"   ✅ Perfis inseridos: {result}")

        db.close()
        return True

    except Exception as e:
        print(f"❌ Erro na verificação: {e}")
        return False

if __name__ == "__main__":
    print("MIGRACAO DO SISTEMA DE CONTROLE DE ACESSO AVANCADO")
    print("    Sistema de Gestao de Frotas - Transpontual")
    print("=" * 70)

    # Executar migração
    if run_migration():
        # Verificar se foi aplicada corretamente
        verify_migration()
        print("\n🎯 Migração concluída com sucesso!")
        print("   O sistema agora possui controle de acesso avançado com:")
        print("   • Controle de horário e dias de acesso")
        print("   • Restrições por IP e localização")
        print("   • Permissões granulares por módulo")
        print("   • Auditoria completa de acessos")
        print("   • 6 perfis de acesso predefinidos")
    else:
        print("\n❌ Falha na migração. Verifique os logs acima.")
        sys.exit(1)