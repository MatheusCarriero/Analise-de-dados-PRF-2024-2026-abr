# Dashboard Interativo - Acidentes PRF 2024/2025/2026

Projeto desenvolvido em Python com Dash, Pandas e Plotly, utilizando três arquivos brutos reais da PRF:

- `datatran2024.csv`
- `datatran2025.csv`
- `datatran2026.csv`

## Objetivo

Desenvolver um pipeline completo de ciência de dados e dois dashboards interativos para analisar acidentes em rodovias federais brasileiras, comparando 2024, 2025 e 2026 em termos de volume, gravidade, letalidade, localização, causas, clima e período do dia.

> Observação importante: os arquivos de 2024 e 2025 estão completos. O arquivo de 2026 enviado contém registros de 2026-01-01 a 2026-04-30; por isso, comparações anuais com 2026 devem considerar que o ano está parcial.

## Estrutura do projeto

```text
projeto_prf_dashboard_2024_2026_completo/
├── app.py
├── requirements.txt
├── README.md
├── resumo_indicadores.json
├── assets/
│   └── style.css
├── data/
│   ├── bruto/
│   │   ├── datatran2024.csv
│   │   ├── datatran2025.csv
│   │   └── datatran2026.csv
│   └── tratado/
│       ├── acidentes_prf_2024_2025_2026_tratado.csv
│       └── resumo_indicadores.json
├── src/
│   └── preparar_dados.py
├── notebooks/
│   ├── analise_exploratoria_prf_2024_2026.ipynb
│   └── notebook_prf_2024_2026.pdf
├── dashboards_html/
│   ├── dashboard_1_visao_geral.html
│   └── dashboard_2_exploracao.html
└── apresentacao/
    └── relatorio_pipeline_prf_2024_2026.pptx
```

## Pipeline de Ciência de Dados

### 1. Aquisição de dados
Os arquivos CSV brutos foram lidos com `pandas`, preservando a origem de cada ano por meio da coluna `ano_arquivo`.

### 2. Integração de dados
As bases de 2024, 2025 e 2026 foram integradas por concatenação, formando uma base única de análise.

### 3. Limpeza e tratamento
Foram aplicados:

- tratamento de valores ausentes;
- padronização de textos;
- conversão de campos numéricos com vírgula decimal;
- conversão de datas e horários;
- remoção de duplicidades pelo campo `id`;
- preparação de variáveis categóricas.

### 4. Transformação de dados
Foram criadas variáveis analíticas como:

- ano, mês, nome do mês e hora;
- período do dia;
- fim de semana;
- acidente fatal;
- total de vítimas;
- taxa de gravidade;
- letalidade por ocorrência;
- classificação de gravidade;
- região do país;
- rótulo da BR.

### 5. Análise exploratória
A análise busca responder perguntas como:

- onde os acidentes se concentram?
- quando ocorrem com maior frequência?
- quais causas são mais recorrentes?
- quais condições estão associadas à maior letalidade?
- volume de acidentes e risco proporcional indicam a mesma coisa?
- como 2024, 2025 e o período disponível de 2026 se comparam?

## Indicadores gerais da base

- Registros analisados: **169,160**
- Período: **2024-01-01 a 2026-04-30**
- Mortos: **14,121**
- Feridos: **195,633**
- UF com maior volume: **MG**
- Principal causa: **Ausência de reação do condutor**
- Taxa geral de letalidade: **8.35%**

## Dashboards

### Dashboard 1 - Visão Executiva
Focado em comunicação rápida dos principais indicadores:

- KPIs gerais;
- evolução mensal por ano;
- comparação anual;
- ranking de UFs;
- principais causas;
- distribuição por gravidade;
- insight textual automático.

### Dashboard 2 - Exploração Analítica
Focado em aprofundamento e comparação:

- mapa por município;
- heatmap por dia e horário;
- letalidade por condição meteorológica;
- comparação regional por ano;
- volume x letalidade por UF;
- tipos de acidente;
- composição da gravidade por causa.

## Como executar

1. Instale as dependências:

```bash
pip install -r requirements.txt
```

2. Gere novamente a base tratada, caso necessário:

```bash
python src/preparar_dados.py
```

3. Execute o dashboard:

```bash
python app.py
```

4. Abra no navegador:

```text
http://127.0.0.1:8050/
```


## Melhorias analíticas acrescentadas no notebook

Além das análises originais, o notebook atualizado inclui:

- comparação equivalente de janeiro a abril entre 2024, 2025 e 2026, evitando distorções pelo recorte parcial de 2026;
- ranking por risco proporcional por UF, considerando mortos a cada 1.000 acidentes e outros indicadores relativos;
- matriz volume x gravidade por UF, separando estados com alto volume e alto risco daqueles com risco proporcional elevado mesmo com menor volume.
