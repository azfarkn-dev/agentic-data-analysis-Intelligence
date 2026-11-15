import streamlit as st
import pandas as pd
import duckdb
import re
import sys
from pathlib import Path

# 1. Page Configuration
st.set_page_config(
    page_title="Agentic Business Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Liquid Glassmorphism CSS Injection
st.markdown("""
<style>
div[data-testid="stVerticalBlock"] > div[style*="border-color"] {
    background: rgba(255, 255, 255, 0.03) !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 16px !important;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37) !important;
}
section[data-testid="stSidebar"] {
    background-color: rgba(15, 23, 42, 0.90) !important;
    backdrop-filter: blur(10px) !important;
}
</style>
""", unsafe_allow_html=True)

# 2. Path & Backend Resolution
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "analytics.duckdb"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

@st.cache_resource(show_spinner=False)
def load_graph():
    from src.graph import app_graph
    return app_graph

try:
    app_graph = load_graph()
    GRAPH_ERROR = None
except Exception as e:
    app_graph = None
    GRAPH_ERROR = str(e)

if "history" not in st.session_state:
    st.session_state["history"] = []

def sanitize_table_name(name: str) -> str:
    clean = re.sub(r'[^a-zA-Z0-9_]', '_', name.strip().lower())
    clean = re.sub(r'_+', '_', clean).strip('_')
    return f"tbl_{clean}" if clean and clean[0].isdigit() else (clean or "uploaded_table")

def get_duckdb_tables():
    try:
        if not DB_PATH.exists():
            return []
        con = duckdb.connect(str(DB_PATH), read_only=True)
        tables = [t[0] for t in con.execute("SHOW TABLES").fetchall()]
        con.close()
        return tables
    except Exception:
        return []

tables_list = get_duckdb_tables()

# ==========================================
# SIDEBAR: CONTROLS & DYNAMIC FILTERS
# ==========================================
st.sidebar.title("🎛️ Control Center")

st.sidebar.subheader("📊 Active Table Focus")
if tables_list:
    active_table = st.sidebar.selectbox("Select table to analyze", tables_list, key="active_table_select")
else:
    active_table = None
    st.sidebar.info("No tables in database. Upload files below.")

st.sidebar.divider()

# Fully Dynamic State-Persistent Filters
st.sidebar.subheader("🔍 Dynamic Filters")
filter_clauses = []
where_sql = ""

if active_table:
    try:
        con = duckdb.connect(str(DB_PATH), read_only=True)
        schema_df = con.execute(f"DESCRIBE {active_table}").df()
        con.close()
        
        cat_cols = schema_df[schema_df['column_type'].str.contains('VARCHAR|TEXT|STRING', case=False, na=False)]['column_name'].tolist()
        
        if cat_cols:
            selected_filter_col = st.sidebar.selectbox("Filter Dimension", ["None"] + cat_cols, key=f"filter_col_{active_table}")
            if selected_filter_col != "None":
                con = duckdb.connect(str(DB_PATH), read_only=True)
                unique_vals = [r[0] for r in con.execute(f"SELECT DISTINCT {selected_filter_col} FROM {active_table} WHERE {selected_filter_col} IS NOT NULL LIMIT 100").fetchall()]
                con.close()
                
                selected_val = st.sidebar.selectbox(f"Select {selected_filter_col}", ["All"] + unique_vals, key=f"filter_val_{active_table}_{selected_filter_col}")
                if selected_val != "All":
                    filter_clauses.append(f"{selected_filter_col} = '{selected_val}'")

        if filter_clauses:
            where_sql = " WHERE " + " AND ".join(filter_clauses)
            
    except Exception as e:
        st.sidebar.caption(f"Filter error: {e}")

st.sidebar.divider()

# Multi-File & Multi-Sheet Ingestion
st.sidebar.subheader("📂 Ingest Reports (Batch)")
uploaded_files = st.sidebar.file_uploader(
    "Upload CSV or Excel datasets",
    type=["csv", "xlsx", "xls"],
    accept_multiple_files=True
)

if uploaded_files:
    st.sidebar.caption(f"{len(uploaded_files)} file(s) queued.")
    if st.sidebar.button("Process & Ingest All Files", type="primary", width="stretch"):
        ingested_tables = []
        errors = []
        try:
            con = duckdb.connect(str(DB_PATH))
            for file in uploaded_files:
                base_name = Path(file.name).stem
                try:
                    if file.name.lower().endswith('.csv'):
                        df_new = pd.read_csv(file)
                        tbl_name = sanitize_table_name(base_name)
                        con.execute(f"CREATE OR REPLACE TABLE {tbl_name} AS SELECT * FROM df_new")
                        ingested_tables.append(f"{tbl_name} ({len(df_new)} rows)")
                    else:
                        excel_sheets = pd.read_excel(file, sheet_name=None)
                        for sheet_name, df_sheet in excel_sheets.items():
                            raw_name = sheet_name if len(excel_sheets) > 1 else base_name
                            tbl_name = sanitize_table_name(raw_name)
                            con.execute(f"CREATE OR REPLACE TABLE {tbl_name} AS SELECT * FROM df_sheet")
                            ingested_tables.append(f"{tbl_name} ({len(df_sheet)} rows)")
                except Exception as file_err:
                    errors.append(f"{file.name}: {file_err}")
            con.close()

            if ingested_tables:
                st.sidebar.success("Ingested:\n- " + "\n- ".join(ingested_tables))
            if errors:
                for err in errors:
                    st.sidebar.error(err)
            if ingested_tables and not errors:
                st.rerun()
        except Exception as e:
            st.sidebar.error(f"Database connection failed: {e}")

st.sidebar.divider()
st.sidebar.subheader("⚠️ System Maintenance")

if st.sidebar.button("🧹 Clear Chat History", width="stretch"):
    st.session_state["history"] = []
    st.rerun()

if st.sidebar.button("🗑️ Reset System & Drop All Tables", type="secondary", width="stretch"):
    try:
        if DB_PATH.exists():
            con = duckdb.connect(str(DB_PATH))
            tables = [t[0] for t in con.execute("SHOW TABLES").fetchall()]
            for tbl in tables:
                con.execute(f"DROP TABLE IF EXISTS {tbl}")
            con.close()
        st.session_state["history"] = []
        st.sidebar.success("System wiped clean!")
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"Error resetting database: {e}")

# ==========================================
# MAIN NAVIGATION TABS
# ==========================================
tab_dashboard, tab_chat = st.tabs(["📊 Executive Command Center", "💬 AI Analyst Chat Copilot"])

# ==========================================
# TAB 1: EXECUTIVE COMMAND CENTER
# ==========================================
with tab_dashboard:
    st.title("📊 Executive Command Center")
    st.caption("Liquid glass analytics workspace with dynamic filters, trend lines, and categorical bar breakdowns.")

    if active_table:
        try:
            con = duckdb.connect(str(DB_PATH), read_only=True)
            schema_df = con.execute(f"DESCRIBE {active_table}").df()
            
            total_rows = con.execute(f"SELECT COUNT(*) FROM {active_table}{where_sql}").fetchone()[0]

            num_cols = schema_df[schema_df['column_type'].str.contains('BIGINT|INTEGER|DOUBLE|DECIMAL|FLOAT|NUMERIC', case=False, na=False)]['column_name'].tolist()
            text_cols = schema_df[schema_df['column_type'].str.contains('VARCHAR|TEXT|STRING', case=False, na=False)]['column_name'].tolist()
            
            # Robust Date Column Detection (matches SQL type OR name containing date/time/day/year)
            date_cols = schema_df[
                schema_df['column_type'].str.contains('DATE|TIMESTAMP', case=False, na=False) |
                schema_df['column_name'].str.contains('date|time|day|year|period', case=False, na=False)
            ]['column_name'].tolist()

            primary_metric_val = 0.0
            primary_metric_name = "Total Records"
            if num_cols:
                first_num = num_cols[0]
                primary_metric_val = con.execute(f"SELECT SUM({first_num}) FROM {active_table}{where_sql}").fetchone()[0] or 0.0
                primary_metric_name = f"Total {first_num.replace('_', ' ').title()}"

            con.close()

            # KPI Scorecards
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Active Table", active_table)
            col2.metric("Filtered Records", f"{total_rows:,}")
            col3.metric(primary_metric_name, f"{primary_metric_val:,.2f}" if isinstance(primary_metric_val, float) else f"{primary_metric_val:,}")
            col4.metric("Indexed Tables", len(tables_list))

            st.markdown("---")

            # Charts Row: Bar Chart & Trend Line Chart
            col_chart1, col_chart2 = st.columns(2)

            with col_chart1:
                st.subheader("📊 Categorical Breakdown (Bar Chart)")
                if text_cols and num_cols:
                    group_col = text_cols[0]
                    val_col = num_cols[0]
                    con = duckdb.connect(str(DB_PATH), read_only=True)
                    bar_df = con.execute(f"""
                        SELECT {group_col} AS dimension, SUM({val_col}) AS metric 
                        FROM {active_table}{where_sql} 
                        GROUP BY {group_col} 
                        ORDER BY metric DESC 
                        LIMIT 10
                    """).df().set_index("dimension")
                    con.close()
                    if not bar_df.empty:
                        st.bar_chart(bar_df)
                    else:
                        st.info("No data available for grouping.")
                elif text_cols:
                    group_col = text_cols[0]
                    con = duckdb.connect(str(DB_PATH), read_only=True)
                    bar_df = con.execute(f"""
                        SELECT {group_col} AS dimension, COUNT(*) AS count 
                        FROM {active_table}{where_sql} 
                        GROUP BY {group_col} 
                        ORDER BY count DESC 
                        LIMIT 10
                    """).df().set_index("dimension")
                    con.close()
                    st.bar_chart(bar_df)
                else:
                    st.info("No categorical dimensions found.")

            with col_chart2:
                st.subheader("📈 Chronological Trend Analysis (Line Chart)")
                if date_cols and num_cols:
                    date_col = date_cols[0]
                    val_col = num_cols[0]
                    con = duckdb.connect(str(DB_PATH), read_only=True)
                    trend_df = con.execute(f"""
                        SELECT CAST({date_col} AS DATE) AS timeline, SUM({val_col}) AS metric 
                        FROM {active_table}{where_sql} 
                        GROUP BY timeline 
                        ORDER BY timeline ASC
                    """).df().set_index("timeline")
                    con.close()
                    if not trend_df.empty:
                        st.line_chart(trend_df)
                    else:
                        st.info("No trend data available.")
                elif date_cols:
                    date_col = date_cols[0]
                    con = duckdb.connect(str(DB_PATH), read_only=True)
                    trend_df = con.execute(f"""
                        SELECT CAST({date_col} AS DATE) AS timeline, COUNT(*) AS count 
                        FROM {active_table}{where_sql} 
                        GROUP BY timeline 
                        ORDER BY timeline ASC
                    """).df().set_index("timeline")
                    con.close()
                    st.line_chart(trend_df)
                else:
                    st.info("No date/timestamp column found in this table for trend plotting.")

            st.markdown("---")
            st.subheader(f"📋 Data Inspector: `{active_table}`")
            con = duckdb.connect(str(DB_PATH), read_only=True)
            df_preview = con.execute(f"SELECT * FROM {active_table}{where_sql} LIMIT 100").df()
            con.close()
            st.dataframe(df_preview, width="stretch")

        except Exception as e:
            st.error(f"Error rendering dashboard: {e}")
    else:
        st.info("👋 Welcome! Upload datasets via the sidebar to begin analyzing trends and filtering records.")

# ==========================================
# TAB 2: AI ANALYST CHAT COPILOT
# ==========================================
with tab_chat:
    st.title("💬 AI Data Analyst Copilot")
    st.caption("Ask analytical questions across your ingested tables. The agent writes SQL, checks RAG rules, and executes Python code.")

    if GRAPH_ERROR:
        st.error(f"LangGraph failed to load: {GRAPH_ERROR}")

    with st.form("ai_query_form", clear_on_submit=True):
        user_prompt = st.text_area(
            "Ask a business question:",
            placeholder="e.g., Show me the revenue trend over time or compare categories.",
            height=100
        )
        submitted = st.form_submit_button("Run AI Analysis", type="primary", width="stretch")

    if submitted and user_prompt.strip():
        if app_graph is None:
            st.error("LangGraph application is not available.")
        else:
            initial_state = {
                "user_query": user_prompt,
                "retrieved_knowledge": "",
                "schema_summary": "",
                "generated_code": "",
                "execution_output": "",
                "execution_error": "",
                "chart_path": "",
                "retry_count": 0,
                "final_answer": ""
            }

            with st.spinner("🤖 Agent querying vector store, writing SQL, and executing code..."):
                try:
                    result = app_graph.invoke(initial_state)
                    raw_answer = result.get("final_answer", "")
                    if isinstance(raw_answer, list):
                        raw_answer = "\n".join([str(b.get("text", b)) if isinstance(b, dict) else str(b) for b in raw_answer])

                    entry = {
                        "query": user_prompt,
                        "answer": str(raw_answer),
                        "code": result.get("generated_code", ""),
                        "output": result.get("execution_output", ""),
                        "error": result.get("execution_error", ""),
                        "knowledge": result.get("retrieved_knowledge", "")
                    }
                    st.session_state["history"].insert(0, entry)
                except Exception as e:
                    st.error(f"Agent execution failed: {str(e)}")

    if st.session_state["history"]:
        st.markdown("### 📋 Analysis History")
        for entry in st.session_state["history"]:
            with st.container(border=True):
                st.markdown(f"**Query:** `{entry['query']}`")
                st.markdown("#### 💡 Executive Answer")
                st.write(entry["answer"] if entry["answer"] else "No answer returned.")

                if entry["error"]:
                    st.error(f"Execution Error: {entry['error']}")

                with st.expander("🐍 View Generated Code & RAG Logs"):
                    st.code(entry["code"] if entry["code"] else "# No code generated", language="python")
                    st.text(entry["output"] if entry["output"] else entry["knowledge"])