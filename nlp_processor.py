
import re
from dataclasses import dataclass
from typing import Optional


# ============================================================
# COMMON TYPO CORRECTIONS
# ============================================================
# This is NOT a food database.
# It only fixes common spelling mistakes.
#
# Food availability is still determined dynamically
# through USDA FoodData Central later in the pipeline.
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

GRAM_UNITS = {
    "g",
    "gram",
    "grams",
    "gm",
    "gms",
}

KILOGRAM_UNITS = {
    "kg",
    "kilogram",
    "kilograms",
    "kilo",
    "kilos",
}

MILLIGRAM_UNITS = {
    "mg",
    "milligram",
    "milligrams",
}

PIECE_UNITS = {
    "piece",
    "pieces",
    "pc",
    "pcs",
    "item",
    "items",
}

ALL_UNITS = (
    GRAM_UNITS
    | KILOGRAM_UNITS
    | MILLIGRAM_UNITS
    | PIECE_UNITS
)


# ============================================================
# INTENT KEYWORDS
# ============================================================

NUTRITION_KEYWORDS = {
    "nutrition",
    "nutritional",
    "nutrients",
    "nutrient",
    "calorie",
    "calories",
    "protein",
    "carbohydrate",
    "carbohydrates",
    "carbs",
    "fat",
    "fiber",
    "fibre",
    "vitamin",
    "vitamins",
    "mineral",
    "minerals",
    "healthy",
}


# ============================================================
# RESULT DATA STRUCTURE
# ============================================================

@dataclass
class ParsedQuery:
    """
    Structured representation of a user's food query.
    """

    original_text: str
    food: Optional[str]
    quantity: Optional[float]
    unit: Optional[str]
    intent: str


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_text(text: str) -> str:
    """
    Normalize user input.

    Example:
        "  I ATE 200G BANANNA!!! "
        ->
        "i ate 200g bananna"
    """

    if not isinstance(text, str):
        return ""

    text = text.lower().strip()

    # Normalize curly apostrophes.
    text = text.replace("â€™", "'")

    # Keep letters, numbers, spaces and decimal points.
    text = re.sub(r"[^a-z0-9.\s]", " ", text)

    # Remove repeated spaces.
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ============================================================
# TYPO CORRECTION
# ============================================================

def correct_word(word: str) -> str:
    """
    Correct a known common typo.

    Unknown food names are left unchanged.
    """

    return COMMON_CORRECTIONS.get(word, word)


def correct_spelling(text: str) -> str:
    """
    Apply typo correction word-by-word.

    This does NOT determine whether a word is a food.
    USDA will perform the actual food lookup later.
    """

    words = text.split()

    corrected_words = [
        correct_word(word)
        for word in words
    ]

    return " ".join(corrected_words)


# ============================================================
# NUMBER PARSING
# ============================================================

def parse_number(value: str) -> Optional[float]:
    """
    Convert numeric text or a number word into a float.
    """

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
    """
    Convert different unit spellings into a standard unit.

    Examples:
        grams -> g
        kilogram -> kg
        milligrams -> mg
        pieces -> piece
    """

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
    Extract quantity and unit from the query.

    Examples:

        "200g banana"
            -> 200, "g"

        "200 grams mango"
            -> 200, "g"

        "2 kg watermelon"
            -> 2, "kg"

        "one apple"
            -> 1, "piece"

        "two bananas"
            -> 2, "piece"

    Returns:
        quantity, unit, remaining_text
    """

    text = text.strip()

    # --------------------------------------------------------
    # Build unit pattern.
    # Longest units are checked first.
    # --------------------------------------------------------

    unit_pattern = "|".join(
        sorted(
            [re.escape(unit) for unit in ALL_UNITS],
            key=len,
            reverse=True,
        )
    )

    # --------------------------------------------------------
    # Pattern 1:
    # numeric quantity + unit
    #
    # Examples:
    # 200g
    # 200 grams
    # 2 kg
    # 500 mg
    # --------------------------------------------------------

    numeric_unit_pattern = (
        rf"\b(\d+(?:\.\d+)?)\s*({unit_pattern})\b"
    )

    match = re.search(
        numeric_unit_pattern,
        text,
    )

    if match:

        quantity = float(match.group(1))
        raw_unit = match.group(2)

        unit = normalize_unit(raw_unit)

        remaining_text = (
            text[:match.start()]
            + " "
            + text[match.end():]
        )

        remaining_text = re.sub(
            r"\s+",
            " ",
            remaining_text,
        ).strip()

        return quantity, unit, remaining_text

    # --------------------------------------------------------
    # Pattern 2:
    # number word + unit
    #
    # Examples:
    # two kg rice
    # five grams almonds
    # --------------------------------------------------------

    number_word_pattern = "|".join(
        sorted(
            [re.escape(word) for word in NUMBER_WORDS],
            key=len,
            reverse=True,
        )
    )

    word_unit_pattern = (
        rf"\b({number_word_pattern})\s+({unit_pattern})\b"
    )

    match = re.search(
        word_unit_pattern,
        text,
    )

    if match:

        quantity = parse_number(match.group(1))
        raw_unit = match.group(2)

        unit = normalize_unit(raw_unit)

        remaining_text = (
            text[:match.start()]
            + " "
            + text[match.end():]
        )

        remaining_text = re.sub(
            r"\s+",
            " ",
            remaining_text,
        ).strip()

        return quantity, unit, remaining_text

    # --------------------------------------------------------
    # Pattern 3:
    # numeric quantity + food
    #
    # Examples:
    # 2 bananas
    # 3 apples
    # --------------------------------------------------------

    numeric_piece_pattern = (
        r"^\s*(\d+(?:\.\d+)?)\s+(.+?)\s*$"
    )

    match = re.match(
        numeric_piece_pattern,
        text,
    )

    if match:

        quantity = float(match.group(1))
        remaining_text = match.group(2).strip()

        if remaining_text:

            return (
                quantity,
                "piece",
                remaining_text,
            )

    # --------------------------------------------------------
    # Pattern 4:
    # number word + food
    #
    # Examples:
    # one apple
    # two bananas
    # three oranges
    # --------------------------------------------------------

    word_piece_pattern = (
        rf"^\s*({number_word_pattern})\s+(.+?)\s*$"
    )

    match = re.match(
        word_piece_pattern,
        text,
    )

    if match:

        quantity = parse_number(match.group(1))
        remaining_text = match.group(2).strip()

        if quantity is not None and remaining_text:

            return (
                quantity,
                "piece",
                remaining_text,
            )

    # --------------------------------------------------------
    # No quantity found.
    # --------------------------------------------------------

    return None, None, text


# ============================================================
# SIMPLE FOOD SINGULARIZATION
# ============================================================

def singularize_food(food: str) -> str:
    """
    Convert simple plural food names to singular.

    Examples:
        bananas  -> banana
        apples   -> apple
        tomatoes -> tomato
        potatoes -> potato
        berries  -> berry

    This is NOT a food database.
    """

    words = food.split()

    if not words:
        return food

    last = words[-1]

    # berries -> berry
    if len(last) > 4 and last.endswith("ies"):
        last = last[:-3] + "y"

    # tomatoes -> tomato
    elif len(last) > 4 and last.endswith("oes"):
        last = last[:-2]

    # apples -> apple
    #
    # Do not remove "s" from words ending in "ss".
    elif (
        len(last) > 3
        and last.endswith("s")
        and not last.endswith("ss")
    ):
        last = last[:-1]

    words[-1] = last

    return " ".join(words)


# ============================================================
# REMOVE COMMON CHATBOT PHRASES
# ============================================================

def clean_food_phrase(text: str) -> str:
    """
    Remove conversational phrases that are not part
    of the food name.

    This does NOT use a fixed food list.
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

        text = re.sub(
            pattern,
            " ",
            text,
            flags=re.IGNORECASE,
        )

    # Remove conversational filler words.
    filler_words = {
        "please",
        "give",
        "me",
        "information",
        "details",
        "about",
        "for",
        "of",
        "the",
        "is",
        "are",
    }

    words = text.split()

    cleaned_words = [
        word
        for word in words
        if word.lower() not in filler_words
    ]

    return " ".join(cleaned_words).strip()


# ============================================================
# INTENT DETECTION
# ============================================================

def detect_intent(text: str) -> str:
    """
    Detect the main intent.

    At this stage the chatbot is focused on nutrition queries.
    """

    text = text.lower()

    words = set(text.split())

    if words.intersection(NUTRITION_KEYWORDS):
        return "nutrition"

    # A food-only query such as "banana" is also interpreted
    # as a nutrition request.
    return "nutrition"


# ============================================================
# FOOD EXTRACTION
# ============================================================

def extract_food(text: str) -> Optional[str]:
    """
    Extract the food phrase after removing:
    - conversational phrases
    - quantity information
    - units
    - filler words

    The returned food is NOT validated here.

    USDA performs the actual food lookup later.
    """

    cleaned = clean_food_phrase(text)

    if not cleaned:
        return None

    # Remove an accidental numeric quantity at the beginning.
    cleaned = re.sub(
        r"^\d+(?:\.\d+)?\s*",
        "",
        cleaned,
    ).strip()

    return cleaned if cleaned else None


# ============================================================
# MAIN QUERY PARSER
# ============================================================

def parse_query(user_text: str) -> ParsedQuery:
    """
    Convert natural-language user input into structured data.

    Examples:

        "200g banana"

        -> food = banana
           quantity = 200
           unit = g
           intent = nutrition


        "two apples"

        -> food = apple
           quantity = 2
           unit = piece
           intent = nutrition
    """

    original_text = user_text

    # --------------------------------------------------------
    # 1. Normalize text
    # --------------------------------------------------------

    normalized = normalize_text(user_text)

    if not normalized:

        return ParsedQuery(
            original_text=original_text,
            food=None,
            quantity=None,
            unit=None,
            intent="unknown",
        )

    # --------------------------------------------------------
    # 2. Correct common spelling mistakes
    # --------------------------------------------------------

    corrected = correct_spelling(normalized)

    # --------------------------------------------------------
    # 3. Extract quantity and unit
    # --------------------------------------------------------

    quantity, unit, remaining_text = extract_quantity(
        corrected
    )

    # --------------------------------------------------------
    # 4. Extract food name
    # --------------------------------------------------------

    food = extract_food(remaining_text)

    # --------------------------------------------------------
    # 5. Singularize only piece-based food quantities
    #
    # Example:
    # 2 bananas -> banana
    #
    # We do not force singularization for gram-based
    # queries because the user's original food phrase
    # should otherwise remain untouched.
    # --------------------------------------------------------

    if food and unit == "piece":
        food = singularize_food(food)

    # --------------------------------------------------------
    # 6. Detect intent
    # --------------------------------------------------------

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
    """
    Convert measurable mass units to grams.

    Examples:
        200 g  -> 200 g
        2 kg   -> 2000 g
        500 mg -> 0.5 g

    Piece quantities intentionally return None.

    We do NOT invent the weight of one food item.
    The actual piece weight will later come from
    USDA portion information when available.
    """

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
# TESTING
# ============================================================

if __name__ == "__main__":

    test_queries = [
        "banana",
        "200g banana",
        "200 grams of mango",
        "I ate 50 g almonds",
        "2 bananas",
        "one apple",
        "100 grams paneer",
        "50g almonds",
        "tell me nutrition of mango",
        "what are the calories in dragon fruit",
        "I ate 2 kg watermelon",
        "two apples",
        "3 tomatoes",
        "two potatoes",
        "500 mg spinach",
        "bananna",
        "I had 150 grams of brocolli",
        "3 berries",
        "i ate chickwn wings",
    ]

    print("=" * 70)
    print("NLP PROCESSOR TEST")
    print("=" * 70)

    for query in test_queries:

        result = parse_query(query)

        print("\n" + "-" * 70)
        print(f"Input     : {query}")
        print(f"Food      : {result.food}")
        print(f"Quantity  : {result.quantity}")
        print(f"Unit      : {result.unit}")
        print(f"Intent    : {result.intent}")

        grams = quantity_to_grams(
            result.quantity,
            result.unit,
        )

        print(f"Grams     : {grams}")

    print("\n" + "=" * 70)
    print("NLP TEST COMPLETED")
    print("=" * 70)
