# FitFindr — Starter Kit

## Demo Video

[FitFinder Demo, Outfits From Your Wardrobe (Loom, with captions)](https://www.loom.com/share/9897ba829e814dbca3061a283c18cc0d)

## What's Included

```txt
ai201-project2-fitfindr-starter/
├── data/
│   ├── listings.json          # 40 mock secondhand listings
│   └── wardrobe_schema.json   # Wardrobe format + example wardrobe
├── utils/
│   └── data_loader.py         # Helper functions for loading the data
├── planning.md                # Your planning template — fill this out first
└── requirements.txt           # Python dependencies
```

## Setup

**macOS / Linux:**

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Windows:**

```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
```

Set your Groq API key in a `.env` file (get a free key at [console.groq.com](https://console.groq.com)):

```txt
GROQ_API_KEY=your_key_here
```

## The Mock Listings Dataset

`data/listings.json` contains 40 mock secondhand listings across categories (tops, bottoms, outerwear, shoes, accessories) and styles (vintage, y2k, grunge, cottagecore, streetwear, and more).

Each listing has: `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.

Load it with:

```python
from utils.data_loader import load_listings
listings = load_listings()
```

## The Wardrobe Schema

`data/wardrobe_schema.json` defines the format your agent uses to represent a user's existing wardrobe. It includes:

- `schema`: field definitions for a wardrobe item
- `example_wardrobe`: a sample wardrobe with 10 items you can use for testing
- `empty_wardrobe`: a starting template for a new user

Load an example wardrobe with:

```python
from utils.data_loader import get_example_wardrobe
wardrobe = get_example_wardrobe()
```

## Tool Inventory

### `search_listings(description: str, size: str | None = None, max_price: float | None = None) -> list[dict]`

Loads all listings via `load_listings()`, filters out anything over `max_price` or that doesn't match `size` (case-insensitive substring match, e.g. `"M"` matches `"S/M"`), scores the remainder by keyword overlap between `description` and each listing's title/description/category/style_tags/brand, drops zero-score listings, and returns the rest sorted by score descending. Returns `[]` if nothing matches — never raises.

### `suggest_outfit(new_item: dict, wardrobe: dict) -> str`

Takes the selected listing (`new_item`) and a wardrobe dict with an `items` list. If `wardrobe["items"]` is empty, prompts the LLM (Groq, `openai/gpt-oss-20b`, temperature 0.8) for general styling advice about the new item. If the wardrobe has items, prompts the LLM to combine the new item with specific named wardrobe pieces into 1-2 complete outfits. Always returns a non-empty string.

### `create_fit_card(outfit: str, new_item: dict) -> str`

Takes the outfit string from `suggest_outfit()` and the same `new_item` dict, and prompts the LLM (Groq, `openai/gpt-oss-20b`, temperature 1.0) for a casual 2-4 sentence social caption mentioning the item's name, price, and platform once each. If `outfit` is empty or whitespace-only, returns an error message string instead of calling the LLM or raising an exception.

---

## Interaction Walkthrough

<!-- Walk through a complete interaction step by step: natural language query → each tool call (and why) → final fit card.
     Walk through this carefully — it's how graders follow your agent's reasoning without a live demo.
     Use a specific example — do not leave this as a template. -->

**User query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?" (example wardrobe)

**Step 1 — Tool called:**

- Tool: `search_listings`
- Input: `description="I'm looking for a vintage graphic tee  I mostly wear baggy jeans and chunky sneakers What's out there and how would I style it"`, `size=None`, `max_price=30.0` (parsed from the query by `_parse_query()` in `agent.py`)
- Why this tool: it's the entry point — nothing else can run until we know which item the user is considering.
- Output: a list of matching listings; the top result is `Graphic Tee — 2003 Tour Bootleg Style` ($24, good condition, size L, Depop).

**Step 2 — Tool called:**

- Tool: `suggest_outfit`
- Input: `new_item=<Graphic Tee listing dict>`, `wardrobe=<example wardrobe, 10 items>`
- Why this tool: the wardrobe is non-empty, so the agent asks the LLM to combine the new tee with named wardrobe pieces rather than giving generic advice.
- Output: "Outfit 1 – Classic 'Grunge-Street' Look" — baggy dark-wash jeans, black denim jacket, and combat boots from the wardrobe, paired with the new tee.

**Step 3 — Tool called:**

- Tool: `create_fit_card`
- Input: `outfit=<outfit string from Step 2>`, `new_item=<same Graphic Tee listing dict>`
- Why this tool: `outfit` is non-empty, so the agent generates a shareable caption instead of returning an error.
- Output: "Grabbed this Graphic Tee – 2003 Tour Bootleg Style for just $24.0 on Depop and threw on baggy dark-wash jeans, a black denim jacket, and my favorite combat boots for a straight-up grunge-street vibe. Feeling the retro edge but keeping it effortless 😎 #thriftstorefinds"

**Final output to user:** The fit card above, along with the listing details and the full outfit suggestion, displayed in the three Gradio output panels.

---

## Error Handling and Fail Points

<!-- For each tool, describe the specific failure mode and what your agent does in response.
     This maps to the error handling section of the rubric (F5-C1). -->

| Tool | Failure mode | Agent response |
| ---- | ------------ | -------------- |
| `search_listings` | No listings match the parsed description/size/max_price | Returns `[]` (never raises); `run_agent()` sets `session["error"]` to a user-facing message and returns the session immediately, skipping `suggest_outfit` and `create_fit_card` entirely |
| `suggest_outfit` | `wardrobe["items"]` is empty (new user) | Skips the wardrobe-combination prompt and instead asks the LLM for general styling advice about the new item, so it still returns a useful non-empty string |
| `create_fit_card` | `outfit` is empty or whitespace-only | Returns an error message string (`"Error: cannot create a fit card without an outfit suggestion."`) without calling the LLM or raising an exception |

---

## Spec Reflection

<!-- Answer both questions with at least 2–3 sentences each. -->

**One way planning.md helped during implementation:**

Having the agent diagram and Planning Loop / State Management sections written out before touching `agent.py` made the branching logic unambiguous: the diagram explicitly showed that an empty `search_listings` result should return early rather than fall through to `suggest_outfit` with empty input. When I handed that diagram plus both spec sections to Claude, I could immediately check the generated code against a concrete visual — confirming it branched on results, wrote every intermediate value into the session dict, and didn't call all three tools unconditionally — instead of having to infer the intended control flow from scratch.

**One divergence from your spec, and why:**

The original tool docstrings called for the Groq model `meta-llama/llama-4-scout-17b-16e-instruct`, but that model returned a 404 ("does not exist or you do not have access to it") for my API key — `client.models.list()` confirmed it isn't in my account's available model list. I swapped both LLM calls in `tools.py` to `openai/gpt-oss-20b`, which is available on my key and produces comparable results (verified outfit/caption quality and output variance across repeated calls before moving on).

---

## AI Usage

**Instance 1 — Implementing the three tools in `tools.py`:**
I gave Claude the Tool 1/2/3 blocks from `planning.md` (inputs, return value, failure mode for each of `search_listings`, `suggest_outfit`, `create_fit_card`) and pointed it at `utils/data_loader.py` so it would reuse `load_listings()` instead of re-implementing file loading. It produced all three functions, including LLM calls to Groq's `meta-llama/llama-4-scout-17b-16e-instruct`. Before trusting the output, I ran it directly: `search_listings` worked as specified, but both LLM calls 404'd — that model isn't available on my Groq API key (confirmed via `client.models.list()`). I swapped the model string to `openai/gpt-oss-20b` in both places, then re-ran `create_fit_card` on the same input several times to confirm the captions actually varied instead of repeating — they did, at temperature 1.0.

**Instance 2 — Implementing the planning loop in `agent.py`:**
I gave Claude the full agent diagram and the Planning Loop + State Management sections of `planning.md`, and asked it to implement `run_agent()` to match. Before running the generated code, I checked it against the spec: does it branch on `search_listings` returning empty (return early with an error, skip the other two tools) rather than calling all three unconditionally? Does every intermediate value (`parsed`, `search_results`, `selected_item`, `outfit_suggestion`, `fit_card`) get written into the session dict rather than passed as loose variables? It matched on both counts, so I ran the exact walkthrough query from `planning.md` and verified `session["search_results"][0] is session["selected_item"]` — confirming state was flowing through the same dict rather than being re-fetched or hardcoded between steps.

---

## Where to Start

1. **Read `planning.md` and fill it out before writing any code.**
2. Verify the data loads correctly by running `python utils/data_loader.py`.
3. Build and test each tool individually before connecting them through your planning loop.

Your implementation files go in this same directory. There's no required file structure for your agent code — organize it however makes sense for your design.
