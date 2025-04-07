#!/usr/bin/env python3
"""
PrintToPDF: Ferramenta para capturar screenshots de páginas web de sitemaps XML e convertê-las em PDF.
"""

import os
import sys
import logging
import re
from urllib.parse import urlparse
from pathlib import Path
import shutil
import time
from datetime import datetime

import click
from tqdm import tqdm

# Importações locais (da mesma pasta)
from crawler import WebCrawler
from pdf_generator import PDFGenerator
from sitemap_parser import SitemapParser
from utils import setup_logging, clean_domain_name

# Configurar logging
logger = logging.getLogger(__name__)

@click.command()
@click.option(
    "--urls-file", 
    default="urls.txt", 
    help="Arquivo com lista de URLs de sitemaps XML, um por linha"
)
@click.option(
    "--output-dir", 
    default="results", 
    help="Diretório de saída para os PDFs"
)
@click.option(
    "--headless/--no-headless",
    default=True,
    help="Executar o navegador em modo headless"
)
@click.option(
    "--browser",
    default="firefox", # Firefox por padrão para melhor captura de página completa
    type=click.Choice(["chrome", "firefox"]),
    help="Navegador a ser usado (chrome ou firefox)"
)
@click.option(
    "--wait-time",
    default=45,  # Aumentado para 45 segundos por padrão
    type=int,
    help="Tempo de espera base para carregamento da página (segundos)"
)
@click.option(
    "--extra-wait-for-media",
    default=20,  # 20 segundos extras para mídia
    type=int,
    help="Tempo adicional de espera para páginas com vídeo/GIF (segundos)"
)
@click.option(
    "--clean/--no-clean",
    default=True,
    help="Limpar diretórios antigos antes de iniciar"
)
@click.option(
    "--skip-final-merge/--do-final-merge",
    default=False,
    help="Pular a criação do PDF final com todos os sites"
)
def main(urls_file, output_dir, headless, browser, wait_time, extra_wait_for_media, clean, skip_final_merge):
    """Captura screenshots de alta qualidade de todas as páginas listadas em sitemaps XML e converte para PDF."""
    # Configurar logging com timestamp
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"printtopdf_{timestamp}.log"
    setup_logging(level=logging.INFO, log_file=str(log_file))
    
    logger.info("Iniciando PrintToPDF para Sitemaps XML com configurações de alta qualidade")
    logger.info(f"Configurações: browser={browser}, wait_time={wait_time}s, extra_wait_for_media={extra_wait_for_media}s")
    
    # Verificar se o arquivo de URLs existe
    if not os.path.exists(urls_file):
        logger.error(f"Arquivo {urls_file} não encontrado.")
        click.echo(f"Erro: Arquivo {urls_file} não encontrado.")
        sys.exit(1)
    
    # Criar diretório de saída
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)
    
    # Inicializar o parser de sitemap
    sitemap_parser = SitemapParser()
    
    # Processar o arquivo de URLs de sitemaps
    domain_urls = sitemap_parser.process_urls_file(urls_file)
    
    if not domain_urls:
        logger.error(f"Nenhuma URL encontrada nos sitemaps em {urls_file}")
        click.echo(f"Erro: Nenhuma URL encontrada nos sitemaps em {urls_file}")
        sys.exit(1)
    
    click.echo(f"Processando {len(domain_urls)} domínios...")
    
    # Lista para armazenar todos os PDFs finais para mesclagem global
    all_merged_pdfs = []
    
    # Processar cada domínio e suas URLs
    for domain, urls in domain_urls.items():
        try:
            cleaned_domain = clean_domain_name(domain)
            click.echo(f"\n{'='*80}")
            click.echo(f"Processando domínio: {domain} ({len(urls)} páginas)")
            click.echo(f"{'='*80}")
            
            # Criar diretório para este domínio
            domain_dir = output_path / cleaned_domain
            pages_dir = domain_dir / "pages"
            
            # Limpar diretórios existentes para evitar misturar com capturas anteriores
            if clean and domain_dir.exists():
                click.echo(f"Limpando diretórios anteriores para {cleaned_domain}...")
                shutil.rmtree(domain_dir)
                
            # Criar diretórios para armazenar os PDFs
            domain_dir.mkdir(exist_ok=True, parents=True)
            pages_dir.mkdir(exist_ok=True, parents=True)
            
            # Inicializar o gerador de PDF
            pdf_generator = PDFGenerator()
            
            # Inicializar o crawler uma vez para todo o domínio
            base_url = f"https://{domain}" if not domain.startswith(('http://', 'https://')) else domain
            crawler = WebCrawler(
                base_url=base_url,
                max_depth=0,  # Não fazer crawling, apenas usar as URLs fornecidas
                headless=headless,
                browser=browser,
                wait_time=wait_time,
                extra_wait_for_media=extra_wait_for_media
            )
            
            # Exibir as URLs a serem processadas
            click.echo(f"Processando {len(urls)} URLs do sitemap")
            
            # Capturar screenshots e criar PDFs individuais
            individual_pdfs = []
            
            with tqdm(total=len(urls), desc="Capturando screenshots") as pbar:
                for i, page_url in enumerate(urls):
                    try:
                        # Nome do arquivo PDF para esta página
                        # Usar última parte da URL ou índice se não for específico
                        url_parts = page_url.rstrip('/').split('/')
                        page_name = url_parts[-1] if url_parts[-1] and url_parts[-1] != domain else f"page_{i+1}"
                        
                        # Limpar o nome de arquivo para ser seguro
                        page_name = re.sub(r'[^a-zA-Z0-9]', '_', page_name)
                        if not page_name or page_name == '_':
                            page_name = f"page_{i+1}"
                        
                        # Garantir nomes únicos para evitar sobrescrever
                        pdf_filename = f"{page_name}.pdf"
                        pdf_path = pages_dir / pdf_filename
                        
                        # Se já existe um arquivo com esse nome, adicionar número
                        counter = 1
                        while pdf_path.exists():
                            pdf_filename = f"{page_name}_{counter}.pdf"
                            pdf_path = pages_dir / pdf_filename
                            counter += 1
                        
                        # Atualizar a barra de progresso com o URL atual
                        short_url = page_url.split('/')[-1] if '/' in page_url else page_url
                        if not short_url:
                            short_url = "homepage"
                        pbar.set_description(f"Capturando {short_url}")
                        
                        # Capturar screenshot (página completa com tempo de espera extra)
                        # Garante carregamento total da página antes de capturar
                        screenshot = crawler.capture_screenshot(page_url)
                        
                        # Converter screenshot para PDF
                        pdf_generator.image_to_pdf(screenshot, str(pdf_path))
                        
                        # Verificar se o PDF foi criado corretamente
                        if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
                            individual_pdfs.append(str(pdf_path))
                            logger.info(f"PDF criado com sucesso: {pdf_path}")
                        else:
                            logger.error(f"Falha ao criar PDF para {page_url}")
                        
                    except Exception as e:
                        logger.error(f"Erro ao processar página {page_url}: {str(e)}")
                        click.echo(f"Erro ao processar página {page_url}: {str(e)}")
                    
                    # Atualizar a barra de progresso
                    pbar.update(1)
            
            # Mesclar todos os PDFs em um único arquivo para este domínio
            if individual_pdfs:
                click.echo("Mesclando PDFs individuais...")
                
                # Verificar se há PDFs válidos para mesclar
                valid_pdfs = pdf_generator.filter_valid_pdfs(individual_pdfs)
                
                if valid_pdfs:
                    # Arquivo mesclado para este domínio
                    merged_pdf_path = domain_dir / f"{cleaned_domain}_completo.pdf"
                    
                    # Mesclar PDFs
                    result = pdf_generator.merge_pdfs(valid_pdfs, str(merged_pdf_path))
                    
                    # Verificar se o arquivo foi criado
                    if result and os.path.exists(merged_pdf_path) and os.path.getsize(merged_pdf_path) > 0:
                        # Adicionar à lista de PDFs mesclados para mesclagem global
                        all_merged_pdfs.append(str(merged_pdf_path))
                        click.echo(f"PDF mesclado salvo em: {merged_pdf_path}")
                    else:
                        logger.error(f"Falha ao criar PDF mesclado para {domain}")
                        click.echo(f"Falha ao criar PDF mesclado para {domain}")
                else:
                    click.echo("Nenhum PDF válido encontrado para mesclar")
            
            # Fechar o crawler
            crawler.close()
            
        except Exception as e:
            logger.error(f"Erro ao processar domínio {domain}: {str(e)}")
            click.echo(f"Erro ao processar domínio {domain}: {str(e)}")
    
    # Criar um PDF final com todas as páginas de todos os domínios
    if all_merged_pdfs and not skip_final_merge:
        click.echo("\nCriando PDF final com todos os domínios...")
        final_pdf_path = output_path / "todos_os_sites.pdf"
        
        try:
            # Verificar se temos PDFs válidos
            valid_merged_pdfs = []
            for pdf_path in all_merged_pdfs:
                if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
                    valid_merged_pdfs.append(pdf_path)
                else:
                    logger.warning(f"PDF inválido ou vazio ignorado: {pdf_path}")
            
            if valid_merged_pdfs:
                pdf_generator = PDFGenerator()
                result = pdf_generator.merge_pdfs(valid_merged_pdfs, str(final_pdf_path))
                
                if result and os.path.exists(final_pdf_path) and os.path.getsize(final_pdf_path) > 0:
                    click.echo(f"PDF final com todos os domínios salvo em: {final_pdf_path}")
                else:
                    logger.error("Falha ao criar PDF final com todos os domínios")
                    click.echo("Falha ao criar PDF final com todos os domínios")
            else:
                logger.warning("Nenhum PDF válido encontrado para criar o PDF final")
                click.echo("Nenhum PDF válido encontrado para criar o PDF final")
        except Exception as e:
            logger.error(f"Erro ao criar PDF final: {str(e)}")
            click.echo(f"Erro ao criar PDF final: {str(e)}")
    
    click.echo("\nProcessamento concluído!")
    click.echo(f"Todos os PDFs estão disponíveis na pasta: {output_path.absolute()}")
    click.echo("Os arquivos estão organizados por domínio dentro da pasta 'results'")
    click.echo("Cada domínio tem sua pasta com:")
    click.echo("  - Uma subpasta 'pages' contendo PDFs individuais para cada página")
    click.echo("  - Um arquivo PDF mesclado com todas as páginas do domínio")
    if os.path.exists(output_path / "todos_os_sites.pdf"):
        click.echo("Além disso, foi criado um PDF final com todos os domínios: todos_os_sites.pdf")

if __name__ == "__main__":
    # Isso permite executar o script diretamente
    main()