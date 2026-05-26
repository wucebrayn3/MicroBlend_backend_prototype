# MicroBlend — Network Plan

## Topology

```
Internet → Modem → Router / Access Point (all Wi-Fi)
```

A single router provides both internet access and local LAN connectivity via Wi-Fi. No wired infrastructure — all devices connect wirelessly.

## Devices

| Device | Role | Notes |
|---|---|---|
| **Server PC / Laptop** | Hosts Django app + SQLite database | Runs during operating hours; shutdown at shift close. No cloud dependency for core operations. |
| **POS Tablet** | Waiter / Cashier station | Place orders, process payments, manage table sessions, resolve page requests. |
| **Kitchen Display** | Order queue for kitchen staff | Receives real-time order alerts and prep status updates via SSE. |
| **Staff Phone** | Mobile staff terminal | Handheld device for waiters and managers to monitor requests and tables. |
| **Customer Phone** | QR scan, menu browsing, ordering | Connects over venue Wi-Fi; no cellular data required. |
| **Admin / Manager Laptop** | Menu management, inventory, reports, cost simulations, audit logs | Administrative functions not needed on the POS floor. |
| **External POS (cloud)** | Third-party POS integration | Syncs orders and menu bidirectionally over the internet via API. |

## Data Flow

- **API + SSE** — All internal devices communicate with the Server via HTTP REST API and Server-Sent Events (SSE) for real-time push.
- **Sync Events** — Outbox pattern: the Server writes sync events to the database; a background worker pushes them to External POS. External POS also pushes order/menu updates back to the Server.
- **Internet dependency** — Only required for External POS sync. Core POS and table management functions work offline on the local Wi-Fi network.

## Security Notes

- The router should have WPA2/3 encryption and a guest network isolated from the POS network.
- The Server PC should be configured to only accept LAN connections (no public-facing ports).
- External POS sync should use HTTPS with API keys.
