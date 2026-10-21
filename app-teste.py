import streamlit as st
import pandas as pd
from datetime import datetime
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
import streamlit.components.v1 as components

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Gestão de Conferência de Mercadorias",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização Corporativa Compacta (Fontes Reduzidas, Tipografia Moderna Inter/Segoe UI)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"], [class*="st-"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        font-size: 13px !important;
    }
    
    /* Títulos e Subtítulos Compactos */
    .main-title {
        font-size: 19px !important;
        font-weight: 700 !important;
        color: #0f134f !important;
        margin-bottom: 4px !important;
        padding-bottom: 6px !important;
        border-bottom: 1.5px solid #e2e8f0 !important;
        letter-spacing: -0.2px !important;
    }
    .sub-title {
        font-size: 12px !important;
        color: #64748b !important;
        margin-bottom: 16px !important;
    }

    /* Cards Corporativos Densos e Modernos */
    .metric-container {
        display: flex;
        gap: 12px;
        margin-bottom: 18px;
        flex-wrap: wrap;
    }
    .metric-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-left: 4px solid #273270;
        padding: 10px 14px;
        border-radius: 8px;
        flex: 1;
        min-width: 170px;
        box-shadow: 0 2px 6px rgba(15, 19, 79, 0.04);
        transition: all 0.2s ease-in-out;
    }
    .metric-card:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 10px rgba(15, 19, 79, 0.08);
    }
    .metric-card span {
        font-size: 10.5px !important;
        color: #64748b;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.4px;
    }
    .metric-card strong {
        display: block;
        font-size: 15px !important;
        color: #0f134f;
        margin-top: 3px;
        font-weight: 700;
    }

    .keyboard-hint {
        background-color: #f8fafc;
        border: 1px solid #cbd5e1;
        padding: 6px 10px;
        border-radius: 5px;
        font-size: 11px !important;
        color: #334155;
        display: inline-block;
        margin-bottom: 10px;
    }
    .keyboard-hint kbd {
        background: #ffffff;
        border: 1px solid #94a3b8;
        border-bottom-width: 2px;
        padding: 1px 4px;
        border-radius: 3px;
        font-weight: 700;
        font-size: 10.5px !important;
        color: #0f134f;
    }

    .divergence-box {
        background-color: #fff7ed;
        border: 1px solid #fdba74;
        border-radius: 6px;
        padding: 12px 14px;
        margin-top: 10px;
        margin-bottom: 10px;
        font-size: 12px !important;
    }

    /* Redução de Fontes em Inputs, Textarea, Select e Checkbox */
    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] > div,
    input, textarea, select {
        font-size: 12.5px !important;
    }
    label p {
        font-size: 12px !important;
        font-weight: 600 !important;
        color: #1e293b !important;
    }
    div[data-testid="stCheckbox"] label p {
        font-size: 12px !important;
        font-weight: 600 !important;
    }

    /* Degradê Aplicado aos Botões com Escala Compacta */
    div.stButton > button, div.stButton > button:hover, div.stButton > button:active, div.stButton > button:focus {
        background: -webkit-linear-gradient(90deg, #0f134f, #273270, #494c8c) !important;
        background: linear-gradient(90deg, #0f134f, #273270, #494c8c) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        padding: 7px 16px !important;
        font-size: 12.5px !important;
        letter-spacing: 0.2px !important;
        box-shadow: 0 2px 8px rgba(15, 19, 79, 0.16) !important;
        transition: opacity 0.2s ease-in-out, transform 0.1s ease-in-out !important;
    }
    div.stButton > button:hover {
        opacity: 0.95 !important;
        transform: scale(1.005) !important;
    }

    /* Barra Lateral com Fontes Corporativas */
    [data-testid="stSidebar"] {
        background-color: #f8fafc;
        border-right: 1px solid #e2e8f0;
    }
    .sidebar-brand {
        padding: 10px 12px;
        border-radius: 6px;
        background: linear-gradient(90deg, #0f134f, #273270, #494c8c);
        color: #ffffff;
        margin-bottom: 14px;
        text-align: center;
        font-weight: 700;
        font-size: 13px !important;
        letter-spacing: 0.4px;
        box-shadow: 0 2px 6px rgba(15, 19, 79, 0.15);
    }
    .sidebar-menu-title {
        font-size: 10.5px !important;
        font-weight: 700 !important;
        color: #64748b !important;
        margin-bottom: 6px !important;
        letter-spacing: 0.5px !important;
    }

    /* Redução de Fontes nas Tabelas e Data Editor */
    [data-testid="stDataFrame"] div, [data-testid="stDataEditor"] div {
        font-size: 12px !important;
    }

    @media print {
        header, .stSidebar, .stButton, [data-testid="stToolbar"], footer, .no-print {
            display: none !important;
        }
        .printable-area {
            display: block !important;
            width: 100% !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            border: 1px solid #1e293b !important;
            padding: 3px 5px !important;
            font-size: 9.5px !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# --- 2. CONFIGURAÇÃO DA API & SESSÃO RESILIENTE ---
API_URL = "https://script.google.com/macros/s/AKfycbz59wGY8R9S3j-jOv0sbxIjwKSLiakWrFBPez9VZWGoMhxdDWpdsTazsjBXsxm9hYMC/exec"

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

# --- 3. COMUNICAÇÃO COM CACHE INTELIGENTE ---
@st.cache_data(ttl=180, show_spinner=False)
def carregar_dados_planilha_cached():
    session = get_session()
    r = session.get(API_URL, timeout=60)
    dados = r.json()
    if isinstance(dados, list):
        return pd.DataFrame(dados)
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
        r = session.get(f"{API_URL}?action=get_conferentes", timeout=40)
        lista = r.json()
        if isinstance(lista, list) and len(lista) > 0:
            return sorted(lista)
        return []
    except Exception:
        return []

def enviar_cadastro_conferente(nome):
    try:
        session = get_session()
        payload = {"action": "cadastrar_conferente", "nome": nome}
        r = session.post(API_URL, json=payload, timeout=50)
        carregar_lista_conferentes.clear()
        return r.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}

def enviar_importacao_planilha(linhas):
    try:
        session = get_session()
        payload = {"action": "importar", "linhas": linhas}
        r = session.post(API_URL, json=payload, timeout=60)
        carregar_dados_planilha_cached.clear()
        return r.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}

def enviar_atualizacao_conferencia(itens):
    try:
        session = get_session()
        payload = {"action": "atualizar", "itens": itens}
        r = session.post(API_URL, json=payload, timeout=60)
        carregar_dados_planilha_cached.clear()
        return r.json()
    except Exception as e:
        return {"status": "error", "message": str(e)}

def formatar_data_br(data_val):
    if data_val is None or pd.isna(data_val):
        return datetime.now().strftime("%d/%m/%Y")
    
    val_str = str(data_val).strip()
    if val_str in ["", "nan", "None"]:
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

# --- 4. EXTRAÇÃO DO EXCEL ---
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

# --- 5. NAVEGAÇÃO POR BOTÕES ---
if "menu_selecionado" not in st.session_state:
    st.session_state.menu_selecionado = "Importar Remessa"

st.sidebar.markdown('<div class="sidebar-brand">ESTOQUE & CONFERÊNCIA</div>', unsafe_allow_html=True)
st.sidebar.markdown('<p class="sidebar-menu-title">MENU DE NAVEGAÇÃO</p>', unsafe_allow_html=True)

opcoes_menu = [
    "Importar Remessa",
    "Folha de Impressão Cega",
    "Digitar Conferência Cega",
    "Cadastrar Novo Conferente"
]

for opcao in opcoes_menu:
    is_active = (st.session_state.menu_selecionado == opcao)
    rotulo = f"▶ {opcao}" if is_active else opcao
    if st.sidebar.button(rotulo, key=f"btn_nav_{opcao}", use_container_width=True):
        st.session_state.menu_selecionado = opcao
        st.rerun()

st.sidebar.write("---")
if st.sidebar.button("🔄 Sincronizar / Atualizar Planilha", use_container_width=True):
    carregar_dados_planilha_cached.clear()
    carregar_lista_conferentes.clear()
    st.rerun()

menu = st.session_state.menu_selecionado

# ==============================================================================
# OPÇÃO: IMPORTAR REMESSA
# ==============================================================================
if menu == "Importar Remessa":
    st.markdown('<div class="main-title">📥 Importação de Remessa</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        num_remessa = st.text_input("Número da Remessa *", placeholder="Ex: REM-2026-001")
    with col2:
        nome_local_input = st.text_input("Local / Filial de Destino *", placeholder="Ex: ALMOXARIFADO CENTRAL")

    arquivo_excel = st.file_uploader("Selecione o arquivo da Remessa", type=["xlsx", "xls"])

    if st.button("Processar e Salvar", type="primary"):
        if not num_remessa or not nome_local_input or not arquivo_excel:
            st.error("Preencha todos os campos obrigatórios e anexe o arquivo.")
        else:
            nome_local = str(nome_local_input).strip().upper()

            with st.spinner("Processando linhas a partir da coluna 'Produto'..."):
                itens = extrair_excel(arquivo_excel)

            if not itens:
                st.warning("Nenhum item válido encontrado no arquivo. Verifique se o cabeçalho possui a coluna 'Produto' ou 'Código'.")
            else:
                data_importacao = datetime.now().strftime("%d/%m/%Y")
                
                linhas_para_sheets = []
                for item in itens:
                    linhas_para_sheets.append([
                        num_remessa,          # A: Remessa
                        nome_local,           # B: Local (MAIÚSCULO)
                        data_importacao,      # C: Data BR
                        item["Produto"],      # D: Produto
                        item["Descricao"],    # E: Descrição
                        item["Quantidade"],   # F: Quantidade
                        "",                   # G: Conferência
                        "",                   # H: Divergência
                        "",                   # I: Conferente
                        ""                    # J: Observação / Justificativa
                    ])

                with st.spinner("Gravando linhas..."):
                    res = enviar_importacao_planilha(linhas_para_sheets)
                    if res.get("status") == "success":
                        st.success(f"✅ {len(linhas_para_sheets)} itens gravados com sucesso para a remessa **{num_remessa}** (Local: **{nome_local}** | Data: **{data_importacao}**)!")
                        df_preview = pd.DataFrame(itens)
                        st.dataframe(df_preview, use_container_width=True)
                    else:
                        st.error(f"Erro: {res.get('message', 'Falha ao processar requisição')}")

# ==============================================================================
# OPÇÃO: FOLHA DE IMPRESSÃO CEGA (ECONÔMICA)
# ==============================================================================
elif menu == "Folha de Impressão Cega":
    st.markdown('<div class="main-title">🖨️ Folha de Separação / Contagem Cega</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Gere a folha física com formato compacto para economia de papel.</div>', unsafe_allow_html=True)

    with st.spinner("Consultando dados..."):
        df = carregar_dados_planilha()

    if df.empty:
        st.info("Nenhuma remessa encontrada.")
    else:
        remessas_disponiveis = [r for r in df["remessa"].dropna().unique().tolist() if str(r).strip() != ""]
        remessa_selecionada = st.selectbox("Selecione a Remessa para Gerar a Impressão:", [""] + remessas_disponiveis)

        if remessa_selecionada:
            dados_remessa = df[df["remessa"] == remessa_selecionada].copy()

            data_cad = formatar_data_br(dados_remessa["data_importacao"].iloc[0]) if not dados_remessa.empty else ""
            local_cad = str(dados_remessa["local"].iloc[0]).upper() if not dados_remessa.empty else ""

            linhas_tabela = ""
            for _, row in dados_remessa.iterrows():
                cod_item = str(row.get('produto', ''))
                desc_item = str(row.get('descricao', ''))
                linhas_tabela += (
                    "<tr>"
                    f"<td style='border: 1px solid #475569; padding: 3px 5px; font-weight: bold; font-size: 9.5px;'>{cod_item}</td>"
                    f"<td style='border: 1px solid #475569; padding: 3px 5px; font-size: 9.5px; line-height: 1.15;'>{desc_item}</td>"
                    "<td style='border: 1px solid #475569; padding: 3px 5px; height: 20px;'></td>"
                    "</tr>"
                )

            documento_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: Arial, Helvetica, sans-serif;
            color: #0f172a;
            margin: 0;
            padding: 4px;
            background-color: #ffffff;
        }}
        .header-box {{
            border-bottom: 1.5px solid #0f134f;
            padding-bottom: 5px;
            margin-bottom: 6px;
        }}
        .header-title {{
            font-size: 13.5px;
            font-weight: bold;
            margin: 0 0 3px 0;
            color: #0f134f;
            text-transform: uppercase;
        }}
        .header-meta {{
            display: flex;
            gap: 16px;
            font-size: 10px;
            color: #334155;
            font-weight: 600;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 5px;
        }}
        th {{
            border: 1px solid #0f134f;
            background-color: #f1f5f9;
            padding: 4px 5px;
            font-size: 10px;
            text-align: left;
            font-weight: bold;
        }}
        .signature-box {{
            margin-top: 20px;
            display: flex;
            justify-content: space-between;
            font-size: 9.5px;
            color: #334155;
            padding-top: 4px;
        }}
        .btn-imprimir {{
            background: linear-gradient(90deg, #0f134f, #273270, #494c8c);
            color: white;
            border: none;
            padding: 6px 14px;
            font-size: 11px;
            font-weight: 600;
            border-radius: 5px;
            cursor: pointer;
            margin-bottom: 8px;
        }}
        @media print {{
            .btn-imprimir {{
                display: none !important;
            }}
            body {{
                padding: 0;
            }}
            @page {{
                margin: 6mm;
            }}
        }}
    </style>
</head>
<body>
    <button class="btn-imprimir" onclick="window.print()">🖨️ Imprimir Folha Econômica</button>

    <div class="header-box">
        <div class="header-title">FOLHA DE CONFERÊNCIA FÍSICA (CONTAGEM CEGA)</div>
        <div class="header-meta">
            <div>REMESSA: {remessa_selecionada}</div>
            <div>LOCAL: {local_cad}</div>
            <div>DATA: {data_cad}</div>
        </div>
    </div>

    <table>
        <thead>
            <tr>
                <th style="width: 18%;">CÓDIGO</th>
                <th style="width: 62%;">DESCRIÇÃO DO PRODUTO</th>
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

            altura_calculada = max(360, 100 + (len(dados_remessa) * 26))
            components.html(documento_html, height=altura_calculada, scrolling=True)

# ==============================================================================
# OPÇÃO: DIGITAR CONFERÊNCIA CEGA & JUSTIFICATIVA POR ITEM
# ==============================================================================
elif menu == "Digitar Conferência Cega":
    st.markdown('<div class="main-title">🔍 Digitação de Conferência Cega e Validação</div>', unsafe_allow_html=True)

    with st.spinner("Buscando registros..."):
        df = carregar_dados_planilha()

    if df.empty:
        st.info("Nenhuma remessa encontrada para conferência.")
    else:
        remessas = [r for r in df["remessa"].dropna().unique().tolist() if str(r).strip() != ""]
        remessa_pesquisa = st.selectbox("Pesquisar pelo Número da Remessa:", [""] + remessas)

        if remessa_pesquisa:
            itens_remessa = df[df["remessa"] == remessa_pesquisa].copy()

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
            <div class="metric-container">
                <div class="metric-card">
                    <span>Remessa</span>
                    <strong>{remessa_pesquisa}</strong>
                </div>
                <div class="metric-card">
                    <span>Local / Depósito</span>
                    <strong>{local_atual}</strong>
                </div>
                <div class="metric-card">
                    <span>Data de Importação</span>
                    <strong>{data_atual_br}</strong>
                </div>
                <div class="metric-card">
                    <span>Itens a Conferir</span>
                    <strong>{len(dados_trabalho)}</strong>
                </div>
            </div>
            """, unsafe_allow_html=True)

            lista_conferentes = carregar_lista_conferentes()
            conferente_anterior = ""
            if "conferente" in dados_trabalho.columns and dados_trabalho["conferente"].dropna().any():
                conferente_anterior = str(dados_trabalho["conferente"].dropna().iloc[0]).strip().upper()

            if not lista_conferentes:
                st.warning("⚠️ Nenhum conferente encontrado na lista. Cadastre um conferente no menu lateral.")
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
                ⚡ <strong>Agilidade de Digitação:</strong> Digite o valor e aperte <kbd>Enter</kbd> para salvar e descer direto para o próximo produto.
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
                key=f"editor_conferencia_{remessa_pesquisa}_{modo_reconferencia}"
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

            st.write("---")
            autorizar_divergencia = st.checkbox("⚠️ Autorizar encerramento/finalização da conferência com divergência")
            justificativas_itens = {}

            if autorizar_divergencia:
                if len(itens_com_divergencia_detectada) == 0:
                    st.info("✨ Não há itens divergentes no momento. Ao salvar, todos os itens constarão como conferidos sem divergência.")
                else:
                    st.markdown("""
                    <div class="divergence-box">
                        <strong style="color: #9a3412;">📝 Justificativa Individual por Item Divergente</strong><br>
                        <span style="font-size: 11.5px; color: #431407;">
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

            if st.button("⚖️ Comparar e Gravar", type="primary"):
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
                        with st.spinner("Gravando conferência e justificativas por item..."):
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
    st.markdown('<div class="main-title">👤 Cadastro de Conferente</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])
    with col1:
        novo_conferente = st.text_input("Nome Completo do Conferente *", placeholder="Ex: JOÃO SILVA")
        if st.button("Cadastrar Conferente", type="primary"):
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

    st.write("---")
    st.write("#### 👥 Conferentes Atualmente Cadastrados:")
    conferentes_atuais = carregar_lista_conferentes()
    if conferentes_atuais:
        df_conf = pd.DataFrame(conferentes_atuais, columns=["Nome do Conferente"])
        st.dataframe(df_conf, use_container_width=True)
    else:
        st.info("Nenhum conferente localizado até o momento.")