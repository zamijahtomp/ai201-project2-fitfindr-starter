# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**
Search the mock listings dataset for items matching the description, optional size, and optional price ceiling.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `description` (str): Keywords describing what the user is looking for (e.g., "vintage graphic tee").
- `size` (str): Size string to filter by, or None to skip size filtering. Matching is case-insensitive (e.g., "M" matches "S/M").
- `max_price` (float): Maximum price (inclusive), or None to skip price filtering.

**What it returns:**
A list of matching listing dicts, sorted by relevance (best match first).

**What happens if it fails or returns nothing:**
Returns an empty list if nothing matches — does NOT raise an exception.

---

### Tool 2: suggest_outfit

**What it does:**
Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

**Input parameters:**

- `new_item` (dict): A listing dict (the item the user is considering buying).
- `wardrobe` (dict): A wardrobe dict with an 'items' key containing a list of wardrobe item dicts. May be empty — handle this gracefully.

**What it returns:**
A non-empty string with outfit suggestions.

**What happens if it fails or returns nothing:**
If the wardrobe is empty, offer general styling advice for the item rather than raising an exception or returning an empty string.

---

### Tool 3: create_fit_card

**What it does:**
Generate a short, shareable outfit caption for the thrifted find.

**Input parameters:**

- `outfit` (str): The outfit suggestion string from suggest_outfit().
- `new_item` (dict): The listing dict for the thrifted item.

**What it returns:**
A 2-4 sentence string usable as an Instagram/TikTok caption.

**What happens if it fails or returns nothing:**
If outfit is empty or missing, return a descriptive error message string — do NOT raise an exception.

---

### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->

---

## Planning Loop

**How does your agent decide which tool to call next?**
Get a description, size, and max price from the user, and use search_listings() to find an outfit that matches. Store results if successful, or return a helpful error message to the user and end the session early. Select and store the top result and along with the wardrobe, create a suggested outfit. Create a fit card with the outfit suggestion and top result and return the session.

---

## State Management

**How does information from one tool get passed to the next?**
All state lives in a single session dict created at the start of the run (`_new_session`). Each planning loop step reads what it needs from the session and writes its result back into the session before moving to the next step, so no data is passed directly between tool calls — it always flows through the dict:

- `parsed` (description/size/max_price) is read by `search_listings`.
- `search_results` and `selected_item` (top result) are read by `suggest_outfit`.
- `outfit_suggestion` and `selected_item` are read by `create_fit_card`.
- `error` is checked after `search_listings` — if set, the loop returns the session immediately and skips `suggest_outfit`/`create_fit_card`.

---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
| ---- | ------------ | -------------- |
| search_listings | No results match the query | "No clothing items matching user's decription were found, ending session." |
| suggest_outfit | Wardrobe is empty | "User's wardrobe is currently empty, offering general advice instead." |
| create_fit_card | Outfit input is missing or incomplete | "Missing or incomplete outfit suggestion, suggesting a new outfit." |

---

## Architecture

<!-- Draw a diagram of your agent showing how the components connect:
     User input → Planning Loop → Tools (search_listings, suggest_outfit, create_fit_card)
                                                                          ↕
                                                                   State / Session
     Show what triggers each tool, how state flows between them, and where error paths branch off.
     Use ASCII art or a Mermaid diagram (https://mermaid.js.org/syntax/flowchart.html).
     Do NOT embed an image — graders need to read your diagram directly in the file;
     an embedded image or screenshot cannot be evaluated.
     You'll share this diagram with an AI tool when asking it to implement
     the planning loop and each individual tool. -->
```txt
User query
    │
    ▼
Planning Loop ───────────────────────────────────────────┐
    │                                                    │
    ├─► search_listings(description, size, max_price)    │
    │       │ results=[]                                 │
    │       ├──► [ERROR] "No listings found..." → return │
    │       │                                            │
    │       │ results=[item, ...]                        │
    │       ▼                                            │
    │   Session: selected_item = results[0]              │
    │       │                                            │
    ├─► suggest_outfit(selected_item, wardrobe)          │
    │       │                                            │
    │   Session: outfit_suggestion = "..."               │
    │       │                                            │
    └─► create_fit_card(outfit_suggestion, selected_item)│
            │                                            │
        Session: fit_card = "..."                        │
            │                                            └─ error path returns here
            ▼
        Return session
```

---

## AI Tool Plan

<!-- For each part of the implementation below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, your agent diagram)
     - What you expect it to produce
     - How you'll verify the output matches your spec before moving on

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Tool 1 spec (inputs, return value, failure mode) and ask it to implement
     search_listings() using load_listings() from the data loader — then test it against 3 queries
     before trusting it" is a plan. -->

**Milestone 3 — Individual tool implementations:**
For each of the tools, I'll give Claude their respective *Tool #* blocks from planning.md (inputs, return value, failure mode). For search_listings(), I'll ask it to implement the function using load_listings() from the data loader. Before running it, I'll check that the generated code filters by all three parameters and handles the empty-results case. Then I'll test it with 3 queries.

**Milestone 4 — Planning loop and state management:**
I plan to use Claude for both the planning loop and state management, giving the agent their respective documentation from planning.md. I expect the app to run as described in *Planning Loop*.

---

## A Complete Interaction (Step by Step)

FitFindr is a catalog of clothing in which the user can report a style they're looking for and get recommandations based on what is in the catalog.
Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**
Call search_listings() with the parameters wintage graphic tee, baggy, $30

**Step 2:**
Search_listings() returns a list of items closely matching the description, e.g. *[Graphic Tee — 2003 Tour Bootleg Style, Vintage Levi's 501 Jeans — Medium Wash,...]*. Use the top item, aka the closest, and the user's wardrobe, as parameters for suggest_outfit(). Return an outfit suggestion. In this case, the top item should be *Graphic Tee — 2003 Tour Bootleg Style*, with the outfit_suggestion being *Graphic Tee — 2003 Tour Bootleg Style, Baggy straight-leg jeans, dark wash, Chunky white sneakers*, with the last two items being from the user's wardrobe.

**Final output to user:**
Using the outfit_suggestion and top item, create a fit card for the user and return a 2-4 sentence string usable as an Instagram/TikTok caption.
