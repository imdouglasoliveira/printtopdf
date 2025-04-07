"""
Versão melhorada do módulo de crawler para garantir carregamento completo da página antes de capturar screenshots.
"""

import logging
import time
import tempfile
import hashlib
from urllib.parse import urlparse, urljoin, urldefrag
from typing import List, Set, Optional, Tuple, Dict
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.common.exceptions import WebDriverException, TimeoutException, JavascriptException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
from io import BytesIO

logger = logging.getLogger(__name__)

class WebCrawler:
    """Crawler aprimorado para garantir carregamento completo da página antes de capturar screenshots."""
    
    def __init__(
        self, 
        base_url: str, 
        max_depth: int = 0,  # Definido para 0 por padrão, pois vamos usar apenas URLs de sitemap
        headless: bool = True,
        browser: str = "firefox",
        wait_time: int = 45,  # Aumentado para 45 segundos por padrão
        extra_wait_for_media: int = 20,  # Aumentado para 20 segundos extras para mídias
        page_load_timeout: int = 180  # Timeout de 3 minutos para carregamento de página
    ):
        """
        Inicializa o crawler.
        
        Args:
            base_url: URL base do site
            max_depth: Profundidade máxima de crawling (0 = usar apenas URLs fornecidas)
            headless: Se o navegador deve ser executado em modo headless
            browser: Navegador a ser usado ('chrome' ou 'firefox')
            wait_time: Tempo de espera para carregamento da página (segundos)
            extra_wait_for_media: Tempo adicional de espera para páginas com elementos multimídia
            page_load_timeout: Timeout de carregamento de página em segundos
        """
        self.base_url = base_url
        self.max_depth = max_depth
        self.headless = headless
        self.browser_type = browser
        self.wait_time = wait_time
        self.extra_wait_for_media = extra_wait_for_media
        self.page_load_timeout = page_load_timeout
        self.visited_urls: Set[str] = set()
        self.content_hashes: Dict[str, str] = {}  # Rastreamento de conteúdo para evitar duplicação
        self.domain = urlparse(base_url).netloc
        
        # Inicializar o driver do navegador
        self.driver = self._init_browser()
        
    def _init_browser(self) -> webdriver.Remote:
        """Inicializa o navegador com as configurações apropriadas."""
        try:
            if self.browser_type.lower() == "chrome":
                options = ChromeOptions()
                if self.headless:
                    options.add_argument("--headless=new")
                
                # Configurações para captura de página completa
                options.add_argument("--window-size=1920,1080")
                options.add_argument("--disable-gpu")
                options.add_argument("--disable-extensions")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                
                # Melhorias para captura de alta qualidade
                options.add_argument("--force-device-scale-factor=1")
                options.add_argument("--high-dpi-support=1")
                
                # Otimizações para melhor renderização de vídeo
                options.add_argument("--autoplay-policy=no-user-gesture-required")
                
                # Preferir Chrome já instalado, caso contrário baixar automaticamente
                try:
                    service = ChromeService()
                    driver = webdriver.Chrome(service=service, options=options)
                except Exception as e:
                    logger.warning(f"Erro ao inicializar Chrome padrão: {str(e)}")
                    from webdriver_manager.chrome import ChromeDriverManager
                    service = ChromeService(ChromeDriverManager().install())
                    driver = webdriver.Chrome(service=service, options=options)
                
            else:  # Firefox como fallback ou opção preferida
                options = FirefoxOptions()
                if self.headless:
                    options.add_argument("--headless")
                options.add_argument("--width=1920")
                options.add_argument("--height=1080")
                
                # Configurações para melhor renderização de vídeo
                options.set_preference("media.autoplay.default", 0)
                options.set_preference("media.autoplay.enabled", True)
                
                # Alta qualidade
                options.set_preference("layout.css.devPixelsPerPx", "1.0")
                
                # Configurações adicionais para garantir carregamento completo
                options.set_preference("network.http.connection-timeout", 60)
                options.set_preference("network.http.connection-retry-timeout", 60)
                options.set_preference("dom.max_script_run_time", 60)
                
                # Preferir Firefox já instalado, caso contrário baixar automaticamente
                try:
                    service = FirefoxService()
                    driver = webdriver.Firefox(service=service, options=options)
                except Exception as e:
                    logger.warning(f"Erro ao inicializar Firefox padrão: {str(e)}")
                    from webdriver_manager.firefox import GeckoDriverManager
                    service = FirefoxService(GeckoDriverManager().install())
                    driver = webdriver.Firefox(service=service, options=options)
                
            # Configurar timeouts 
            driver.set_page_load_timeout(self.page_load_timeout)
            driver.implicitly_wait(15)
            
            return driver
        
        except Exception as e:
            logger.error(f"Erro ao inicializar o navegador: {str(e)}")
            raise

    def _is_resource_url(self, url: str) -> bool:
        """
        Verifica se a URL é um recurso estático (imagem, CSS, JS, etc.) que não deve ser capturado.
        
        Args:
            url: URL para verificar
            
        Returns:
            True se for um recurso estático, False caso contrário
        """
        static_extensions = [
            '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.ico', '.webp',
            '.css', '.js', '.json', '.xml', '.pdf', '.doc', '.docx', '.xls', '.xlsx',
            '.zip', '.rar', '.tar', '.gz', '.mp3', '.mp4', '.avi', '.mov', '.wmv',
            '.woff', '.woff2', '.ttf', '.eot', '.otf'
        ]
        
        parsed_url = urlparse(url)
        path = parsed_url.path.lower()
        
        for ext in static_extensions:
            if path.endswith(ext):
                return True
        
        static_dirs = [
            '/wp-content/uploads/', '/images/', '/img/', '/css/', '/js/',
            '/assets/', '/static/', '/media/', '/fonts/', '/downloads/'
        ]
        
        for directory in static_dirs:
            if directory in path:
                return True
        
        return False
    
    def discover_pages(self) -> List[str]:
        """
        Esta função não é mais necessária, pois agora usamos URLs diretamente dos sitemaps.
        Mantida apenas para compatibilidade.
        
        Returns:
            Lista vazia
        """
        logger.warning("Método discover_pages() não é usado com sitemaps.")
        return []
    
    def _get_page_dimensions(self) -> Tuple[int, int]:
        """
        Obtém as dimensões completas da página, incluindo conteúdo que requer rolagem.
        
        Returns:
            Tupla com (largura, altura) em pixels
        """
        total_height = self.driver.execute_script("""
            return Math.max(
                document.body.scrollHeight, 
                document.body.offsetHeight, 
                document.documentElement.clientHeight, 
                document.documentElement.scrollHeight, 
                document.documentElement.offsetHeight
            );
        """)
        
        total_width = self.driver.execute_script("""
            return Math.max(
                document.body.scrollWidth, 
                document.body.offsetWidth, 
                document.documentElement.clientWidth, 
                document.documentElement.scrollWidth, 
                document.documentElement.offsetWidth
            );
        """)
        
        return (total_width, total_height)
    
    def _has_media_elements(self) -> bool:
        """
        Verifica se a página contém elementos de mídia como vídeos ou GIFs.
        
        Returns:
            True se encontrar elementos de mídia, False caso contrário
        """
        try:
            has_videos = self.driver.execute_script("""
                return document.querySelectorAll('video, iframe[src*="youtube"], iframe[src*="vimeo"]').length > 0;
            """)
            
            has_gifs = self.driver.execute_script("""
                var images = document.getElementsByTagName('img');
                for (var i = 0; i < images.length; i++) {
                    if (images[i].src.toLowerCase().endsWith('.gif')) {
                        return true;
                    }
                }
                return false;
            """)
            
            has_animations = self.driver.execute_script("""
                var elements = document.querySelectorAll('[class*="animate"], [class*="slider"], [class*="carousel"], [class*="banner"]');
                return elements.length > 0;
            """)
            
            return has_videos or has_gifs or has_animations
            
        except Exception as e:
            logger.warning(f"Erro ao verificar elementos de mídia: {str(e)}")
            return False
    
    def _wait_for_page_load_completion(self):
        """
        Aguarda até que a página esteja completamente carregada,
        com checagens adicionais para garantir que todos os recursos estão carregados.
        """
        try:
            WebDriverWait(self.driver, 60).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
        except TimeoutException:
            logger.warning("Timeout aguardando document.readyState='complete'")
        
        try:
            self.driver.execute_script("""
                return new Promise((resolve) => {
                    var images = document.getElementsByTagName('img');
                    var loaded = 0;
                    var total = images.length;
                    if (total === 0) {
                        resolve(true);
                        return;
                    }
                    function checkImage(img) {
                        if (img.complete) {
                            loaded++;
                            if (loaded >= total) {
                                resolve(true);
                            }
                        } else {
                            img.addEventListener('load', function() {
                                loaded++;
                                if (loaded >= total) {
                                    resolve(true);
                                }
                            });
                            
                            img.addEventListener('error', function() {
                                loaded++;
                                if (loaded >= total) {
                                    resolve(true);
                                }
                            });
                        }
                    }
                    for (var i = 0; i < images.length; i++) {
                        checkImage(images[i]);
                    }
                    setTimeout(function() {
                        resolve(true);
                    }, 30000);
                });
            """)
        except Exception as e:
            logger.warning(f"Erro ao aguardar carregamento de imagens: {str(e)}")
        
        try:
            self.driver.execute_script("""
                var checkLoading = function() {
                    var loaders = document.querySelectorAll(
                        '.loading, .loader, [class*="loading"], [class*="loader"], [class*="progress"], .spinner'
                    );
                    
                    for(var i = 0; i < loaders.length; i++) {
                        var display = window.getComputedStyle(loaders[i]).display;
                        var visibility = window.getComputedStyle(loaders[i]).visibility;
                        var opacity = window.getComputedStyle(loaders[i]).opacity;
                        
                        if(display !== 'none' && visibility !== 'hidden' && opacity !== '0') {
                            return false;
                        }
                    }
                    return true;
                };
                
                var startTime = new Date().getTime();
                while(!checkLoading()) {
                    if(new Date().getTime() - startTime > 15000) {
                        break;
                    }
                    new Promise(r => setTimeout(r, 500));
                }
            """)
        except Exception as e:
            logger.warning(f"Erro ao verificar elementos de carregamento: {str(e)}")
            
        try:
            previous_height = -1
            current_height = self.driver.execute_script("return document.body.scrollHeight")
            start_time = time.time()
            while previous_height != current_height and time.time() - start_time < 10:
                previous_height = current_height
                time.sleep(1)
                current_height = self.driver.execute_script("return document.body.scrollHeight")
            logger.debug(f"Altura da página estabilizada em {current_height}px")
        except Exception as e:
            logger.warning(f"Erro ao verificar estabilidade da altura da página: {str(e)}")
            
        try:
            self.driver.execute_script("""
                return new Promise((resolve) => {
                    if (typeof jQuery !== 'undefined') {
                        function checkAjax() {
                            if (jQuery.active === 0) {
                                resolve(true);
                                return;
                            }
                            setTimeout(checkAjax, 500);
                        }
                        checkAjax();
                    } else {
                        resolve(true);
                    }
                    setTimeout(function() {
                        resolve(true);
                    }, 10000);
                });
            """)
        except Exception as e:
            logger.warning(f"Erro ao verificar requisições AJAX: {str(e)}")
    
    def _pause_videos_and_animations(self):
        """
        Pausa vídeos e animações na página, além de ajustar elementos fixos/sticky
        para posição absoluta, mantendo a localização original.
        """
        try:
            self.driver.execute_script("""
                // Pausar vídeos
                var videos = document.querySelectorAll('video');
                for(var i = 0; i < videos.length; i++) {
                    try {
                        videos[i].pause();
                        videos[i].currentTime = 0;
                    } catch(e) {}
                }
                
                // Pausar iframes de vídeo (YouTube, Vimeo, etc.)
                var iframes = document.querySelectorAll('iframe[src*="youtube"], iframe[src*="vimeo"]');
                for(var i = 0; i < iframes.length; i++) {
                    try {
                        var iframe = iframes[i];
                        var src = iframe.getAttribute('src');
                        if(src.indexOf('youtube') > -1) {
                            if(src.indexOf('?') > -1) {
                                iframe.setAttribute('src', src + '&autoplay=0&controls=0');
                            } else {
                                iframe.setAttribute('src', src + '?autoplay=0&controls=0');
                            }
                        } else if(src.indexOf('vimeo') > -1) {
                            if(src.indexOf('?') > -1) {
                                iframe.setAttribute('src', src + '&autoplay=0');
                            } else {
                                iframe.setAttribute('src', src + '?autoplay=0');
                            }
                        }
                    } catch(e) {}
                }
                
                // Pausar carrosséis e sliders
                var carousels = document.querySelectorAll('.carousel, .slider, [class*="carousel"], [class*="slider"], [class*="banner"]');
                for(var i = 0; i < carousels.length; i++) {
                    carousels[i].style.animationPlayState = 'paused';
                    carousels[i].style.webkitAnimationPlayState = 'paused';
                }
                
                // Injetar estilo para pausar animações CSS
                var styleSheet = document.createElement('style');
                styleSheet.type = 'text/css';
                styleSheet.innerText = '* { animation-play-state: paused !important; -webkit-animation-play-state: paused !important; transition: none !important; }';
                document.head.appendChild(styleSheet);
                
                // Remover pop-ups, banners, etc.
                var elementsToRemove = document.querySelectorAll(
                    '.cookie-banner, .popup, .modal, .notification-bar, .toast, .overlay, [class*="cookie"], [class*="popup"], [class*="modal"], [class*="notification"], [class*="overlay"], [class*="toast"]'
                );
                for(var i = 0; i < elementsToRemove.length; i++) {
                    elementsToRemove[i].style.display = 'none';
                }
                
                // Ajustar elementos fixos/sticky para posição absoluta,
                // mantendo a posição original na página
                var fixedElements = document.querySelectorAll(
                    'header, footer, nav, .header, .footer, .nav, [class*="header"], [class*="footer"], [class*="navigation"], [class*="navbar"], [class*="nav-bar"], .fixed, .sticky'
                );
                
                for(var i = 0; i < fixedElements.length; i++) {
                    var element = fixedElements[i];
                    var style = window.getComputedStyle(element);
                    if(style.position === 'fixed' || style.position === 'sticky') {
                        var rect = element.getBoundingClientRect();
                        var currentTop = rect.top + window.scrollY;
                        var currentLeft = rect.left + window.scrollX;
                        
                        element.style.position = 'absolute';
                        element.style.top = currentTop + 'px';
                        element.style.left = currentLeft + 'px';
                        element.style.width = rect.width + 'px';
                        // Ajustar z-index se necessário
                        element.style.zIndex = '1';
                    }
                }
            """)
        except JavascriptException as e:
            logger.warning(f"Erro ao tentar pausar vídeos ou ajustar elementos fixos: {str(e)}")
    
    def _scroll_page_and_wait(self, wait_after_scroll=60):
        """
        Rola a página até o final e aguarda um período extra para garantir que todos
        os elementos sejam carregados.
        
        Args:
            wait_after_scroll: Tempo de espera em segundos após o scroll (padrão 60s)
        """
        try:
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            while True:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
            time.sleep(wait_after_scroll)
        except Exception as e:
            logger.warning(f"Erro ao realizar scroll e espera: {str(e)}")
    
    def capture_screenshot(self, url: str) -> Image.Image:
        """
        Captura um screenshot da página completa, incluindo todo o conteúdo que requer rolagem.
        Aguarda carregamento completo e trata elementos de mídia.
        
        Args:
            url: URL da página para capturar
            
        Returns:
            Objeto PIL Image com o screenshot
        """
        if self._is_resource_url(url):
            logger.info(f"Ignorando captura de recurso estático: {url}")
            return Image.new('RGB', (1, 1), color='white')
            
        try:
            logger.info(f"Iniciando captura de screenshot de {url}")
            self.driver.get(url)
            
            # Aguarda carregamento inicial
            time.sleep(self.wait_time)
            
            # Executa o scroll completo e aguarda 60 segundos após o scroll
            self._scroll_page_and_wait(wait_after_scroll=60)
            
            # Pausa vídeos, animações e ajusta elementos fixos
            logger.info("Pausando vídeos, animações e ajustando elementos fixos")
            self._pause_videos_and_animations()
            
            time.sleep(2)
            
            if self.browser_type.lower() == "firefox":
                try:
                    logger.info("Usando captura nativa do Firefox para página completa")
                    screenshot_bytes = self.driver.get_full_page_screenshot_as_png()
                    image = Image.open(BytesIO(screenshot_bytes))
                    logger.info(f"Screenshot capturado com dimensões: {image.size}")
                    return image
                except Exception as e:
                    logger.warning(f"Erro ao usar captura nativa do Firefox: {str(e)}")
            
            total_width, total_height = self._get_page_dimensions()
            logger.info(f"Dimensões da página: {total_width}x{total_height}px")
            
            view_height = min(total_height, 16000)
            self.driver.set_window_size(total_width, view_height)
            
            time.sleep(2)
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
            if total_height > 15000 or (total_width > 1920 and total_height > 10000):
                logger.info("Página muito longa, usando método de costura de screenshots")
                return self._capture_full_screenshot_with_stitching(total_width, total_height)
            
            logger.info("Capturando screenshot completo")
            screenshot_bytes = self.driver.get_screenshot_as_png()
            image = Image.open(BytesIO(screenshot_bytes))
            
            img_width, img_height = image.size
            logger.info(f"Dimensões do screenshot: {img_width}x{img_height}px")
            
            if img_height < total_height * 0.9:
                logger.info("Captura simples insuficiente. Tentando método de costura.")
                return self._capture_full_screenshot_with_stitching(total_width, total_height)
            
            return image
                
        except TimeoutException:
            logger.warning(f"Timeout ao carregar {url}, tentando novamente com tempo maior")
            self.driver.set_page_load_timeout(240)
            self.driver.get(url)
            time.sleep(self.wait_time * 2)
            self._pause_videos_and_animations()
            total_width, total_height = self._get_page_dimensions()
            self.driver.set_window_size(total_width, min(total_height, 15000))
            time.sleep(2)
            screenshot_bytes = self.driver.get_screenshot_as_png()
            self.driver.set_page_load_timeout(self.page_load_timeout)
            image = Image.open(BytesIO(screenshot_bytes))
            return image
            
        except WebDriverException as e:
            logger.error(f"Erro do WebDriver ao capturar screenshot de {url}: {str(e)}")
            logger.info("Reiniciando o WebDriver devido a erro")
            self.close()
            self.driver = self._init_browser()
            self.driver.get(url)
            time.sleep(self.wait_time * 2)
            self._pause_videos_and_animations()
            total_width, total_height = self._get_page_dimensions()
            self.driver.set_window_size(total_width, min(total_height, 15000))
            time.sleep(2)
            screenshot_bytes = self.driver.get_screenshot_as_png()
            image = Image.open(BytesIO(screenshot_bytes))
            return image
            
        except Exception as e:
            logger.error(f"Erro ao capturar screenshot de {url}: {str(e)}")
            return Image.new('RGB', (1920, 1080), color='white')
    
    def _capture_full_screenshot_with_stitching(self, total_width: int, total_height: int) -> Image.Image:
        """
        Captura uma página completa usando o método de tirar múltiplos screenshots e costurá-los.
        
        Args:
            total_width: Largura total da página
            total_height: Altura total da página
            
        Returns:
            Imagem completa da página
        """
        logger.info(f"Iniciando captura com costura para página de dimensões {total_width}x{total_height}px")
        
        viewport_width = min(1920, total_width)
        viewport_height = 1080
        
        self.driver.set_window_size(viewport_width, viewport_height)
        time.sleep(2)
        
        full_screenshot = Image.new('RGB', (total_width, total_height))
        
        offset = 0
        last_scrolled_pos = -1
        overlap = 300
        
        while offset < total_height:
            self.driver.execute_script(f"window.scrollTo(0, {offset});")
            time.sleep(1)
            
            current_scroll_position = self.driver.execute_script("return window.pageYOffset;")
            
            if current_scroll_position == last_scrolled_pos:
                logger.info(f"Fim da página detectado em {current_scroll_position}px")
                break
                
            last_scrolled_pos = current_scroll_position
            
            screenshot_bytes = self.driver.get_screenshot_as_png()
            screenshot = Image.open(BytesIO(screenshot_bytes))
            
            full_screenshot.paste(screenshot, (0, current_scroll_position))
            logger.debug(f"Screenshot parcial colado em y={current_scroll_position}px")
            
            offset += viewport_height - overlap
            
            if offset >= total_height:
                break
        
        logger.info("Captura com costura concluída")
        return full_screenshot
    
    def close(self):
        """Fecha o navegador."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logger.warning(f"Erro ao fechar o navegador: {str(e)}")
