---
name: clawmart-manager
description: Search, download, publish, and sync Claw Mart listings from your agent. Use for profile info, catalog search, bulk downloads, publishing listings, uploading new versions, and sync status. Requires CLAWMART_API_KEY environment variable.
---

# Claw Mart Manager

**Version:** 1.1.0
**Price:** Free
**Type:** Skill

## Description

Full Claw Mart lifecycle management from inside your OpenClaw agent. Search the catalog, download all your purchased skills at once, manage your creator listings, upload new versions, and get a sync status report showing what's live vs. stale — all without touching the browser.

Significantly enhanced version of the standard creator skill. Adds bulk download, catalog search, sync diffing, and automatic Skill Inspector integration.

## Prerequisites

- Claw Mart creator account (free tier works for downloads; creator subscription required for publishing)
- API key from your Claw Mart dashboard (API Keys tab)
- Environment variable: `CLAWMART_API_KEY=cm_live_...`

## Setup

1. Add your API key to OpenClaw environment: `CLAWMART_API_KEY=cm_live_...`
2. Copy `SKILL.md` into your OpenClaw skills directory (e.g. `skills/clawmart-manager/SKILL.md`)
3. Reload OpenClaw
4. Test with: "Show my Claw Mart profile"

## Commands

**Account**
- "Show my Claw Mart profile"
- "Validate my Claw Mart API key"

**Catalog Search**
- "Search Claw Mart for [topic]"
- "Find memory management skills on Claw Mart"
- "What agent orchestration tools exist on Claw Mart?"

**Downloads (Purchased + Created)**
- "Download all my Claw Mart packages"
- "Pull [skill-name] from Claw Mart"
- "What can I download from Claw Mart?"
- "List everything I've purchased"

**Creator / Publish**
- "Show my Claw Mart listings"
- "Create a new Claw Mart listing for [description]"
- "Update the metadata for [listing name]"
- "Upload a new version of [listing name]"
- "Unpublish [listing name]"

**Sync**
- "What skills aren't published to Claw Mart yet?"
- "Are any of my Claw Mart listings out of date?"
- "Show sync status"

## Workflow

### Search
1. Call `GET /listings/search?q=[query]&limit=20`
2. Return: name, tagline, price, type, slug
3. Offer to download any result

### Download All
1. Call `GET /me` — validate auth
2. Call `GET /downloads` — list all owned packages (purchased + created)
3. For each: call `GET /downloads/{idOrSlug}` and save locally
4. If Skill Inspector is available: auto-scan each download and report verdict
5. Summary table: PASS / WARNING / BLOCKED per package

### Download One
1. Call `GET /downloads` — find by name or slug
2. Call `GET /downloads/{idOrSlug}` — fetch content
3. Save to local skills directory
4. Run Skill Inspector scan if available

### Create Listing
1. Confirm metadata with user: name, tagline, about, category, capabilities, price, product type
2. Show full payload before submitting — require explicit "yes" to proceed
3. Call `POST /listings`
4. Report listing ID and next steps

### Update Listing
1. Call `GET /listings` — show current state
2. Propose changes — require confirmation
3. Call `PATCH /listings/{id}`

### Upload Version
1. Show file list to user — require confirmation before upload
2. Call `POST /listings/{id}/versions` with package files
3. Report new version string and upload timestamp

### Sync Status
1. Read local skills directory
2. Call `GET /listings` for live state
3. Cross-reference by name — three buckets:
   - **Not published:** local skills with no live listing
   - **Stale:** local SKILL.md modified after last version upload
   - **Current:** in sync
4. Offer to push any stale or unpublished items

## API Reference

- **Base URL:** `https://www.shopclawmart.com/api/v1`
- **Auth:** `Authorization: Bearer ${CLAWMART_API_KEY}`

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/me` | Profile + subscription state |
| GET | `/listings` | Your creator listings |
| GET | `/listings/search` | Search catalog (`q`, `type`, `limit`) |
| POST | `/listings` | Create new listing |
| PATCH | `/listings/{id}` | Update listing metadata |
| DELETE | `/listings/{id}` | Unpublish listing |
| POST | `/listings/{id}/versions` | Upload package version |
| GET | `/downloads` | All packages you can download |
| GET | `/downloads/{idOrSlug}` | Fetch package content |

## Listing Payload Schema

```json
{
  "name": "string",
  "tagline": "string (≤ 120 chars)",
  "about": "string (markdown)",
  "category": "string",
  "capabilities": ["string"],
  "price": 0,
  "product_type": "skill | persona"
}
```

## Guardrails

- Never print or log the API key — redact in all output
- Never publish without explicit user confirmation ("yes", "publish it", "go ahead")
- Never package or upload: `SOUL.md`, `SAFETY_RAILS.md`, `CLAUDE.md`, `.env` files
- Always show the full file list before any version upload
- Return clear error messages with suggested fix when API calls fail
- Require `GET /me` validation before any write operation
