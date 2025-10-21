# Configuração do OCR para Cupons Fiscais

Este documento explica como configurar o sistema de OCR (Reconhecimento Óptico de Caracteres) para extrair automaticamente informações de cupons fiscais de abastecimento.

## Pré-requisitos

### 1. Instalar Tesseract OCR

O sistema usa o Tesseract OCR para reconhecimento de texto em imagens. Você precisa instalá-lo no seu sistema operacional:

#### Windows
1. Baixe o instalador do Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
2. Execute o instalador
3. Durante a instalação, certifique-se de incluir o pacote de idioma **Português**
4. Adicione o Tesseract ao PATH do sistema (geralmente: `C:\Program Files\Tesseract-OCR`)

#### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-por
```

#### MacOS
```bash
brew install tesseract tesseract-lang
```

### 2. Instalar Dependências Python

No diretório `backend_fastapi`, execute:

```bash
pip install -r requirements.txt
```

Isso instalará:
- `pytesseract` - Interface Python para o Tesseract
- `Pillow` - Processamento de imagens

## Verificar Instalação

Para verificar se o Tesseract está instalado corretamente:

```bash
tesseract --version
```

Você deve ver a versão do Tesseract instalada.

## Como Usar

### No Formulário Web

1. Acesse: `http://localhost:8050/abastecimentos/new`
2. No card "Extrair do Cupom Fiscal", clique em "Escolher arquivo"
3. Selecione uma foto do cupom fiscal
4. Clique em "Extrair Dados do Cupom"
5. Os campos do formulário serão preenchidos automaticamente

### Via API

Endpoint: `POST /api/v1/abastecimentos/upload-cupom`

```bash
curl -X POST \
  http://localhost:8005/api/v1/abastecimentos/upload-cupom \
  -F "file=@cupom.jpg"
```

Resposta:
```json
{
  "success": true,
  "data": {
    "posto": "Posto Oásis",
    "litros": 87.15,
    "valor_litro": 5.59,
    "valor_total": 487.17,
    "data_abastecimento": "2025-09-29T10:41:00",
    "tipo_combustivel": "Diesel",
    "numero_cupom": "000893951"
  },
  "message": "Cupom processado com sucesso"
}
```

## Informações Extraídas

O sistema tenta extrair as seguintes informações do cupom:

- **Posto**: Nome do posto de combustível
- **Data e Hora**: Data e hora do abastecimento
- **Litros**: Quantidade de combustível
- **Valor por Litro**: Preço por litro
- **Valor Total**: Valor total pago
- **Tipo de Combustível**: Diesel, Gasolina, Etanol, etc.
- **Número do Cupom**: Número da nota fiscal eletrônica

## Dicas para Melhores Resultados

1. **Qualidade da Foto**
   - Tire a foto com boa iluminação
   - Evite sombras e reflexos
   - Mantenha o cupom plano e reto
   - Foto nítida (sem tremor)

2. **Enquadramento**
   - Centralize o cupom na foto
   - Capture todo o cupom
   - Evite cortar informações importantes

3. **Estado do Cupom**
   - Cupons limpos e legíveis produzem melhores resultados
   - Evite cupons muito amassados ou rasgados

## Solução de Problemas

### Erro: "OCR não disponível"

**Causa**: Tesseract não está instalado ou não está no PATH

**Solução**:
1. Verifique se o Tesseract está instalado: `tesseract --version`
2. Adicione o Tesseract ao PATH do sistema
3. Reinicie o servidor da API

### Erro: "Erro ao processar cupom"

**Causa**: Imagem com qualidade ruim ou formato não suportado

**Solução**:
1. Verifique o formato da imagem (JPG, PNG suportados)
2. Tire uma nova foto com melhor qualidade
3. Preencha os dados manualmente

### Dados extraídos incorretos

**Causa**: Cupom com formatação não padrão ou baixa qualidade

**Solução**:
1. Verifique os dados extraídos antes de salvar
2. Corrija manualmente os campos incorretos
3. O sistema é um assistente, não substitui a verificação humana

## Arquitetura Técnica

```
┌─────────────────┐
│  Frontend       │
│  (upload foto)  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│  API FastAPI            │
│  /upload-cupom          │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  CupomExtractor         │
│  - Pré-processamento    │
│  - OCR (Tesseract)      │
│  - Parsing de dados     │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  Dados Estruturados     │
│  {posto, litros, etc}   │
└─────────────────────────┘
```

## Melhorias Futuras

- [ ] Suporte para mais formatos de cupom
- [ ] Treinamento de modelo específico para cupons brasileiros
- [ ] Validação cruzada com dados do veículo
- [ ] Cache de resultados
- [ ] Suporte para múltiplos cupons em lote

## Suporte

Em caso de problemas, verifique:
1. Logs da API em: `backend_fastapi/logs/`
2. Console do navegador para erros JavaScript
3. Versão do Tesseract: deve ser 4.0 ou superior
