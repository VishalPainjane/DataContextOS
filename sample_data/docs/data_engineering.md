# Data Engineering Team — Data Documentation

## Team Overview
The Data Engineering team owns the ingestion pipelines, data warehouse, and data quality monitoring.

**Team Lead:** Sarah Chen (sarah.chen@company.com)

## Owned Assets

| Model | Domain | SLA | Description |
|-------|--------|-----|-------------|
| `stg_orders` | Finance | 6h | Cleaned orders from production DB |
| `stg_customers` | Marketing | 12h | Deduplicated customer records |
| `stg_products` | Product | 24h | Normalized product catalog |
| `stg_order_items` | Finance | 6h | Order line items |
| `stg_payments` | Finance | 4h | Payment transactions from Stripe |

## Data Quality Rules
- All staging models must have `not_null` and `unique` tests on primary keys
- Foreign key relationships tested with `relationships` tests
- Freshness checks run every hour via dbt source freshness

## Freshness SLAs
- **Finance data:** 4-6 hours (critical for daily reconciliation)
- **Customer data:** 12 hours (marketing campaigns, batch)
- **Product data:** 24 hours (catalog changes are infrequent)
- **Event data:** 1 hour (real-time product analytics)
