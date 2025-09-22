# Como Habilitar a API de Abastecimentos Completa

## Status Atual da API

### ✅ Funcionalidades Implementadas
- `GET /api/v1/abastecimentos` - Lista abastecimentos
- `POST /api/v1/abastecimentos` - Cria novo abastecimento
- `GET /api/v1/abastecimentos/{id}` - Busca abastecimento por ID

### ❌ Funcionalidades Faltantes
- `PUT /api/v1/abastecimentos/{id}` - Atualizar abastecimento
- `DELETE /api/v1/abastecimentos/{id}` - Excluir abastecimento
- Filtro `motorista_id` não funciona adequadamente
- Dados de `motorista_id` não são retornados na listagem

## Implementações Necessárias

### 1. Rota PUT para Atualização

```python
@app.put("/api/v1/abastecimentos/{abastecimento_id}")
async def update_abastecimento(
    abastecimento_id: int,
    abastecimento_data: dict,
    db: Session = Depends(get_db)
):
    abastecimento = db.query(Abastecimento).filter(
        Abastecimento.id == abastecimento_id
    ).first()

    if not abastecimento:
        raise HTTPException(status_code=404, detail="Abastecimento não encontrado")

    # Atualizar campos
    for campo, valor in abastecimento_data.items():
        if hasattr(abastecimento, campo):
            setattr(abastecimento, campo, valor)

    db.commit()
    db.refresh(abastecimento)
    return abastecimento
```

### 2. Rota DELETE para Exclusão

```python
@app.delete("/api/v1/abastecimentos/{abastecimento_id}")
async def delete_abastecimento(
    abastecimento_id: int,
    db: Session = Depends(get_db)
):
    abastecimento = db.query(Abastecimento).filter(
        Abastecimento.id == abastecimento_id
    ).first()

    if not abastecimento:
        raise HTTPException(status_code=404, detail="Abastecimento não encontrado")

    db.delete(abastecimento)
    db.commit()
    return {"message": "Abastecimento excluído com sucesso"}
```

### 3. Corrigir Filtro de Motorista

```python
@app.get("/api/v1/abastecimentos")
async def list_abastecimentos(
    skip: int = 0,
    limit: int = 100,
    veiculo_id: Optional[int] = None,
    motorista_id: Optional[int] = None,  # ← ADICIONAR ESTE PARÂMETRO
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Abastecimento)

    if veiculo_id:
        query = query.filter(Abastecimento.veiculo_id == veiculo_id)

    # ← ADICIONAR ESTE FILTRO
    if motorista_id:
        query = query.filter(Abastecimento.motorista_id == motorista_id)

    if data_inicio:
        query = query.filter(Abastecimento.data_abastecimento >= data_inicio)

    if data_fim:
        query = query.filter(Abastecimento.data_abastecimento <= data_fim)

    return query.offset(skip).limit(limit).all()
```

### 4. Incluir motorista_id na Resposta

```python
# Na resposta da listagem, garantir que inclui:
{
    "id": abast.id,
    "motorista_id": abast.motorista_id,  # ← IMPORTANTE
    "veiculo_id": abast.veiculo_id,
    "veiculo_placa": abast.veiculo.placa,
    "motorista_nome": abast.motorista.nome,
    # ... outros campos
}
```

## Após Implementar na API

### O Flask Dashboard será automaticamente habilitado:

1. **Edição funcionará**: Botões de editar enviarão PUT para a API
2. **Exclusão funcionará**: Botões de excluir enviarão DELETE para a API
3. **Filtros otimizados**: Filtro de motorista funcionará direto na API
4. **Performance melhor**: Menos processamento no Flask

### Status dos Botões

Atualmente os botões estão visíveis com tooltips informativos:
- ⚠️ "Editar (API em desenvolvimento)"
- ⚠️ "Excluir (API em desenvolvimento)"

Após implementar a API, eles funcionarão normalmente.

## Testando as Implementações

### Testar PUT:
```bash
curl -X PUT "http://localhost:8005/api/v1/abastecimentos/1" \
  -H "Content-Type: application/json" \
  -d '{"litros": "160.0", "valor_litro": "6.00"}'
```

### Testar DELETE:
```bash
curl -X DELETE "http://localhost:8005/api/v1/abastecimentos/1"
```

### Testar Filtro:
```bash
curl "http://localhost:8005/api/v1/abastecimentos?motorista_id=7"
```

## Arquivos para Referência

- `EXEMPLO_API_ABASTECIMENTOS.py` - Código de exemplo completo
- Flask Dashboard já está preparado para usar as novas rotas
- Templates já estão com botões habilitados

## Resultado Final

Após implementar essas 4 melhorias na API:
- ✅ CRUD completo de abastecimentos
- ✅ Filtros funcionando 100% na API
- ✅ Interface totalmente funcional
- ✅ Performance otimizada
- ✅ Experiência do usuário completa