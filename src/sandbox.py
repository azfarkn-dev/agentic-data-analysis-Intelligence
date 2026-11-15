import io
import sys
import traceback
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for saving plots
import matplotlib.pyplot as plt
import pandas as pd
import duckdb

def run_analytics_code(code_string: str) -> dict:
    """
    Executes Python code in a controlled environment with access to pandas, duckdb,
    and pre-loaded DataFrames. Captures print outputs and saved chart paths.
    """
    # Pre-load dataframes so the agent can query them instantly via DuckDB or Pandas
    customers = pd.read_csv("data/raw/customers.csv")
    orders = pd.read_csv("data/raw/orders.csv")
    
    # Setup local namespace with tools and data
    local_vars = {
        "pd": pd,
        "duckdb": duckdb,
        "customers": customers,
        "orders": orders,
        "plt": plt
    }
    
    # Capture stdout
    old_stdout = sys.stdout
    new_stdout = io.StringIO()
    sys.stdout = new_stdout
    
    success = True
    error_message = ""
    
    try:
        # Clear any existing matplotlib figures
        plt.clf()
        plt.close('all')
        
        # Execute the generated code string
        exec(code_string, {"__builtins__": __builtins__}, local_vars)
        
        # Check if a chart was generated and saved
        chart_path = "outputs/charts/latest_analysis.png"
        if plt.get_fignums():
            plt.savefig(chart_path, bbox_inches="tight", dpi=300)
            plt.close('all')
        else:
            chart_path = None
            
    except Exception as e:
        success = False
        error_message = traceback.format_exc()
        chart_path = None
        
    finally:
        sys.stdout = old_stdout
        
    captured_output = new_stdout.getvalue()
    
    return {
        "success": success,
        "output": captured_output,
        "error": error_message,
        "chart_path": chart_path
    }