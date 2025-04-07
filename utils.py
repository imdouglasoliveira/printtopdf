"""
Módulo com funções utilitárias para o projeto PrintToPDF.
"""

import os
import sys
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Union

def setup_logging(
    level: int = logging.INFO,
    log_file: Union[str, None] = None
) -> None:
    """
    Configura o sistema de logging.
    
    Args:
        level: Nível de logging (padrão: INFO)
        log_file: Arquivo de log opcional
    """
    # Formato personalizado
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Configurar handlers
    handlers = [logging.StreamHandler(sys.stdout)]
    
    if log_file:
        # Criar diretório para o arquivo de log se não existir
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        # Adicionar handler de arquivo
        handlers.append(logging.FileHandler(log_file))
    
    # Configurar logging
    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=handlers
    )

def clean_domain_name(domain: str) -> str:
    """
    Limpa o nome do domínio para uso como nome de diretório.
    
    Args:
        domain: Nome do domínio
        
    Returns:
        Nome do domínio limpo
    """
    # Remover 'www.' se presente
    domain = domain.lower()
    if domain.startswith('www.'):
        domain = domain[4:]
        
    # Remover caracteres inválidos
    domain = re.sub(r'[^a-z0-9.-]', '_', domain)
    
    return domain

def create_timestamp() -> str:
    """
    Cria uma string de timestamp para uso em nomes de arquivo.
    
    Returns:
        String de timestamp formatada
    """
    return datetime.now().strftime('%Y%m%d_%H%M%S')

def ensure_dir(directory: Union[str, Path]) -> str:
    """
    Garante que um diretório exista, criando-o se necessário.
    
    Args:
        directory: Caminho do diretório
        
    Returns:
        Caminho absoluto do diretório
    """
    if isinstance(directory, str):
        directory = Path(directory)
        
    # Criar diretório se não existir
    directory.mkdir(parents=True, exist_ok=True)
    
    return str(directory.absolute())

def get_file_extension(file_path: str) -> str:
    """
    Obtém a extensão de um arquivo.
    
    Args:
        file_path: Caminho do arquivo
        
    Returns:
        Extensão do arquivo (sem o ponto)
    """
    return os.path.splitext(file_path)[1].lstrip('.')

def is_image_file(file_path: str) -> bool:
    """
    Verifica se um arquivo é uma imagem com base na extensão.
    
    Args:
        file_path: Caminho do arquivo
        
    Returns:
        True se for uma imagem, False caso contrário
    """
    image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']
    extension = get_file_extension(file_path).lower()
    return extension in image_extensions

def is_pdf_file(file_path: str) -> bool:
    """
    Verifica se um arquivo é um PDF com base na extensão.
    
    Args:
        file_path: Caminho do arquivo
        
    Returns:
        True se for um PDF, False caso contrário
    """
    return get_file_extension(file_path).lower() == 'pdf'