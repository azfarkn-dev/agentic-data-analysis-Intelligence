# 📊 Enterprise-Grade Agentic Business Intelligence Platform

An autonomous, zero-cost, local-first data analytics workspace built with **Streamlit**, **DuckDB**, **LangGraph**, and **ChromaDB**. Designed for seamless data exploration, it bridges the gap between traditional BI dashboards and autonomous AI agents.

---

## 🚀 Key Features

* **Liquid Glassmorphism UI:** A modern, frosted-glass dark theme workspace designed for high-focus executive data consumption.
* **Batch Multi-File & Multi-Sheet Ingestion:** Upload multiple CSV files or multi-tab Excel workbooks simultaneously; DuckDB automatically normalizes, sanitizes, and indexes them.
* **Schema-Agnostic Dynamic Filtering:** Introspects database schemas on the fly to dynamically build state-persistent dimension filters (e.g., region, department, category, tier).
* **Dual Visualization Engine:** Instantly plots categorical breakdowns (bar charts) alongside chronological trend analysis (smooth line plots), automatically recognizing date columns even when stored as text.
* **Autonomous AI Analyst Copilot:** Powered by **LangGraph** and **ChromaDB**, allowing users to ask natural language business questions. The agent searches vector-stored business rules, writes and validates SQL/Python code, executes queries locally, and returns executive answers.
* **Data Inspector & System Maintenance:** Live table previewer (up to 100 rows) with full database reset and chat history clearing capabilities.

---

## 🛠️ Tech Stack

* **Frontend:** Streamlit (Custom CSS Glassmorphism)
* **Storage & Processing:** DuckDB, Pandas, Openpyxl
* **Agentic Reasoning & RAG:** LangGraph, LangChain, ChromaDB, HuggingFace Embeddings (`sentence-transformers/all-MiniLM-L6-v2`)

---

## 📁 Project Structure

```text
agentic-analytics/
├── src/
│   ├── app.py              # Main Streamlit dashboard (Liquid Glass UI)
│   └── graph.py            # LangGraph agent workflow & RAG logic
├── samples/                # Sample test datasets (SaaS, Traffic, HR, Inventory, Trends)
├── .gitignore
├── requirements.txt
└── README.md
