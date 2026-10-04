from rapidfuzz import fuzz

from nutrition_service import search_food


# ============================================================
# FOOD MATCHER
# ============================================================

# Common spelling corrections.
# This is NOT a food database.
# It only handles frequent spelling variations/typos.
COMMON_CORRECTIONS = {
    "bananna": "banana",
    "banan": "banana",
    "brocolli": "broccoli",
    "brocoli": "broccoli",
    "chiken": "chicken",
    "chikn": "chicken",
    "tomatos": "tomato",
    "potatos": "potato",
    "spinich": "spinach",
    "carot": "carrot",
    "aple": "apple",
    "oragne": "orange",
    "strawbery": "strawberry",
    "avacado": "avocado",
}


# Terms that usually indicate a prepared/branded product.
# These should be penalized when the user asks for a basic food.
PRODUCT_TERMS = {
    "sauce",
    "sauced",
    "frozen",
    "dinner",
    "entree",
    "meal",
    "replacement",
    "powder",
    "supplement",
    "bar",
    "cookie",
    "cereal",
    "chips",
    "crackers",
    "sausage",
    "nuggets",
    "fingers",
    "pizza",
    "sandwich",
    "burger",
    "breaded",
    "fried",
    "flavored",
    "seasoned",
    "stir",
    "snack",
}


# Data types that are generally more useful for generic foods.
PREFERRED_DATA_TYPES = {
    "foundation": 20,
    "sr legacy": 18,
    "survey (fndds)": 16,
    "sub-ingredients": 10,
    "branded": -12,
}


def normalize_food_name(name: str) -> str:
    """
    Normalize food names for comparison.
    """

    if not name:
        return ""

    name = name.lower().strip()

    name = name.replace("-", " ")
    name = name.replace("_", " ")

    # Remove repeated whitespace.
    name = " ".join(name.split())

    return name


def correct_common_spelling(name: str) -> str:
    """
    Correct common spelling mistakes.

    This does not attempt to create a finite food vocabulary.
    It only corrects frequent misspellings.
    """

    normalized = normalize_food_name(name)

    return COMMON_CORRECTIONS.get(
        normalized,
        normalized,
    )


def contains_product_terms(description: str) -> bool:
    """
    Check whether a USDA description looks like a
    prepared or branded food product.
    """

    description = normalize_food_name(description)

    words = set(description.split())

    return bool(words.intersection(PRODUCT_TERMS))


def score_food_result(query: str, food: dict) -> float:
    """
    Calculate a reliability score for a USDA search result.
    """

    query = normalize_food_name(query)

    description = normalize_food_name(
        food.get("description", "")
    )

    if not query or not description:
        return 0.0

    # Exact match should be strongest.
    if description == query:
        base_score = 100.0

    else:
        ratio_score = fuzz.ratio(
            query,
            description,
        )

        partial_score = fuzz.partial_ratio(
            query,
            description,
        )

        token_score = fuzz.token_set_ratio(
            query,
            description,
        )

        base_score = (
            (ratio_score * 0.40)
            + (partial_score * 0.25)
            + (token_score * 0.35)
        )

    # --------------------------------------------------------
    # Data type adjustment
    # --------------------------------------------------------

    data_type = normalize_food_name(
        food.get("dataType", "")
    )

    type_bonus = PREFERRED_DATA_TYPES.get(
        data_type,
        0,
    )

    # --------------------------------------------------------
    # Product penalty
    # --------------------------------------------------------

    product_penalty = 0

    if contains_product_terms(description):
        product_penalty = 20

    # --------------------------------------------------------
    # Exact first-word match
    # --------------------------------------------------------

    query_words = query.split()
    description_words = description.split()

    word_bonus = 0

    if query_words and description_words:

        if query_words[0] == description_words[0]:
            word_bonus += 8

    # --------------------------------------------------------
    # Final score
    # --------------------------------------------------------

    final_score = (
        base_score
        + type_bonus
        + word_bonus
        - product_penalty
    )

    return round(
        max(0.0, min(100.0, final_score)),
        2,
    )


def rank_food_results(
    query: str,
    foods: list[dict],
) -> list[dict]:
    """
    Rank USDA food results.
    """

    ranked = []

    for food in foods:

        score = score_food_result(
            query,
            food,
        )

        ranked.append(
            {
                "food": food,
                "score": score,
            }
        )

    ranked.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    return ranked


def search_with_correction(
    food_name: str,
    page_size: int = 20,
):
    """
    Search USDA using both the original spelling
    and a corrected spelling when available.
    """

    original_query = normalize_food_name(
        food_name
    )

    corrected_query = correct_common_spelling(
        food_name
    )

    queries = []

    if original_query:
        queries.append(original_query)

    if (
        corrected_query
        and corrected_query not in queries
    ):
        queries.append(corrected_query)

    all_foods = []

    for query in queries:

        foods = search_food(
            query,
            page_size=page_size,
        )

        all_foods.extend(foods)

    # Remove duplicate FDC IDs.
    unique_foods = {}

    for food in all_foods:

        fdc_id = food.get("fdcId")

        if fdc_id is not None:
            unique_foods[fdc_id] = food

    return list(unique_foods.values()), corrected_query


def find_best_food_match(
    food_name: str,
    page_size: int = 20,
    minimum_score: float = 72.0,
):
    """
    Find the safest USDA food match.

    Returns None when confidence is insufficient.
    """

    if not food_name:
        return None

    original_query = normalize_food_name(
        food_name
    )

    foods, corrected_query = search_with_correction(
        food_name,
        page_size=page_size,
    )

    if not foods:
        return None

    # Rank against corrected spelling when available.
    ranking_query = corrected_query or original_query

    ranked_results = rank_food_results(
        ranking_query,
        foods,
    )

    if not ranked_results:
        return None

    best = ranked_results[0]

    if best["score"] < minimum_score:
        return None

    food = best["food"]

    score = best["score"]

    if score >= 90:
        confidence = "high"

    elif score >= 80:
        confidence = "medium"

    else:
        confidence = "low"

    return {
        "food": food,
        "score": score,
        "confidence": confidence,
        "query": food_name,
        "corrected_query": corrected_query,
        "matched_name": food.get("description"),
        "fdc_id": food.get("fdcId"),
        "data_type": food.get("dataType"),
    }


def get_food_suggestions(
    food_name: str,
    page_size: int = 10,
):
    """
    Return safe ranked suggestions.
    """

    if not food_name:
        return []

    foods, corrected_query = search_with_correction(
        food_name,
        page_size=page_size,
    )

    if not foods:
        return []

    ranking_query = corrected_query

    ranked_results = rank_food_results(
        ranking_query,
        foods,
    )

    suggestions = []

    for item in ranked_results[:5]:

        food = item["food"]

        suggestions.append(
            {
                "name": food.get("description"),
                "fdc_id": food.get("fdcId"),
                "data_type": food.get("dataType"),
                "score": item["score"],
            }
        )

    return suggestions


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    test_foods = [
        "banana",
        "bananna",
        "brocolli",
        "chiken",
        "spinach",
        "apple",
        "orange",
        "avocado",
    ]

    print("=" * 70)
    print("FOOD MATCHER TEST")
    print("=" * 70)

    for food_name in test_foods:

        print(
            f"\nSearching for: {food_name}"
        )

        result = find_best_food_match(
            food_name
        )

        if result:

            print(
                f"Matched food : "
                f"{result['matched_name']}"
            )

            print(
                f"Corrected     : "
                f"{result['corrected_query']}"
            )

            print(
                f"Score         : "
                f"{result['score']}"
            )

            print(
                f"Confidence    : "
                f"{result['confidence']}"
            )

            print(
                f"FDC ID        : "
                f"{result['fdc_id']}"
            )

            print(
                f"Data Type     : "
                f"{result['data_type']}"
            )

        else:

            print(
                "No reliable food match found."
            )

    print("\n" + "=" * 70)
    print("FOOD MATCHER TEST COMPLETED")
    print("=" * 70)