from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc

BASE_DIR = Path(__file__).parent
DATA_PATH = BASE_DIR / "data" / "tratado" / "acidentes_prf_2024_2025_2026_tratado.csv"

DIA_ORDEM = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]
MES_ORDEM = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
GRAVIDADE_ORDEM = ["Sem vítimas", "Com feridos leves", "Com feridos graves", "Fatal"]


def carregar_dados():
    df = pd.read_csv(DATA_PATH, sep=";", encoding="utf-8-sig", low_memory=False)
    df["data_inversa"] = pd.to_datetime(df["data_inversa"], errors="coerce")
    df["ano"] = df["ano"].astype(int)
    for col in ["uf", "condicao_metereologica", "fase_dia", "tipo_acidente", "causa_acidente", "gravidade", "regiao", "tipo_pista", "periodo_hora", "municipio", "br_label"]:
        if col in df.columns:
            df[col] = df[col].fillna("Não informado").astype(str).str.strip()
    for col in ["acidente_fatal", "fim_de_semana"]:
        if col in df.columns and df[col].dtype == object:
            df[col] = df[col].astype(str).str.lower().isin(["true", "1", "sim"])
    return df


df = carregar_dados()

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
server = app.server
app.title = "Dashboard PRF - Acidentes 2024/2025/2026"


def format_num(valor):
    try:
        return f"{int(valor):,}".replace(",", ".")
    except Exception:
        return "0"


def pct(valor):
    if pd.isna(valor):
        valor = 0
    return f"{valor:.2f}%".replace(".", ",")


def top_value(series, default="Não informado"):
    if series.dropna().empty:
        return default
    return str(series.value_counts().index[0])


def filtrar_dados(anos, ufs, climas, fases, tipos, regioes):
    dff = df.copy()
    if anos:
        dff = dff[dff["ano"].isin(anos)]
    if ufs:
        dff = dff[dff["uf"].isin(ufs)]
    if climas:
        dff = dff[dff["condicao_metereologica"].isin(climas)]
    if fases:
        dff = dff[dff["fase_dia"].isin(fases)]
    if tipos:
        dff = dff[dff["tipo_acidente"].isin(tipos)]
    if regioes:
        dff = dff[dff["regiao"].isin(regioes)]
    return dff


def kpi_card(titulo, valor, detalhe=""):
    return dbc.Card(
        dbc.CardBody([
            html.Div(titulo, className="kpi-title"),
            html.Div(valor, className="kpi-value"),
            html.Div(detalhe, className="kpi-detail")
        ]),
        className="kpi-card h-100"
    )


def filtros_layout():
    anos = sorted(df["ano"].dropna().unique())
    return dbc.Card(dbc.CardBody([
        html.H5("Filtros interativos", className="mb-1"),
        html.P(
            "Os filtros atualizam os dois dashboards e permitem comparar 2024, 2025 e 2026 por UF, região, clima, fase do dia e tipo de acidente. Atenção: 2026 está parcial conforme o arquivo enviado.",
            className="text-muted mb-3"
        ),
        dbc.Row([
            dbc.Col([html.Label("Ano", className="filter-label"), dcc.Dropdown(options=[{"label": str(x), "value": int(x)} for x in anos], value=[int(x) for x in anos], multi=True, id="filtro-ano", clearable=False)], md=2),
            dbc.Col([html.Label("Região", className="filter-label"), dcc.Dropdown(options=[{"label": x, "value": x} for x in sorted(df["regiao"].dropna().unique())], value=None, multi=True, id="filtro-regiao", placeholder="Todas")], md=2),
            dbc.Col([html.Label("UF", className="filter-label"), dcc.Dropdown(options=[{"label": x, "value": x} for x in sorted(df["uf"].dropna().unique())], value=None, multi=True, id="filtro-uf", placeholder="Todas")], md=2),
            dbc.Col([html.Label("Condição meteorológica", className="filter-label"), dcc.Dropdown(options=[{"label": x, "value": x} for x in sorted(df["condicao_metereologica"].dropna().unique())], value=None, multi=True, id="filtro-clima", placeholder="Todas")], md=2),
            dbc.Col([html.Label("Fase do dia", className="filter-label"), dcc.Dropdown(options=[{"label": x, "value": x} for x in sorted(df["fase_dia"].dropna().unique())], value=None, multi=True, id="filtro-fase", placeholder="Todas")], md=2),
            dbc.Col([html.Label("Tipo de acidente", className="filter-label"), dcc.Dropdown(options=[{"label": x, "value": x} for x in sorted(df["tipo_acidente"].dropna().unique())], value=None, multi=True, id="filtro-tipo", placeholder="Todos")], md=2),
        ], className="g-3")
    ]), className="filter-card mb-3")


def padronizar_figura(fig):
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=20, r=20, t=70, b=35),
        title=dict(font=dict(size=16), x=0.02),
        legend_title_text="",
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="Segoe UI, Arial")
    )
    return fig


def figura_vazia(titulo, mensagem="Sem dados para os filtros selecionados"):
    fig = go.Figure()
    fig.add_annotation(text=mensagem, x=0.5, y=0.5, showarrow=False, font=dict(size=16))
    fig.update_layout(title=titulo, template="plotly_white", height=380)
    return fig


def gerar_insights(dff):
    acidentes = len(dff)
    mortos = dff["mortos"].sum() if acidentes else 0
    taxa_letalidade = mortos / acidentes * 100 if acidentes else 0
    uf_top = top_value(dff["uf"])
    causa_top = top_value(dff["causa_acidente"])
    fase = dff.groupby("fase_dia").agg(acidentes=("id", "count"), fatais=("acidente_fatal", "sum")).reset_index()
    if fase.empty:
        fase_critica = {"fase_dia": "Não informado", "fatal_pct": 0}
    else:
        fase["fatal_pct"] = (fase["fatais"] / fase["acidentes"] * 100).fillna(0)
        fase_critica = fase.sort_values("fatal_pct", ascending=False).iloc[0]
    return acidentes, mortos, taxa_letalidade, uf_top, causa_top, fase_critica


app.layout = dbc.Container(fluid=True, children=[
    html.Div([
        html.Div("Projeto de Ciência de Dados com Dash", className="eyebrow"),
        html.H1("Acidentes em Rodovias Federais - PRF 2024, 2025 e 2026"),
        html.P("Pipeline completo com dados brutos da PRF, integração dos três anos, tratamento, variáveis analíticas e dois dashboards interativos para comparar volume, severidade, causas, clima e período dos acidentes.")
    ], className="hero"),
    filtros_layout(),
    dcc.Tabs(id="tabs", value="dashboard-1", children=[
        dcc.Tab(label="Dashboard 1 - Visão Executiva", value="dashboard-1"),
        dcc.Tab(label="Dashboard 2 - Exploração Analítica", value="dashboard-2")
    ]),
    html.Div(id="conteudo-dashboard", className="dashboard-content")
])


@app.callback(
    Output("conteudo-dashboard", "children"),
    Input("tabs", "value"),
    Input("filtro-ano", "value"),
    Input("filtro-uf", "value"),
    Input("filtro-clima", "value"),
    Input("filtro-fase", "value"),
    Input("filtro-tipo", "value"),
    Input("filtro-regiao", "value")
)
def atualizar_dashboard(tab, anos, ufs, climas, fases, tipos, regioes):
    dff = filtrar_dados(anos, ufs, climas, fases, tipos, regioes)
    if dff.empty:
        return dbc.Alert("Nenhum registro foi encontrado para os filtros selecionados.", color="warning", className="mt-3")

    acidentes, mortos, taxa_letalidade, uf_top, causa_top, fase_critica = gerar_insights(dff)
    feridos = int(dff["feridos"].sum())
    fatais = int(dff["acidente_fatal"].sum())
    severidade_media = dff["taxa_gravidade"].mean()
    br_series = dff.dropna(subset=["br_label"])["br_label"].value_counts()
    br_top = br_series.index[0] if not br_series.empty else "Não informado"

    if tab == "dashboard-1":
        mensal = dff.groupby(["ano", "mes", "mes_nome"], as_index=False).agg(acidentes=("id", "count"), mortos=("mortos", "sum"), feridos=("feridos", "sum")).sort_values(["ano", "mes"])
        mensal["mes_nome"] = pd.Categorical(mensal["mes_nome"], MES_ORDEM, ordered=True)
        top_uf = dff.groupby("uf", as_index=False).agg(acidentes=("id", "count"), mortos=("mortos", "sum"), feridos=("feridos", "sum"))
        top_uf["letalidade_%"] = (top_uf["mortos"] / top_uf["acidentes"] * 100).round(2)
        causas = dff["causa_acidente"].value_counts().head(10).reset_index(); causas.columns = ["causa_acidente", "acidentes"]
        gravidade = dff["gravidade"].value_counts().reset_index(); gravidade.columns = ["gravidade", "acidentes"]
        gravidade["gravidade"] = pd.Categorical(gravidade["gravidade"], GRAVIDADE_ORDEM, ordered=True)
        anual = dff.groupby("ano", as_index=False).agg(acidentes=("id", "count"), mortos=("mortos", "sum"), feridos=("feridos", "sum"), fatais=("acidente_fatal", "sum"))
        anual["letalidade_%"] = (anual["mortos"] / anual["acidentes"] * 100).round(2)

        fig_mensal = padronizar_figura(px.line(mensal, x="mes_nome", y="acidentes", color="ano", markers=True, title="Tendência mensal: evolução dos acidentes por ano", labels={"mes_nome":"Mês", "acidentes":"Acidentes"}))
        fig_anual = padronizar_figura(px.bar(anual, x="ano", y="acidentes", text="acidentes", title="Comparação anual do volume de acidentes", labels={"ano":"Ano", "acidentes":"Acidentes"}))
        fig_uf = padronizar_figura(px.bar(top_uf.sort_values("acidentes", ascending=False).head(10).sort_values("acidentes"), x="acidentes", y="uf", orientation="h", title="Ranking de UFs por volume de acidentes", text="acidentes"))
        fig_causas = padronizar_figura(px.bar(causas.sort_values("acidentes"), x="acidentes", y="causa_acidente", orientation="h", title="Principais causas registradas", text="acidentes"))
        fig_gravidade = padronizar_figura(px.pie(gravidade.sort_values("gravidade"), names="gravidade", values="acidentes", hole=.45, title="Distribuição dos acidentes por gravidade"))

        insight = (
            f"Nos filtros selecionados, {uf_top} concentra o maior volume de ocorrências e a causa mais recorrente é '{causa_top}'. "
            f"A fase do dia com maior proporção de acidentes fatais é '{fase_critica['fase_dia']}', com {fase_critica['fatal_pct']:.2f}% de ocorrências fatais. "
            "A leitura executiva combina volume e severidade para evitar uma interpretação limitada apenas pela quantidade absoluta de acidentes."
        )

        return html.Div([
            dbc.Alert("Observação metodológica: 2024 e 2025 estão completos nos arquivos enviados; 2026 possui registros até abril, então comparações anuais devem considerar o período parcial.", color="info", className="mt-3"),
            dbc.Row([
                dbc.Col(kpi_card("Total de acidentes", format_num(acidentes), "Ocorrências registradas"), md=2),
                dbc.Col(kpi_card("Mortos", format_num(mortos), "Vítimas fatais"), md=2),
                dbc.Col(kpi_card("Feridos", format_num(feridos), "Leves + graves"), md=2),
                dbc.Col(kpi_card("Acidentes fatais", format_num(fatais), "Ocorrências com morte"), md=2),
                dbc.Col(kpi_card("Taxa de letalidade", pct(taxa_letalidade), "Mortos/acidentes"), md=2),
                dbc.Col(kpi_card("BR destaque", br_top, "Maior volume"), md=2)
            ], className="g-3 mt-2"),
            dbc.Alert(insight, color="light", className="insight-box mt-3"),
            dbc.Row([dbc.Col(dcc.Graph(figure=fig_mensal), md=8), dbc.Col(dcc.Graph(figure=fig_anual), md=4)], className="g-3"),
            dbc.Row([dbc.Col(dcc.Graph(figure=fig_uf), md=6), dbc.Col(dcc.Graph(figure=fig_gravidade), md=6)], className="g-3"),
            dbc.Row([dbc.Col(dcc.Graph(figure=fig_causas), md=12)], className="g-3"),
        ])

    # Dashboard 2 - Exploração Analítica
    heat = dff.groupby(["dia_semana", "hora"], as_index=False).agg(acidentes=("id", "count"))
    heat["dia_semana"] = pd.Categorical(heat["dia_semana"], DIA_ORDEM, ordered=True)
    matriz = heat.pivot_table(index="dia_semana", columns="hora", values="acidentes", aggfunc="sum", fill_value=0).reindex(DIA_ORDEM)
    fig_heat = padronizar_figura(px.imshow(matriz, aspect="auto", title="Concentração de acidentes: dia da semana x horário", labels=dict(x="Hora", y="Dia da semana", color="Acidentes")))

    clima = dff.groupby("condicao_metereologica", as_index=False).agg(acidentes=("id", "count"), mortos=("mortos", "sum"), feridos_graves=("feridos_graves", "sum"))
    clima["letalidade_%"] = (clima["mortos"] / clima["acidentes"] * 100).round(2)
    fig_clima = padronizar_figura(px.bar(clima.sort_values("letalidade_%", ascending=False).head(10), x="condicao_metereologica", y="letalidade_%", title="Letalidade proporcional por condição meteorológica", text="letalidade_%", labels={"condicao_metereologica":"Condição meteorológica", "letalidade_%":"Letalidade (%)"}))
    fig_clima.update_xaxes(tickangle=-25)

    regiao = dff.groupby(["regiao", "ano"], as_index=False).agg(acidentes=("id", "count"), mortos=("mortos", "sum"))
    fig_regiao = padronizar_figura(px.bar(regiao, x="regiao", y="acidentes", color="ano", barmode="group", title="Comparação regional por ano", labels={"regiao":"Região", "acidentes":"Acidentes"}))

    tipo = dff["tipo_acidente"].value_counts().head(15).reset_index(); tipo.columns = ["tipo_acidente", "acidentes"]
    fig_tipo = padronizar_figura(px.treemap(tipo, path=["tipo_acidente"], values="acidentes", title="Tipos de acidente mais frequentes"))

    severidade_uf = dff.groupby("uf", as_index=False).agg(acidentes=("id", "count"), mortos=("mortos", "sum"), gravidade_media=("taxa_gravidade", "mean"))
    min_amostra = max(30, int(len(dff) * 0.002))
    severidade_uf = severidade_uf[severidade_uf["acidentes"] >= min_amostra]
    if severidade_uf.empty:
        fig_sev = figura_vazia("Volume x letalidade por UF")
        top_linha = {"uf": "Não informado", "letalidade_%": 0}
    else:
        severidade_uf["letalidade_%"] = (severidade_uf["mortos"] / severidade_uf["acidentes"] * 100).round(2)
        fig_sev = padronizar_figura(px.scatter(severidade_uf, x="acidentes", y="letalidade_%", size="gravidade_media", hover_name="uf", title="Volume x letalidade por UF", labels={"acidentes":"Volume de acidentes", "letalidade_%":"Letalidade (%)"}))
        top_linha = severidade_uf.sort_values("letalidade_%", ascending=False).iloc[0]

    causa_grav = dff[dff["causa_acidente"].isin(dff["causa_acidente"].value_counts().head(8).index)]
    causa_grav = causa_grav.groupby(["causa_acidente", "gravidade"], as_index=False).agg(acidentes=("id", "count"))
    fig_causa_grav = padronizar_figura(px.bar(causa_grav, x="acidentes", y="causa_acidente", color="gravidade", orientation="h", title="Composição da gravidade nas principais causas", labels={"causa_acidente":"Causa", "acidentes":"Acidentes"}))

    mapa = dff.dropna(subset=["latitude", "longitude"])
    mapa = mapa.groupby(["uf", "municipio"], as_index=False).agg(acidentes=("id", "count"), mortos=("mortos", "sum"), latitude=("latitude", "mean"), longitude=("longitude", "mean"))
    mapa = mapa.sort_values("acidentes", ascending=False).head(600)
    if mapa.empty:
        fig_mapa = figura_vazia("Distribuição geográfica dos acidentes")
    else:
        fig_mapa = px.scatter_mapbox(
            mapa,
            lat="latitude",
            lon="longitude",
            size="acidentes",
            color="mortos",
            hover_name="municipio",
            hover_data={"uf": True, "acidentes": True, "mortos": True, "latitude": False, "longitude": False},
            zoom=3.1,
            center={"lat": -14.235, "lon": -51.9253},
            mapbox_style="open-street-map",
            title="Distribuição geográfica dos acidentes por município"
        )
        fig_mapa = padronizar_figura(fig_mapa)
        fig_mapa.update_layout(height=470)

    insight2 = (
        f"A exploração analítica mostra que volume e risco não são a mesma coisa: a UF {top_linha['uf']} aparece com uma das maiores letalidades proporcionais entre as UFs com amostra relevante. "
        "Por isso, o dashboard usa indicadores relativos, como letalidade e gravidade média, além dos rankings absolutos."
    )

    return html.Div([
        dbc.Row([
            dbc.Col(kpi_card("Severidade média", f"{severidade_media:.3f}", "Índice ponderado"), md=3),
            dbc.Col(kpi_card("Fase crítica", fase_critica['fase_dia'], f"{fase_critica['fatal_pct']:.2f}% fatais"), md=3),
            dbc.Col(kpi_card("Causa principal", causa_top[:32], "Maior frequência"), md=3),
            dbc.Col(kpi_card("UF principal", uf_top, "Maior volume"), md=3)
        ], className="g-3 mt-2"),
        dbc.Alert(insight2, color="light", className="insight-box mt-3"),
        dbc.Row([dbc.Col(dcc.Graph(figure=fig_mapa), md=12)], className="g-3"),
        dbc.Row([dbc.Col(dcc.Graph(figure=fig_heat), md=7), dbc.Col(dcc.Graph(figure=fig_clima), md=5)], className="g-3"),
        dbc.Row([dbc.Col(dcc.Graph(figure=fig_regiao), md=6), dbc.Col(dcc.Graph(figure=fig_sev), md=6)], className="g-3"),
        dbc.Row([dbc.Col(dcc.Graph(figure=fig_causa_grav), md=7), dbc.Col(dcc.Graph(figure=fig_tipo), md=5)], className="g-3"),
    ])


if __name__ == "__main__":
    app.run(debug=True)
