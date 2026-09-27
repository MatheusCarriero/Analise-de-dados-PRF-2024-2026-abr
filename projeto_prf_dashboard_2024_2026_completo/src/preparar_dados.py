from pathlib import Path
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "bruto"
OUT_DIR = BASE_DIR / "data" / "tratado"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MES_MAP = {1:'Jan',2:'Fev',3:'Mar',4:'Abr',5:'Mai',6:'Jun',7:'Jul',8:'Ago',9:'Set',10:'Out',11:'Nov',12:'Dez'}
REGIAO_UF = {
    'AC':'Norte','AP':'Norte','AM':'Norte','PA':'Norte','RO':'Norte','RR':'Norte','TO':'Norte',
    'AL':'Nordeste','BA':'Nordeste','CE':'Nordeste','MA':'Nordeste','PB':'Nordeste','PE':'Nordeste','PI':'Nordeste','RN':'Nordeste','SE':'Nordeste',
    'DF':'Centro-Oeste','GO':'Centro-Oeste','MT':'Centro-Oeste','MS':'Centro-Oeste',
    'ES':'Sudeste','MG':'Sudeste','RJ':'Sudeste','SP':'Sudeste',
    'PR':'Sul','RS':'Sul','SC':'Sul'
}


def normalizar_numero(s):
    return pd.to_numeric(
        s.astype(str).str.replace(',', '.', regex=False).str.strip().replace({'nan': np.nan, 'None': np.nan, '': np.nan}),
        errors='coerce'
    )


def periodo_por_hora(h):
    if pd.isna(h):
        return 'Não informado'
    h = int(h)
    if 0 <= h < 6:
        return 'Madrugada'
    if 6 <= h < 12:
        return 'Manhã'
    if 12 <= h < 18:
        return 'Tarde'
    return 'Noite'


def gravidade_linha(row):
    if row.get('mortos', 0) > 0:
        return 'Fatal'
    if row.get('feridos_graves', 0) > 0:
        return 'Com feridos graves'
    if row.get('feridos_leves', 0) > 0 or row.get('feridos', 0) > 0:
        return 'Com feridos leves'
    return 'Sem vítimas'


def preparar_dados(anos=(2024, 2025, 2026)):
    frames = []
    for ano in anos:
        path = RAW_DIR / f"datatran{ano}.csv"
        df = pd.read_csv(path, sep=';', encoding='latin1', low_memory=False)
        df.columns = [str(c).strip() for c in df.columns]
        df['ano_arquivo'] = ano
        frames.append(df)

    df = pd.concat(frames, ignore_index=True)

    text_cols = ['uf','municipio','causa_acidente','tipo_acidente','classificacao_acidente','fase_dia','sentido_via','condicao_metereologica','tipo_pista','tracado_via','uso_solo','regional','delegacia','uop']
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].fillna('Não informado').astype(str).str.strip()

    df['data_inversa'] = pd.to_datetime(df['data_inversa'], errors='coerce')
    df['hora'] = pd.to_datetime(df['horario'], format='%H:%M:%S', errors='coerce').dt.hour
    df['ano'] = df['data_inversa'].dt.year.fillna(df['ano_arquivo']).astype(int)
    df['mes'] = df['data_inversa'].dt.month.astype('Int64')
    df['mes_nome'] = df['mes'].map(MES_MAP).fillna('Não informado')
    df['periodo_hora'] = df['hora'].apply(periodo_por_hora)
    df['fim_de_semana'] = df['dia_semana'].str.lower().isin(['sábado', 'domingo', 'sabado'])

    numeric_cols = ['id','br','km','pessoas','mortos','feridos_leves','feridos_graves','ilesos','ignorados','feridos','veiculos','latitude','longitude']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = normalizar_numero(df[col])

    for col in ['mortos','feridos_leves','feridos_graves','ilesos','ignorados','feridos','pessoas','veiculos']:
        df[col] = df[col].fillna(0).astype(int)

    df['id'] = df['id'].astype('Int64')
    df['br'] = df['br'].astype('Int64')
    df = df.drop_duplicates(subset=['id'], keep='first')

    df['acidente_fatal'] = df['mortos'] > 0
    df['total_vitimas'] = df['mortos'] + df['feridos_leves'] + df['feridos_graves']
    denom = df['pessoas'].replace({0: np.nan})
    df['taxa_gravidade'] = ((df['mortos']*3 + df['feridos_graves']*2 + df['feridos_leves']) / denom).fillna(0).round(3)
    df['gravidade'] = df.apply(gravidade_linha, axis=1)
    df['regiao'] = df['uf'].map(REGIAO_UF).fillna('Não informado')
    df['letalidade_ocorrencia'] = np.where(df['pessoas'] > 0, (df['mortos'] / df['pessoas']).round(4), 0)
    df['br_label'] = np.where(df['br'].notna(), 'BR-' + df['br'].astype('Int64').astype(str), 'Não informado')

    first_cols = ['id','data_inversa','ano_arquivo','ano','mes','mes_nome','dia_semana','horario','hora','periodo_hora','fim_de_semana','uf','regiao','br','br_label','km','municipio','causa_acidente','tipo_acidente','classificacao_acidente','gravidade','fase_dia','sentido_via','condicao_metereologica','tipo_pista','tracado_via','uso_solo','pessoas','mortos','feridos_leves','feridos_graves','ilesos','ignorados','feridos','veiculos','acidente_fatal','total_vitimas','taxa_gravidade','letalidade_ocorrencia','latitude','longitude','regional','delegacia','uop']
    cols = [c for c in first_cols if c in df.columns] + [c for c in df.columns if c not in first_cols]
    return df[cols]


if __name__ == '__main__':
    df = preparar_dados()
    out = OUT_DIR / 'acidentes_prf_2024_2025_2026_tratado.csv'
    df.to_csv(out, sep=';', encoding='utf-8-sig', index=False)
    print(f'Base tratada gerada: {out}')
    print(f'Registros: {len(df):,}'.replace(',', '.'))
