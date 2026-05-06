# Finance Analytics — Data Documentation

## Overview
The finance analytics domain covers revenue, payments, and financial reconciliation. Owned by the Finance Team (finance-team@company.com).

## Key Models

### fct_orders
The primary orders fact table. Used for revenue reporting and customer analytics.
- **Owner:** analytics-team
- **SLA:** 6 hours
- **Sensitivity:** internal
- **Used by:** Executive Dashboard, Monthly Revenue Report, Customer LTV analysis

### fct_revenue_daily
Daily revenue aggregation. Critical for month-end financial reconciliation.
- **Owner:** finance-team
- **SLA:** 4 hours
- **Sensitivity:** confidential
- **Used by:** CFO Dashboard, Board Reporting, Investor Deck

## Governance Notes
- Revenue figures must match Stripe dashboard within 0.1% tolerance
- All financial models require `not_null` tests on amount columns
- Confidential models must not be exposed to external tools without approval
