
import re
from dataclasses import dataclass
from typing import Optional


# ============================================================
# COMMON SPELLING CORRECTIONS
# Food information is retrieved dynamically from USDA.
# ============================================================

COMMON_CORRECTIONS = {
    "bananna": "banana",
    "banan": "banana",
    "brocolli": "broccoli",
    "brocoli": "broccoli",
    "chiken": "chicken",
    "chikn": "chicken",
    "chickn": "chicken",
    "chickwn": "chicken",
    "tomatos": "tomato",
    "potatos": "potato",
    "spinich": "spinach",
    "carot": "carrot",
    "aple": "apple",
    "apl": "apple",
    "oragne": "orange",
    "strawbery": "strawberry",
    "avacado": "avocado",
}


NUMBER_WORDS = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
}


GRAM_UNITS = {"g", "gram", "grams", "gm", "gms"}
KILOGRAM_UNITS = {"kg", "kilogram", "kilograms", "kilo", "kilos"}
MILLIGRAM_UNITS = {"mg", "milligram", "milligrams"}
PIECE_UNITS = {"piece", "pieces", "pc", "pcs", "item", "items"}

ALL_UNITS = GRAM_UNITS | KILOGRAM_UNITS | MILLIGRAM_UNITS | PIECE_UNITS


@dataclass
class ParsedQuery:
    """Structured representation of a user's food query."""

    original_text: str
    food: Optional[str]
    quantity: Optional[float]
    unit: Optional[str]
    intent: str


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_text(text: str) -> str:
    """Normalize user input while preserving decimal quantities."""

    if not isinstance(text, str):
        return ""

    text = text.lower().strip()
    text = text.replace("’", "'")
    text = re.sub(r"[^a-z0-9.\s]", " ", text)
    text = re.sub(r"(?<!\d)\.(?!\d)", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def correct_word(word: str) -> str:
    """Correct a known spelling mistake."""

    return COMMON_CORRECTIONS.get(word, word)


def correct_spelling(text: str) -> str:
    """Correct known spelling mistakes word by word."""

    return " ".join(correct_word(word) for word in text.split())


def parse_number(value: str) -> Optional[float]:
    """Convert a number or number word to float."""

    value = value.strip().lower()

    if value in NUMBER_WORDS:
        return float(NUMBER_WORDS[value])

    try:
        return float(value)
    except ValueError:
        return None


def normalize_unit(unit: str) -> str:
    """Normalize supported quantity units."""

    unit = unit.lower().strip()

    if unit in GRAM_UNITS:
        return "g"
    if unit in KILOGRAM_UNITS:
        return "kg"
    if unit in MILLIGRAM_UNITS:
        return "mg"
    if unit in PIECE_UNITS:
        return "piece"

    return unit


# ============================================================
# QUANTITY EXTRACTION
# ============================================================

def extract_quantity(text: str):
    """
    Return (quantity, unit, remaining_text).

    Supports:
      200g banana
      200 grams of mango
      2 kg rice
      2 apples
      two bananas
      2 bananas in a nutrition question
      I ate 150 grams of apple
    """

    text = text.strip()

    unit_pattern = "|".join(
        re.escape(unit)
        for unit in sorted(ALL_UNITS, key=len, reverse=True)
    )

    number_word_pattern = "|".join(
        re.escape(word)
        for word in sorted(NUMBER_WORDS, key=len, reverse=True)
    )

    # 200g banana, 150 grams of apple, 2 kg rice.
    match = re.search(
        rf"\b(\d+(?:\.\d+)?)\s*({unit_pattern})\b",
        text,
    )

    if match:
        quantity = float(match.group(1))
        unit = normalize_unit(match.group(2))
        remaining = (
            text[:match.start()] + " " + text[match.end():]
        ).strip()

        return quantity, unit, re.sub(r"\s+", " ", remaining)

    # One hundred grams is intentionally not interpreted here;
    # this supports number words followed by a known unit.
    match = re.search(
        rf"\b({number_word_pattern})\s+({unit_pattern})\b",
        text,
    )

    if match:
        quantity = parse_number(match.group(1))
        unit = normalize_unit(match.group(2))
        remaining = (
            text[:match.start()] + " " + text[match.end():]
        ).strip()

        return quantity, unit, re.sub(r"\s+", " ", remaining)

    # Counted food quantities, e.g. "2 bananas" or "two boiled eggs".
    match = re.search(
        rf"\b(\d+(?:\.\d+)?|{number_word_pattern})\s+"
        r"(?=[a-z])",
        text,
    )

    if match:
        prefix = text[:match.start()].strip()

        # The quantity can appear after a natural-language question
        # prefix, not only at the start of the input.
        allowed_prefixes = {
            "",
            "i ate",
            "i had",
            "i have",
            "i just ate",
            "i consumed",
            "i have eaten",
            "tell me the nutrition facts for",
            "tell me nutrition facts for",
            "nutrition facts for",
            "nutrition information for",
            "what are the nutrition facts for",
            "what are the nutrition facts of",
            "what is the nutrition information for",
            "give me the nutrition information for",
            "give me the nutrition facts for",
            "tell me the nutrition information for",
        }

        if prefix in allowed_prefixes:
            quantity = parse_number(match.group(1))

            if quantity is not None:
                remaining = (
                    text[:match.start()] + " " + text[match.end():]
                ).strip()

                return (
                    quantity,
                    "piece",
                    re.sub(r"\s+", " ", remaining),
                )

    return None, None, text


# ============================================================
# FOOD PHRASE CLEANING
# ============================================================

def clean_food_phrase(text: str) -> str:
    """Remove question wording and retain the food description."""

    text = text.strip().lower()

    removable_phrases = [
        r"\bcan you tell me\b",
        r"\bcould you tell me\b",
        r"\bplease tell me\b",
        r"\bi want to know\b",
        r"\bi would like to know\b",
        r"\btell me\b",
        r"\bshow me\b",
        r"\bgive me\b",
        r"\bwhat are the nutrition facts of\b",
        r"\bwhat are the nutrition facts for\b",
        r"\bwhat are the nutrients in\b",
        r"\bwhat nutrients does\b",
        r"\bwhat nutrients do\b",
        r"\bwhat nutrients are\b",
        r"\bwhat nutrients\b",
        r"\bwhat are the calories in\b",
        r"\bwhat is the nutrition in\b",
        r"\bwhat is the nutritional value of\b",
        r"\bwhat is the nutritional content of\b",
        r"\bwhat is the nutrition information for\b",
        r"\bwhat is the nutrition information of\b",
        r"\bwhat is\b",
        r"\bwhat are\b",
        r"\bwhat's\b",
        r"\bhow much\b",
        r"\bhow many\b",
        r"\bhow nutritious is\b",
        r"\bnutritional value of\b",
        r"\bnutritional content of\b",
        r"\bnutritional information for\b",
        r"\bnutritional information of\b",
        r"\bnutrition information for\b",
        r"\bnutrition information of\b",
        r"\bnutrition facts for\b",
        r"\bnutrition facts of\b",
        r"\bnutrition in\b",
        r"\bnutrition for\b",
        r"\bnutrition of\b",
        r"\bprotein content of\b",
        r"\bprotein is in\b",
        r"\bprotein in\b",
        r"\bcalorie content of\b",
        r"\bcalories are in\b",
        r"\bcalories in\b",
        r"\bcarbohydrates are in\b",
        r"\bcarbohydrates in\b",
        r"\bcarbs in\b",
        r"\bfat is in\b",
        r"\bfat in\b",
        r"\bfiber in\b",
        r"\bfibre in\b",
        r"\bcalculate the nutrients for\b",
        r"\bcalculate the nutrients\b",
        r"\bcalculate\b",
        r"\bi have eaten\b",
        r"\bi just ate\b",
        r"\bi ate\b",
        r"\bi eat\b",
        r"\bi had\b",
        r"\bi have\b",
        r"\bi consumed\b",
        r"\bi get from eating\b",
        r"\bfrom eating\b",
        r"\bdid i consume\b",
        r"\bdid i eat\b",
        r"\bwhat did i get\b",
        r"\bhow many calories did i consume\b",
        r"\bhow many calories did i eat\b",
        r"\bhow much protein does it contain\b",
        r"\bwhat nutrients did i get\b",
        r"\bdoes it contain\b",
        r"\bfor breakfast\b",
        r"\bfor lunch\b",
        r"\bfor dinner\b",
        r"\bthis morning\b",
        r"\blast night\b",
    ]

    for pattern in removable_phrases:
        text = re.sub(pattern, " ", text)

    serving_words = {
        "small", "medium", "large",
        "cup", "cups", "bowl", "bowls",
        "plate", "plates", "glass", "glasses",
        "slice", "slices", "serving", "servings",
    }

    filler_words = {
        "a", "an", "the", "please", "me",
        "information", "details", "about", "of",
        "is", "are", "in", "per", "does", "do",
        "contain", "contains", "did", "i", "it",
        "there", "for", "what", "how", "much", "many",
        "calorie", "calories", "protein", "nutrient",
        "nutrients", "nutrition", "nutritional",
        "value", "facts", "content", "tell", "give",
        "show", "can", "you", "could", "would",
        "like", "to", "know", "want", "get",
        "ate", "eat", "eaten", "had", "have",
        "consumed", "calculate", "my", "just",
        "healthy", "carbs", "carbohydrates",
        "fat", "fiber", "fibre", "vitamin",
        "vitamins", "mineral", "minerals",
        "instead", "then", "breakfast", "lunch",
        "dinner", "morning", "night",
    }

    words = [
        word
        for word in text.split()
        if word not in filler_words and word not in serving_words
    ]

    return re.sub(r"\s+", " ", " ".join(words)).strip(" .")


# ============================================================
# FOOD NAME NORMALIZATION
# ============================================================

def singularize_food(food: str) -> str:
    """Normalize simple plurals while preserving meaningful food names."""

    food = food.strip()

    if not food:
        return food

    preserve_plural = {
        "chicken wings",
        "chicken thighs",
        "chicken breasts",
        "french fries",
        "green beans",
        "kidney beans",
        "baked beans",
        "chocolate chips",
        "oats",
        "lentils",
    }

    if food in preserve_plural:
        return food

    words = food.split()
    last = words[-1]

    irregular = {
        "potatoes": "potato",
        "tomatoes": "tomato",
        "leaves": "leaf",
    }

    if last in irregular:
        last = irregular[last]
    elif len(last) > 4 and last.endswith("ies"):
        last = last[:-3] + "y"
    elif (
        len(last) > 3
        and last.endswith("s")
        and not last.endswith(("ss", "us", "is"))
    ):
        last = last[:-1]

    words[-1] = last
    return " ".join(words)


# ============================================================
# INTENT DETECTION AND MAIN PARSER
# ============================================================

def detect_intent(text: str) -> str:
    """Identify a nutrition request."""

    return "nutrition" if text.strip() else "unknown"


def extract_food(text: str) -> Optional[str]:
    """Extract the cleaned food name."""

    cleaned = clean_food_phrase(text)
    cleaned = re.sub(r"^\d+(?:\.\d+)?\s*", "", cleaned).strip()

    return cleaned or None


def parse_query(user_text: str) -> ParsedQuery:
    """Parse a natural-language nutrition query."""

    original_text = user_text if isinstance(user_text, str) else ""
    normalized = normalize_text(original_text)

    if not normalized:
        return ParsedQuery(
            original_text=original_text,
            food=None,
            quantity=None,
            unit=None,
            intent="unknown",
        )

    corrected = correct_spelling(normalized)
    quantity, unit, remaining_text = extract_quantity(corrected)
    food = extract_food(remaining_text)

    if food:
        food = singularize_food(food)

    return ParsedQuery(
        original_text=original_text,
        food=food,
        quantity=quantity,
        unit=unit,
        intent=detect_intent(corrected),
    )


# ============================================================
# UNIT CONVERSION
# ============================================================

def quantity_to_grams(
    quantity: Optional[float],
    unit: Optional[str],
) -> Optional[float]:
    """Convert mass quantities to grams."""

    if quantity is None or unit is None:
        return None

    unit = normalize_unit(unit)

    if unit == "g":
        return quantity
    if unit == "kg":
        return quantity * 1000
    if unit == "mg":
        return quantity / 1000

    # A count such as 2 bananas cannot be converted accurately
    # without an estimated or measured weight per item.
    if unit == "piece":
        return None

    return None


# ============================================================
# MANUAL TESTS
# ============================================================

if __name__ == "__main__":
    test_queries = [
        "banana",
        "200g banana",
        "200 grams of mango",
        "I ate 50 g almonds",
        "2 bananas",
        "one apple",
        "tell me nutrition of mango",
        "what are the calories in dragon fruit",
        "I ate 2 kg watermelon",
        "two apples",
        "3 tomatoes",
        "500 mg spinach",
        "bananna",
        "I had 150 grams of brocolli",
        "i ate chickwn wings",
        "apl",
        "I ate a small cup of cake",
        "How much protein is in 100g of banana?",
        "Nutrition in dragon fruit",
        "What nutrients does an egg contain?",
        "Give me the nutrition information for potatoes.",
        "I ate 200g of rice. How many calories did I consume?",
        "Tell me the nutrition facts for 2 bananas.",
        "I ate 150 grams of apple. Calculate the nutrients.",
        "How much fat is there in 250g of boiled potato?",
        "I had two boiled eggs for breakfast. What nutrients did I get?",
    ]

    print("=" * 70)
    print("NLP PROCESSOR TEST")
    print("=" * 70)

    for query in test_queries:
        result = parse_query(query)
        grams = quantity_to_grams(result.quantity, result.unit)

        print(f"\nInput    : {query}")
        print(f"Food     : {result.food}")
        print(f"Quantity : {result.quantity}")
        print(f"Unit     : {result.unit}")
        print(f"Intent   : {result.intent}")
        print(f"Grams    : {grams}")

    print("\nNLP TEST COMPLETED")
