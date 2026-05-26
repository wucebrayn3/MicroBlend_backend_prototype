# MicroBlend — Chen Notation ERD Explanation

## Overview

The Entity-Relationship Diagram (Chen notation) models the complete MicroBlend database — 26 entities and 35 relationships across 7 domain areas. Each entity is a rectangle, attributes are ovals, and relationships are diamonds with verbs and cardinality labels (1, N, M).

---

## Domain 1: Users & Notifications

### users
Central actor table supporting all account types: customers, waiters, kitchen/bar staff, cashiers, and admins. Guest accounts (is_guest) allow walk-in customers to order without registration. The soft-delete flag (is_deleted) preserves foreign key integrity when accounts are removed.

**Relationships (14 outbound):**
- `places` 1:N → orders
- `owns` 1:N → order_playlists
- `opens` 1:N → table_sessions (as the staff who opened)
- `sits at` 1:N → table_sessions (as the customer)
- `requests (scan)` 1:N → table_scan_requests
- `requests (staff)` 1:N → staff_page_requests
- `resolves` 1:N → staff_page_requests
- `receives` 1:N → notifications
- `performs` 1:N → audit_logs
- `submits` 1:N → feedback_entries
- `generates` 1:N → generated_reports
- `creates` 1:N → cost_simulations
- `triggers` 1:N → realtime_events
- `acts upon` 1:N → inventory_movements

### notification
In-app alert records. Can target a specific user (recipient FK) or broadcast to all users of a given role (role_target string). Category enables client-side filtering.

### debounce_record
Standalone idempotency guard with a unique constraint on (actor_key, action, object_key). No foreign keys to keep it fast — uses loose strings so it works for any actor type (user ID, device ID, system ID).

---

## Domain 2: Menu & Ingredients

### category
Groups menu items (e.g. Appetizers, Main Course, Desserts). Sort_order controls display order.

### menu_item
Sellable items assigned to a preparation station (kitchen or bar). The is_available flag is toggled automatically when ingredient stock is insufficient.

### menu_item_ingredient
M:N junction between menu_item and ingredient with a payload (quantity_required). The relationship itself carries the data — neither parent owns it alone.

### ingredient
Raw materials tracked in inventory with a unit of measure (g/ml/pc) and a reorder_level threshold for low-stock alerts.

---

## Domain 3: Inventory

### inventory_batch
Records individual deliveries of an ingredient. Tracks quantity_added, quantity_remaining, unit_cost, and expiration_date for FIFO cost tracking and spoilage monitoring.

### inventory_movement
Immutable log of every inventory transaction: restock, deduct, adjust, or delete. Links to the actor who performed it and optionally to the batch and order that caused the movement.

---

## Domain 4: Orders

### order
Core transaction record with three parallel status tracks (kitchen, bar, cashier) that advance independently. Denormalized fields (placed_by_name, placed_for_name) preserve context if related users are deleted. Channel identifies how the order entered (customer_account, guest, waiter_assisted, bulk, pos_sync).

### order_item
Line items with denormalized copies of item_name, station, and unit_price at time of order. This snapshot ensures historical receipts remain accurate after menu changes.

### order_status_log
Immutable audit trail for every status transition. Records who changed it, what it changed to, and optional JSON metadata.

### feedback_entry
Customer feedback and problem reports. Links to both the submitting user and the order. Entry_type distinguishes feedback from reports; status tracks the handling lifecycle.

---

## Domain 5: Order Playlists

### order_playlist
Saved order template owned by a user. Unique on (owner_id, name) prevents duplicate named playlists.

### order_playlist_item
Junction between playlist and menu_item with quantity. Unique on (playlist_id, menu_item_id).

---

## Domain 6: Table Management

### table
Physical tables with a display identifier, seating capacity, status (vacant/occupied/merged/blocked), zone for area grouping, and an auto-generated QR code value.

### table_merge_group
Groups of merged tables (M:N with table via the implicit junction table_merge_group_tables). Allows flexible table combinations for large parties.

### table_session
A seating session representing customer occupation of a table. Tracks which staff opened it, which customer is seated, how they arrived (source: qr/walk_in/waiter/manual), party size, and active duration.

### table_scan_request
QR code scan intent from a customer. Records the table, the requesting user, the device used, and the moderation outcome (pending/approved/blocked).

### staff_page_request
Customer request for staff assistance. Reason categorizes the need (cleanup/payment/accident). Links to both table and session for context, and tracks who resolved it.

---

## Domain 7: Analytics, Integration & System

### audit_log
Generic action log using a polymorphic FK pattern: target_type + target_id + target_label can reference any entity without formal FK constraints. Captures actor, action, role snapshot, and JSON metadata.

### generated_report
Report generation request and result storage. Supports daily, weekly, monthly, annual, and custom date ranges. Report data is stored as JSON payload.

### cost_simulation
What-if cost analysis scenarios. Users input assumptions (ingredient prices, quantities, waste) as JSON; the system computes projected costs and margins stored as results JSON.

### external_system
Registered integration partners (POS, mobile, kiosk). Type and active flag control routing and enable/disable sync without removing configuration.

### sync_event
Outbox-pattern event log for external system sync. Events are written during the main request and consumed asynchronously. The idempotency_key prevents duplicate processing.

### realtime_event
SSE (Server-Sent Events) data store. Events are created by domain services and consumed by clients via the polling-based SSE endpoint at /api/realtime/stream/. Targeting by role or user restricts which clients receive each event.

---

## Key Notation Conventions

| Element | Chen Symbol | Meaning |
|---|---|---|
| Entity | Rectangle | A table in the database |
| Attribute | Oval | A column/field of the table |
| Relationship | Diamond | A foreign key or link between tables |
| 1 | On edge near entity | "One" side of the relationship |
| N, M | On edge near entity | "Many" side of the relationship |
| (wk) | Entity label | Weak/associative entity (junction table) |
| (m2m) | Relationship label | Implicit many-to-many relationship |

## Summary Statistics

| Metric | Count |
|---|---|
| Entities | 26 |
| Relationships | 35 |
| User outbound relationships | 14 |
| Weak / associative entities | 6 |
