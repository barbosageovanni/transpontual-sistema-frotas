# backend_fastapi/app/services/cupom_extractor.py
"""
Serviço para extração de dados de cupons fiscais de abastecimento usando OCR
"""
import re
from datetime import datetime
from typing import Dict, Optional, List
import io
from PIL import Image
import logging

logger = logging.getLogger(__name__)

class CupomExtractor:
    """Extrai informações de cupons fiscais de abastecimento"""

    def __init__(self):
        """Inicializa o extrator de cupons"""
        try:
            import pytesseract
            self.pytesseract = pytesseract
            self.ocr_available = True
        except ImportError:
            logger.warning("pytesseract não disponível. OCR desabilitado.")
            self.ocr_available = False

    def extract_from_image(self, image_file) -> Dict[str, any]:
        """
        Extrai dados de um cupom fiscal a partir de uma imagem

        Args:
            image_file: Arquivo de imagem (bytes ou file object)

        Returns:
            Dicionário com os dados extraídos
        """
        if not self.ocr_available:
            raise Exception("OCR não disponível. Instale pytesseract: pip install pytesseract")

        try:
            # Carregar imagem
            if isinstance(image_file, bytes):
                image = Image.open(io.BytesIO(image_file))
            else:
                image = Image.open(image_file)

            # Pré-processamento da imagem
            image = self._preprocess_image(image)

            # Extrair texto usando OCR
            # Tentar português primeiro, depois inglês como fallback
            try:
                text = self.pytesseract.image_to_string(image, lang='por')
            except Exception as e:
                logger.warning(f"Erro ao usar idioma português, tentando inglês: {str(e)}")
                text = self.pytesseract.image_to_string(image, lang='eng')

            # LOG: Mostrar texto extraído
            logger.info("=" * 50)
            logger.info("OCR EXTRACTION COMPLETED")
            logger.info(f"Text length: {len(text)} characters")
            logger.info(f"Text preview (first 500 chars):\n{text[:500]}")
            logger.info("=" * 50)

            # Extrair informações do texto
            data = self._parse_cupom_text(text)

            # LOG: Mostrar dados extraídos
            logger.info("PARSED DATA:")
            logger.info(f"  Posto: {data.get('posto')}")
            logger.info(f"  Litros: {data.get('litros')}")
            logger.info(f"  Valor/Litro: {data.get('valor_litro')}")
            logger.info(f"  Valor Total: {data.get('valor_total')}")
            logger.info(f"  Data: {data.get('data_abastecimento')}")
            logger.info(f"  Tipo: {data.get('tipo_combustivel')}")
            logger.info(f"  Cupom: {data.get('numero_cupom')}")

            return data

        except Exception as e:
            logger.error(f"Erro ao extrair dados do cupom: {str(e)}")
            raise Exception(f"Erro ao processar imagem: {str(e)}")

    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Pré-processa a imagem para melhorar a qualidade do OCR

        Args:
            image: Imagem PIL

        Returns:
            Imagem pré-processada
        """
        try:
            from PIL import ImageEnhance, ImageFilter

            # Log tamanho original
            logger.info(f"Imagem original: {image.size} - Modo: {image.mode}")

            # Redimensionar se muito pequena (mínimo 1000px de largura)
            if image.width < 1000:
                scale = 1000 / image.width
                new_size = (int(image.width * scale), int(image.height * scale))
                image = image.resize(new_size, Image.Resampling.LANCZOS)
                logger.info(f"Imagem redimensionada para: {image.size}")

            # Converter para escala de cinza
            image = image.convert('L')

            # Aumentar brilho
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(1.2)

            # Aumentar contraste
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.5)

            # Aumentar nitidez
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(2.0)

            # Aplicar filtro de nitidez adicional
            image = image.filter(ImageFilter.SHARPEN)

            logger.info(f"Pré-processamento concluído: {image.size}")

            return image

        except Exception as e:
            logger.warning(f"Erro no pré-processamento: {str(e)}")
            return image

    def _parse_cupom_text(self, text: str) -> Dict[str, any]:
        """
        Extrai informações estruturadas do texto do cupom

        Args:
            text: Texto extraído do cupom

        Returns:
            Dicionário com dados estruturados
        """
        data = {
            'posto': None,
            'litros': None,
            'valor_litro': None,
            'valor_total': None,
            'data_abastecimento': None,
            'tipo_combustivel': None,
            'numero_cupom': None,
            'raw_text': text
        }

        try:
            # Extrair nome do posto (primeiras linhas geralmente)
            posto = self._extract_posto(text)
            if posto:
                data['posto'] = posto

            # Extrair data e hora
            data_hora = self._extract_data_hora(text)
            if data_hora:
                data['data_abastecimento'] = data_hora
                data['emissao'] = data_hora

            # Extrair valores (litros, preço por litro, total)
            valores = self._extract_valores(text)
            data.update(valores)

            # Extrair tipo de combustível
            tipo = self._extract_tipo_combustivel(text)
            if tipo:
                data['tipo_combustivel'] = tipo
                data['descricao'] = tipo

            # Extrair número do cupom/nota fiscal
            numero = self._extract_numero_cupom(text)
            if numero:
                data['numero_cupom'] = numero
                data['nfc_e'] = numero

        except Exception as e:
            logger.error(f"Erro ao parsear texto do cupom: {str(e)}")

        return data

    def _extract_posto(self, text: str) -> Optional[str]:
        """Extrai o nome do posto"""
        lines = text.split('\n')
        # Geralmente o nome está nas primeiras 5-10 linhas
        for line in lines[:10]:
            line = line.strip()
            # Procurar por palavras-chave de postos e marcas conhecidas
            keywords = ['posto', 'combustivel', 'gasolina', 'diesel', 'auto',
                       'mercado', 'servicos', 'eireli', 'ltda', 'me', 'sa',
                       'ipiranga', 'shell', 'petrobras', 'br', 'alesat',
                       'raizen', 'ultragaz', 'gas', 'energy', 'rodoporto', 'oasis']
            if line and len(line) > 5 and any(keyword in line.lower() for keyword in keywords):
                # Limpar linha mas manter espaços
                posto = re.sub(r'[^a-zA-Z0-9\s\-]', '', line)
                if len(posto) > 5:  # Nome razoável
                    return posto.strip()
        # Se não encontrar com keywords, pegar a primeira linha significativa
        for line in lines[:5]:
            line = line.strip()
            if line and len(line) > 5 and not line.isdigit():
                return re.sub(r'[^a-zA-Z0-9\s\-]', '', line).strip()
        return None

    def _extract_data_hora(self, text: str) -> Optional[str]:
        """Extrai data e hora do cupom"""
        # Padrões de data comuns em cupons fiscais
        patterns = [
            r'(\d{2}/\d{2}/\d{4})\s+(\d{2}:\d{2}(?::\d{2})?)',  # DD/MM/YYYY HH:MM[:SS]
            r'(\d{2}-\d{2}-\d{4})\s+(\d{2}:\d{2}(?::\d{2})?)',  # DD-MM-YYYY HH:MM[:SS]
            r'(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2}(?::\d{2})?)',  # YYYY-MM-DD HH:MM[:SS]
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    data_str = match.group(1)
                    hora_str = match.group(2)

                    # Tentar converter para datetime
                    if '/' in data_str:
                        fmt_data = "%d/%m/%Y"
                    elif data_str.startswith('20'):  # YYYY-MM-DD
                        fmt_data = "%Y-%m-%d"
                    else:
                        fmt_data = "%d-%m-%Y"

                    fmt_hora = "%H:%M:%S" if hora_str.count(':') == 2 else "%H:%M"
                    dt = datetime.strptime(f"{data_str} {hora_str}", f"{fmt_data} {fmt_hora}")

                    return dt.isoformat()
                except Exception as e:
                    logger.warning(f"Erro ao parsear data: {str(e)}")
                    continue

        return None

    def _extract_valores(self, text: str) -> Dict[str, Optional[float]]:
        """Extrai valores numéricos (litros, preço/litro, total)"""
        resultado = {
            'litros': None,
            'valor_litro': None,
            'valor_total': None,
            'vl_unit': None
        }

        # Procurar por litros - ACEITAR INTEIROS E DECIMAIS
        # Padrões: "10,5 L", "10.5L", "50 L", "Qtd: 10,5", "LITROS: 50"
        litros_patterns = [
            r'(\d+[,\.]\d+)\s*[Ll](?:itros?)?',  # 10,5 L ou 10.5 Litros
            r'(\d+)\s*[Ll](?:itros?)?',  # 50 L ou 50 Litros (INTEIRO)
            r'[Qq][Tt][Dd][\s:]*(\d+[,\.]?\d*)',  # Qtd: 10,5 ou Qtd: 50
            r'[Ll][Ii][Tt][Rr][Oo][Ss]?[\s:]*(\d+[,\.]?\d*)',  # LITROS: 50
            r'(\d+[,\.]\d+)\s*[Kk][Gg]',  # Para gases como GNV em kg
            r'(\d+)\s*[Kk][Gg]',  # KG inteiro
        ]

        for pattern in litros_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    valor = match.group(1).replace(',', '.')
                    resultado['litros'] = float(valor)
                    break
                except:
                    continue

        # Procurar por valor por litro e valor total
        # Padrão comum: "R$ 5,59" ou "5.59"
        valores_monetarios = re.findall(r'[Rr]\$?\s*(\d+[,\.]\d{2,3})', text)

        if valores_monetarios:
            # Converter todos para float
            valores = []
            for v in valores_monetarios:
                try:
                    valores.append(float(v.replace(',', '.')))
                except:
                    continue

            if len(valores) >= 2:
                # Geralmente: preço/litro vem antes do total
                # Valor por litro é geralmente menor que 10
                valores_ordenados = sorted(valores)

                for v in valores_ordenados:
                    if v < 15 and not resultado['valor_litro']:  # Preço por litro
                        resultado['valor_litro'] = v
                    elif v >= 15 and not resultado['valor_total']:  # Total
                        resultado['valor_total'] = v

        # Validar: se temos litros e valor/litro, calcular total
        if resultado['litros'] and resultado['valor_litro']:
            total_calculado = resultado['litros'] * resultado['valor_litro']
            if not resultado['valor_total']:
                resultado['valor_total'] = round(total_calculado, 2)
            # Validar se o total está correto (margem de erro de 5%)
            elif resultado['valor_total']:
                diferenca = abs(resultado['valor_total'] - total_calculado)
                if diferenca / total_calculado > 0.05:  # Erro maior que 5%
                    logger.warning(f"Inconsistência nos valores: calculado={total_calculado:.2f}, encontrado={resultado['valor_total']:.2f}")

        return resultado

    def _extract_tipo_combustivel(self, text: str) -> Optional[str]:
        """Extrai o tipo de combustível"""
        text_lower = text.lower()

        tipos = {
            'diesel': ['diesel', 'dies', 'oleo', 's10', 's500', 's5000'],
            'gasolina': ['gasolina', 'gas comum', 'gasol'],
            'etanol': ['etanol', 'alcool'],
            'gnv': ['gnv', 'gas natural'],
            'arla': ['arla', 'arla 32', 'arla32']
        }

        for tipo, keywords in tipos.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return tipo.capitalize()

        return 'Diesel'  # Padrão para frotas

    def _extract_numero_cupom(self, text: str) -> Optional[str]:
        """Extrai número do cupom fiscal"""
        # Procurar por padrões de NFC-e ou número de cupom
        patterns = [
            r'[Nn][Ff][Cc][-\s]?[Ee]:?\s*(\d+)',  # NFC-e: 000893951
            r'[Cc]upom[\s:]*[Nn]?[º°]?[\s:]*(\d+)',  # Cupom: 123456 ou Cupom Nº 123456
            r'[Nn]ota[\s:]*[Ff]?[Ii]?[Ss]?[Cc]?[Aa]?[Ll]?[\s:]*[Nn]?[º°]?[\s:]*(\d+)',  # Nota Fiscal Nº 123456
            r'[Cc][Oo][Oo]:?\s*(\d+)',  # COO: 123456
            r'[Dd][Oo][Cc](?:umento)?[\s:]*(\d+)',  # DOC: 123456 ou Documento: 123456
            r'[Nn][Ff][\s:-]*(\d+)',  # NF-123456 ou NF: 123456
            r'(?:^|\n)\s*(\d{6,})',  # Sequência de 6+ dígitos no início de linha
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        return None


# Função helper para uso direto
def extract_cupom_data(image_file) -> Dict[str, any]:
    """
    Função auxiliar para extrair dados de cupom fiscal

    Args:
        image_file: Arquivo de imagem

    Returns:
        Dicionário com dados extraídos
    """
    extractor = CupomExtractor()
    return extractor.extract_from_image(image_file)
