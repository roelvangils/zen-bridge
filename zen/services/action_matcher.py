"""
Action matching service for finding elements without AI.

This module provides multiple strategies for matching user actions to page elements:
1. Literal text matching
2. Common actions dictionary
3. URL pattern matching
4. Fuzzy text matching
5. Synonym matching
"""

from __future__ import annotations

from typing import Any


class ActionMatcher:
    """Intelligent action matcher that finds elements without AI."""

    # Common action patterns
    COMMON_ACTIONS = {
        "home": {
            "href_patterns": ["/", "/home", "/index", "/homepage"],
            "texts": ["home", "homepage", "main page"],
        },
        "login": {
            "href_patterns": ["/login", "/signin", "/sign-in", "/auth"],
            "texts": ["login", "sign in", "signin", "log in"],
        },
        "logout": {
            "href_patterns": ["/logout", "/signout", "/sign-out"],
            "texts": ["logout", "sign out", "signout", "log out"],
        },
        "signup": {
            "href_patterns": ["/signup", "/register", "/join"],
            "texts": ["sign up", "signup", "register", "join", "create account"],
        },
        "search": {
            "types": ["search", "input-search"],
            "texts": ["search", "find"],
            "aria_labels": ["search"],
        },
        "contact": {
            "href_patterns": ["/contact", "/support", "/help"],
            "texts": ["contact", "contact us", "get in touch", "support"],
        },
        "about": {
            "href_patterns": ["/about", "/about-us"],
            "texts": ["about", "about us", "who we are"],
        },
        "products": {
            "href_patterns": ["/products", "/shop", "/store", "/catalog"],
            "texts": ["products", "shop", "store", "catalog"],
        },
        "pricing": {
            "href_patterns": ["/pricing", "/plans", "/pricing-plans"],
            "texts": ["pricing", "plans", "pricing plans", "cost"],
        },
        "blog": {
            "href_patterns": ["/blog", "/news", "/articles"],
            "texts": ["blog", "news", "articles", "posts"],
        },
        "cart": {
            "href_patterns": ["/cart", "/basket", "/shopping-cart"],
            "texts": ["cart", "basket", "shopping cart", "bag"],
        },
        "checkout": {
            "href_patterns": ["/checkout", "/cart/checkout"],
            "texts": ["checkout", "proceed to checkout", "complete order"],
        },
        "settings": {
            "href_patterns": ["/settings", "/preferences", "/account/settings"],
            "texts": ["settings", "preferences", "configuration"],
        },
        "profile": {
            "href_patterns": ["/profile", "/account", "/user", "/me"],
            "texts": ["profile", "account", "my account", "user profile"],
        },
        "help": {
            "href_patterns": ["/help", "/support", "/faq"],
            "texts": ["help", "support", "faq", "faqs"],
        },
    }

    # Synonyms for better matching
    SYNONYMS = {
        "home": ["homepage", "main", "index", "start"],
        "login": ["signin", "sign in", "log in", "authenticate"],
        "logout": ["signout", "sign out", "log out"],
        "search": ["find", "lookup", "query"],
        "contact": ["reach us", "get in touch", "support"],
        "products": ["catalog", "shop", "store", "items"],
        "about": ["about us", "who we are", "our story"],
        "pricing": ["price", "cost", "plans"],
        "cart": ["basket", "bag", "shopping cart"],
        "settings": ["preferences", "config", "configuration", "options"],
        "profile": ["account", "user", "me"],
    }

    def __init__(self, config: dict[str, Any] | None = None):
        """Initialize action matcher with configuration."""
        self.config = config or {}

    def find_literal_match(
        self, action_normalized: str, actionable_elements: list[dict]
    ) -> dict | None:
        """
        Find element whose text literally matches the action.

        Returns best match with score, or None if no good match found.
        """
        action_words = set(action_normalized.split())

        if not action_words:
            return None

        matches = []

        for element in actionable_elements:
            # Normalize element text
            element_text = self._normalize_text(element.get("text", ""))
            element_words = set(element_text.split())

            if not element_words:
                continue

            # Calculate word overlap
            overlap = action_words & element_words
            overlap_ratio = len(overlap) / len(action_words) if action_words else 0

            # Also check href for links
            href_score = 0
            if element.get("href"):
                href_normalized = self._normalize_text(element["href"])
                href_words = set(href_normalized.split("/"))
                href_overlap = action_words & href_words
                href_score = len(href_overlap) / len(action_words) if action_words else 0

            # Take best score
            score = max(overlap_ratio, href_score)

            if score > 0:
                matches.append({"element": element, "score": score, "matched_words": overlap})

        # Sort by score
        matches.sort(key=lambda x: x["score"], reverse=True)

        threshold = self.config.get("literal_match_threshold", 0.8)

        # Return best match if it meets threshold
        if matches and matches[0]["score"] >= threshold:
            return matches[0]

        return None

    def find_common_action_match(
        self, action_normalized: str, actionable_elements: list[dict]
    ) -> dict | None:
        """
        Find element using common action patterns.

        Checks if action matches a known pattern (like "login", "home", etc.)
        and looks for elements matching those patterns.
        """
        # Check if action matches a common pattern
        for pattern_name, patterns in self.COMMON_ACTIONS.items():
            if pattern_name in action_normalized or action_normalized in pattern_name:
                # Found a common pattern, look for matching elements
                return self._find_by_pattern(patterns, actionable_elements)

        return None

    def _find_by_pattern(self, patterns: dict, actionable_elements: list[dict]) -> dict | None:
        """Find element matching a common action pattern."""
        matches = []

        for element in actionable_elements:
            score = 0

            # Check href patterns
            if "href_patterns" in patterns and element.get("href"):
                href = element["href"].lower()
                for pattern in patterns["href_patterns"]:
                    if pattern in href:
                        score = 1.0
                        break

            # Check text patterns
            if "texts" in patterns:
                element_text = self._normalize_text(element.get("text", ""))
                for text_pattern in patterns["texts"]:
                    if text_pattern in element_text or element_text in text_pattern:
                        score = max(score, 0.9)

            # Check types
            if "types" in patterns and element.get("type"):
                if element["type"] in patterns["types"]:
                    score = max(score, 0.9)

            # Check aria labels
            if "aria_labels" in patterns and element.get("ariaLabel"):
                aria = self._normalize_text(element["ariaLabel"])
                for aria_pattern in patterns["aria_labels"]:
                    if aria_pattern in aria:
                        score = max(score, 0.9)

            if score > 0:
                matches.append({"element": element, "score": score})

        # Sort by score and return best
        matches.sort(key=lambda x: x["score"], reverse=True)
        if matches:
            return matches[0]

        return None

    def find_fuzzy_match(
        self, action_normalized: str, actionable_elements: list[dict]
    ) -> dict | None:
        """
        Find element using fuzzy text matching.

        Handles typos and slight variations in text.
        """
        if not self.config.get("use_fuzzy_matching", True):
            return None

        max_distance = self.config.get("max_fuzzy_distance", 2)

        matches = []

        for element in actionable_elements:
            element_text = self._normalize_text(element.get("text", ""))

            # Calculate Levenshtein distance
            distance = self._levenshtein_distance(action_normalized, element_text)

            # If distance is small relative to text length, it's a match
            if distance <= max_distance:
                score = 1.0 - (distance / max(len(action_normalized), 1))
                matches.append({"element": element, "score": score})

        matches.sort(key=lambda x: x["score"], reverse=True)

        threshold = 0.8

        if matches and matches[0]["score"] >= threshold:
            return matches[0]

        return None

    def find_synonym_match(
        self, action_normalized: str, actionable_elements: list[dict]
    ) -> dict | None:
        """
        Find element using synonym expansion.

        Expands action with synonyms and searches for matches.
        """
        # Find synonyms for action words
        action_words = action_normalized.split()
        expanded_words = set(action_words)

        for word in action_words:
            if word in self.SYNONYMS:
                expanded_words.update(self.SYNONYMS[word])

        # Now search with expanded words
        matches = []

        for element in actionable_elements:
            element_text = self._normalize_text(element.get("text", ""))
            element_words = set(element_text.split())

            # Check overlap with expanded words
            overlap = expanded_words & element_words
            if overlap:
                score = len(overlap) / len(action_words) if action_words else 0
                matches.append({"element": element, "score": score})

        matches.sort(key=lambda x: x["score"], reverse=True)

        threshold = 0.8

        if matches and matches[0]["score"] >= threshold:
            return matches[0]

        return None

    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison (lowercase, remove special chars)."""
        import string

        text = text.lower()
        text = text.translate(str.maketrans("", "", string.punctuation))
        return " ".join(text.split())  # Normalize whitespace

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings."""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                # Cost of insertions, deletions, or substitutions
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]
