"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    Before writing code, fill in the Tool 1 section of planning.md.
    """
    listings = load_listings()

    keywords = [kw for kw in description.lower().split() if kw]

    candidates = []
    for listing in listings:
        if max_price is not None and listing["price"] > max_price:
            continue
        if size is not None and size.strip().lower() not in listing["size"].lower():
            continue
        candidates.append(listing)

    scored = []
    for listing in candidates:
        haystack = " ".join(
            [
                listing.get("title", ""),
                listing.get("description", ""),
                listing.get("category", ""),
                " ".join(listing.get("style_tags", [])),
                listing.get("brand") or "",
            ]
        ).lower()
        score = sum(haystack.count(kw) for kw in keywords)
        if score > 0:
            scored.append((score, listing))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [listing for _, listing in scored]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1-2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.

    Before writing code, fill in the Tool 2 section of planning.md.
    """
    client = _get_groq_client()

    item_desc = (
        f"{new_item.get('title', 'this item')} "
        f"({', '.join(new_item.get('style_tags', []))}), "
        f"colors: {', '.join(new_item.get('colors', []))}, "
        f"category: {new_item.get('category', 'unknown')}"
    )

    items = wardrobe.get("items", [])

    if not items:
        prompt = (
            f"A user is considering buying this thrifted item: {item_desc}.\n\n"
            "They don't have any wardrobe items logged yet. Give general "
            "styling advice for this piece: what kinds of items would pair "
            "well with it, what vibe/aesthetic it suits, and a couple of "
            "outfit ideas using items they'd likely already own. Keep it to "
            "2-4 sentences."
        )
    else:
        wardrobe_desc = "\n".join(
            f"- {w.get('name', 'item')} ({w.get('category', 'unknown')}, "
            f"{', '.join(w.get('style_tags', []))})"
            for w in items
        )
        prompt = (
            f"A user is considering buying this thrifted item: {item_desc}.\n\n"
            f"Their existing wardrobe includes:\n{wardrobe_desc}\n\n"
            "Suggest 1-2 complete outfits that combine the new item with "
            "specific named pieces from their wardrobe. Be concrete about "
            "what goes with what and why it works."
        )

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
    )
    return response.choices[0].message.content


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2-4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    Before writing code, fill in the Tool 3 section of planning.md.
    """
    if not outfit or not outfit.strip():
        return "Error: cannot create a fit card without an outfit suggestion."

    client = _get_groq_client()

    title = new_item.get("title", "this piece")
    price = new_item.get("price", "?")
    platform = new_item.get("platform", "a resale app")

    prompt = (
        f"Write a short, casual OOTD-style social media caption (2-4 sentences, "
        f"for Instagram/TikTok) for a thrifted outfit post.\n\n"
        f"The thrifted item: {title}, ${price}, found on {platform}.\n"
        f"The full outfit: {outfit}\n\n"
        "Mention the item name, price, and platform naturally, each once. "
        "Capture the specific vibe of the outfit. Sound like a real person "
        "posting, not an ad or product description. Feel free to use casual "
        "language, maybe an emoji or two, but don't overdo it."
    )

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": prompt}],
        temperature=1.0,
    )
    return response.choices[0].message.content
