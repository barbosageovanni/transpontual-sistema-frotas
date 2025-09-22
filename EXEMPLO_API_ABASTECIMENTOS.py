# EXEMPLO DE IMPLEMENTAÇÃO PARA COMPLETAR A API DE ABASTECIMENTOS
# Este arquivo mostra como implementar as rotas faltantes PUT e DELETE

from fastapi import HTTPException, Depends
from typing import Optional

# Exemplo baseado no padrão das outras rotas da API

@app.put("/api/v1/abastecimentos/{abastecimento_id}")
async def update_abastecimento(
    abastecimento_id: int,
    abastecimento_data: dict,  # ou um schema específico AbastecimentoUpdate
    db: Session = Depends(get_db)
):
    """
    Atualizar abastecimento existente
    """
    # Buscar abastecimento existente
    abastecimento = db.query(Abastecimento).filter(
        Abastecimento.id == abastecimento_id
    ).first()

    if not abastecimento:
        raise HTTPException(status_code=404, detail="Abastecimento não encontrado")

    # Atualizar campos
    for campo, valor in abastecimento_data.items():
        if hasattr(abastecimento, campo):
            setattr(abastecimento, campo, valor)

    # Salvar alterações
    db.commit()
    db.refresh(abastecimento)

    return abastecimento


@app.delete("/api/v1/abastecimentos/{abastecimento_id}")
async def delete_abastecimento(
    abastecimento_id: int,
    db: Session = Depends(get_db)
):
    """
    Excluir abastecimento
    """
    # Buscar abastecimento
    abastecimento = db.query(Abastecimento).filter(
        Abastecimento.id == abastecimento_id
    ).first()

    if not abastecimento:
        raise HTTPException(status_code=404, detail="Abastecimento não encontrado")

    # Excluir
    db.delete(abastecimento)
    db.commit()

    return {"message": "Abastecimento excluído com sucesso"}


# TAMBÉM SERIA ÚTIL CORRIGIR O FILTRO DE MOTORISTA:

@app.get("/api/v1/abastecimentos")
async def list_abastecimentos(
    skip: int = 0,
    limit: int = 100,
    veiculo_id: Optional[int] = None,
    motorista_id: Optional[int] = None,  # ADICIONAR ESTE PARÂMETRO
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Lista abastecimentos com filtros (VERSÃO CORRIGIDA)
    """
    query = db.query(Abastecimento)

    if veiculo_id:
        query = query.filter(Abastecimento.veiculo_id == veiculo_id)

    # CORRIGIR: Adicionar filtro por motorista_id
    if motorista_id:
        query = query.filter(Abastecimento.motorista_id == motorista_id)

    if data_inicio:
        query = query.filter(Abastecimento.data_abastecimento >= data_inicio)

    if data_fim:
        query = query.filter(Abastecimento.data_abastecimento <= data_fim)

    abastecimentos = query.offset(skip).limit(limit).all()

    # IMPORTANTE: Incluir dados de veiculo e motorista na resposta
    resultado = []
    for abast in abastecimentos:
        abast_dict = {
            "id": abast.id,
            "data_abastecimento": abast.data_abastecimento,
            "veiculo_id": abast.veiculo_id,
            "motorista_id": abast.motorista_id,
            "odometro": abast.odometro,
            "litros": abast.litros,
            "valor_litro": abast.valor_litro,
            "valor_total": abast.valor_total,
            "posto": abast.posto,
            "tipo_combustivel": abast.tipo_combustivel,
            "numero_cupom": abast.numero_cupom,
            "observacoes": abast.observacoes,
            # Adicionar dados relacionados
            "veiculo_placa": abast.veiculo.placa if abast.veiculo else None,
            "veiculo_marca": abast.veiculo.marca if abast.veiculo else None,
            "veiculo_modelo": abast.veiculo.modelo if abast.veiculo else None,
            "motorista_nome": abast.motorista.nome if abast.motorista else None,
        }
        resultado.append(abast_dict)

    return resultado

"""
RESUMO DAS ALTERAÇÕES NECESSÁRIAS NA API:

1. ✅ Adicionar rota PUT /api/v1/abastecimentos/{id} para atualização
2. ✅ Adicionar rota DELETE /api/v1/abastecimentos/{id} para exclusão
3. ✅ Corrigir filtro motorista_id na listagem
4. ✅ Incluir motorista_id na resposta da listagem
5. ✅ Manter dados de veiculo_placa e motorista_nome para compatibilidade

DEPOIS DESSAS ALTERAÇÕES:
- Os botões de editar/excluir funcionarão
- O filtro de motorista funcionará direto na API
- A interface ficará mais responsiva
"""