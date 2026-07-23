# The Shatranj Heritage

**Bangladesh's first dedicated e-commerce platform for chess.**

Chess has grown steadily in Bangladesh over the past decade, but the market for chess equipment, books, and handcrafted sets remains scattered across general marketplaces, informal importers, and a handful of physical shops. The Shatranj Heritage exists to fix that: a specialized platform that brings commerce, community, craftsmanship, and education together for players, collectors, schools, clubs, tournament organizers, and local artisans.

## Vision

> To become the most trusted and inspiring destination for chess enthusiasts by connecting players, artisans, educators, and organizations through a unified commerce and community platform that celebrates the culture of chess.

Beyond selling products, the platform is built to showcase Bangladeshi craftsmanship, give local artisans national (and eventually international) visibility, and strengthen the country's chess community — with an ambition to grow into the leading chess commerce ecosystem across South Asia.

## Who it's for

- **Casual & competitive players** — from beginners buying their first set to tournament players needing FIDE-standard boards, clocks, and equipment
- **Collectors** — premium wooden, marble, and brass sets, limited editions, artistic pieces
- **Gift buyers** — personalized and corporate chess gifts
- **Schools, academies, clubs & tournament organizers** — bulk and institutional procurement
- **Local artisans** — a digital storefront and nationwide reach for handcrafted chess products

## Project status

This project is currently in the **planning and requirements stage** — no application code has been written yet. The focus so far has been on defining *what* to build and *why* before *how*.

## Documentation

Full product and engineering requirements live in [`docs/`](docs/):

| Document | Purpose |
| --- | --- |
| [Product Vision Document](docs/Product%20Vision%20Document.md) | Why the product exists, target audience, vision & mission |
| [Business Requirements Document](docs/Business%20Requirements%20Document.md) | Business goals, capabilities, rules, and constraints |
| [Software Requirements Specification](docs/Software%20Requirements%20Specification.md) | Functional & non-functional requirements, architecture, data model, API design |
| [Product Backlog & User Stories](docs/Product%20Backlog%20and%20User%20Stories.md) | Epics, user stories, and MVP scope for implementation |
| [Entity Relationship Diagram & Database Schema](docs/Entity%20Relationship%20Diagram%20and%20Database%20Schema.md) | ERD and field-level PostgreSQL schema, ready for migrations |

## Planned technology stack

As proposed in the SRS, pending final confirmation:

| Layer | Choice |
| --- | --- |
| Frontend | Next.js (React + TypeScript) |
| Backend | FastAPI (Python) |
| Database | PostgreSQL |
| Cache | Redis |
| Search | PostgreSQL Full-Text Search (MVP), Elasticsearch/OpenSearch later if needed |
| Object Storage | S3-compatible storage |
| Auth | JWT + Refresh Tokens |
| Payments | SSLCommerz (bKash, Nagad, Rocket, cards), Cash on Delivery |
| Deployment | Docker, GitHub Actions CI/CD |
| Monitoring | Prometheus + Grafana |

The initial architecture is a **modular monolith** rather than microservices, to keep MVP delivery fast and simple while preserving clean module boundaries for future extraction.

## Roadmap

- **V1 (MVP)** — Product catalog, search, cart, checkout, payments, order management, inventory, admin dashboard
- **V2** — Wishlist, reviews & ratings, coupons, blogs & buying guides, richer CMS
- **V3** — Multi-vendor marketplace for artisans, mobile apps, AI-powered recommendations, regional (South Asia) expansion

## License

Not yet decided.
