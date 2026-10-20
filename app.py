import sqlite3
import streamlit as st
import pandas as pd
from datetime import datetime
import streamlit.components.v1 as components

# --- 1. CONFIGURAÇÃO DA PÁGINA & TEMA CLARO CORPORATIVO ---
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

    /* Regras de Impressão para Folha A4 Cega */
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

# --- 2. BANCO DE DADOS LOCAL (ZERO CONFIGURAÇÃO / SEM SECRETS) ---
DB_NAME = "conferencia_mercadorias.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conferencia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            remessa TEXT,
            local TEXT,
            data_importacao TEXT,
            produto TEXT,
            descricao TEXT,
            quantidade REAL,
            conferencia REAL,
            divergencia REAL
        )
    """)
    conn.commit()
    conn.close()

init_db()

def salvar_remessa_db(linhas):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.executemany("""
        INSERT INTO conferencia 
        (remessa, local, data_importacao, produto, descricao, quantidade, conferencia, divergencia)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, linhas)
    conn.commit()
    conn.close()

def carregar_dados_db():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM conferencia ORDER BY id ASC", conn)
    conn.close()
    return df

def atualizar_conferencia_db(registros_atualizados):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    for reg in registros_atualizados:
        cursor.execute("""
            UPDATE conferencia
            SET conferencia = ?, divergencia = ?
            WHERE id = ?
        """, (reg["conferencia"], reg["divergencia"], reg["id"]))
    conn.commit()
    conn.close()

# --- 3. EXTRAÇÃO ASSERTIVA DO EXCEL ---
def extrair_excel(uploaded_file):
    itens = []
    df_raw = pd.read_excel(uploaded_file, header=None, dtype=str)
    
    linha_cabecalho = None
    idx_col_prod = None
    idx_col_desc = None
    idx_col_qtd = None

    # Varre as linhas procurando onde começa a tabela de produtos
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
                
                # Identifica coluna do código do produto
                if any(k in v for k in ["produto", "código", "codigo", "item"]) and idx_col_prod is None:
                    idx_col_prod = c_idx
                # Identifica descrição
                elif any(k in v for k in ["descri", "nome", "especifica"]) and idx_col_desc is None:
                    idx_col_desc = c_idx
                # Identifica quantidade (ignora lote e número de série)
                elif any(k in v for k in ["quant", "qtd"]) and not any(k in v for k in ["lote", "série", "serie"]):
                    idx_col_qtd = c_idx
            break

    if linha_cabecalho is None:
        return itens

    # Fallbacks estruturais
    if idx_col_prod is None:
        idx_col_prod = 0
    if idx_col_desc is None and len(df_raw.columns) > 1:
        idx_col_desc = 1

    # Itera sobre os dados a partir da linha logo abaixo do cabeçalho
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

# --- 4. BARRA LATERAL ---
st.sidebar.markdown("### 🏢 Logística & Estoque")
menu = st.sidebar.radio(
    "Navegação:",
    ["1. Importar Remessa (Excel)", "2. Folha de Impressão Cega", "3. Digitar Conferência", "4. Exportar Dados"]
)

# ==============================================================================
# OPÇÃO 1: IMPORTAR REMESSA (EXCEL)
# ==============================================================================
if menu == "1. Importar Remessa (Excel)":
    st.markdown('<div class="main-title">📥 Importação de Remessa via Planilha Excel</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Carregue o arquivo Excel (.xlsx / .xls), ignorando cabeçalhos prévios e lotes/séries.</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        num_remessa = st.text_input("Número da Remessa *", placeholder="Ex: REM-2026-001")
    with col2:
        nome_local = st.text_input("Local / Filial de Destino *", placeholder="Ex: Almoxarifado Central")

    arquivo_excel = st.file_uploader("Selecione o arquivo Excel da Remessa", type=["xlsx", "xls"])

    if st.button("Processar e Salvar no Sistema", type="primary"):
        if not num_remessa or not nome_local or not arquivo_excel:
            st.error("Preencha todos os campos obrigatórios e anexe o arquivo Excel.")
        else:
            with st.spinner("Processando linhas do Excel a partir da coluna 'Produto'..."):
                itens = extrair_excel(arquivo_excel)

            if not itens:
                st.warning("Nenhum item válido foi encontrado no arquivo. Verifique se o cabeçalho possui a coluna 'Produto' ou 'Código'.")
            else:
                data_importacao = datetime.now().strftime("%d/%m/%Y %H:%M")
                linhas_inserir = []

                for item in itens:
                    linhas_inserir.append((
                        num_remessa,
                        nome_local,
                        data_importacao,
                        item["Produto"],
                        item["Descricao"],
                        item["Quantidade"],
                        None,  # Conferencia vazia
                        None   # Divergencia vazia
                    ))

                try:
                    salvar_remessa_db(linhas_inserir)
                    st.success(f"✅ {len(linhas_inserir)} itens importados com sucesso para a remessa **{num_remessa}**!")
                    
                    df_preview = pd.DataFrame(itens)
                    st.dataframe(df_preview, use_container_width=True)
                except Exception as e:
                    st.error(f"Erro ao salvar no banco local: {e}")

# ==============================================================================
# OPÇÃO 2: FOLHA DE IMPRESSÃO CEGA (SEM QUANTIDADES)
# ==============================================================================
elif menu == "2. Folha de Impressão Cega":
    st.markdown('<div class="main-title">🖨️ Folha de Separação / Contagem Cega</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Gere a folha de contagem física sem as quantidades esperadas para anotação em campo.</div>', unsafe_allow_html=True)

    df = carregar_dados_db()

    if df.empty:
        st.info("Nenhuma remessa encontrada no sistema. Importe um arquivo na Opção 1.")
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
# OPÇÃO 3: FORMULÁRIO DE CONFERÊNCIA & VALIDAÇÃO
# ==============================================================================
elif menu == "3. Digitar Conferência":
    st.markdown('<div class="main-title">🔍 Validação e Digitação da Conferência</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Consulte os itens pela Remessa, informe as quantidades físicas e valide divergências.</div>', unsafe_allow_html=True)

    df = carregar_dados_db()

    if df.empty:
        st.info("Nenhuma remessa encontrada para conferência.")
    else:
        remessas = [r for r in df["remessa"].dropna().unique().tolist() if str(r).strip() != ""]
        remessa_pesquisa = st.selectbox("Pesquisar pelo Número da Remessa:", [""] + remessas)

        if remessa_pesquisa:
            itens_remessa = df[df["remessa"] == remessa_pesquisa].copy()

            local_atual = itens_remessa["local"].iloc[0]
            data_atual = itens_remessa["data_importacao"].iloc[0]

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
                    <span>Total de Itens</span>
                    <strong>{len(itens_remessa)}</strong>
                </div>
            </div>
            """, unsafe_allow_html=True)

            itens_remessa["quantidade"] = pd.to_numeric(itens_remessa["quantidade"], errors="coerce").fillna(0.0)
            itens_remessa["conferencia"] = pd.to_numeric(itens_remessa["conferencia"], errors="coerce").fillna(0.0)

            st.write("Insira as quantidades contadas na coluna **Conferência**:")
            df_editavel = itens_remessa[["id", "produto", "descricao", "quantidade", "conferencia"]].copy()

            editado = st.data_editor(
                df_editavel,
                column_config={
                    "id": None,  # Oculta o ID da visualização
                    "produto": st.column_config.TextColumn("Código", disabled=True),
                    "descricao": st.column_config.TextColumn("Descrição", disabled=True),
                    "quantidade": st.column_config.NumberColumn("Qtd. Esperada", disabled=True, format="%.2f"),
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
                key="editor_conferencia"
            )

            # Divergência = Conferido - Esperado
            editado["divergencia"] = editado["conferencia"] - editado["quantidade"]

            # Realce visual condicional
            def colorir_divergencia(valor):
                if valor < 0:
                    return "background-color: #fee2e2; color: #991b1b; font-weight: 700;"
                elif valor > 0:
                    return "background-color: #dcfce7; color: #166534; font-weight: 700;"
                else:
                    return "background-color: #f0fdf4; color: #15803d; font-weight: 600;"

            st.write("#### Painel Dinâmico de Divergências")
            st.dataframe(
                editado[["produto", "descricao", "quantidade", "conferencia", "divergencia"]].style.applymap(
                    colorir_divergencia, subset=["divergencia"]
                ),
                use_container_width=True
            )

            # Bloqueio caso haja divergência
            itens_divergentes = editado[editado["divergencia"] != 0]
            total_divergencias = len(itens_divergentes)

            st.write("---")
            if total_divergencias == 0:
                st.success("✨ **Perfeito!** Todos os itens foram conferidos e as quantidades estão exatamente iguais às da remessa.")
                
                if st.button("Gravar Conferência Sem Divergências", type="primary"):
                    with st.spinner("Atualizando registros no sistema..."):
                        registros_para_atualizar = []
                        for _, row in editado.iterrows():
                            registros_para_atualizar.append({
                                "id": int(row["id"]),
                                "conferencia": float(row["conferencia"]),
                                "divergencia": float(row["divergencia"])
                            })
                        
                        atualizar_conferencia_db(registros_para_atualizar)
                        st.success("✅ Conferência validada e gravada com sucesso!")
                        st.balloons()
            else:
                st.error(f"⚠️ **Atenção:** Existem **{total_divergencias} produto(s) com divergência**. O salvamento fica bloqueado até que os valores estejam conferidos sem divergência.")

# ==============================================================================
# OPÇÃO 4: EXPORTAR DADOS
# ==============================================================================
elif menu == "4. Exportar Dados":
    st.markdown('<div class="main-title">📤 Exportação de Registros</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Baixe a tabela completa de conferência em formato Excel (.xlsx).</div>', unsafe_allow_html=True)

    df_export = carregar_dados_db()
    if df_export.empty:
        st.info("Nenhum registro para exportar.")
    else:
        st.dataframe(df_export, use_container_width=True)
        
        # Gera o arquivo Excel para download
        excel_buffer = pd.ExcelWriter("conferencia_exportada.xlsx", engine="openpyxl")
        df_export.to_excel(excel_buffer, index=False, sheet_name="Conferencia")
        excel_buffer.close()

        with open("conferencia_exportada.xlsx", "rb") as f:
            st.download_button(
                label="📥 Baixar Planilha em Excel (.xlsx)",
                data=f,
                file_name=f"conferencia_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary"
            )