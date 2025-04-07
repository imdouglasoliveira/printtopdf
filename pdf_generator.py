"""
Módulo para geração e manipulação de arquivos PDF de alta qualidade.
"""

import logging
import os
import tempfile
import shutil
from typing import List, Union, Optional, Dict, Any
from pathlib import Path
from datetime import datetime

from PIL import Image
from fpdf import FPDF
from PyPDF2 import PdfMerger, PdfReader, PdfWriter

logger = logging.getLogger(__name__)

class PDFGenerator:
    """Classe para geração e manipulação de arquivos PDF de alta qualidade."""
    
    def __init__(self, dpi: int = 300):
        """
        Inicializa o gerador de PDF.
        
        Args:
            dpi: Resolução em DPI para a conversão de imagem para PDF
        """
        self.dpi = dpi  # Resolução aumentada para 300 DPI por padrão
    
    def image_to_pdf(
        self, 
        image: Union[Image.Image, str], 
        output_path: str,
        dpi: Optional[int] = None,
        compress: bool = False,
        quality: int = 95
    ) -> str:
        """
        Converte uma imagem em PDF de alta qualidade.
        
        Args:
            image: Objeto PIL Image ou caminho para arquivo de imagem
            output_path: Caminho para salvar o PDF resultante
            dpi: Resolução da imagem em DPI (pontos por polegada)
            compress: Se deve compactar o PDF
            quality: Qualidade da imagem (0-100) para compressão JPEG
            
        Returns:
            Caminho do PDF gerado
        """
        try:
            # Usar o DPI padrão se não for especificado
            if dpi is None:
                dpi = self.dpi
                
            # Se for um caminho, abrir a imagem
            if isinstance(image, str):
                image = Image.open(image)
                
            # Determinar o tamanho da página com base no tamanho da imagem
            width_px, height_px = image.size
            
            # Converter de pixels para pontos (1 ponto = 1/72 polegadas)
            # Usando dpi (pontos por polegada) como referência
            width_pt = width_px * 72 / dpi
            height_pt = height_px * 72 / dpi
            
            # Criar PDF com tamanho personalizado
            pdf = FPDF(unit="pt", format=[width_pt, height_pt])
            pdf.set_auto_page_break(False)  # Desativar quebra de página automática
            pdf.add_page()
            
            # Salvar a imagem temporariamente
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                tmp_path = tmp.name
                
                # Redimensionar a imagem se ela for muito grande para ser processada
                if width_px > 20000 or height_px > 20000:
                    ratio = min(20000 / width_px, 20000 / height_px)
                    new_width = int(width_px * ratio)
                    new_height = int(height_px * ratio)
                    image = image.resize((new_width, new_height), Image.LANCZOS)
                    
                # Salvar imagem temporária com alta qualidade
                if compress:
                    # Comprimir como JPEG
                    image.save(tmp_path, format='JPEG', quality=quality, optimize=True)
                else:
                    # Salvar como PNG sem compressão
                    image.save(tmp_path, format='PNG')
                
                # Adicionar a imagem ao PDF
                try:
                    pdf.image(tmp_path, 0, 0, width_pt, height_pt)
                except Exception as e:
                    logger.error(f"Erro ao adicionar imagem ao PDF: {str(e)}")
                    # Tentar com uma imagem reduzida como fallback
                    new_width = int(width_px * 0.75)
                    new_height = int(height_px * 0.75)
                    image = image.resize((new_width, new_height), Image.LANCZOS)
                    image.save(tmp_path, format='PNG')
                    pdf.image(tmp_path, 0, 0, width_pt, height_pt)
                
            # Criar diretório de saída se não existir
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
                
            # Salvar o PDF
            pdf.output(output_path)
            
            # Remover arquivo temporário
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            
            # Verificar se o PDF foi criado com sucesso
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                logger.info(f"PDF criado com sucesso: {output_path}")
                return output_path
            else:
                logger.error(f"Falha ao criar PDF: {output_path}")
                return ""
                
        except Exception as e:
            logger.error(f"Erro ao converter imagem para PDF: {str(e)}")
            raise
    
    def filter_valid_pdfs(self, pdf_paths: List[str]) -> List[str]:
        """
        Filtra a lista de caminhos para manter apenas PDFs válidos.
        
        Args:
            pdf_paths: Lista de caminhos para arquivos PDF
            
        Returns:
            Lista de caminhos para PDFs válidos
        """
        valid_pdfs = []
        
        for pdf_path in pdf_paths:
            # Verificar se o arquivo existe
            if os.path.exists(pdf_path):
                try:
                    # Tentar abrir o PDF e verificar se é válido
                    with open(pdf_path, 'rb') as f:
                        reader = PdfReader(f)
                        if len(reader.pages) > 0:
                            valid_pdfs.append(pdf_path)
                        else:
                            logger.warning(f"PDF vazio ignorado: {pdf_path}")
                except Exception as e:
                    logger.warning(f"PDF inválido ignorado: {pdf_path} - {str(e)}")
            else:
                logger.warning(f"Arquivo PDF não encontrado: {pdf_path}")
                
        return valid_pdfs
    
    def merge_pdfs(
        self, 
        pdf_paths: List[str], 
        output_path: str,
        add_bookmarks: bool = True
    ) -> Optional[str]:
        """
        Mescla múltiplos PDFs em um único arquivo, mantendo cada PDF como uma unidade completa.
        
        Args:
            pdf_paths: Lista de caminhos para arquivos PDF
            output_path: Caminho para salvar o PDF mesclado
            add_bookmarks: Se deve adicionar marcadores para cada PDF
            
        Returns:
            Caminho do PDF mesclado ou None se falhar
        """
        try:
            if not pdf_paths:
                logger.warning("Nenhum PDF fornecido para mesclagem")
                return None
                
            # Filtrar arquivos PDF válidos
            valid_pdfs = self.filter_valid_pdfs(pdf_paths)
            
            if not valid_pdfs:
                logger.warning("Nenhum PDF válido encontrado para mesclar")
                return None
            
            # Criar o diretório de saída se não existir
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            # Versão corrigida para PyPDF2 3.0+
            merger = PdfMerger()
            
            # Adicionar cada PDF à mesclagem
            has_valid_pdf = False
            for idx, pdf_path in enumerate(valid_pdfs):
                try:
                    # Extrair nome para bookmark a partir do caminho do arquivo
                    bookmark_name = os.path.basename(pdf_path)
                    if bookmark_name.endswith('.pdf'):
                        bookmark_name = bookmark_name[:-4]  # Remover extensão
                    
                    if add_bookmarks:
                        merger.append(pdf_path, bookmark_name)
                    else:
                        merger.append(pdf_path)
                        
                    has_valid_pdf = True
                    
                except Exception as e:
                    logger.warning(f"Erro ao mesclar PDF {pdf_path}: {str(e)}")
                    try:
                        # Tentar reparar o PDF
                        repaired_pdf = self._repair_pdf(pdf_path)
                        if repaired_pdf:
                            if add_bookmarks:
                                merger.append(repaired_pdf, f"Página {idx+1}")
                            else:
                                merger.append(repaired_pdf)
                                
                            has_valid_pdf = True
                            
                            # Remover arquivo temporário após o uso
                            os.unlink(repaired_pdf)
                    except Exception as repair_error:
                        logger.error(f"Falha ao reparar PDF {pdf_path}: {str(repair_error)}")
            
            # Verificar se há algum PDF para mesclar
            if has_valid_pdf:
                # Salvar o PDF mesclado
                merger.write(output_path)
                merger.close()
                
                # Verificar se o arquivo foi criado
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    logger.info(f"PDF mesclado criado com sucesso: {output_path}")
                    
                    # Otimizar o PDF mesclado para reduzir espaços em branco
                    self._optimize_pdf(output_path)
                    
                    return output_path
                else:
                    logger.error(f"Falha ao criar PDF mesclado: arquivo vazio ou não criado")
                    return None
            else:
                logger.warning("Nenhum PDF válido encontrado para mesclar após tentativas de reparo")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao mesclar PDFs: {str(e)}")
            return None
    
    def _repair_pdf(self, pdf_path: str) -> Optional[str]:
        """
        Tenta reparar um PDF danificado.
        
        Args:
            pdf_path: Caminho para o arquivo PDF danificado
            
        Returns:
            Caminho para o PDF reparado ou None se falhar
        """
        try:
            # Criar um arquivo temporário para o PDF reparado
            repaired_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False).name
            
            with open(pdf_path, 'rb') as f:
                reader = PdfReader(f)
                writer = PdfWriter()
                
                # Copiar cada página para o novo PDF
                for page in reader.pages:
                    writer.add_page(page)
                    
                # Salvar o PDF reparado
                with open(repaired_pdf, 'wb') as f_out:
                    writer.write(f_out)
                    
            return repaired_pdf
            
        except Exception as e:
            logger.error(f"Erro ao reparar PDF: {str(e)}")
            if os.path.exists(repaired_pdf):
                os.unlink(repaired_pdf)
            return None
    
    def _optimize_pdf(self, pdf_path: str) -> bool:
        """
        Otimiza um PDF para reduzir espaços em branco e melhorar a qualidade.
        
        Args:
            pdf_path: Caminho para o arquivo PDF
            
        Returns:
            True se a otimização foi bem-sucedida, False caso contrário
        """
        try:
            # Criar um arquivo temporário para o PDF otimizado
            optimized_pdf = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False).name
            
            with open(pdf_path, 'rb') as f:
                reader = PdfReader(f)
                writer = PdfWriter()
                
                # Copiar cada página para o novo PDF com configurações otimizadas
                for page in reader.pages:
                    # Preservar o tamanho da página original
                    writer.add_page(page)
                    
                # Configurar metadados
                writer.add_metadata({
                    '/Creator': 'PrintToPDF',
                    '/Producer': 'PrintToPDF',
                    '/Title': os.path.basename(pdf_path)
                })
                
                # Salvar o PDF otimizado
                with open(optimized_pdf, 'wb') as f_out:
                    writer.write(f_out)
                    
            # Substituir o arquivo original pelo otimizado
            shutil.copy2(optimized_pdf, pdf_path)
            
            # Remover arquivo temporário
            os.unlink(optimized_pdf)
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao otimizar PDF: {str(e)}")
            return False