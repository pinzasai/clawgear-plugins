---
name: notion-content
description: Format and create content for Notion pages using Notion-flavored Markdown. Use whenever creating, updating, or writing any content that will be published to Notion — page bodies, PR docs, project plans, research docs, meeting notes, or any structured content. NOT for querying the API or automation logic.
---

# Notion Content Formatting

When writing content for Notion, always use Notion-flavored Markdown (NFM). See `references/notion-flavored-markdown.md` for the full spec.

## Core rules

- Use tabs for indentation (not spaces)
- Escape these characters outside code blocks: `\ * ~ \` $ [ ] < > { } | ^ `
- Never escape characters inside code blocks — write them literally
- Empty lines are stripped unless you use `<empty-block/>` on its own line
- Prefer structure over walls of text: use headings, callouts, toggles, tables

## When to use which block

| Content type | Block to use |
|---|---|
| Key info / warnings | `::: callout` with an emoji icon |
| Long lists of details | `<details>` toggle |
| Structured data | `<table>` with header-row |
| Code snippets | ` ```language ``` ` |
| Section breaks | `---` divider |
| Side-by-side layout | `<columns>` |

## Formatting for quality

Good Notion pages are **scannable**. Follow this structure:

1. **H1 title** — one clear title only
2. **Callout** — TL;DR or key context (optional but recommended)
3. **H2 sections** — major topics
4. **H3 subsections** — details within topics
5. **Bullets / numbered lists** — for items, steps, options
6. **Tables** — for comparisons, contacts, structured data
7. **Toggles** — for details that don't need to be visible by default

## Full spec

Read `references/notion-flavored-markdown.md` before writing complex content (tables, callouts, columns, equations, mentions, synced blocks).
