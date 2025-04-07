# Projeto: Web Crawler e Geração de PDF

Este projeto tem como objetivo realizar a captura (crawling) de dados de sites e, em seguida, gerar PDFs a partir dessas informações. Ele utiliza Python, gerencia dependências via Poetry e conta com scripts específicos para a coleta de dados, manipulação e formatação dos resultados.

## Sumário

- [Visão Geral](#visão-geral)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Pré-requisitos](#pré-requisitos)
- [Instalação](#instalação)
- [Uso](#uso)
  - [Execução do Crawler](#execução-do-crawler)
  - [Geração de PDF](#geração-de-pdf)
- [Logs e Resultados](#logs-e-resultados)
- [Contribuindo](#contribuindo)
- [Licença](#licença)

---

## Visão Geral

1. **Crawler:** O arquivo `crawler.py` é responsável por rastrear um ou mais sites, coletando informações de acordo com critérios pré-definidos (por exemplo, textos, links ou dados específicos).
2. **Geração de PDF:** O arquivo `pdf_generator.py` converte as informações coletadas em documentos PDF.
3. **Automação e Scripts Auxiliares:** O `main.py` e outros scripts podem orquestrar as etapas do processo, além de gerenciar logs e armazenar resultados.

Este projeto foi criado para simplificar a coleta e formatação de informações, oferecendo uma solução automatizada de ponta a ponta.

---

## Estrutura do Projeto

```
.
├── printToPdf/
│   ├── ...
│   └── __init__.py
├── logs/
│   └── ... (arquivos de log)
├── results/
│   └── ... (resultados gerados, possivelmente PDFs ou JSONs)
├── venv/            # Ambiente virtual (se não estiver usando Poetry)
├── __init__.py
├── .gitattributes
├── .gitignore
├── crawler.py       # Script principal para rastreamento (crawling)
├── main.py          # Script principal de orquestração
├── pdf_generator.py # Script para geração de PDFs
├── poetry.lock      # Gerado pelo Poetry
├── pyproject.toml   # Configuração do Poetry (dependências)
├── README.md        # Este arquivo
├── sitemap_parser.py # Possível parser de sitemap
├── urls.txt         # Lista de URLs para o crawler (exemplo)
└── utils.py         # Funções utilitárias
```

- **crawler.py**: Contém a lógica principal de raspagem (web scraping).
- **pdf_generator.py**: Cria PDFs a partir dos dados coletados.
- **main.py**: Pode orquestrar a execução do crawler e do gerador de PDF.
- **sitemap_parser.py**: Faz o parsing de sitemaps para encontrar links de forma automatizada.
- **utils.py**: Armazena funções auxiliares (ex.: formatação de dados, funções de rede, etc.).
- **logs/**: Pasta para armazenar logs gerados durante o processo.
- **results/**: Pasta onde são salvos arquivos de saída (PDFs, JSON, CSV, etc.).

---

## Pré-requisitos

- **Python 3.8+** (recomendado)
- **Poetry** para gerenciar dependências (opcional, mas recomendado)
  - Instalação do Poetry: [Instruções Oficiais](https://python-poetry.org/docs/#installation)

---

## Instalação

1. **Clonar o repositório**:
   ```bash
   git clone https://github.com/seu-usuario/seu-repositorio.git
   cd seu-repositorio
   ```

2. **Instalar as dependências** usando Poetry:
   ```bash
   poetry install
   ```
   Se preferir, é possível usar `pip` e o arquivo `requirements.txt` (se existir), mas a configuração principal está no `pyproject.toml`.

3. **Ativar o ambiente virtual** (caso esteja usando Poetry):
   ```bash
   poetry shell
   ```
   Ou, caso esteja usando `venv` padrão do Python:
   ```bash
   python -m venv venv
   source venv/bin/activate  # (Linux/Mac)
   venv\Scripts\activate     # (Windows)
   pip install -r requirements.txt
   ```

---

## Uso

### Execução do Crawler

1. **Configurar as URLs**: Se o arquivo `urls.txt` for utilizado, adicione nele as URLs que deseja rastrear.
2. **Rodar o script**:
   ```bash
   python crawler.py
   ```
   - Opcionalmente, utilize `main.py` caso ele gerencie o fluxo completo:
     ```bash
     python main.py
     ```
3. **Logs e resultados**: Durante a execução, os logs são gerados na pasta `logs/` e os resultados podem ser armazenados na pasta `results/`.

### Geração de PDF

- Após coletar os dados, execute o script `pdf_generator.py` para criar PDFs:
  ```bash
  python pdf_generator.py
  ```
- O PDF resultante será salvo na pasta `results/`, ou em outra pasta configurada no script.

---

## Logs e Resultados

- **logs/**: Armazena informações sobre erros, avisos e status do processo de crawling e geração de PDF.
- **results/**: Contém os arquivos de saída (PDFs, JSONs, etc.) resultantes da execução.

---

## Contribuindo

1. Faça um fork do repositório.
2. Crie uma nova branch para sua feature ou correção:
   ```bash
   git checkout -b minha-nova-feature
   ```
3. Faça commit das suas alterações:
   ```bash
   git commit -m "Adiciona nova feature de exemplo"
   ```
4. Faça push para a branch criada:
   ```bash
   git push origin minha-nova-feature
   ```
5. Abra um Pull Request no GitHub.

---

## Licença

Este projeto está sob a licença [MIT](LICENSE). Sinta-se à vontade para usar, modificar e distribuir. Para mais detalhes, consulte o arquivo de licença.