import streamlit as st
import pandas as pd
from datetime import datetime
import json
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
import streamlit.components.v1 as components
import altair as alt
import os
from pathlib import Path
from PIL import Image

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Gestão de Conferência de Mercadorias",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- LOCALIZADOR DO LOGOTIPO ---
def encontrar_e_carregar_logotipo():
    nomes_possiveis = [
        "logotipo.png", "logotipo.PNG", "logotipo.jpg", "logotipo.jpeg",
        "logo.png", "logo.PNG", "logo.jpg", "logo.jpeg"
    ]
    pastas_busca = [
        Path.cwd(),
        Path(__file__).parent.resolve() if "__file__" in locals() else Path.cwd()
    ]
    for pasta in pastas_busca:
        for nome in nomes_possiveis:
            candidato = pasta / nome
            if candidato.is_file():
                try:
                    return Image.open(candidato)
                except Exception:
                    pass
    for pasta in pastas_busca:
        try:
            for arq in pasta.rglob("*"):
                if arq.is_file() and arq.name.lower() in [n.lower() for n in nomes_possiveis]:
                    try:
                        return Image.open(arq)
                    except Exception:
                        pass
        except Exception:
            pass
    return None

img_logo_obj = encontrar_e_carregar_logotipo()

# --- 2. CSS GLOBAL: HEADER FULL-WIDTH & CORPO CENTRALIZADO ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* Ocultar barras padrão do Streamlit */
    [data-testid="stSidebar"], section[data-testid="stSidebar"], header[data-testid="stHeader"] {
        display: none !important;
    }

    /* Fundo da página Slate-100 */
    html, body, [class*="css"], [class*="st-"] {
        font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
        background-color: #f1f5f9 !important;
        color: #1e293b !important;
    }

    /* Container global da página: centralizado com margens confortáveis */
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 3rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        max-width: 1320px !important;
        margin: 0 auto !important;
    }

    /* BARRA SUPERIOR TOTALMENTE UNIFICADA */
    div[data-testid="stVerticalBlock"] > div:has(.navbar-header-marker) {
        background: #ffffff !important;
        border-bottom: 1px solid #e2e8f0 !important;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05) !important;
        padding: 10px 18px !important;
        margin-bottom: 22px !important;
        border-radius: 0 0 14px 14px !important;
    }

    /* Logotipo Container */
    [data-testid="stImage"] {
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
    }
    [data-testid="stImage"] img {
        max-height: 48px !important;
        max-width: 125px !important;
        width: auto !important;
        object-fit: contain !important;
    }
    .brand-fallback-box {
        width: 44px;
        height: 44px;
        background: #0284c7;
        color: #ffffff;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
    }

    .header-title-text {
        font-size: 16px !important;
        font-weight: 700 !important;
        color: #0f172a !important;
        letter-spacing: -0.2px;
        margin: 0 !important;
        line-height: 1.2 !important;
    }
    .header-subtitle-text {
        font-size: 11.5px !important;
        color: #64748b !important;
        margin: 2px 0 0 0 !important;
    }

    /* PÍLULA DE NAVEGAÇÃO INTERNA */
    div.nav-pill-wrapper {
        background-color: #f1f5f9;
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 4px;
        display: flex;
        gap: 6px;
        align-items: center;
    }

    /* Configuração dos botões */
    div.nav-pill-wrapper div.stButton > button {
        border-radius: 10px !important;
        font-size: 12px !important;
        font-weight: 600 !important;
        padding: 5px 12px !important;
        height: 38px !important;
        transition: all 0.15s ease-in-out !important;
        white-space: nowrap !important;
        border: 1px solid transparent !important;
    }

    /* Botão Inativo */
    div.nav-btn-inactive div.stButton > button {
        background-color: #ffffff !important;
        color: #64748b !important;
        border: 1px solid #e2e8f0 !important;
        box-shadow: none !important;
    }
    div.nav-btn-inactive div.stButton > button:hover {
        background-color: #f8fafc !important;
        color: #0f172a !important;
        border-color: #cbd5e1 !important;
    }

    /* Botão Ativo */
    div.nav-btn-active div.stButton > button {
        background-color: #0284c7 !important;
        color: #ffffff !important;
        border: 1px solid #0284c7 !important;
        box-shadow: 0 4px 6px -1px rgba(2, 132, 199, 0.25) !important;
    }

    /* Botão Sincronizar */
    div.nav-btn-sync div.stButton > button {
        background-color: #ecfdf5 !important;
        color: #065f46 !important;
        border: 1px solid #a7f3d0 !important;
    }
    div.nav-btn-sync div.stButton > button:hover {
        background-color: #d1fae5 !important;
        border-color: #6ee7b7 !important;
    }

    /* KPI CARDS */
    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
        gap: 14px;
        margin-bottom: 22px;
    }
    .kpi-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px 18px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
        position: relative;
        overflow: hidden;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px -1px rgba(0, 0, 0, 0.06);
    }
    .kpi-card::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background: #0284c7;
    }
    .kpi-card.green::before { background: #16a34a; }
    .kpi-card.red::before { background: #dc2626; }

    .kpi-label {
        font-size: 11px !important;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #64748b;
        margin-bottom: 4px;
    }
    .kpi-value {
        font-size: 21px !important;
        font-weight: 700;
        color: #0f172a;
        line-height: 1.2;
    }

    /* Inputs e formulários */
    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] > div,
    input, textarea, select {
        background-color: #ffffff !important;
        border-radius: 8px !important;
        border: 1px solid #cbd5e1 !important;
        font-size: 13px !important;
    }

    .keyboard-hint {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 8px 12px;
        border-radius: 8px;
        font-size: 11.5px !important;
        color: #334155;
        display: inline-block;
        margin-bottom: 12px;
    }
    .keyboard-hint kbd {
        background: #f1f5f9;
        border: 1px solid #cbd5e1;
        border-bottom-width: 2px;
        padding: 2px 5px;
        border-radius: 4px;
        font-weight: 700;
        font-size: 11px !important;
        color: #0f172a;
    }

    .divergence-box {
        background-color: #fff7ed;
        border: 1px solid #fed7aa;
        border-left: 4px solid #ea580c;
        border-radius: 8px;
        padding: 14px 16px;
        margin: 14px 0;
        font-size: 12.5px !important;
    }

    @media print {
        body * { visibility: hidden; }
        .no-print, [data-testid="stToolbar"], footer, div:has(.navbar-header-marker) {
            display: none !important;
        }
        .printable-area, .printable-area * {
            visibility: visible;
        }
        .printable-area {
            position: absolute;
            left: 0;
            top: 0;
            width: 100%;
            padding: 20px;
            background: #ffffff !important;
            color: #000000 !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# --- 3. COMUNICAÇÃO HTTP COM GOOGLE APPS SCRIPT ---
API_URL = "https://script.google.com/macros/s/AKfycbx6Dvaz55Vd9gzOmG5HHhvdrkRSF9w1kx4Ie7mxrWcQnjjOj1rf0ND7JIGEb1Jk-yCi/exec"

def get_session():
    session = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=1.5,
        status_forcelist=[500, 502, 503, 504],
        raise_on_status=False
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

def enviar_dados_apps_script(payload: dict) -> dict:
    try:
        session = get_session()
        payload_str = json.dumps(payload, default=str)
        headers = {"Content-Type": "text/plain;charset=utf-8"}
        
        response = session.post(
            API_URL,
            data=payload_str,
            headers=headers,
            allow_redirects=True,
            timeout=60
        )
        
        if response.status_code != 200:
            return {"status": "error", "message": f"HTTP {response.status_code}: {response.text[:200]}"}
        
        try:
            return response.json()
        except Exception:
            return {"status": "error", "message": f"Resposta inválida da API: {response.text[:250]}"}
    except Exception as ex:
        return {"status": "error", "message": f"Falha de conexão: {str(ex)}"}

def normalizar_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    if "remessa" in df.columns:
        df["remessa"] = df["remessa"].fillna("").astype(str)
        df["remessa"] = df["remessa"].str.replace(r"\.0$", "", regex=True).str.strip()

    for col in ["produto", "descricao", "local", "conferente", "observacao"]:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str).str.strip()

    return df

@st.cache_data(ttl=180, show_spinner=False)
def carregar_dados_planilha_cached():
    try:
        session = get_session()
        r = session.get(f"{API_URL}?action=listar", allow_redirects=True, timeout=60)
        if r.status_code == 200:
            try:
                dados = r.json()
                if isinstance(dados, list):
                    df = pd.DataFrame(dados)
                    return normalizar_dataframe(df)
            except Exception:
                pass
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()

def carregar_dados_planilha():
    try:
        return carregar_dados_planilha_cached()
    except Exception as e:
        st.error(f"Erro ao buscar registros da planilha: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=300, show_spinner=False)
def carregar_lista_conferentes():
    try:
        session = get_session()
        r = session.get(f"{API_URL}?action=get_conferentes", allow_redirects=True, timeout=40)
        if r.status_code == 200:
            try:
                lista = r.json()
                if isinstance(lista, list) and len(lista) > 0:
                    return sorted([str(x).strip() for x in lista if str(x).strip()])
            except Exception:
                return []
        return []
    except Exception:
        return []

def enviar_cadastro_conferente(nome):
    payload = {"action": "cadastrar_conferente", "nome": nome}
    res = enviar_dados_apps_script(payload)
    carregar_lista_conferentes.clear()
    return res

def enviar_importacao_planilha(linhas):
    payload = {"action": "importar", "linhas": linhas}
    res = enviar_dados_apps_script(payload)
    carregar_dados_planilha_cached.clear()
    return res

def enviar_atualizacao_conferencia(itens):
    payload = {"action": "atualizar", "itens": itens}
    res = enviar_dados_apps_script(payload)
    carregar_dados_planilha_cached.clear()
    return res

def formatar_data_br(data_val):
    if data_val is None or pd.isna(data_val):
        return datetime.now().strftime("%d/%m/%Y")
    
    val_str = str(data_val).strip()
    if val_str in ["", "nan", "None", "00:00:00"]:
        return datetime.now().strftime("%d/%m/%Y")

    if len(val_str) == 10 and val_str[2] == "/" and val_str[5] == "/":
        return val_str

    try:
        dt = pd.to_datetime(val_str, errors="coerce", dayfirst=True)
        if pd.notna(dt):
            return dt.strftime("%d/%m/%Y")
    except Exception:
        pass

    if " " in val_str:
        partes = val_str.split(" ")
        for p in partes:
            if "/" in p and len(p) == 10:
                return p

    return datetime.now().strftime("%d/%m/%Y")

def injetar_atalho_teclado_tab():
    components.html("""
    <script>
    (function() {
        const parentDoc = window.parent.document;
        parentDoc.addEventListener('keydown', function(e) {
            if ((e.key === 'Tab' || e.key === 'Enter') && !e.shiftKey) {
                const active = parentDoc.activeElement;
                if (active && (active.tagName === 'INPUT' || active.tagName === 'TEXTAREA')) {
                    const downEvent = new KeyboardEvent('keydown', {
                        key: 'ArrowDown',
                        code: 'ArrowDown',
                        keyCode: 40,
                        which: 40,
                        bubbles: true,
                        cancelable: true
                    });
                    
                    if (e.key === 'Tab') {
                        e.preventDefault();
                        active.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, bubbles: true }));
                        setTimeout(() => {
                            parentDoc.dispatchEvent(downEvent);
                        }, 20);
                    }
                }
            }
        }, true);
    })();
    </script>
    """, height=0, width=0)

def extrair_excel(uploaded_file):
    itens = []
    df_raw = pd.read_excel(uploaded_file, header=None, dtype=str)
    
    linha_cabecalho = None
    idx_col_prod = None
    idx_col_desc = None
    idx_col_qtd = None

    for r_idx in range(min(50, len(df_raw))):
        linha = df_raw.iloc[r_idx]
        linha_limpa = [str(val).strip().lower() for val in linha.dropna()]
        texto_linha = " ".join(linha_limpa)

        if any(termo in texto_linha for termo in ["produto", "código", "codigo", "item"]):
            linha_cabecalho = r_idx
            
            for c_idx, val in enumerate(linha):
                if pd.isna(val):
                    continue
                v = str(val).strip().lower()
                
                if any(k in v for k in ["produto", "código", "codigo", "item"]) and idx_col_prod is None:
                    idx_col_prod = c_idx
                elif any(k in v for k in ["descri", "nome", "especifica"]) and idx_col_desc is None:
                    idx_col_desc = c_idx
                elif any(k in v for k in ["quant", "qtd"]) and not any(k in v for k in ["lote", "série", "serie"]):
                    idx_col_qtd = c_idx
            break

    if linha_cabecalho is None:
        return itens

    if idx_col_prod is None:
        idx_col_prod = 0
    if idx_col_desc is None and len(df_raw.columns) > 1:
        idx_col_desc = 1

    for r_idx in range(linha_cabecalho + 1, len(df_raw)):
        linha = df_raw.iloc[r_idx]

        if linha.dropna().empty:
            continue

        cod = str(linha.iloc[idx_col_prod]).strip() if idx_col_prod < len(linha) and pd.notna(linha.iloc[idx_col_prod]) else ""
        desc = str(linha.iloc[idx_col_desc]).strip() if idx_col_desc is not None and idx_col_desc < len(linha) and pd.notna(linha.iloc[idx_col_desc]) else ""

        cod_lower = cod.lower()
        if not cod or cod_lower in ["none", "nan", "total", "subtotal", "produto", "código", "codigo", ""]:
            continue

        qtd = 0.0
        if idx_col_qtd is not None and idx_col_qtd < len(linha) and pd.notna(linha.iloc[idx_col_qtd]):
            qtd_str = str(linha.iloc[idx_col_qtd]).strip().replace(".", "").replace(",", ".")
            try:
                qtd = float(qtd_str)
            except ValueError:
                qtd = 0.0
        else:
            for val in reversed(linha):
                if pd.notna(val):
                    val_str = str(val).strip().replace(".", "").replace(",", ".")
                    try:
                        qtd = float(val_str)
                        break
                    except ValueError:
                        continue

        itens.append({
            "Produto": cod,
            "Descricao": desc if desc.lower() not in ["none", "nan"] else "",
            "Quantidade": qtd
        })

    return itens

# --- 4. HEADER SUPERIOR TOTALMENTE UNIFICADO ---
if "menu_selecionado" not in st.session_state:
    st.session_state.menu_selecionado = "Dashboard"

df_stats = carregar_dados_planilha_cached()
total_itens_carregados = len(df_stats) if not df_stats.empty else 0

# Container unificado do topo sem divs quebradas
with st.container():
    col_logo, col_info, col_nav = st.columns([0.8, 2.5, 6.7], vertical_alignment="center")

    with col_logo:
        st.markdown('<div class="navbar-header-marker"></div>', unsafe_allow_html=True)
        if img_logo_obj is not None:
            st.image(img_logo_obj, width=110)
        else:
            st.markdown('<div class="brand-fallback-box">📦</div>', unsafe_allow_html=True)

    with col_info:
        st.markdown(f"""
        <div>
            <h1 class="header-title-text">Gestão de Conferência de Mercadorias</h1>
            <p class="header-subtitle-text">Controle Operacional, Ordens & Estoque · <strong>{total_itens_carregados}</strong> itens na base</p>
        </div>
        """, unsafe_allow_html=True)

    with col_nav:
        st.markdown('<div class="nav-pill-wrapper">', unsafe_allow_html=True)
        cb1, cb2, cb3, cb4, cb5, cb_sync = st.columns([1.2, 1.2, 1.4, 1.5, 1.5, 1.2])

        opcoes_nav = [
            (cb1, "Dashboard", "📊 Dashboard"),
            (cb2, "Importar Remessa", "📥 Importar"),
            (cb3, "Folha de Impressão Cega", "🖨️ Folha Cega"),
            (cb4, "Digitar Conferência Cega", "🔍 Conferência"),
            (cb5, "Cadastrar Novo Conferente", "👤 Conferentes")
        ]

        for col_btn, nome_menu, label_btn in opcoes_nav:
            with col_btn:
                is_active = (st.session_state.menu_selecionado == nome_menu)
                classe = "nav-btn-active" if is_active else "nav-btn-inactive"
                st.markdown(f'<div class="{classe}">', unsafe_allow_html=True)
                if st.button(label_btn, key=f"nav_top_{nome_menu}", use_container_width=True):
                    st.session_state.menu_selecionado = nome_menu
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

        with cb_sync:
            st.markdown('<div class="nav-btn-sync">', unsafe_allow_html=True)
            if st.button("🔄 Sincronizar", key="nav_top_sync", use_container_width=True):
                carregar_dados_planilha_cached.clear()
                carregar_lista_conferentes.clear()
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

menu = st.session_state.menu_selecionado

# ==============================================================================
# OPÇÃO: DASHBOARD
# ==============================================================================
if menu == "Dashboard":
    with st.spinner("Compilando indicadores..."):
        df_raw = carregar_dados_planilha()

    if df_raw.empty:
        st.info("Nenhum registro encontrado na aba Conferencia para gerar o resumo.")
    else:
        df = df_raw.copy()
        
        data_col = df["data_importacao"] if "data_importacao" in df.columns else pd.Series(index=df.index, dtype=str)
        dt_parsed = pd.to_datetime(data_col, format="%d/%m/%Y", errors="coerce")
        dt_parsed = dt_parsed.fillna(pd.to_datetime(data_col, errors="coerce", dayfirst=True))
        
        df["dt_parsed"] = pd.to_datetime(dt_parsed, errors="coerce")
        df["dt_parsed"] = df["dt_parsed"].fillna(pd.Timestamp.now().normalize())

        df["mes_ano"] = df["dt_parsed"].dt.strftime("%m/%Y")
        df["dia_str"] = df["dt_parsed"].dt.strftime("%d/%m/%Y")

        df["quantidade"] = pd.to_numeric(df.get("quantidade", 0), errors="coerce").fillna(0.0)
        df["conferencia"] = pd.to_numeric(df.get("conferencia", None), errors="coerce")
        df["divergencia"] = pd.to_numeric(df.get("divergencia", None), errors="coerce")

        with st.container(border=True):
            col_f1, col_f2 = st.columns([1, 1])
            with col_f1:
                confs_unicos = sorted([str(c).strip() for c in df.get("conferente", pd.Series()).dropna().unique() if str(c).strip() != ""])
                lista_confs = ["TODOS"] + confs_unicos
                filtro_conf = st.selectbox("Filtrar por Conferente:", lista_confs)
            with col_f2:
                remessas_unicas = sorted([str(r).strip() for r in df.get("remessa", pd.Series()).dropna().unique() if str(r).strip() not in ["", "nan", "None"]])
                remessas_todas = ["TODAS"] + remessas_unicas
                filtro_rem = st.selectbox("Filtrar por Remessa:", remessas_todas)

        df_filtrado = df.copy()
        if filtro_conf != "TODOS" and "conferente" in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado["conferente"] == filtro_conf]
        if filtro_rem != "TODAS" and "remessa" in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado["remessa"] == filtro_rem]

        total_remessas = df_filtrado["remessa"].nunique() if "remessa" in df_filtrado.columns else 0
        total_itens = len(df_filtrado)
        itens_conferidos = df_filtrado[df_filtrado["conferencia"].notna()]
        total_conferidos = len(itens_conferidos)
        
        itens_sem_erro = df_filtrado[df_filtrado["divergencia"] == 0]
        itens_com_erro = df_filtrado[(df_filtrado["divergencia"].notna()) & (df_filtrado["divergencia"] != 0)]
        
        taxa_acuracia = (len(itens_sem_erro) / total_conferidos * 100) if total_conferidos > 0 else 100.0

        acuracia_cor_class = "green" if taxa_acuracia >= 98 else "red"
        divergencias_cor_class = "red" if len(itens_com_erro) > 0 else "green"

        st.markdown(f"""
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-label">Remessas Auditadas</div>
                <div class="kpi-value">{total_remessas}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Itens Conferidos</div>
                <div class="kpi-value">{total_conferidos} <span style="font-size: 13px; font-weight: 500; color: #64748b;">/ {total_itens}</span></div>
            </div>
            <div class="kpi-card {acuracia_cor_class}">
                <div class="kpi-label">Acuracidade Físico x Remessa</div>
                <div class="kpi-value">{taxa_acuracia:.1f}%</div>
            </div>
            <div class="kpi-card {divergencias_cor_class}">
                <div class="kpi-label">Itens com Divergência</div>
                <div class="kpi-value">{len(itens_com_erro)}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        with st.container(border=True):
            col_g1, col_g2 = st.columns(2)

            with col_g1:
                st.markdown("##### 📅 Conferências Realizadas por Mês")
                df_mes = df_filtrado[df_filtrado["conferencia"].notna()].groupby("mes_ano").size().reset_index(name="Qtd")
                if not df_mes.empty:
                    max_val_mes = float(df_mes["Qtd"].max() * 1.18) if df_mes["Qtd"].max() > 0 else 10.0
                    barras_mes = alt.Chart(df_mes).mark_bar(color="#0284c7", cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
                        x=alt.X("mes_ano:N", title="Mês/Ano", sort=None, axis=alt.Axis(labelAngle=0)),
                        y=alt.Y("Qtd:Q", title="Qtd. Itens", scale=alt.Scale(domain=[0, max_val_mes]))
                    )
                    textos_mes = barras_mes.mark_text(
                        align="center",
                        baseline="bottom",
                        dy=-4,
                        fontSize=11,
                        fontWeight=600,
                        color="#0f172a"
                    ).encode(
                        text="Qtd:Q"
                    )
                    chart_mes = (barras_mes + textos_mes).properties(height=260)
                    st.altair_chart(chart_mes, use_container_width=True)
                else:
                    st.info("Sem dados suficientes para a evolução mensal.")

            with col_g2:
                st.markdown("##### 📊 Volume de Conferência por Dia")
                df_dia = df_filtrado[df_filtrado["conferencia"].notna()].groupby(["dt_parsed", "dia_str"]).size().reset_index(name="Qtd").sort_values("dt_parsed")
                if not df_dia.empty:
                    max_val_dia = float(df_dia["Qtd"].max() * 1.18) if df_dia["Qtd"].max() > 0 else 10.0
                    barras_dia = alt.Chart(df_dia).mark_bar(color="#38bdf8", cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
                        x=alt.X("dia_str:N", title="Data", sort=None, axis=alt.Axis(labelAngle=-45)),
                        y=alt.Y("Qtd:Q", title="Qtd. Itens", scale=alt.Scale(domain=[0, max_val_dia]))
                    )
                    textos_dia = barras_dia.mark_text(
                        align="center",
                        baseline="bottom",
                        dy=-4,
                        fontSize=11,
                        fontWeight=600,
                        color="#0f172a"
                    ).encode(
                        text="Qtd:Q"
                    )
                    chart_dia = (barras_dia + textos_dia).properties(height=260)
                    st.altair_chart(chart_dia, use_container_width=True)
                else:
                    st.info("Sem dados suficientes para a evolução diária.")

        with st.container(border=True):
            col_e1, col_e2 = st.columns(2)

            with col_e1:
                st.markdown("##### ⚠️ Diagnóstico Geral de Divergências")
                
                def classificar_erro(div):
                    if pd.isna(div):
                        return "Pendente"
                    elif div == 0:
                        return "Sem Divergência"
                    elif div < 0:
                        return "Falta Física"
                    else:
                        return "Sobra Física"

                df_status = df_filtrado.copy()
                df_status["Diagnóstico"] = df_status["divergencia"].apply(classificar_erro)
                df_resumo_erros = df_status["Diagnóstico"].value_counts().reset_index()
                df_resumo_erros.columns = ["Diagnóstico", "Qtd. Itens"]
                df_resumo_erros["Percentual (%)"] = ((df_resumo_erros["Qtd. Itens"] / len(df_status)) * 100).round(1)

                st.dataframe(
                    df_resumo_erros,
                    column_config={
                        "Diagnóstico": "Diagnóstico",
                        "Qtd. Itens": st.column_config.NumberColumn("Qtd. Itens", format="%d"),
                        "Percentual (%)": st.column_config.NumberColumn("Percentual", format="%.1f%%")
                    },
                    hide_index=True,
                    use_container_width=True
                )

            with col_e2:
                st.markdown("##### 🏷️ Ranking de Produtos com Maior Divergência")
                df_erros_itens = df_filtrado[df_filtrado["divergencia"].fillna(0) != 0].copy()
                
                if not df_erros_itens.empty and "produto" in df_erros_itens.columns:
                    df_top_erros = df_erros_itens.groupby(["produto", "descricao"])["divergencia"].count().reset_index(name="Ocorrências")
                    df_top_erros = df_top_erros.sort_values("Ocorrências", ascending=False).head(10)
                    st.dataframe(
                        df_top_erros,
                        column_config={
                            "produto": "Código",
                            "descricao": "Descrição do Produto",
                            "Ocorrências": st.column_config.NumberColumn("Qtd. Divergências", format="%d")
                        },
                        hide_index=True,
                        use_container_width=True
                    )
                else:
                    st.success("🎉 Nenhuma divergência registrada no filtro atual!")

# ==============================================================================
# OPÇÃO: IMPORTAR REMESSA
# ==============================================================================
elif menu == "Importar Remessa":
    with st.container(border=True):
        st.markdown("#### 📥 Importação de Remessa do Fornecedor")

        col1, col2 = st.columns(2)
        with col1:
            num_remessa = st.text_input("Número da Remessa *", placeholder="Ex: 268326")
        with col2:
            nome_local_input = st.text_input("Local / Estoque de Destino *", placeholder="Ex: S.R. EMBALAGENS")

        arquivo_excel = st.file_uploader("Selecione o arquivo da Remessa (.xlsx ou .xls)", type=["xlsx", "xls"])

        if st.button("Processar e Salvar Remessa"):
            if not num_remessa or not nome_local_input or not arquivo_excel:
                st.error("Preencha todos os campos obrigatórios e anexe o arquivo.")
            else:
                nome_local = str(nome_local_input).strip().upper()
                remessa_limpa = str(num_remessa).strip()

                with st.spinner("Processando linhas a partir da coluna 'Produto'..."):
                    itens = extrair_excel(arquivo_excel)

                if not itens:
                    st.warning("Nenhum item válido encontrado no arquivo. Verifique se o cabeçalho possui a coluna 'Produto' ou 'Código'.")
                else:
                    data_importacao = datetime.now().strftime("%d/%m/%Y")
                    
                    linhas_para_sheets = []
                    for item in itens:
                        linhas_para_sheets.append([
                            remessa_limpa,
                            nome_local,
                            data_importacao,
                            str(item["Produto"]).strip(),
                            str(item["Descricao"]).strip(),
                            float(item["Quantidade"]),
                            "",
                            "",
                            "",
                            ""
                        ])

                    with st.spinner("Gravando linhas na aba Conferencia..."):
                        res = enviar_importacao_planilha(linhas_para_sheets)
                        if res.get("status") == "success":
                            st.success(f"✅ {len(linhas_para_sheets)} itens gravados com sucesso para a remessa **{remessa_limpa}** (Estoque: **{nome_local}**)!")
                            df_preview = pd.DataFrame(itens)
                            st.dataframe(df_preview, use_container_width=True)
                        else:
                            st.error(f"Erro: {res.get('message', 'Falha ao processar requisição')}")

# ==============================================================================
# OPÇÃO: FOLHA DE IMPRESSÃO CEGA
# ==============================================================================
elif menu == "Folha de Impressão Cega":
    with st.container(border=True):
        st.markdown("#### 🖨️ Ficha de Contagem Cega para Impressão")

        with st.spinner("Consultando dados..."):
            df = carregar_dados_planilha()

        if df.empty:
            st.info("Nenhuma remessa encontrada na aba Conferencia.")
        else:
            remessas_disponiveis = [
                str(r).strip() for r in df["remessa"].dropna().unique().tolist()
                if str(r).strip() not in ["", "nan", "None"]
            ]
            remessa_selecionada = st.selectbox("Selecione a Remessa para Gerar a Impressão:", [""] + remessas_disponiveis)

            if remessa_selecionada:
                remessa_busca = str(remessa_selecionada).strip()
                dados_remessa = df[df["remessa"].astype(str).str.strip() == remessa_busca].copy()

                if dados_remessa.empty:
                    st.warning("Nenhum item localizado para a remessa selecionada.")
                else:
                    data_cad = formatar_data_br(dados_remessa["data_importacao"].iloc[0])
                    local_cad = str(dados_remessa["local"].iloc[0]).upper()

                    linhas_tabela = ""
                    for _, row in dados_remessa.iterrows():
                        cod_item = str(row.get('produto', ''))
                        desc_item = str(row.get('descricao', ''))
                        linhas_tabela += (
                            "<tr>"
                            f"<td style='border: 1px solid #cbd5e1; padding: 4px 6px; font-weight: 700; font-size: 10px; color: #0f172a;'>{cod_item}</td>"
                            f"<td style='border: 1px solid #cbd5e1; padding: 4px 6px; font-size: 10px; color: #334155; line-height: 1.2;'>{desc_item}</td>"
                            "<td style='border: 1px solid #cbd5e1; padding: 4px 6px; height: 22px;'></td>"
                            "</tr>"
                        )

                    documento_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
            color: #0f172a;
            margin: 0;
            padding: 4px;
            background-color: #ffffff;
        }}
        .header-box {{
            border-bottom: 2px solid #0f172a;
            padding-bottom: 6px;
            margin-bottom: 8px;
        }}
        .header-title {{
            font-size: 13.5px;
            font-weight: 800;
            margin: 0 0 4px 0;
            color: #0f172a;
            text-transform: uppercase;
        }}
        .header-meta {{
            display: flex;
            gap: 20px;
            font-size: 10.5px;
            color: #475569;
            font-weight: 600;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 6px;
        }}
        th {{
            border: 1px solid #94a3b8;
            background-color: #f8fafc;
            padding: 5px 6px;
            font-size: 10px;
            text-align: left;
            font-weight: 700;
            color: #0f172a;
        }}
        .signature-box {{
            margin-top: 24px;
            display: flex;
            justify-content: space-between;
            font-size: 10px;
            color: #475569;
        }}
        .btn-imprimir {{
            background: #0284c7;
            color: white;
            border: none;
            padding: 7px 16px;
            font-size: 11.5px;
            font-weight: 600;
            border-radius: 6px;
            cursor: pointer;
            margin-bottom: 10px;
        }}
        @media print {{
            .btn-imprimir {{
                display: none !important;
            }}
            @page {{
                margin: 6mm;
            }}
        }}
    </style>
</head>
<body>
    <button class="btn-imprimir" onclick="window.print()">🖨️ Imprimir Folha de Contagem</button>

    <div class="header-box">
        <div class="header-title">Folha de Conferência Física (Contagem Cega)</div>
        <div class="header-meta">
            <div>REMESSA: <strong>{remessa_selecionada}</strong></div>
            <div>LOCAL: <strong>{local_cad}</strong></div>
            <div>DATA: <strong>{data_cad}</strong></div>
        </div>
    </div>

    <table>
        <thead>
            <tr>
                <th style="width: 20%;">CÓDIGO</th>
                <th style="width: 60%;">DESCRIÇÃO DO PRODUTO</th>
                <th style="width: 20%; text-align: center;">QTD. CONFERIDA</th>
            </tr>
        </thead>
        <tbody>
            {linhas_tabela}
        </tbody>
    </table>

    <div class="signature-box">
        <div>Assinatura do Conferente: _____________________________________</div>
        <div>Data da Conferência: ____/____/________</div>
    </div>
</body>
</html>"""

                    altura_calculada = max(360, 110 + (len(dados_remessa) * 28))
                    components.html(documento_html, height=altura_calculada, scrolling=True)

# ==============================================================================
# OPÇÃO: DIGITAR CONFERÊNCIA CEGA
# ==============================================================================
elif menu == "Digitar Conferência Cega":
    with st.container(border=True):
        st.markdown("#### 🔍 Digitação de Contagem e Validação de Divergências")

        with st.spinner("Buscando registros..."):
            df = carregar_dados_planilha()

        if df.empty:
            st.info("Nenhuma remessa encontrada para conferência.")
        else:
            remessas = [
                str(r).strip() for r in df["remessa"].dropna().unique().tolist()
                if str(r).strip() not in ["", "nan", "None"]
            ]
            remessa_pesquisa = st.selectbox("Pesquisar pelo Número da Remessa:", [""] + remessas)

            if remessa_pesquisa:
                remessa_alvo = str(remessa_pesquisa).strip()
                itens_remessa = df[df["remessa"].astype(str).str.strip() == remessa_alvo].copy()

                if itens_remessa.empty:
                    st.warning("Nenhum item localizado para a remessa selecionada.")
                else:
                    local_atual = str(itens_remessa["local"].iloc[0]).upper()
                    data_atual_br = formatar_data_br(itens_remessa["data_importacao"].iloc[0])

                    itens_remessa["quantidade"] = pd.to_numeric(itens_remessa["quantidade"], errors="coerce").fillna(0.0)
                    itens_remessa["conferencia"] = pd.to_numeric(itens_remessa["conferencia"], errors="coerce")
                    itens_remessa["divergencia"] = pd.to_numeric(itens_remessa["divergencia"], errors="coerce")

                    ja_conferida = itens_remessa["conferencia"].notna().any()
                    itens_divergentes = itens_remessa[itens_remessa["divergencia"].fillna(1) != 0].copy()

                    if ja_conferida and len(itens_divergentes) > 0:
                        modo_reconferencia = True
                        dados_trabalho = itens_divergentes.copy()
                        st.warning(f"⚠️ **Segunda Conferência (Apenas Divergências):** Foram identificados **{len(itens_divergentes)} item(ns)** divergentes. Reconte apenas os itens listados abaixo.")
                    elif ja_conferida and len(itens_divergentes) == 0:
                        modo_reconferencia = False
                        dados_trabalho = itens_remessa.copy()
                        st.success("✨ **Remessa 100% Conferida e Sem Divergências!** Todos os itens foram validados com sucesso.")
                    else:
                        modo_reconferencia = False
                        dados_trabalho = itens_remessa.copy()
                        st.info("📋 **Primeira Conferência (Contagem Cega):** Digite a quantidade física contada para cada produto.")

                    st.markdown(f"""
                    <div class="kpi-grid">
                        <div class="kpi-card">
                            <div class="kpi-label">Remessa</div>
                            <div class="kpi-value">{remessa_alvo}</div>
                        </div>
                        <div class="kpi-card">
                            <div class="kpi-label">Local / Depósito</div>
                            <div class="kpi-value">{local_atual}</div>
                        </div>
                        <div class="kpi-card">
                            <div class="kpi-label">Data de Importação</div>
                            <div class="kpi-value">{data_atual_br}</div>
                        </div>
                        <div class="kpi-card">
                            <div class="kpi-label">Itens a Conferir</div>
                            <div class="kpi-value">{len(dados_trabalho)}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    lista_conferentes = carregar_lista_conferentes()
                    conferente_anterior = ""
                    if "conferente" in dados_trabalho.columns and dados_trabalho["conferente"].dropna().any():
                        conferente_anterior = str(dados_trabalho["conferente"].dropna().iloc[0]).strip().upper()

                    if not lista_conferentes:
                        st.warning("⚠️ Nenhum conferente localizado na coluna D da aba 'Local-Estoque'.")
                        nome_conferente_final = ""
                    else:
                        idx_default = 0
                        if conferente_anterior in lista_conferentes:
                            idx_default = lista_conferentes.index(conferente_anterior) + 1
                        
                        nome_conferente_sel = st.selectbox(
                            "Selecione o Conferente Responsável *",
                            ["-- Selecione o conferente --"] + lista_conferentes,
                            index=idx_default
                        )
                        nome_conferente_final = "" if nome_conferente_sel == "-- Selecione o conferente --" else nome_conferente_sel

                    dados_trabalho["conferencia"] = dados_trabalho["conferencia"].fillna(0.0)
                    df_editavel = dados_trabalho[["row_index", "produto", "descricao", "conferencia"]].copy()

                    st.markdown("""
                    <div class="keyboard-hint">
                        ⚡ <strong>Agilidade de Digitação:</strong> Digite o valor e aperte <kbd>Enter</kbd> para registrar e descer direto para o próximo produto.
                    </div>
                    """, unsafe_allow_html=True)

                    injetar_atalho_teclado_tab()

                    editado = st.data_editor(
                        df_editavel,
                        column_config={
                            "row_index": None,
                            "produto": st.column_config.TextColumn("Código", disabled=True),
                            "descricao": st.column_config.TextColumn("Descrição", disabled=True),
                            "conferencia": st.column_config.NumberColumn(
                                "Conferência (Físico)",
                                min_value=0.0,
                                step=1.0,
                                format="%.2f",
                                required=True
                            ),
                        },
                        use_container_width=True,
                        hide_index=True,
                        key=f"editor_conferencia_{remessa_alvo}_{modo_reconferencia}"
                    )

                    mapa_esperado = dados_trabalho.set_index("row_index")["quantidade"].to_dict()
                    itens_com_divergencia_detectada = []

                    for _, row in editado.iterrows():
                        r_id = int(row["row_index"])
                        conf_val = float(row["conferencia"])
                        qtd_esp = mapa_esperado.get(r_id, 0.0)
                        if conf_val - qtd_esp != 0:
                            itens_com_divergencia_detectada.append({
                                "row_index": r_id,
                                "produto": str(row["produto"]),
                                "descricao": str(row["descricao"]),
                                "conferido": conf_val,
                                "divergencia": conf_val - qtd_esp
                            })

                    st.markdown("<hr style='margin: 18px 0; border: none; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)
                    autorizar_divergencia = st.checkbox("⚠️ Autorizar encerramento/finalização da conferência com divergência")
                    justificativas_itens = {}

                    if autorizar_divergencia:
                        if len(itens_com_divergencia_detectada) == 0:
                            st.info("✨ Não há itens divergentes no momento. Ao salvar, todos os itens constarão como conferidos sem divergência.")
                        else:
                            st.markdown("""
                            <div class="divergence-box">
                                <strong style="color: #9a3412;">📝 Justificativa Individual por Item Divergente</strong><br>
                                <span style="font-size: 12px; color: #7c2d12;">
                                    Informe a justificativa específica para cada produto que apresentou divergência. Ela será gravada na linha exata do produto (Coluna J).
                                </span>
                            </div>
                            """, unsafe_allow_html=True)

                            for item_div in itens_com_divergencia_detectada:
                                r_id = item_div["row_index"]
                                label_item = f"Produto: {item_div['produto']} - {item_div['descricao']} (Qtd Físico: {item_div['conferido']:.2f})"
                                
                                obs_anterior = ""
                                if "observacao" in dados_trabalho.columns:
                                    linha_orig = dados_trabalho[dados_trabalho["row_index"] == r_id]
                                    if not linha_orig.empty and pd.notna(linha_orig["observacao"].iloc[0]):
                                        obs_anterior = str(linha_orig["observacao"].iloc[0]).strip()

                                justificativas_itens[r_id] = st.text_input(
                                    f"Justificativa para {label_item} *",
                                    value=obs_anterior,
                                    placeholder="Ex: Mercadoria avariada / Sobra de lote / Falta confirmada no fornecedor",
                                    key=f"justificativa_item_{r_id}"
                                )

                    if st.button("⚖️ Comparar e Gravar Conferência"):
                        if not nome_conferente_final:
                            st.error("⚠️ Selecione o **Nome do Conferente** na lista antes de gravar.")
                        else:
                            justificativas_pendentes = False
                            if autorizar_divergencia:
                                for it in itens_com_divergencia_detectada:
                                    r_id = it["row_index"]
                                    if not str(justificativas_itens.get(r_id, "")).strip():
                                        justificativas_pendentes = True
                                        break

                            if autorizar_divergencia and justificativas_pendentes:
                                st.error("⚠️ Você optou por autorizar a divergência. É **obrigatório** preencher a justificativa para todos os produtos divergentes listados acima.")
                            else:
                                with st.spinner("Gravando conferência na aba Conferencia..."):
                                    itens_atualizar = []
                                    resultados_exibicao = []

                                    for _, row in editado.iterrows():
                                        r_id = int(row["row_index"])
                                        conf_val = float(row["conferencia"])
                                        qtd_esp = mapa_esperado.get(r_id, 0.0)
                                        div_val = conf_val - qtd_esp

                                        obs_do_item = ""
                                        if div_val != 0 and autorizar_divergencia:
                                            obs_do_item = str(justificativas_itens.get(r_id, "")).strip().upper()

                                        itens_atualizar.append({
                                            "row_index": r_id,
                                            "conferencia": conf_val,
                                            "divergencia": div_val,
                                            "conferente": nome_conferente_final,
                                            "observacao": obs_do_item
                                        })

                                        status = "Correto (Sem Divergência)" if div_val == 0 else "Divergente"
                                        resultados_exibicao.append({
                                            "produto": row["produto"],
                                            "descricao": row["descricao"],
                                            "conferencia": conf_val,
                                            "conferente": nome_conferente_final,
                                            "status": status,
                                            "justificativa": obs_do_item,
                                            "_tem_erro": (div_val != 0)
                                        })

                                    res = enviar_atualizacao_conferencia(itens_atualizar)

                                    if res.get("status") == "success":
                                        msg_sucesso = f"✅ Dados gravados com sucesso! Conferente: **{nome_conferente_final}**."
                                        if autorizar_divergencia and len(itens_com_divergencia_detectada) > 0:
                                            msg_sucesso += " Justificativas lançadas na linha de cada produto divergente (Coluna J)."
                                        st.success(msg_sucesso)
                                        
                                        df_resultado = pd.DataFrame(resultados_exibicao)
                                        
                                        def colorir_status(val):
                                            if "Divergente" in str(val):
                                                return "background-color: #fee2e2; color: #991b1b; font-weight: 700;"
                                            else:
                                                return "background-color: #f0fdf4; color: #15803d; font-weight: 600;"

                                        st.write("### 📊 Resultado da Conferência")
                                        
                                        colunas_tabela = ["produto", "descricao", "conferencia", "conferente", "status"]
                                        if autorizar_divergencia:
                                            colunas_tabela.append("justificativa")

                                        df_mostrar = df_resultado[colunas_tabela]
                                        styler_res = df_mostrar.style
                                        if hasattr(styler_res, "map"):
                                            styler_res = styler_res.map(colorir_status, subset=["status"])
                                        else:
                                            styler_res = styler_res.applymap(colorir_status, subset=["status"])

                                        st.dataframe(
                                            styler_res,
                                            column_config={
                                                "produto": "Código",
                                                "descricao": "Descrição",
                                                "conferencia": st.column_config.NumberColumn("Qtd. Conferida", format="%.2f"),
                                                "conferente": "Conferente",
                                                "status": "Situação da Contagem",
                                                "justificativa": "Justificativa (Coluna J)"
                                            },
                                            use_container_width=True
                                        )

                                        total_erros = df_resultado["_tem_erro"].sum()
                                        if total_erros == 0:
                                            st.balloons()
                                            st.success("🎉 **Perfeito!** Todos os itens batem com a remessa.")
                                        else:
                                            if autorizar_divergencia:
                                                st.info("ℹ️ **Conferência Finalizada com Justificativa:** As pendências foram autorizadas e registradas nos itens específicos.")
                                        else:
                                            st.warning(f"⚠️ **Atenção:** Existem **{total_erros} item(ns) divergente(s)**. Busque a remessa novamente para realizar a segunda conferência ou marque a opção de autorizar a divergência com justificativa item a item.")
                                else:
                                    mensagem_erro = res.get("message", "Falha na comunicação com a planilha")
                                    st.error(f"Erro ao salvar: {mensagem_erro}")

# ==============================================================================
# OPÇÃO: CADASTRAR NOVO CONFERENTE
# ==============================================================================
elif menu == "Cadastrar Novo Conferente":
    with st.container(border=True):
        st.markdown("#### 👤 Cadastro de Novo Conferente")
        st.caption("Os conferentes cadastrados são registrados na Coluna D da aba **Local-Estoque**.")

        col1, col2 = st.columns([2, 1])
        with col1:
            novo_conferente = st.text_input("Nome Completo do Conferente *", placeholder="Ex: JOÃO SILVA")
            if st.button("Cadastrar Conferente"):
                if not novo_conferente.strip():
                    st.error("Informe o nome do conferente para realizar o cadastro.")
                else:
                    nome_formatado = novo_conferente.strip().upper()
                    with st.spinner("Salvando novo conferente..."):
                        res = enviar_cadastro_conferente(nome_formatado)
                        if res.get("status") == "success":
                            st.success(f"✅ Conferente **{nome_formatado}** cadastrado com sucesso!")
                            st.balloons()
                        else:
                            mensagem_erro = res.get("message", "Falha de comunicação")
                            st.error(f"Erro ao cadastrar: {mensagem_erro}")

        st.markdown("<hr style='margin: 18px 0; border: none; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)
        st.write("#### 👥 Conferentes Atualmente Cadastrados:")
        conferentes_atuais = carregar_lista_conferentes()
        if conferentes_atuais:
            df_conf = pd.DataFrame(conferentes_atuais, columns=["Nome do Conferente"])
            st.dataframe(df_conf, use_container_width=True)
        else:
            st.info("Nenhum conferente localizado até o momento.")