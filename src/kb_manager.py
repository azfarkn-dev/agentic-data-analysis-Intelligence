import os
import duckdb
import pandas as pd
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

load_dotenv()

DB_DIR = "data/vector_db"
GLOSSARY_PATH = "data/knowledge_base/business_glossary.md"

def get_vector_store():
    """Initializes local ChromaDB with free HuggingFace embeddings."""
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    if os.path.exists(GLOSSARY_PATH):
        # Split markdown by headers to keep definitions clean
        headers_to_split_on = [("#", "Header 1"), ("##", "Header 2")]
        markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
        
        with open(GLOSSARY_PATH, "r", encoding="utf-8") as f:
            markdown_text = f.read()
            
        docs = markdown_splitter.split_text(markdown_text)
        
        # Persist to local vector DB
        vector_store = Chroma.from_documents(
            documents=docs,
            embedding=embeddings,
            persist_directory=DB_DIR
        )
        print("Knowledge base successfully indexed into ChromaDB (local & free).")
        return vector_store
    else:
        raise FileNotFoundError(f"Glossary not found at {GLOSSARY_PATH}. Run setup_data.py first.")

def get_schema_summary():
    """Inspects raw CSV files using DuckDB and returns table schemas + sample rows."""
    con = duckdb.connect(database=":memory:")
    
    # Register CSV files as virtual tables
    con.execute("CREATE TABLE customers AS SELECT * FROM 'data/raw/customers.csv'")
    con.execute("CREATE TABLE orders AS SELECT * FROM 'data/raw/orders.csv'")
    
    schema_info = []
    tables = ["customers", "orders"]
    
    for table in tables:
        schema_info.append(f"--- Table: {table} ---")
        # Get column names and types
        cols = con.execute(f"DESCRIBE {table}").fetchall()
        for col in cols:
            schema_info.append(f"  - {col[0]} ({col[1]})")
            
        # Get 2 sample rows
        samples = con.execute(f"SELECT * FROM {table} LIMIT 2").fetchdf()
        schema_info.append(f"  Sample Data:\n{samples.to_string(index=False)}\n")
        
    con.close()
    return "\n".join(schema_info)

if __name__ == "__main__":
    vs = get_vector_store()
    print("\n--- Schema Summary ---")
    print(get_schema_summary())