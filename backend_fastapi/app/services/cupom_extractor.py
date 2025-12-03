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
        Extrai dados de um cupom fiscal a partir de uma imagem ou PDF

        Args:
            image_file: Arquivo de imagem ou PDF (bytes ou file object)

        Returns:
            Dicionário com os dados extraídos
        """
        try:
            # Verificar se é PDF
            if isinstance(image_file, bytes):
                file_bytes = image_file
            else:
                file_bytes = image_file if isinstance(image_file, bytes) else image_file.read()

            # Detectar tipo de arquivo pelos magic bytes
            is_pdf = file_bytes[:4] == b'%PDF'

            if is_pdf:
                logger.info("Arquivo detectado como PDF, processando...")
                return self._extract_from_pdf(file_bytes)

            # Se não for PDF, processar como imagem
            if not self.ocr_available:
                raise Exception("OCR não disponível. Instale pytesseract: pip install pytesseract")

            # Carregar imagem
            if isinstance(image_file, bytes):
                image = Image.open(io.BytesIO(image_file))
            else:
                image = Image.open(io.BytesIO(file_bytes))

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

    def _extract_from_pdf(self, pdf_bytes: bytes) -> Dict[str, any]:
        """
        Extrai dados de um cupom fiscal a partir de um arquivo PDF

        Args:
            pdf_bytes: Conteúdo do arquivo PDF em bytes

        Returns:
            Dicionário com os dados extraídos
        """
        try:
            # Tentar usar PyMuPDF (fitz) primeiro
            try:
                import fitz  # PyMuPDF

                logger.info("Usando PyMuPDF para extrair texto do PDF")

                # Abrir PDF
                pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")

                # Extrair texto de todas as páginas
                text = ""
                for page_num in range(len(pdf_document)):
                    page = pdf_document[page_num]
                    text += page.get_text()

                pdf_document.close()

                logger.info(f"Texto extraído do PDF ({len(text)} caracteres)")
                logger.info(f"Preview do texto:\n{text[:500]}")

            except ImportError:
                # Fallback para pdfplumber
                logger.info("PyMuPDF não disponível, tentando pdfplumber")
                import pdfplumber

                pdf_file = io.BytesIO(pdf_bytes)
                text = ""

                with pdfplumber.open(pdf_file) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"

                logger.info(f"Texto extraído do PDF ({len(text)} caracteres)")
                logger.info(f"Preview do texto:\n{text[:500]}")

            # Se conseguiu extrair texto, processar
            if text and len(text.strip()) > 50:
                data = self._parse_cupom_text(text)
                return data
            else:
                # Se não conseguiu extrair texto suficiente, tentar OCR na primeira página
                logger.warning("Texto insuficiente extraído do PDF, tentando renderizar como imagem")
                return self._extract_from_pdf_as_image(pdf_bytes)

        except Exception as e:
            logger.error(f"Erro ao processar PDF: {str(e)}")
            # Tentar como último recurso renderizar como imagem
            try:
                return self._extract_from_pdf_as_image(pdf_bytes)
            except:
                raise Exception(f"Erro ao processar PDF: {str(e)}")

    def _extract_from_pdf_as_image(self, pdf_bytes: bytes) -> Dict[str, any]:
        """
        Converte PDF para imagem e aplica OCR

        Args:
            pdf_bytes: Conteúdo do arquivo PDF em bytes

        Returns:
            Dicionário com os dados extraídos
        """
        try:
            import fitz  # PyMuPDF

            if not self.ocr_available:
                raise Exception("OCR não disponível e não foi possível extrair texto do PDF")

            logger.info("Convertendo PDF para imagem...")

            # Abrir PDF
            pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")

            # Pegar primeira página
            page = pdf_document[0]

            # Renderizar em alta resolução
            mat = fitz.Matrix(2.0, 2.0)  # 2x zoom para melhor qualidade
            pix = page.get_pixmap(matrix=mat)

            # Converter para PIL Image
            img_bytes = pix.tobytes("png")
            image = Image.open(io.BytesIO(img_bytes))

            pdf_document.close()

            logger.info(f"PDF convertido para imagem: {image.size}")

            # Processar como imagem normal
            image = self._preprocess_image(image)

            # Extrair texto usando OCR
            try:
                text = self.pytesseract.image_to_string(image, lang='por')
            except Exception as e:
                logger.warning(f"Erro ao usar idioma português, tentando inglês: {str(e)}")
                text = self.pytesseract.image_to_string(image, lang='eng')

            logger.info(f"OCR do PDF concluído: {len(text)} caracteres")

            # Extrair informações do texto
            data = self._parse_cupom_text(text)
            return data

        except ImportError:
            raise Exception("PyMuPDF não está instalado. Instale com: pip install PyMuPDF")
        except Exception as e:
            logger.error(f"Erro ao converter PDF para imagem: {str(e)}")
            raise Exception(f"Erro ao processar PDF como imagem: {str(e)}")

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
            'placa': None,
            'odometro': None,
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

            # Extrair placa do veículo
            placa = self._extract_placa(text)
            if placa:
                data['placa'] = placa

            # Extrair odômetro (KM)
            odometro = self._extract_odometro(text)
            if odometro:
                data['odometro'] = odometro

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
        # Padrões: "10,5 L", "10.5L", "50 L", "Qtd: 10,5", "Qtde.:29,24", "LITROS: 50"
        litros_patterns = [
            r'[Qq][Tt][Dd][Ee]?\.?[\s:]*(\d+[,\.]\d+)',  # Qtde.:29,24 ou Qtd: 10,5 (PRIORIDADE ALTA)
            r'[Qq][Uu][Aa][Nn][Tt][Ii]?[Dd]?[Aa]?[Dd]?[Ee]?\.?[\s:]*(\d+[,\.]\d+)',  # Quantidade: 10,5
            r'(\d+[,\.]\d+)\s*[Ll](?:itros?|ts?)?',  # 10,5 L ou 10.5 Litros ou 10.5LT
            r'(\d+)\s*[Ll](?:itros?|ts?)?',  # 50 L ou 50 Litros ou 50 LT (INTEIRO)
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

        # Procurar por valor unitário e valor total com padrões específicos

        # 1. Tentar extrair valor unitário (Vl. Unit., Vl Unit, Preço, etc.)
        valor_unit_patterns = [
            r'[Vv][Ll]\.?\s*[Uu][Nn][Ii][Tt]\.?[\s:]*(\d+[,\.]\d{2,3})',  # Vl. Unit.: 6,84
            r'[Pp][Rr][Ee][ÇçC][Oo][\s/]*[Ll]?[Ii]?[Tt]?[Rr]?[Oo]?[\s:]*[Rr]\$?\s*(\d+[,\.]\d{2,3})',  # Preço/Litro: R$ 6,84
            r'[Vv][Aa][Ll][Oo][Rr][\s/]*[Uu][Nn][Ii][Tt][\s:]*[Rr]\$?\s*(\d+[,\.]\d{2,3})',  # Valor Unit: R$ 6,84
        ]

        for pattern in valor_unit_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    resultado['valor_litro'] = float(match.group(1).replace(',', '.'))
                    break
                except:
                    continue

        # 2. Tentar extrair valor total (Vl. Total, Valor pago, Valor a pagar, etc.)
        valor_total_patterns = [
            r'[Vv][Ll]\.?\s*[Tt][Oo][Tt][Aa][Ll][\s:]*(\d+[,\.]\d{2})',  # Vl. Total 200,00
            r'[Vv][Aa][Ll][Oo][Rr]\s+[Pp][Aa][Gg][Oo][\s:]*[Rr]\$?[\s:]*(\d+[,\.]\d{2})',  # Valor pago R$: 200,00
            r'[Vv][Aa][Ll][Oo][Rr]\s+[Aa]\s+[Pp][Aa][Gg][Aa][Rr][\s:]*[Rr]\$?[\s:]*(\d+[,\.]\d{2})',  # Valor a pagar R$: 200,00
            r'[Tt][Oo][Tt][Aa][Ll][\s:]*[Rr]\$?[\s:]*(\d+[,\.]\d{2})',  # Total R$ 200,00
        ]

        for pattern in valor_total_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    resultado['valor_total'] = float(match.group(1).replace(',', '.'))
                    break
                except:
                    continue

        # 3. Fallback: se não encontrou com padrões específicos, usar busca genérica
        if not resultado['valor_litro'] or not resultado['valor_total']:
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
                    # Valor por litro é geralmente menor que 15
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
            r'[Nn][úu]mero[\s:]*(\d{6,})',  # Número: 1148298 (PRIORIDADE ALTA)
            r'[Nn][Ff][Cc][-\s]?[Ee]:?\s*(\d+)',  # NFC-e: 000893951
            r'[Cc]upom[\s:]*[Nn]?[º°]?[\s:]*(\d{5,})',  # Cupom: 123456 ou Cupom Nº 123456
            r'[Nn]ota[\s:]*[Ff]?[Ii]?[Ss]?[Cc]?[Aa]?[Ll]?[\s:]*[Nn]?[úuº°]?[Mm]?[Ee]?[Rr]?[Oo]?[\s:]*(\d{5,})',  # Nota Fiscal Nº 123456
            r'[Cc][Oo][Oo]:?\s*(\d{5,})',  # COO: 123456
            r'[Dd][Oo][Cc](?:umento)?[\s:]*(\d{5,})',  # DOC: 123456 ou Documento: 123456
            r'[Nn][Ff][\s:-]*(\d{5,})',  # NF-123456 ou NF: 123456
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                numero = match.group(1)
                # Filtrar números muito longos que podem ser CNPJ, chave de acesso, etc
                if len(numero) <= 10:
                    return numero

        return None

    def _extract_placa(self, text: str) -> Optional[str]:
        """Extrai placa do veículo do cupom"""
        # Padrões de placa brasileira (ABC1234 ou ABC1D23)
        patterns = [
            r'[Pp][Ll][Aa][Cc][Aa][\s:;]+([A-Z]{3}[0-9][A-Z0-9][0-9]{2})',  # PLACA: KPG7I19 ou PLACA: ABC1234
            r'[Pp][Ll][Aa][Cc][Aa][\s:;]+([A-Z]{3}[-\s]?[0-9]{4})',  # PLACA: ABC-1234 ou PLACA: ABC1234
            r'[Vv][Ee][Ii][Cc](?:ulo)?[\s:]+[Pp][Ll][Aa][Cc][Aa][\s:]+([A-Z]{3}[0-9][A-Z0-9][0-9]{2})',  # Veículo Placa: KPG7I19
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                placa = match.group(1).replace('-', '').replace(' ', '').upper()
                # Validar formato de placa (7 caracteres)
                if len(placa) == 7:
                    return placa

        return None

    def _extract_odometro(self, text: str) -> Optional[int]:
        """Extrai odômetro (KM) do veículo do cupom"""
        patterns = [
            r'[Kk][Mm][\s:;]+(\d{3,7})',  # KM: 508870 ou KM:508870
            r'[Oo][Dd][Oo][Mm][Ee][Tt][Rr][Oo][\s:]+(\d{3,7})',  # Odometro: 508870
            r'[Qq][Uu][Ii][Ll][Oo][Mm][Ee][Tt][Rr][Aa][Gg][Ee][Mm][\s:]+(\d{3,7})',  # Quilometragem: 508870
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    km = int(match.group(1))
                    # Validar se é um valor razoável (entre 0 e 9.999.999 km)
                    if 0 <= km <= 9999999:
                        return km
                except:
                    continue

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
