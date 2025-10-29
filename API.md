# API Reference

Complete API documentation for the VALUES.md Dilemmas API.

---

## Base URL

```
Production: https://values-md-dilemmas.fly.dev
Local:      http://localhost:8080
```

---

## Authentication

Protected endpoints require an API key in the request header:

```bash
X-API-Key: your-api-key-here
```

Get your API key from the project administrator.

---

## Public Endpoints

### GET /

**Dilemma browser (HTML)**

View all dilemmas in a web interface.

```bash
curl https://values-md-dilemmas.fly.dev/
```

### GET /research

**Research experiments index (HTML)**

Browse all research experiments and findings.

```bash
curl https://values-md-dilemmas.fly.dev/research
```

### GET /research/{experiment_slug}

**Single experiment findings (HTML)**

View detailed findings for a specific experiment.

**Parameters:**
- `experiment_slug` (path) - Experiment folder name (e.g., "2025-10-24-bias-under-pressure")

**Example:**
```bash
curl https://values-md-dilemmas.fly.dev/research/2025-10-24-bias-under-pressure
```

---

## Protected Endpoints

All protected endpoints require authentication via `X-API-Key` header.

### POST /api/generate

**Generate a new dilemma**

Creates a new ethical dilemma using LLM generation and saves it to the database.

**Headers:**
- `X-API-Key: your-api-key` (required)
- `Content-Type: application/json`

**Request Body:**
```json
{
  "difficulty": 7,
  "prompt_version": "v8_concise",
  "add_variables": true,
  "num_actors": 2,
  "num_stakes": 2
}
```

**Parameters:**
- `difficulty` (required) - Integer 1-10, target difficulty level
- `prompt_version` (optional) - Prompt version to use ("v2_structured", "v8_concise", etc.)
- `add_variables` (optional) - Boolean, extract variables for bias testing
- `num_actors` (optional) - Integer 1-5, number of actors to include
- `num_stakes` (optional) - Integer 1-5, number of stakes to include

**Response:** Full `Dilemma` object (JSON)

**Example:**
```bash
curl -X POST https://values-md-dilemmas.fly.dev/api/generate \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "difficulty": 7,
    "prompt_version": "v8_concise",
    "add_variables": true
  }'
```

**Rate Limit:** Approximately 1 request per minute (generation takes ~10-30 seconds)

---

### GET /api/dilemmas

**List and search dilemmas**

Retrieve dilemmas with filtering, searching, and pagination.

**Headers:**
- `X-API-Key: your-api-key` (required)

**Query Parameters:**
- `limit` (optional) - Integer 1-500, default 50. Number of results to return
- `offset` (optional) - Integer ≥0, default 0. Pagination offset
- `difficulty_min` (optional) - Integer 1-10. Minimum difficulty filter
- `difficulty_max` (optional) - Integer 1-10. Maximum difficulty filter
- `tags` (optional) - String, comma-separated tags (e.g., "privacy,autonomy")
- `created_by` (optional) - String, filter by creator (e.g., "human", "gpt-4")
- `search` (optional) - String, search in title and situation text
- `sort` (optional) - String, default "created_at". Field to sort by
- `order` (optional) - String, default "desc". Sort order ("asc" or "desc")

**Response:**
```json
{
  "items": [Dilemma, ...],
  "total": 142,
  "limit": 50,
  "offset": 0
}
```

**Examples:**

```bash
# Get first 10 dilemmas
curl "https://values-md-dilemmas.fly.dev/api/dilemmas?limit=10" \
  -H "X-API-Key: your-api-key"

# Get difficult dilemmas (7+)
curl "https://values-md-dilemmas.fly.dev/api/dilemmas?difficulty_min=7" \
  -H "X-API-Key: your-api-key"

# Search for privacy dilemmas
curl "https://values-md-dilemmas.fly.dev/api/dilemmas?search=privacy&tags=privacy" \
  -H "X-API-Key: your-api-key"

# Pagination: get next page
curl "https://values-md-dilemmas.fly.dev/api/dilemmas?limit=50&offset=50" \
  -H "X-API-Key: your-api-key"
```

---

### GET /api/dilemma/{id}

**Get single dilemma (JSON)**

Retrieve a specific dilemma by ID.

**Headers:**
- `X-API-Key: your-api-key` (required)

**Parameters:**
- `id` (path) - Dilemma UUID

**Response:** Full `Dilemma` object (JSON)

**Example:**
```bash
curl "https://values-md-dilemmas.fly.dev/api/dilemma/99d8e75a-db9c-4367-b8ee-0519a3fdb8e3" \
  -H "X-API-Key: your-api-key"
```

---

### GET /api/stats

**Database statistics**

Get overview statistics about the database contents.

**Headers:**
- `X-API-Key: your-api-key` (required)

**Response:**
```json
{
  "dilemmas_count": 142,
  "judgements_count": 1250,
  "experiments_count": 6,
  "models_tested": [
    "anthropic/claude-sonnet-4.5",
    "google/gemini-2.5-pro",
    "openai/gpt-4.1"
  ],
  "difficulty_distribution": {
    "5": 12,
    "6": 28,
    "7": 45,
    "8": 38,
    "9": 15,
    "10": 4
  }
}
```

**Example:**
```bash
curl "https://values-md-dilemmas.fly.dev/api/stats" \
  -H "X-API-Key: your-api-key"
```

---

## Data Models

### Dilemma

```typescript
{
  id: string;                           // UUID
  version: number;                      // Version number
  parent_id: string | null;             // Parent dilemma if variation

  // Content
  title: string;                        // Short title
  situation_template: string;           // Situation description (may contain {PLACEHOLDERS})
  question: string;                     // The ethical question
  choices: DilemmaChoice[];             // Available choices

  // Variations
  variables: Record<string, string[]>;  // Variable substitutions
  modifiers: string[];                  // Scenario modifiers

  // Taxonomy
  tags: string[];                       // Categorization tags
  institution_type: string | null;      // Institution context

  // Mode contexts
  theory_context: string | null;        // Theory mode context
  action_context: string;               // Action mode context (AI role)

  // Action mode tools
  available_tools: ToolSchema[];        // Tools available in action mode

  // Metadata
  difficulty_intended: number;          // 1-10
  created_at: string;                   // ISO timestamp
  created_by: string;                   // Creator ID
  source: string | null;                // Source of dilemma
  notes: string | null;                 // Additional notes

  // Generation metadata
  is_llm_generated: boolean;
  generator_model: string | null;
  generator_prompt_version: string | null;
  seed_components: object | null;
  generator_settings: object | null;
}
```

### DilemmaChoice

```typescript
{
  id: string;              // Choice identifier
  label: string;           // Short label
  description: string;     // Full description
  tool_name: string | null; // Tool to call in action mode
}
```

### ToolSchema

```typescript
{
  name: string;            // Tool function name
  description: string;     // What the tool does
  parameters: object;      // JSON Schema parameters
}
```

---

## Error Responses

### 401 Unauthorized

API key missing or invalid.

```json
{
  "detail": "Invalid API key"
}
```

### 404 Not Found

Resource not found.

```json
{
  "detail": "Dilemma not found"
}
```

### 500 Internal Server Error

Server error (e.g., generation failed).

```json
{
  "detail": "Generation failed: [error message]"
}
```

---

## Rate Limits

- **GET requests:** No strict limit (reasonable use expected)
- **POST /api/generate:** ~1 request per minute (generation takes time)

Excessive usage may result in rate limiting or API key suspension.

---

## Best Practices

1. **Cache results** - Don't repeatedly fetch the same data
2. **Use pagination** - Request smaller batches instead of all at once
3. **Filter server-side** - Use query parameters instead of filtering client-side
4. **Handle errors** - Always check response status and handle 4xx/5xx errors
5. **Respect rate limits** - Wait for generation to complete before next request

---

## Examples

### Python

```python
import httpx

API_KEY = "your-api-key"
BASE_URL = "https://values-md-dilemmas.fly.dev"

headers = {"X-API-Key": API_KEY}

# List dilemmas
response = httpx.get(
    f"{BASE_URL}/api/dilemmas",
    headers=headers,
    params={"limit": 10, "difficulty_min": 7}
)
dilemmas = response.json()

# Generate dilemma
response = httpx.post(
    f"{BASE_URL}/api/generate",
    headers={**headers, "Content-Type": "application/json"},
    json={
        "difficulty": 7,
        "prompt_version": "v8_concise"
    }
)
new_dilemma = response.json()
```

### JavaScript

```javascript
const API_KEY = "your-api-key";
const BASE_URL = "https://values-md-dilemmas.fly.dev";

// List dilemmas
const response = await fetch(`${BASE_URL}/api/dilemmas?limit=10`, {
  headers: { "X-API-Key": API_KEY }
});
const data = await response.json();
console.log(`Found ${data.total} dilemmas`);

// Generate dilemma
const genResponse = await fetch(`${BASE_URL}/api/generate`, {
  method: "POST",
  headers: {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    difficulty: 7,
    prompt_version: "v8_concise"
  })
});
const newDilemma = await genResponse.json();
```

---

## Support

For API issues or questions:
- Check logs: `flyctl logs`
- File issue: [GitHub Issues](https://github.com/your-repo/issues)
- Email: your-email@example.com
