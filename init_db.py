import os
from pathlib import Path
import duckdb
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
CHROMA_DIR = PROJECT_ROOT / "chroma_db"

def init_duckdb():
    print("--- Initializing DuckDB Database ---")
    db_path = PROJECT_ROOT / "analytics.duckdb"
    
    # Connect to DuckDB (creates file if it doesn't exist)
    con = duckdb.connect(str(db_path))
    
    # Check if data folder exists
    if not DATA_DIR.is_dir():
        print(f"Warning: 'data' folder not found at {DATA_DIR}. Please place your CSVs there.")
        con.close()
        return

    # Load customers and orders if CSVs exist
    customers_csv = DATA_DIR / "customers.csv"
    orders_csv = DATA_DIR / "orders.csv"
    
    if customers_csv.exists():
        con.execute(f"CREATE OR REPLACE TABLE customers AS SELECT * FROM read_csv_auto('{customers_csv}')")
        print("Loaded `customers` table.")
        
    if orders_csv.exists():
        con.execute(f"CREATE OR REPLACE TABLE orders AS SELECT * FROM read_csv_auto('{orders_csv}')")
        print("Loaded `orders` table.")
        
    con.close()
    print(f"DuckDB database saved successfully to {db_path}\n")

def init_knowledge_base():
    print("--- Initializing ChromaDB Knowledge Base ---")
    glossary_path = DATA_DIR / "business_glossary.md"
    
    if not glossary_path.exists():
        # Create a default sample glossary if none exists
        DATA_DIR.mkdir(exist_ok=True, parents=True)
        default_glossary = """# Business Glossary & Rules
- **Net Revenue**: Calculated as `gross_amount - discount_amount`.
- **Completed Orders**: Orders where `status == 'Completed'`.
- **Test Accounts**: Exclude all customers where `is_internal_test == True` or `is_internal_test == 1` from official financial reporting.
- **Enterprise Orders**: Orders belonging to the 'Enterprise' customer segment.
"""
        with open(glossary_path, "w", encoding="utf-8") as f:
            f.write(default_glossary)
        print("Created default `business_glossary.md` in data/ folder.")

    with open(glossary_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Split by markdown headers or bullet points to create chunks
    chunks = [doc.strip() for doc in content.split("\n- ") if doc.strip()]
    documents = [Document(page_content=chunk, metadata={"source": "business_glossary.md"}) for chunk in chunks]
    
    # Initialize HuggingFace embeddings (free, local execution)
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    # Create and persist Chroma vector store
    vector_store = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=str(CHROMA_DIR)
    )
    print(f"ChromaDB knowledge base indexed and saved to {CHROMA_DIR}\n")

if __name__ == "__main__":
    init_duckdb()
    init_knowledge_base()
    print("Initialization complete! You can now run your Streamlit app.")