# MicroBlend Backend

MicroBlend is a Django REST backend for a spatially distributed restaurant setup where kitchen, cashier, bar, hangout, and dining functions operate across a large local area network. The backend is designed as a microservices-ready modular system: each Django app is a bounded context that can stay in one deployment for local/offline use today, then be extracted into independent services later if needed.

## Service Boundaries

- `apps.users`: account registration/login by email or mobile, device binding, RBAC, self-service account updates, and admin user control.
- `apps.menu`: categories, menu items, ingredient requirements, customer-safe menu output, and one-click order playlists.
- `apps.inventory`: ingredients, restock batches, stock movements, and automatic menu availability based on required ingredient quantities.
- `apps.tables`: table metadata, QR scan requests, table groups, occupancy changes, and universal staff paging.
- `apps.table_sessions`: active table occupancy sessions tied to QR/manual/waiter flows.
- `apps.orders`: draft orders, playlist ordering, waiter-assisted ordering, bulk order flags, kitchen/bar/cashier workflow, cancellation/edit rules, receipts, and audit trail hooks.
- `apps.notifications`: role-targeted notifications and backend debounce protection.
- `apps.integrations`: external POS systems and offline sync events for secondary POS/mobile clients on local Wi-Fi.
- `apps.analytics`: admin dashboard snapshots, report generation, backups, resets, and costing/profit simulations.
- `apps.audit_logs`: critical action logging for sensitive staff/admin operations.
- `apps.feedback`: customer feedback and incident/report submissions.
- `apps.realtime`: SSE-based live event feed for inventory/menu/order/table updates.

## Offline And Real-Time Strategy

- The backend runs on the local network and does not require internet to process orders.
- `apps.integrations.SyncEvent` acts as a local sync outbox so mobile clients or a secondary POS can pull changes after reconnecting.
- Role-targeted notifications give kitchen, bar, cashier, and waiter workflows a near-real-time backend signal even when the frontend is implemented separately.
- Backend debounce rules provide a second safety layer if the frontend debounce is bypassed.
- `apps.realtime` exposes a role-aware event stream so clients can receive live updates without polling full resources.

## Key Business Rules Implemented

- RBAC for `admin`, `staff`, and `customer`, with staff subdivisions for waiter, cashier, kitchen, and bar.
- Orders can be saved as drafts, then submitted.
- Orders can be cancelled or edited until preparation has started.
- Bulk orders are marked for cashier verification.
- Menu availability depends on real ingredient requirements, not just a single stock flag.
- High-value orders silently alert cashier staff.
- Demand-driven notifications warn the relevant production station before stock runs too low.
- Table QR scans are treated as requests that staff can approve or block.
- Staff page requests go into a shared pool and are explicitly finished by staff.
- Admin-only analytics, reports, simulations, backup, and reset endpoints are exposed.

## API Surface

- Auth and accounts: `/api/identity/...`
- Menu and playlists: `/api/menu-items/`, `/api/categories/`, `/api/order-playlists/`
- Inventory: `/api/inventory/...`
- Tables and paging: `/api/tables/`, `/api/table-scan-requests/`, `/api/table-groups/`, `/api/staff-pages/`
- Sessions: `/api/table-sessions/`
- Orders: `/api/orders/`, including `submit`, `cancel`, `kitchen_update`, `bar_update`, `cashier_update`, and `from_playlist`
- Notifications: `/api/notifications/`
- Integrations and sync: `/api/integrations/...`
- Realtime feed: `/api/realtime/events/`, `/api/realtime/stream/`
- Analytics: `/api/analytics/...`
- OpenAPI schema: `/api/schema/`
- Swagger UI: `/api/docs/`

## Verification

Validated with:

- Django system checks
- Targeted Django tests covering user constraints, ingredient-aware availability, debounce, table/session generation, order lifecycle, and analytics snapshot behavior

## Notes

- The committed `backend/db.sqlite3` predates the rebuilt migration graph. For a clean setup, create a fresh database and run migrations from the current codebase.
- The original project virtual environment points to a missing Python install on this machine. The code itself is valid, but local execution may require recreating the virtualenv before normal `python manage.py ...` usage.
- WebSockets are not enabled in this environment yet. Real-time updates currently use Server-Sent Events (SSE) endpoints.
