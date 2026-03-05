---
name: notion-workspace
description: Create, update, read, and manage Notion pages, databases, and blocks via the Notion API. Use when creating new pages, appending content to existing pages, querying databases, searching Notion, or sharing pages with collaborators. API key is stored at ~/.config/notion/api_key. NOT for formatting decisions — use the notion-content skill for Notion-flavored Markdown guidance.
---

# Notion Workspace

Interact with Notion via the REST API using curl or Python.

## Auth

API key location: `~/.config/notion/api_key`

```bash
# Load your Notion API key from wherever you store it
NOTION_KEY=your_notion_api_key_here
```

Standard headers:
```bash
-H "Authorization: Bearer $NOTION_KEY"
-H "Notion-Version: 2022-06-01"
-H "Content-Type: application/json"
```

## Common Operations

### Create a page
```bash
# Set NOTION_KEY from your stored credentials
curl -s -X POST https://api.notion.com/v1/pages \
  -H "Authorization: Bearer $NOTION_KEY" \
  -H "Notion-Version: 2022-06-01" \
  -H "Content-Type: application/json" \
  -d '{
    "parent": {"type": "page_id", "page_id": "PARENT_PAGE_ID"},
    "properties": {
      "title": {"title": [{"text": {"content": "Page Title"}}]}
    },
    "children": [
      {"object":"block","type":"paragraph","paragraph":{"rich_text":[{"text":{"content":"Body content here"}}]}}
    ]
  }' | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('url','ERROR:',d.get('message')))"
```

### Append blocks to existing page
```bash
curl -s -X PATCH "https://api.notion.com/v1/blocks/PAGE_ID/children" \
  -H "Authorization: Bearer $NOTION_KEY" \
  -H "Notion-Version: 2022-06-01" \
  -H "Content-Type: application/json" \
  -d '{"children": [{"object":"block","type":"paragraph","paragraph":{"rich_text":[{"text":{"content":"New content"}}]}}]}'
```

### Search pages
```bash
curl -s -X POST https://api.notion.com/v1/search \
  -H "Authorization: Bearer $NOTION_KEY" \
  -H "Notion-Version: 2022-06-01" \
  -H "Content-Type: application/json" \
  -d '{"query": "search term", "filter": {"value": "page", "property": "object"}}' \
  | python3 -c "import json,sys; [print(r['id'], r['url'], r['properties']['title']['title'][0]['plain_text'] if r['properties'].get('title',{}).get('title') else '?') for r in json.load(sys.stdin)['results']]"
```

### Get a page
```bash
curl -s "https://api.notion.com/v1/pages/PAGE_ID" \
  -H "Authorization: Bearer $NOTION_KEY" \
  -H "Notion-Version: 2022-06-01"
```

### Query a database
```bash
curl -s -X POST "https://api.notion.com/v1/databases/DB_ID/query" \
  -H "Authorization: Bearer $NOTION_KEY" \
  -H "Notion-Version: 2022-06-01" \
  -H "Content-Type: application/json" \
  -d '{"page_size": 20}'
```

### Share page with user (add collaborator)
```bash
# Notion sharing is done by inviting via email through the UI — API doesn't expose share invitations directly
# Instead, use page permissions endpoint to check/set access
curl -s "https://api.notion.com/v1/pages/PAGE_ID" \
  -H "Authorization: Bearer $NOTION_KEY" \
  -H "Notion-Version: 2022-06-01" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('url'))"
```

## Block Types Quick Reference

| Type | JSON structure |
|------|---------------|
| Paragraph | `{"type":"paragraph","paragraph":{"rich_text":[{"text":{"content":"..."}}]}}` |
| Heading 1 | `{"type":"heading_1","heading_1":{"rich_text":[{"text":{"content":"..."}}]}}` |
| Heading 2 | `{"type":"heading_2","heading_2":{"rich_text":[{"text":{"content":"..."}}]}}` |
| Bullet list | `{"type":"bulleted_list_item","bulleted_list_item":{"rich_text":[{"text":{"content":"..."}}]}}` |
| Numbered list | `{"type":"numbered_list_item","numbered_list_item":{"rich_text":[{"text":{"content":"..."}}]}}` |
| Code block | `{"type":"code","code":{"rich_text":[{"text":{"content":"..."}}],"language":"python"}}` |
| Divider | `{"type":"divider","divider":{}}` |
| To-do | `{"type":"to_do","to_do":{"rich_text":[{"text":{"content":"..."}}],"checked":false}}` |

## Page ID Format

Notion page IDs appear in URLs as: `notion.so/Page-Title-<32-char-id>`
Strip hyphens when using in API calls, or use the UUID format with hyphens — both work.

## Known Setup

- Integration name: "Pinzas"
- Account: pinzasrojas@proton.me
- Shared with: bayaslacker@gmail.com (Baira, Comfy project collaborator)
- Active pages: Comfy PR Research, Comfy Social Media Analysis

## Troubleshooting

- **401 Unauthorized**: Key expired or wrong — check `~/.config/notion/api_key`
- **404 on page**: Page not shared with the integration — open page in Notion → Connections → add Pinzas integration
- **Blocks not appearing**: Check block JSON structure matches types above exactly
