
import re
from dataclasses import dataclass
from typing import Optional


# ============================================================
# COMMON TYPO CORRECTIONS
# ============================================================
# This is a typo-correction dictionary, NOT a food database.
# Food information is retrieved dynamically from USDA later.
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


# ============================================================
# NUMBER WORDS
# ============================================================
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


# ============================================================
# SUPPORTED QUANTITY UNITS
# ============================================================
GRAM_UNITS = {"g", "gram", "grams", "gm", "gms"}
KILOGRAM_UNITS = {
    "kg", "kilogram", "kilograms", "kilo", "kilos"
}
MILLIGRAM_UNITS = {"mg", "milligram", "milligrams"}
PIECE_UNITS = {"piece", "pieces", "pc", "pcs", "item", "items"}

ALL_UNITS = GRAM_UNITS | KILOGRAM_UNITS | MILLIGRAM_UNITS | PIECE_UNITS


# ============================================================
# INTENT KEYWORDS
# ============================================================
NUTRITION_KEYWORDS = {
    "nutrition", "nutritional", "nutrients", "nutrient",
    "calorie", "calories", "protein", "carbohydrate",
    "carbohydrates", "carbs", "fat", "fiber", "fibre",
    "vitamin", "vitamins", "mineral", "minerals", "healthy",
}


# ============================================================
# RESULT DATA STRUCTURE
# ============================================================
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
    """Normalize input text."""
    if not isinstance(text, str):
        return ""

    text = text.lower().strip()
    text = text.replace("â€™", "'")
    text = re.sub(r"[^a-z0-9.\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# ============================================================
# TYPO CORRECTION
# ============================================================
def correct_word(word: str) -> str:
    """Correct a known typo; leave unknown words unchanged."""
    return COMMON_CORRECTIONS.get(word, word)


def correct_spelling(text: str) -> str:
    """Correct known spelling mistakes word by word."""
    return " ".join(correct_word(word) for word in text.split())


# ============================================================
# NUMBER PARSING
# ============================================================
def parse_number(value: str) -> Optional[float]:
    """Convert a number or number word to float."""
    value = value.strip().lower()

    if value in NUMBER_WORDS:
        return float(NUMBER_WORDS[value])

    try:
        return float(value)
    except ValueError:
        return None


# ============================================================
# UNIT NORMALIZATION
# ============================================================
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
        200 grams mango
        2 kg rice
        2 apples
        two bananas
    """
    text = text.strip()

    unit_pattern = "|".join(
        sorted(
            (re.escape(unit) for unit in ALL_UNITS),
            key=len,
            reverse=True,
        )
    )

    # Numeric quantity + unit
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

    number_word_pattern = "|".join(
        sorted(
            (re.escape(word) for word in NUMBER_WORDS),
            key=len,
            reverse=True,
        )
    )

    # Number word + unit
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

    # Numeric count + food, e.g. 2 apples
    match = re.match(
        r"^\s*(\d+(?:\.\d+)?)\s+(.+?)\s*$",
        text,
    )

    if match and match.group(2).strip():
        return float(match.group(1)), "piece", match.group(2).strip()

    # Number word + food, e.g. two apples
    match = re.match(
        rf"^\s*({number_word_pattern})\s+(.+?)\s*$",
        text,
    )

    if match:
        quantity = parse_number(match.group(1))
        remaining = match.group(2).strip()

        if quantity is not None and remaining:
            return quantity, "piece", remaining

    return None, None, text


# ============================================================
# SIMPLE FOOD SINGULARIZATION
# ============================================================
def singularize_food(food: str) -> str:
    """Convert simple plural food names to singular."""
    words = food.split()

    if not words:
        return food

    last = words[-1]

    if len(last) > 4 and last.endswith("ies"):
        last = last[:-3] + "y"
    elif len(last) > 4 and last.endswith("oes"):
        last = last[:-2]
    elif (
        len(last) > 3
        and last.endswith("s")
        and not last.endswith("ss")
    ):
        last = last[:-1]

    words[-1] = last
    return " ".join(words)


# ============================================================
# REMOVE CONVERSATIONAL AND SERVING WORDS
# ============================================================
def clean_food_phrase(text: str) -> str:
    """
    Remove conversational phrases and common serving descriptors.

    Note: removing serving words does NOT determine serving weight.
    A cup or slice must not be converted to grams without reliable
    portion information.
    """
    text = text.strip()

    removable_phrases = [
        r"\bi have eaten\b",
        r"\bi ate\b",
        r"\bi eat\b",
        r"\bi had\b",
        r"\bi have\b",
        r"\bi consumed\b",
        r"\bplease tell me\b",
        r"\bcan you tell me\b",
        r"\bcould you tell me\b",
        r"\btell me\b",
        r"\bshow me\b",
        r"\bwhat is\b",
        r"\bwhat are\b",
        r"\bhow many\b",
        r"\bhow much\b",
        r"\bnutrition of\b",
        r"\bnutritional value of\b",
        r"\bnutrition information of\b",
        r"\bnutrition information for\b",
        r"\bcalories in\b",
        r"\bcalorie content of\b",
        r"\bprotein in\b",
        r"\bcarbohydrates in\b",
        r"\bcarbs in\b",
        r"\bfat in\b",
        r"\bfiber in\b",
        r"\bfibre in\b",
    ]

    for pattern in removable_phrases:
        text = re.sub(pattern, " ", text, flags=re.IGNORECASE)

    # These words describe a serving rather than the food itself.
    serving_descriptors = {
        "small", "medium", "large",
        "cup", "cups", "bowl", "bowls",
        "plate", "plates", "glass", "glasses",
        "slice", "slices", "serving", "servings",
    }

    filler_words = {
        "a", "an", "please", "give", "me",
        "information", "details", "about", "for",
        "of", "the", "is", "are",
    }

    cleaned_words = [
        word
        for word in text.split()
        if word.lower() not in filler_words
        and word.lower() not in serving_descriptors
    ]

    return " ".join(cleaned_words).strip()


# ============================================================
# INTENT DETECTION
# ============================================================
def detect_intent(text: str) -> str:
    """Detect nutrition intent; food-only queries default to nutrition."""
    words = set(text.lower().split())

    if words.intersection(NUTRITION_KEYWORDS):
        return "nutrition"

    return "nutrition"


# ============================================================
# FOOD EXTRACTION
# ============================================================
def extract_food(text: str) -> Optional[str]:
    """Extract a food phrase after removing conversational words."""
    cleaned = clean_food_phrase(text)

    if not cleaned:
        return None

    cleaned = re.sub(r"^\d+(?:\.\d+)?\s*", "", cleaned).strip()
    return cleaned if cleaned else None


# ============================================================
# MAIN QUERY PARSER
# ============================================================
def parse_query(user_text: str) -> ParsedQuery:
    """Convert natural-language input into structured query data."""
    original_text = user_text
    normalized = normalize_text(user_text)

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

    if food and unit == "piece":
        food = singularize_food(food)

    intent = detect_intent(corrected)

    return ParsedQuery(
        original_text=original_text,
        food=food,
        quantity=quantity,
        unit=unit,
        intent=intent,
    )


# ============================================================
# QUANTITY TO GRAMS
# ============================================================
def quantity_to_grams(
    quantity: Optional[float],
    unit: Optional[str],
) -> Optional[float]:
    """Convert mass units to grams; piece counts need portion data."""
    if quantity is None or unit is None:
        return None

    unit = normalize_unit(unit)

    if unit == "g":
        return quantity
    if unit == "kg":
        return quantity * 1000
    if unit == "mg":
        return quantity / 1000
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
    ]

    print("=" * 70)
    print("NLP PROCESSOR TEST")
    print("=" * 70)

    for query in test_queries:
        result = parse_query(query)
        grams = quantity_to_grams(result.quantity, result.unit)

        print(f"\nInput     : {query}")
        print(f"Food      : {result.food}")
        print(f"Quantity  : {result.quantity}")
        print(f"Unit      : {result.unit}")
        print(f"Intent    : {result.intent}")
        print(f"Grams     : {grams}")

    print("\nNLP TEST COMPLETED")
