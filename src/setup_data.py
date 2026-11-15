import os
import random
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

def setup_directories():
    dirs = ["data/raw", "data/knowledge_base", "outputs/charts"]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    print("Directory structure verified.")

def generate_datasets():
    np.random.seed(42)
    random.seed(42)

    # 1. Generate Customers Table
    num_customers = 1000
    segments = ["Enterprise", "Mid-Market", "SMB", "Self-Serve"]
    regions = ["North America", "Europe", "APAC", "LATAM"]
    
    customers = pd.DataFrame({
        "customer_id": [f"CUST-{i:04d}" for i in range(1, num_customers + 1)],
        "segment": np.random.choice(segments, num_customers, p=[0.15, 0.25, 0.35, 0.25]),
        "region": np.random.choice(regions, num_customers, p=[0.45, 0.30, 0.15, 0.10]),
        "signup_date": [
            (datetime(2024, 1, 1) + timedelta(days=random.randint(0, 700))).strftime("%Y-%m-%d")
            for _ in range(num_customers)
        ],
        "is_internal_test": np.random.choice([True, False], num_customers, p=[0.03, 0.97])
    })

    # 2. Generate Orders Table
    num_orders = 5000
    statuses = ["Completed", "Refunded", "Cancelled", "Pending"]
    
    order_dates = [
        datetime(2025, 1, 1) + timedelta(days=random.randint(0, 650))
        for _ in range(num_orders)
    ]
    
    orders = pd.DataFrame({
        "order_id": [f"ORD-{i:05d}" for i in range(1, num_orders + 1)],
        "customer_id": np.random.choice(customers["customer_id"], num_orders),
        "order_date": [d.strftime("%Y-%m-%d") for d in order_dates],
        "gross_amount": np.round(np.random.lognormal(mean=5.5, sigma=0.9, size=num_orders), 2),
        "discount_amount": np.round(np.random.uniform(0, 40, size=num_orders), 2),
        "status": np.random.choice(statuses, num_orders, p=[0.80, 0.08, 0.07, 0.05]),
        "currency": ["USD" if d >= datetime(2025, 6, 1) else random.choice(["USD", "EUR"]) for d in order_dates]
    })
    
    # Ensure discount never exceeds gross_amount
    orders["discount_amount"] = np.minimum(orders["discount_amount"], orders["gross_amount"] * 0.5)

    customers.to_csv("data/raw/customers.csv", index=False)
    orders.to_csv("data/raw/orders.csv", index=False)
    print("Generated data/raw/customers.csv and data/raw/orders.csv")

def generate_knowledge_base():
    glossary_content = """# Company Analytics Knowledge Base & Business Glossary

## 1. Core KPI Definitions
- **Gross Merchandise Value (GMV):** Sum of `gross_amount` across all orders regardless of status.
- **Net Revenue:** Sum of `(gross_amount - discount_amount)` ONLY for orders where `status == 'Completed'`, AND excluding customers where `is_internal_test == True`.
- **Churn / Refund Rate:** Percentage of non-cancelled orders where `status == 'Refunded'`.

## 2. Customer Segment Rules
- **Enterprise Accounts:** Any customer with `segment == 'Enterprise'` OR cumulative completed Net Revenue greater than $25,000.
- **Internal Test Accounts:** Customers flagged with `is_internal_test == True` are QA/sandbox accounts and MUST be excluded from all customer counts, revenue, and retention metrics unless explicitly requested.

## 3. Data Caveats & Historical Quirks
- **Currency Conversion:** Prior to June 1, 2025 (`2025-06-01`), European orders were logged in `EUR`. For all financial aggregations, convert `EUR` to `USD` using a fixed historical rate of `1 EUR = 1.10 USD`.
- **Pending Orders:** Orders in `Pending` status represent uncollected invoices and should never be counted toward realized revenue.
"""
    with open("data/knowledge_base/business_glossary.md", "w", encoding="utf-8") as f:
        f.write(glossary_content.strip())
    print("Generated data/knowledge_base/business_glossary.md")

if __name__ == "__main__":
    setup_directories()
    generate_datasets()
    generate_knowledge_base()