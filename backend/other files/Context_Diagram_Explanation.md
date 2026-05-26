# MicroBlend Context Diagram

The system is a single process — **MicroBlend** — an integrated point-of-sale and table management platform for hospitality venues. Eight external entities interact with it:

## External Entities & Flows

| Entity | Incoming to System | Outgoing from System |
|---|---|---|
| **Customer** | QR scan, place order, submit feedback, staff page request | Order confirmation, receipt/bill, notification |
| **Waiter** | Open/manage table sessions, place/modify orders, resolve staff page requests | Table status updates, pending request alerts |
| **Kitchen Staff** | View orders, update preparation status | New order alerts, order queue |
| **Bar Staff** | View drink orders, update bar status | New drink order alerts, drink queue |
| **Cashier** | View bills, process payments, verify bulk orders | Pending payment notifications |
| **Administrator** | Manage menu, categories, inventory, users, reports, cost simulations, external systems | Analytics, reports, audit logs |
| **External POS** | Sync orders, sync menu | Sync events (outbox pattern) |
| **Mobile / Kiosk** | Browse menu, submit order | Order status updates |

## Key Characteristics

- **Human actors** (Customer, Waiter, Kitchen, Bar, Cashier, Admin) interact via the system's UI or QR-based flows.
- **System actors** (External POS, Mobile/Kiosk) interact via API with idempotency (sync_events) for reliable async sync.
- The system owns all data internally — inventory tracking, table state, order lifecycle with parallel kitchen/bar/cashier status tracks.
