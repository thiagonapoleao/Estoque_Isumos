import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os
import base64
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
import streamlit.components.v1 as components
import altair as alt

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Gestão de Insumos & Conferência",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. CSS CORPORATIVO PADRÃO SÓLIDO (SEM DEGRADÊ) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"], [class*="st-"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        font-size: 13px !important;
        color: #1e293b;
    }

    /* Oculta sidebar não utilizada */
    [data-testid="stSidebar"] {
        display: none !important;
    }

    /* Top Bar Header Sólido */
    .top-header {
        background-color: #0f134f;
        padding: 12px 24px;
        border-radius: 8px;
        margin-bottom: 14px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        color: #ffffff;
        border-bottom: 2px solid #273270;
    }
    .top-header-title {
        font-size: 18px !important;
        font-weight: 700 !important;
        color: #ffffff !important;
        margin: 0;
        letter-spacing: -0.2px;
    }
    .top-header-subtitle {
        font-size: 11.5px !important;
        color: #cbd5e1 !important;
        margin: 0;
    }
    .top-header-badge {
        background-color: #273270;
        padding: 5px 12px;
        border-radius: 6px;
        font-size: 11px !important;
        font-weight: 600;
        color: #ffffff;
    }

    /* Cards de Métricas Sólidos */
    .metric-container {
        display: flex;
        gap: 12px;
        margin-bottom: 20px;
        flex-wrap: wrap;
    }
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-left: 4px solid #0f134f;
        padding: 12px 16px;
        border-radius: 6px;
        flex: 1;
        min-width: 170px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
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
        font-size: 18px !important;
        color: #0f134f;
        margin-top: 3px;
        font-weight: 700;
    }

    /* Botões Padrão Sólido */
    div.stButton > button[kind="primary"] {
        background-color: #0f134f !important;
        color: #ffffff !important;
        border: 1px solid #0f134f !important;
        border-radius: 5px !important;
        font-weight: 600 !important;
        padding: 7px 16px !important;
        box-shadow: none !important;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #273270 !important;
        border-color: #273270 !important;
    }
    div.stButton > button[kind="secondary"] {
        background-color: #ffffff !important;
        color: #334155 !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 5px !important;
        font-weight: 500 !important;
    }
    div.stButton > button[kind="secondary"]:hover {
        background-color: #f8fafc !important;
        border-color: #94a3b8 !important;
        color: #0f134f !important;
    }

    /* Box de Dicas e Divergências */
    .keyboard-hint {
        background-color: #f8fafc;
        border: 1px solid #cbd5e1;
        padding: 6px 12px;
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
        border-radius: 5px;
        padding: 10px 14px;
        margin: 10px 0;
        font-size: 12px !important;
    }

    /* Impressão */
    @media print {
        header, .top-header, .stButton, [data-testid="stToolbar"], footer, .no-print {
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

# --- 3. CONFIGURAÇÃO DA API & SESSÃO RESILIENTE ---
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

    if "quantidade" in df.columns:
        df["quantidade"] = pd.to_numeric(df["quantidade"], errors="coerce").fillna(0.0)
    if "conferencia" in df.columns:
        df["conferencia"] = pd.to_numeric(df["conferencia"], errors="coerce")
    if "divergencia" in df.columns:
        df["divergencia"] = pd.to_numeric(df["divergencia"], errors="coerce")

    return df

@st.cache_data(ttl=120, show_spinner=False)
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

# --- 4. MOTOR DE LEITURA DO EXCEL ---
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

# --- 5. LOGOTIPO & CABEÇALHO SUPERIOR PADRONIZADO ---
def obter_logo_base64():
    possiveis_caminhos = [
        "assets/Mastercafe-logo.png",
        "assets/Mastercafe-logo1.png",
        "assets/logo.png",
        "Mastercafe-logo.png",
        "Mastercafe-logo1.png",
        "logo.png"
    ]
    for p in possiveis_caminhos:
        if os.path.exists(p):
            with open(p, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode("utf-8")
    return None

logo_b64 = obter_logo_base64()

col_logo, col_titulo = st.columns([1.2, 5.8])

with col_logo:
    if logo_b64:
        st.markdown(f'<img src="data:image/png;base64,{logo_b64}" style="max-height: 52px; margin-top: 4px;">', unsafe_allow_html=True)
    else:
        caminhos_img = ["assets/Mastercafe-logo.png", "Mastercafe-logo.png", "logo.png"]
        logo_direto = next((p for p in caminhos_img if os.path.exists(p)), None)
        if logo_direto:
            st.image(logo_direto, width=150)
        else:
            st.markdown('<div style="height: 48px;"></div>', unsafe_allow_html=True)

with col_titulo:
    st.markdown("""
    <div style="padding-top: 4px;">
        <h2 style="margin: 0; color: #0f134f; font-weight: 700; font-size: 20px; letter-spacing: -0.3px;">
            Gestão de Estoque ∙ Conferência de Mercadorias
        </h2>
        <div style="font-size: 12px; color: #64748b; margin-top: 1px;">
            Auditoria, Separação Cega e Conciliação Física de Insumos
        </div>
    </div>
    """, unsafe_allow_html=True)

st.write("")

# --- 6. BARRA DE NAVEGAÇÃO NO TOPO (PADRÃO HORIZONTAL) ---
if "menu_selecionado" not in st.session_state:
    st.session_state.menu_selecionado = "Dashboard de Resumo"

opcoes_nav = [
    ("📊 Dashboard", "Dashboard de Resumo"),
    ("📥 Importar Remessa", "Importar Remessa"),
    ("🖨️ Folha Cega", "Folha de Impressão Cega"),
    ("🔍 Conferência Física", "Digitar Conferência Cega"),
    ("👤 Conferentes", "Cadastrar Novo Conferente")
]

cols_nav = st.columns([2, 2, 2, 2.2, 1.8, 0.8])
for idx, (label, rota) in enumerate(opcoes_nav):
    with cols_nav[idx]:
        is_ativo = (st.session_state.menu_selecionado == rota)
        tipo_botao = "primary" if is_ativo else "secondary"
        if st.button(label, key=f"nav_top_{rota}", use_container_width=True, type=tipo_botao):
            st.session_state.menu_selecionado = rota
            st.rerun()

with cols_nav[5]:
    if st.button("🔄", help="Atualizar e sincronizar com Google Sheets", use_container_width=True):
        carregar_dados_planilha_cached.clear()
        carregar_lista_conferentes.clear()
        st.rerun()

st.write("---")

menu = st.session_state.menu_selecionado

# ==============================================================================
# OPÇÃO: DASHBOARD DE RESUMO
# ==============================================================================
if menu == "Dashboard de Resumo":
    with st.spinner("Compilando indicadores da aba Conferencia..."):
        df_raw = carregar_dados_planilha()

    if df_raw.empty:
        st.info("Nenhum registro encontrado na aba Conferencia da planilha.")
        st.caption("Verifique o compartilhamento da planilha ou clique em 🔄 para sincronizar.")
    else:
        df = df_raw.copy()

        data_col = df["data_importacao"] if "data_importacao" in df.columns else pd.Series(index=df.index, dtype=str)
        dt_parsed = pd.to_datetime(data_col, format="%d/%m/%Y", errors="coerce")
        dt_parsed = dt_parsed.fillna(pd.to_datetime(data_col, errors="coerce", dayfirst=True))
        
        df["dt_parsed"] = pd.to_datetime(dt_parsed, errors="coerce").fillna(pd.Timestamp.now().normalize())
        df["mes_ano"] = df["dt_parsed"].dt.strftime("%m/%Y")
        df["dia_str"] = df["dt_parsed"].dt.strftime("%d/%m/%Y")

        col_f1, col_f2 = st.columns([2, 2])
        with col_f1:
            confs_unicos = sorted([
                str(c).strip() for c in df.get("conferente", pd.Series()).dropna().unique() 
                if str(c).strip() not in ["", "nan", "None"]
            ])
            lista_confs = ["TODOS"] + confs_unicos
            filtro_conf = st.selectbox("Filtrar por Conferente:", lista_confs)
        with col_f2:
            remessas_unicas = sorted([
                str(r).strip() for r in df.get("remessa", pd.Series()).dropna().unique() 
                if str(r).strip() not in ["", "nan", "None"]
            ])
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

        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-card">
                <span>Remessas em Base</span>
                <strong>{total_remessas}</strong>
            </div>
            <div class="metric-card">
                <span>Itens Conferidos</span>
                <strong>{total_conferidos} de {total_itens}</strong>
            </div>
            <div class="metric-card">
                <span>Acuracidade Físico x Remessa</span>
                <strong style="color: {'#16a34a' if taxa_acuracia >= 98 else '#dc2626'};">{taxa_acuracia:.1f}%</strong>
            </div>
            <div class="metric-card">
                <span>Itens Divergentes</span>
                <strong style="color: {'#dc2626' if len(itens_com_erro) > 0 else '#16a34a'};">{len(itens_com_erro)}</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.write("---")

        col_g1, col_g2 = st.columns(2)

        with col_g1:
            st.markdown("##### 📅 Volume por Mês")
            base_grafico = df_filtrado[df_filtrado["conferencia"].notna()]
            if base_grafico.empty:
                base_grafico = df_filtrado
                
            df_mes = base_grafico.groupby("mes_ano").size().reset_index(name="Qtd")
            if not df_mes.empty:
                max_val_mes = float(df_mes["Qtd"].max() * 1.18) if df_mes["Qtd"].max() > 0 else 10.0
                barras_mes = alt.Chart(df_mes).mark_bar(color="#0f134f", cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
                    x=alt.X("mes_ano:N", title="Mês/Ano", sort=None, axis=alt.Axis(labelAngle=0)),
                    y=alt.Y("Qtd:Q", title="Qtd. Itens", scale=alt.Scale(domain=[0, max_val_mes]))
                )
                textos_mes = barras_mes.mark_text(
                    align="center",
                    baseline="bottom",
                    dy=-4,
                    fontSize=11,
                    fontWeight=600,
                    color="#0f134f"
                ).encode(
                    text="Qtd:Q"
                )
                chart_mes = (barras_mes + textos_mes).properties(height=260)
                st.altair_chart(chart_mes, use_container_width=True)
            else:
                st.info("Sem dados para a evolução mensal.")

        with col_g2:
            st.markdown("##### 📊 Top 10 Remessas por Volume")
            df_rem_graf = df_filtrado.groupby("remessa").size().reset_index(name="Qtd").sort_values("Qtd", ascending=False).head(10)
            if not df_rem_graf.empty:
                max_val_rem = float(df_rem_graf["Qtd"].max() * 1.18) if df_rem_graf["Qtd"].max() > 0 else 10.0
                barras_rem = alt.Chart(df_rem_graf).mark_bar(color="#273270", cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
                    x=alt.X("remessa:N", title="Remessa", sort=None, axis=alt.Axis(labelAngle=-45)),
                    y=alt.Y("Qtd:Q", title="Qtd. Itens", scale=alt.Scale(domain=[0, max_val_rem]))
                )
                textos_rem = barras_rem.mark_text(
                    align="center",
                    baseline="bottom",
                    dy=-4,
                    fontSize=11,
                    fontWeight=600,
                    color="#0f134f"
                ).encode(
                    text="Qtd:Q"
                )
                chart_rem = (barras_rem + textos_rem).properties(height=260)
                st.altair_chart(chart_rem, use_container_width=True)
            else:
                st.info("Sem dados para o gráfico de remessas.")

        st.write("---")
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
    st.markdown("#### 📥 Importação de Arquivo de Remessa")
    st.markdown("Selecione o arquivo Excel e informe os dados da remessa para gravação direta na aba **Conferencia**.")

    col1, col2 = st.columns(2)
    with col1:
        num_remessa = st.text_input("Número da Remessa *", placeholder="Ex: 268326")
    with col2:
        nome_local_input = st.text_input("Local / Estoque de Destino *", placeholder="Ex: S.R. EMBALAGENS")

    arquivo_excel = st.file_uploader("Selecione o arquivo da Remessa", type=["xlsx", "xls"])

    if st.button("Salvar Remessa", type="primary"):
        if not num_remessa or not nome_local_input or not arquivo_excel:
            st.error("Preencha todos os campos obrigatórios e anexe o arquivo.")
        else:
            nome_local = str(nome_local_input).strip().upper()
            remessa_limpa = str(num_remessa).strip()

            with st.spinner("Processando linhas do arquivo..."):
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

                with st.spinner("Gravando linhas no Google Sheets..."):
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
    st.markdown("#### 🖨️ Folha de Separação / Contagem Cega")
    st.markdown("Gere a folha física com formato compacto para economia de papel e conferência física.")

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
                        f"<td style='border: 1px solid #475569; padding: 4px 6px; font-weight: bold; font-size: 10px;'>{cod_item}</td>"
                        f"<td style='border: 1px solid #475569; padding: 4px 6px; font-size: 10px; line-height: 1.15;'>{desc_item}</td>"
                        "<td style='border: 1px solid #475569; padding: 4px 6px; height: 22px;'></td>"
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
            padding: 6px;
            background-color: #ffffff;
        }}
        .header-box {{
            border-bottom: 2px solid #0f134f;
            padding-bottom: 6px;
            margin-bottom: 8px;
        }}
        .header-title {{
            font-size: 14px;
            font-weight: bold;
            margin: 0 0 4px 0;
            color: #0f134f;
            text-transform: uppercase;
        }}
        .header-meta {{
            display: flex;
            gap: 20px;
            font-size: 10.5px;
            color: #334155;
            font-weight: 600;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 6px;
        }}
        th {{
            border: 1px solid #0f134f;
            background-color: #f1f5f9;
            padding: 5px 6px;
            font-size: 10.5px;
            text-align: left;
            font-weight: bold;
        }}
        .signature-box {{
            margin-top: 24px;
            display: flex;
            justify-content: space-between;
            font-size: 10px;
            color: #334155;
            padding-top: 6px;
        }}
        .btn-imprimir {{
            background-color: #0f134f;
            color: white;
            border: none;
            padding: 7px 16px;
            font-size: 11px;
            font-weight: 600;
            border-radius: 4px;
            cursor: pointer;
            margin-bottom: 10px;
        }}
        .btn-imprimir:hover {{
            background-color: #273270;
        }}
        @media print {{
            .btn-imprimir {{
                display: none !important;
            }}
            body {{
                padding: 0;
            }}
            @page {{
                margin: 8mm;
            }}
        }}
    </style>
</head>
<body>
    <button class="btn-imprimir" onclick="window.print()">Imprimir Folha de Contagem</button>

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

                altura_calculada = max(380, 120 + (len(dados_remessa) * 28))
                components.html(documento_html, height=altura_calculada, scrolling=True)

# ==============================================================================
# OPÇÃO: DIGITAR CONFERÊNCIA CEGA & JUSTIFICATIVA POR ITEM
# ==============================================================================
elif menu == "Digitar Conferência Cega":
    st.markdown("#### 🔍 Digitação de Conferência Cega e Validação")

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
                    st.success("✨ **Remessa 100% Validada!** Todos os itens foram conferidos sem divergência.")
                else:
                    modo_reconferencia = False
                    dados_trabalho = itens_remessa.copy()
                    st.info("📋 **Primeira Conferência:** Digite a quantidade física contada para cada item.")

                st.markdown(f"""
                <div class="metric-container">
                    <div class="metric-card">
                        <span>Remessa</span>
                        <strong>{remessa_alvo}</strong>
                    </div>
                    <div class="metric-card">
                        <span>Local / Depósito</span>
                        <strong>{local_atual}</strong>
                    </div>
                    <div class="metric-card">
                        <span>Data de Entrada</span>
                        <strong>{data_atual_br}</strong>
                    </div>
                    <div class="metric-card">
                        <span>Itens a Validar</span>
                        <strong>{len(dados_trabalho)}</strong>
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
                    ⚡ <strong>Agilidade de Digitação:</strong> Digite a contagem e aperte <kbd>Enter</kbd> para descer direto para o próximo produto.
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

                st.write("---")
                autorizar_divergencia = st.checkbox("⚠️ Autorizar encerramento/finalização com divergência")
                justificativas_itens = {}

                if autorizar_divergencia:
                    if len(itens_com_divergencia_detectada) == 0:
                        st.info("✨ Não há itens divergentes no momento. Ao salvar, todos os itens constarão como conferidos sem divergência.")
                    else:
                        st.markdown("""
                        <div class="divergence-box">
                            <strong style="color: #9a3412;">📝 Justificativa Individual por Item Divergente</strong><br>
                            <span style="font-size: 11.5px; color: #431407;">
                                Informe a justificativa específica para cada produto que apresentou divergência. Ela será gravada na coluna Justificativa da planilha.
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

                if st.button("Gravar Conferência", type="primary"):
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
                            st.error("⚠️ É **obrigatório** preencher a justificativa para todos os produtos divergentes listados acima.")
                        else:
                            with st.spinner("Gravando conferência no Google Sheets..."):
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
                                        msg_sucesso += " Justificativas lançadas com sucesso."
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
                                            "justificativa": "Justificativa"
                                        },
                                        use_container_width=True
                                    )

                                    total_erros = df_resultado["_tem_erro"].sum()
                                    if total_erros == 0:
                                        st.balloons()
                                        st.success("🎉 **Perfeito!** Todos os itens batem com a remessa.")
                                    else:
                                        if autorizar_divergencia:
                                            st.info("ℹ️ **Conferência Finalizada com Justificativa:** As pendências foram autorizadas.")
                                        else:
                                            st.warning(f"⚠️ **Atenção:** Existem **{total_erros} item(ns) divergente(s)**.")
                                else:
                                    mensagem_erro = res.get("message", "Falha na comunicação com a planilha")
                                    st.error(f"Erro ao salvar: {mensagem_erro}")

# ==============================================================================
# OPÇÃO: CADASTRAR NOVO CONFERENTE
# ==============================================================================
elif menu == "Cadastrar Novo Conferente":
    st.markdown("#### 👤 Cadastro de Conferente")
    st.markdown("Os conferentes cadastrados são armazenados na Coluna D da aba **Local-Estoque**.")

    col1, col2 = st.columns([2, 1])
    with col1:
        novo_conferente = st.text_input("Nome Completo do Conferente *", placeholder="Ex: JOÃO SILVA")
        if st.button("Cadastrar", type="primary"):
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