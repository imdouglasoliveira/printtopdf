# PrintToPDF

Uma ferramenta para capturar screenshots de todas as páginas de múltiplos sites e convertê-las em arquivos PDF, organizados por domínio.

## Recursos

- Extrai todas as URLs de um website através de crawling automático
- Captura screenshots de cada página
- Converte screenshots para PDF
- Cria PDF individuais e também um PDF mesclado para cada site
- Organiza os resultados em pastas por domínio

## Instalação

Certifique-se de ter o Poetry instalado:

```bash
# Instalar Poetry (se ainda não tiver)
curl -sSL https://install.python-poetry.org | python3 -

# Clonar o repositório e instalar
git clone https://seu-repositorio/printtopdf.git
cd printtopdf
poetry install
```

## Uso

1. Criar um arquivo `urls.txt` com os URLs dos sites para processar, um por linha:

```
https://exemplo.com
https://outrosite.com
```

2. Executar a ferramenta:

```bash
# Utilizando Poetry
poetry run printtopdf

# Ou depois de ativar o ambiente virtual
printtopdf
```

3. Os resultados serão organizados na pasta `results/`:

```
output/
├── exemplo.com/
│   ├── pages/
│   │   ├── page_1.pdf
│   │   ├── page_2.pdf
│   │   └── ...
│   └── exemplo.com_completo.pdf
└── outrosite.com/
    ├── pages/
    │   ├── page_1.pdf
    │   ├── page_2.pdf
    │   └── ...
    └── outrosite.com_completo.pdf
```

## Opções

```
Uso: printtopdf [OPÇÕES]

Opções:
  --urls-file TEXT    Caminho para o arquivo com lista de URLs (padrão: urls.txt)
  --output-dir TEXT   Diretório de saída (padrão: output)
  --max-depth INTEGER Profundidade máxima de crawling (padrão: 3)
  --help              Mostrar esta mensagem e sair
```

## Requisitos

- Python 3.9+
- Google Chrome ou Firefox instalado