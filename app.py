import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import streamlit.components.v1 as components

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Gestão de Conferência de Mercadorias",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
    }
    .main-title {
        font-size: 24px;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 6px;
        padding-bottom: 8px;
        border-bottom: 2px solid #e2e8f0;
    }
    .sub-title {
        font-size: 14px;
        color: #64748b;
        margin-bottom: 20px;
    }
    .metric-container {
        display: flex;
        gap: 16px;
        margin-bottom: 20px;
        flex-wrap: wrap;
    }
    .metric-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 14px 18px;
        border-radius: 8px;
        flex: 1;
        min-width: 180px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .metric-card span {
        font-size: 12px;
        color: #64748b;
        font-weight: 600;
        text-transform: uppercase;
    }
    .metric-card strong {
        display: block;
        font-size: 18px;
        color: #0f172a;
        margin-top: 4px;
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
            padding: 8px !important;
            font-size: 12px !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# --- 2. CONFIGURAÇÃO DA API DO GOOGLE APPS SCRIPT ---
API_URL = "https://script.google.com/macros/s/AKfycbz59wGY8R9S3j-jOv0sbxIjwKSLiakWrFBPez9VZWGoMhxdDWpdsTazsjBXsxm9hYMC/exec"

# --- 3. COMUNICAÇÃO COM A PLANILHA ---
def carregar_dados_planilha():
    try:
        r = requests.get(API_URL, timeout=30)
        dados = r.json()
        if isinstance(dados, list):
            return pd.DataFrame(dados)
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro ao buscar registros da planilha: {e}")
        return pd.DataFrame()

def enviar_importacao_planilha(linhas):
    payload = {
        "action": "importar",
        "linhas": linhas
    }
    r = requests.post(API_URL, json=payload, timeout=40)
    return r.json()

def enviar_atualizacao_conferencia(itens):
    payload = {
        "action": "atualizar",
        "itens": itens
    }
    r = requests.post(API_URL, json=payload, timeout=40)
    return r.json()

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

# --- 5. BARRA LATERAL ---
st.sidebar.markdown("### 🏢 Logística & Estoque")
menu = st.sidebar.radio(
    "Navegação:",
    ["1. Importar Remessa (Excel)", "2. Folha de Impressão Cega", "3. Digitar Conferência Cega"]
)

# ==============================================================================
# OPÇÃO 1: IMPORTAR EXCEL E SALVAR NA PLANILHA GOOGLE
# ==============================================================================
if menu == "1. Importar Remessa (Excel)":
    st.markdown('<div class="main-title">📥 Importação de Remessa via Planilha Excel</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Gravação direta na aba Conferencia da Planilha Google.</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        num_remessa = st.text_input("Número da Remessa *", placeholder="Ex: REM-2026-001")
    with col2:
        nome_local = st.text_input("Local / Filial de Destino *", placeholder="Ex: Almoxarifado Central")

    arquivo_excel = st.file_uploader("Selecione o arquivo Excel da Remessa", type=["xlsx", "xls"])

    if st.button("Processar e Salvar na Planilha Google", type="primary"):
        if not num_remessa or not nome_local or not arquivo_excel:
            st.error("Preencha todos os campos obrigatórios e anexe o arquivo Excel.")
        else:
            with st.spinner("Processando linhas do Excel a partir da coluna 'Produto'..."):
                itens = extrair_excel(arquivo_excel)

            if not itens:
                st.warning("Nenhum item válido encontrado no arquivo. Verifique se o cabeçalho possui a coluna 'Produto' ou 'Código'.")
            else:
                data_importacao = datetime.now().strftime("%d/%m/%Y %H:%M")
                
                linhas_para_sheets = []
                for item in itens:
                    linhas_para_sheets.append([
                        num_remessa,          # Coluna A
                        nome_local,           # Coluna B
                        data_importacao,      # Coluna C
                        item["Produto"],      # Coluna D
                        item["Descricao"],    # Coluna E
                        item["Quantidade"],   # Coluna F
                        "",                   # Coluna G (aberta para conferência)
                        ""                    # Coluna H (aberta para divergência)
                    ])

                with st.spinner("Gravando linhas diretamente na planilha Google Sheets..."):
                    try:
                        res = enviar_importacao_planilha(linhas_para_sheets)
                        if res.get("status") == "success":
                            st.success(f"✅ {len(linhas_para_sheets)} itens gravados com sucesso na planilha para a remessa **{num_remessa}**!")
                            df_preview = pd.DataFrame(itens)
                            st.dataframe(df_preview, use_container_width=True)
                        else:
                            st.error(f"Erro reportado pela planilha: {res.get('message')}")
                    except Exception as e:
                        st.error(f"Falha de conexão com a planilha: {e}")

# ==============================================================================
# OPÇÃO 2: FOLHA DE IMPRESSÃO CEGA (SEM QUANTIDADES)
# ==============================================================================
elif menu == "2. Folha de Impressão Cega":
    st.markdown('<div class="main-title">🖨️ Folha de Separação / Contagem Cega</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Gere a folha de contagem física sem as quantidades esperadas para anotação em campo.</div>', unsafe_allow_html=True)

    with st.spinner("Consultando dados na planilha Google..."):
        df = carregar_dados_planilha()

    if df.empty:
        st.info("Nenhuma remessa encontrada na planilha.")
    else:
        remessas_disponiveis = [r for r in df["remessa"].dropna().unique().tolist() if str(r).strip() != ""]
        remessa_selecionada = st.selectbox("Selecione a Remessa para Gerar a Impressão:", [""] + remessas_disponiveis)

        if remessa_selecionada:
            dados_remessa = df[df["remessa"] == remessa_selecionada].copy()

            data_cad = dados_remessa["data_importacao"].iloc[0] if not dados_remessa.empty else ""
            local_cad = dados_remessa["local"].iloc[0] if not dados_remessa.empty else ""

            col_btn, _ = st.columns([2, 5])
            with col_btn:
                if st.button("🖨️ Imprimir Folha de Contagem", type="primary"):
                    components.html("<script>window.parent.print();</script>", height=0, width=0)

            html_folha = f"""
            <div class="printable-area" style="background:#ffffff; padding:24px; border:1px solid #cbd5e1; border-radius:8px; margin-top:10px;">
                <div style="border-bottom: 2px solid #0f172a; padding-bottom: 12px; margin-bottom: 16px;">
                    <h2 style="margin: 0; font-size: 20px; color: #0f172a;">FOLHA DE CONFERÊNCIA FÍSICA (CONTAGEM CEGA)</h2>
                    <div style="display: flex; gap: 30px; margin-top: 10px; font-size: 13px; color: #334155;">
                        <div><strong>REMESSA:</strong> {remessa_selecionada}</div>
                        <div><strong>LOCAL:</strong> {local_cad}</div>
                        <div><strong>DATA IMPORTAÇÃO:</strong> {data_cad}</div>
                    </div>
                </div>

                <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                    <thead>
                        <tr style="background-color: #f8fafc;">
                            <th style="border: 1px solid #94a3b8; padding: 10px; width: 15%; text-align: left; font-size: 13px;">CÓDIGO</th>
                            <th style="border: 1px solid #94a3b8; padding: 10px; width: 60%; text-align: left; font-size: 13px;">DESCRIÇÃO DO PRODUTO</th>
                            <th style="border: 1px solid #94a3b8; padding: 10px; width: 25%; text-align: center; font-size: 13px;">QTD. CONFERIDA</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            for _, row in dados_remessa.iterrows():
                html_folha += f"""
                    <tr>
                        <td style="border: 1px solid #cbd5e1; padding: 10px; font-size: 13px; font-weight: 600;">{row['produto']}</td>
                        <td style="border: 1px solid #cbd5e1; padding: 10px; font-size: 13px;">{row['descricao']}</td>
                        <td style="border: 1px solid #cbd5e1; padding: 10px; height: 36px; text-align: center; background-color: #fcfcfc;"></td>
                    </tr>
                """
            
            html_folha += """
                    </tbody>
                </table>
                <div style="margin-top: 30px; display: flex; justify-content: space-between; font-size: 12px; color: #475569;">
                    <div>Assinatura do Conferente: _____________________________________</div>
                    <div>Data da Conferência: ____/____/________</div>
                </div>
            </div>
            """
            st.markdown(html_folha, unsafe_allow_html=True)

# ==============================================================================
# OPÇÃO 3: DIGITAÇÃO CEGA, COMPARAÇÃO, GRAVAÇÃO E RECONFERÊNCIA DE DIVERGÊNCIAS
# ==============================================================================
elif menu == "3. Digitar Conferência Cega":
    st.markdown('<div class="main-title">🔍 Digitação de Conferência Cega e Validação</div>', unsafe_allow_html=True)

    with st.spinner("Buscando registros na planilha Google..."):
        df = carregar_dados_planilha()

    if df.empty:
        st.info("Nenhuma remessa encontrada na planilha para conferência.")
    else:
        remessas = [r for r in df["remessa"].dropna().unique().tolist() if str(r).strip() != ""]
        remessa_pesquisa = st.selectbox("Pesquisar pelo Número da Remessa:", [""] + remessas)

        if remessa_pesquisa:
            itens_remessa = df[df["remessa"] == remessa_pesquisa].copy()

            local_atual = itens_remessa["local"].iloc[0]
            data_atual = itens_remessa["data_importacao"].iloc[0]

            # Converte colunas numéricas
            itens_remessa["quantidade"] = pd.to_numeric(itens_remessa["quantidade"], errors="coerce").fillna(0.0)
            itens_remessa["conferencia"] = pd.to_numeric(itens_remessa["conferencia"], errors="coerce")
            itens_remessa["divergencia"] = pd.to_numeric(itens_remessa["divergencia"], errors="coerce")

            # Identifica se a remessa já passou por uma primeira conferência
            ja_conferida = itens_remessa["conferencia"].notna().any()
            
            # Filtra itens com divergência (divergência diferente de zero)
            itens_divergentes = itens_remessa[itens_remessa["divergencia"].fillna(1) != 0].copy()

            # --- DEFINIÇÃO DO MODO (PRIMEIRA CONFERÊNCIA OU SEGUNDA CONFERÊNCIA/CORREÇÃO) ---
            if ja_conferida and len(itens_divergentes) > 0:
                modo_reconferencia = True
                dados_trabalho = itens_divergentes.copy()
                st.warning(f"⚠️ **Segunda Conferência:** Esta remessa possui **{len(itens_divergentes)} item(ns) com divergência**. Exibindo apenas os itens divergentes para correção.")
            elif ja_conferida and len(itens_divergentes) == 0:
                modo_reconferencia = False
                dados_trabalho = itens_remessa.copy()
                st.success("✨ **Remessa 100% Conferida e Sem Divergências!** Todos os itens batem com o esperado.")
            else:
                modo_reconferencia = False
                dados_trabalho = itens_remessa.copy()
                st.info("📋 **Primeira Conferência (Contagem Cega):** Digite os valores contados fisicamente. As quantidades esperadas não são exibidas nesta etapa.")

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
                    <strong>{data_atual}</strong>
                </div>
                <div class="metric-card">
                    <span>Itens em Tela</span>
                    <strong>{len(dados_trabalho)}</strong>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Prepara a tabela de digitação (sem mostrar a quantidade esperada)
            dados_trabalho["conferencia"] = dados_trabalho["conferencia"].fillna(0.0)
            df_editavel = dados_trabalho[["row_index", "produto", "descricao", "conferencia"]].copy()

            st.write("Digite as quantidades físicas conferidas abaixo:")
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

            # --- BOTÃO DE COMPARAÇÃO & GRAVAÇÃO NA PLANILHA ---
            if st.button("⚖️ Comparar e Gravar Conferência na Planilha", type="primary"):
                with st.spinner("Calculando divergências e gravando diretamente na planilha..."):
                    # Mapeia as quantidades esperadas para calcular divergência
                    mapa_esperado = dados_trabalho.set_index("row_index")["quantidade"].to_dict()
                    
                    itens_atualizar = []
                    resultados_comparacao = []

                    for _, row in editado.iterrows():
                        r_id = int(row["row_index"])
                        conf_val = float(row["conferencia"])
                        qtd_esp = mapa_esperado.get(r_id, 0.0)
                        div_val = conf_val - qtd_esp

                        itens_atualizar.append({
                            "row_index": r_id,
                            "conferencia": conf_val,
                            "divergencia": div_val
                        })

                        resultados_comparacao.append({
                            "produto": row["produto"],
                            "descricao": row["descricao"],
                            "qtd_esperada": qtd_esp,
                            "conferencia": conf_val,
                            "divergencia": div_val
                        })

                    # Grava diretamente no Google Sheets através da API
                    try:
                        res = enviar_atualizacao_conferencia(itens_atualizar)
                        if res.get("status") == "success":
                            st.success("✅ Conferência e divergências gravadas com sucesso na planilha Google!")
                            
                            df_resultado = pd.DataFrame(resultados_comparacao)
                            
                            # Função para colorir a divergência
                            def colorir_divergencia(valor):
                                if valor < 0:
                                    return "background-color: #fee2e2; color: #991b1b; font-weight: 700;"
                                elif valor > 0:
                                    return "background-color: #dcfce7; color: #166534; font-weight: 700;"
                                else:
                                    return "background-color: #f0fdf4; color: #15803d; font-weight: 600;"

                            # Painel de resultados da comparação
                            st.write("### 📊 Resultado da Comparação")
                            styler_res = df_resultado.style
                            if hasattr(styler_res, "map"):
                                styler_res = styler_res.map(colorir_divergencia, subset=["divergencia"])
                            else:
                                styler_res = styler_res.applymap(colorir_divergencia, subset=["divergencia"])

                            st.dataframe(
                                styler_res,
                                column_config={
                                    "produto": "Código",
                                    "descricao": "Descrição",
                                    "qtd_esperada": st.column_config.NumberColumn("Qtd. Esperada", format="%.2f"),
                                    "conferencia": st.column_config.NumberColumn("Qtd. Conferida", format="%.2f"),
                                    "divergencia": st.column_config.NumberColumn("Divergência", format="%.2f"),
                                },
                                use_container_width=True
                            )

                            erros = df_resultado[df_resultado["divergencia"] != 0]
                            if len(erros) == 0:
                                st.balloons()
                                st.success("🎉 **Nenhuma divergência encontrada!** Remessa totalmente conferida.")
                            else:
                                st.warning(f"⚠️ **Atenção:** Foram encontrados **{len(erros)} item(ns) com divergência**. Ao buscar novamente esta remessa, o formulário exibirá apenas estes itens para a segunda conferência.")
                        else:
                            st.error(f"Erro ao salvar na planilha: {res.get('message')}")
                    except Exception as e:
                        st.error(f"Falha de conexão com a planilha: {e}")