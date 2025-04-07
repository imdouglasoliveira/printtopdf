"""
Módulo para processamento de arquivos sitemap XML e extração de URLs.
"""

import logging
import requests
from typing import List, Set, Optional
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class SitemapParser:
    """Parser para extrair URLs de arquivos sitemap XML."""
    
    def __init__(self, timeout: int = 30):
        """
        Inicializa o parser de sitemap.
        
        Args:
            timeout: Tempo limite para requisições em segundos
        """
        self.timeout = timeout
        
    def is_sitemap_url(self, url: str) -> bool:
        """
        Verifica se a URL parece ser um sitemap XML.
        
        Args:
            url: URL para verificar
            
        Returns:
            True se parece ser um sitemap, False caso contrário
        """
        lower_url = url.lower()
        return (
            "sitemap" in lower_url and 
            (".xml" in lower_url or lower_url.endswith("/sitemap"))
        )
    
    def extract_urls_from_sitemap(self, sitemap_url: str) -> List[str]:
        """
        Extrai URLs de um arquivo sitemap XML.
        
        Args:
            sitemap_url: URL do arquivo sitemap
            
        Returns:
            Lista de URLs encontradas no sitemap
        """
        try:
            logger.info(f"Processando sitemap: {sitemap_url}")
            
            # Fazer requisição para obter o conteúdo do sitemap
            response = requests.get(sitemap_url, timeout=self.timeout)
            response.raise_for_status()
            
            # Verificar se é um arquivo XML
            content_type = response.headers.get('content-type', '').lower()
            if 'xml' not in content_type and 'text' not in content_type:
                logger.warning(f"Conteúdo não é XML: {content_type}")
                return []
                
            # Analisar o XML
            root = ET.fromstring(response.content)
            
            # Determinar o tipo de sitemap (padrão ou índice)
            # Verificar namespaces
            namespaces = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            urls = []
            
            # Verificar se é um índice de sitemaps (contém <sitemap> tags)
            sitemaps = root.findall('.//sm:sitemap/sm:loc', namespaces)
            if sitemaps:
                logger.info(f"Sitemap índice detectado com {len(sitemaps)} sub-sitemaps")
                
                # Processar cada sub-sitemap recursivamente
                for sitemap in sitemaps:
                    sub_sitemap_url = sitemap.text.strip() if sitemap.text else ""
                    if sub_sitemap_url:
                        sub_urls = self.extract_urls_from_sitemap(sub_sitemap_url)
                        urls.extend(sub_urls)
                        
            else:
                # É um sitemap regular (contém <url> tags)
                url_elements = root.findall('.//sm:url/sm:loc', namespaces)
                if not url_elements:
                    # Tentar sem namespace (alguns sitemaps não usam)
                    url_elements = root.findall('.//url/loc')
                
                # Extrair URLs
                for url_elem in url_elements:
                    url = url_elem.text.strip() if url_elem.text else ""
                    if url:
                        urls.append(url)
                
                logger.info(f"Extraídas {len(urls)} URLs do sitemap")
            
            return urls
            
        except requests.RequestException as e:
            logger.error(f"Erro ao acessar sitemap {sitemap_url}: {str(e)}")
            return []
        except ET.ParseError as e:
            logger.error(f"Erro ao analisar XML de {sitemap_url}: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Erro ao processar sitemap {sitemap_url}: {str(e)}")
            return []
    
    def extract_domain_from_url(self, url: str) -> str:
        """
        Extrai o domínio de uma URL.
        
        Args:
            url: URL para extrair o domínio
            
        Returns:
            Domínio extraído
        """
        parsed = urlparse(url)
        return parsed.netloc
    
    def process_urls_file(self, file_path: str) -> dict:
        """
        Processa um arquivo contendo URLs de sitemaps.
        
        Args:
            file_path: Caminho para o arquivo com URLs
            
        Returns:
            Dicionário com domínios como chaves e listas de URLs como valores
        """
        try:
            with open(file_path, 'r') as f:
                sitemap_urls = [line.strip() for line in f if line.strip()]
                
            results = {}
            
            for sitemap_url in sitemap_urls:
                # Verificar se é um sitemap
                if not self.is_sitemap_url(sitemap_url):
                    logger.warning(f"URL não parece ser um sitemap: {sitemap_url}")
                    continue
                    
                # Extrair URLs do sitemap
                page_urls = self.extract_urls_from_sitemap(sitemap_url)
                
                if page_urls:
                    # Usar o domínio como chave
                    domain = self.extract_domain_from_url(sitemap_url)
                    
                    if domain in results:
                        # Adicionar URLs à lista existente
                        results[domain].extend(page_urls)
                        # Remover duplicatas
                        results[domain] = list(set(results[domain]))
                    else:
                        # Criar nova entrada
                        results[domain] = page_urls
            
            return results
            
        except Exception as e:
            logger.error(f"Erro ao processar arquivo de URLs: {str(e)}")
            return {}