# Company Analytics Knowledge Base & Business Glossary

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