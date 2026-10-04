
from typing import Any, Dict, Optional

from nlp_processor import parse_query, quantity_to_grams
from nutrition_service import (
    get_food_with_nutrition,
    calculate_nutrition_for_grams,
)


# ============================================================
# DISPLAY HELPERS
# ============================================================

def format_number(value: Any, decimals: int = 2) -> str:
    """Format numeric values cleanly."""

    if value is None:
        return "N/A"

    try:
        number = float(value)

        if number.is_integer():
            return str(int(number))

        return f"{number:.{decimals}f}"

    except (TypeError, ValueError):
        return str(value)


def format_nutrition(
    nutrition: Dict[str, Any],
) -> str:
    """Convert nutrition data into readable text."""

    fields = [
        ("calories", "🔥 Calories", "kcal"),
        ("protein_g", "💪 Protein", "g"),
        ("carbohydrates_g", "🍞 Carbohydrates", "g"),
        ("fat_g", "🥑 Fat", "g"),
        ("fiber_g", "🌾 Fiber", "g"),
        ("sugar_g", "🍬 Sugar", "g"),
        ("calcium_mg", "🦴 Calcium", "mg"),
        ("iron_mg", "🩸 Iron", "mg"),
        ("sodium_mg", "🧂 Sodium", "mg"),
        ("vitamin_c_mg", "🍊 Vitamin C", "mg"),
    ]

    lines = []

    for key, label, unit in fields:

        if key not in nutrition:
            continue

        value = nutrition[key]

        if value is None:
            continue

        lines.append(
            f"{label}: {format_number(value)} {unit}"
        )

    if not lines:
        return "No nutrition values were available."

    return "\n".join(lines)


# ============================================================
# NO MATCH RESPONSE
# ============================================================

def build_not_found_response(
    food: Optional[str],
) -> str:
    """Safe response when no reliable food is found."""

    if food:

        return (
            f"❌ I couldn't find reliable nutrition "
            f"information for **{food}** in the current "
            "food database.\n\n"
            "Please try another food name or provide a "
            "more specific description."
        )

    return (
        "❌ I couldn't identify the food from your message.\n\n"
        "Please enter a food name such as **banana**, "
        "**mango**, **paneer**, or **dragon fruit**."
    )


# ============================================================
# MAIN CHAT FUNCTION
# ============================================================

def chat(
    user_message: str,
) -> Dict[str, Any]:
    """
    Process a natural-language food nutrition query.

    Example:

        "I ate 200g banana"

    Pipeline:

        User message
              ↓
        NLP processor
              ↓
        Food + quantity + unit
              ↓
        Dynamic USDA lookup
              ↓
        Nutrition calculation
              ↓
        Chatbot response
    """

    # --------------------------------------------------------
    # STEP 1 — NLP
    # --------------------------------------------------------

    parsed = parse_query(
        user_message
    )

    # --------------------------------------------------------
    # STEP 2 — FOOD VALIDATION
    # --------------------------------------------------------

    if not parsed.food:

        return {
            "success": False,
            "message": build_not_found_response(
                None
            ),
            "food": None,
            "quantity": parsed.quantity,
            "unit": parsed.unit,
            "grams": None,
            "nutrition": None,
            "matched_food": None,
            "fdc_id": None,
        }

    # --------------------------------------------------------
    # STEP 3 — DYNAMIC USDA SEARCH
    # --------------------------------------------------------

    try:

        food_data = get_food_with_nutrition(
            parsed.food
        )

    except Exception as exc:

        print(
            f"Nutrition lookup error: {exc}"
        )

        food_data = None

    # --------------------------------------------------------
    # STEP 4 — NO RELIABLE MATCH
    # --------------------------------------------------------

    if not food_data:

        return {
            "success": False,
            "message": build_not_found_response(
                parsed.food
            ),
            "food": parsed.food,
            "quantity": parsed.quantity,
            "unit": parsed.unit,
            "grams": None,
            "nutrition": None,
            "matched_food": None,
            "fdc_id": None,
        }

    # --------------------------------------------------------
    # STEP 5 — GET USDA RESULT
    # --------------------------------------------------------

    matched_food = food_data.get(
        "food",
        parsed.food,
    )

    fdc_id = food_data.get(
        "fdc_id"
    )

    data_type = food_data.get(
        "data_type"
    )

    match_score = food_data.get(
        "match_score"
    )

    nutrition = food_data.get(
        "nutrition",
        {},
    )

    # --------------------------------------------------------
    # STEP 6 — QUANTITY → GRAMS
    # --------------------------------------------------------

    grams = quantity_to_grams(
        parsed.quantity,
        parsed.unit,
    )

    calculated_nutrition = nutrition

    quantity_description = (
        "per 100 g"
    )

    # --------------------------------------------------------
    # STEP 7 — GRAM-BASED CALCULATION
    # --------------------------------------------------------

    if grams is not None:

        calculated_nutrition = (
            calculate_nutrition_for_grams(
                nutrition,
                grams,
            )
        )

        quantity_description = (
            f"for {format_number(grams)} g"
        )

    # --------------------------------------------------------
    # STEP 8 — PIECE QUANTITY
    # --------------------------------------------------------
    #
    # IMPORTANT:
    #
    # We do NOT assume that USDA's serving_size is
    # automatically the weight of one piece.
    #
    # The current nutrition service provides food_portions,
    # so we only calculate pieces when we can safely obtain
    # a USDA portion weight.
    # --------------------------------------------------------

    elif (
        parsed.quantity is not None
        and parsed.unit == "piece"
    ):

        food_portions = food_data.get(
            "food_portions",
            [],
        )

        portion_grams = None
        portion_description = None

        # Look for a USDA portion that represents one item.
        for portion in food_portions:

            if not isinstance(
                portion,
                dict,
            ):
                continue

            description = str(
                portion.get(
                    "portion_description",
                    "",
                )
            ).lower()

            gram_weight = portion.get(
                "gram_weight"
            )

            if (
                gram_weight is not None
                and (
                    "1 " in description
                    or "one " in description
                )
            ):

                try:

                    portion_grams = float(
                        gram_weight
                    )

                    portion_description = (
                        portion.get(
                            "portion_description"
                        )
                    )

                    break

                except (
                    TypeError,
                    ValueError,
                ):

                    continue

        if portion_grams:

            total_grams = (
                float(parsed.quantity)
                * portion_grams
            )

            calculated_nutrition = (
                calculate_nutrition_for_grams(
                    nutrition,
                    total_grams,
                )
            )

            quantity_description = (
                f"for {format_number(parsed.quantity)} "
                f"piece(s) "
                f"({format_number(portion_grams)} g "
                f"each, USDA portion: "
                f"{portion_description})"
            )

        else:

            # Do NOT invent a piece weight.
            calculated_nutrition = nutrition

            quantity_description = (
                f"for {format_number(parsed.quantity)} "
                "piece(s) — USDA piece weight "
                "was unavailable, so nutrition is "
                "shown per 100 g"
            )

    # --------------------------------------------------------
    # STEP 9 — FORMAT NUTRITION
    # --------------------------------------------------------

    nutrition_text = format_nutrition(
        calculated_nutrition
    )

    # --------------------------------------------------------
    # STEP 10 — BUILD CHATBOT RESPONSE
    # --------------------------------------------------------

    message = (
        "### 🍎 Nutrition Information\n\n"
        f"**Food:** {matched_food}\n\n"
        f"**Amount:** {quantity_description}\n\n"
        f"{nutrition_text}\n\n"
        f"**Data source:** USDA FoodData Central\n\n"
        f"**Data type:** {data_type}\n\n"
        f"**USDA FDC ID:** {fdc_id}"
    )

    # Add match score when available.
    if match_score is not None:

        message += (
            f"\n\n**Match score:** "
            f"{format_number(match_score)}"
        )

    # --------------------------------------------------------
    # STEP 11 — STRUCTURED RESULT
    # --------------------------------------------------------

    return {
        "success": True,
        "message": message,
        "food": parsed.food,
        "quantity": parsed.quantity,
        "unit": parsed.unit,
        "grams": grams,
        "nutrition": calculated_nutrition,
        "matched_food": matched_food,
        "fdc_id": fdc_id,
        "data_type": data_type,
        "match_score": match_score,
    }


# ============================================================
# COMMAND-LINE TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 70)
    print("FOOD NUTRITION CHATBOT TEST")
    print("=" * 70)

    test_queries = [

        # Basic food
        "banana",

        # Quantity
        "200g banana",

        # Natural language
        "200 grams of mango",

        # Sentence
        "I ate 50 g almonds",

        # Indian food
        "100 grams paneer",

        # Dynamic unseen food
        "tell me nutrition of dragon fruit",

        # Kilogram
        "I ate 2 kg watermelon",

        # Piece
        "one apple",

        # Typo correction
        "bananna",

        # More unseen foods
        "cantaloupe",

        "asparagus",
    ]

    for query in test_queries:

        print("\n" + "-" * 70)
        print(f"USER: {query}")
        print("-" * 70)

        try:

            result = chat(
                query
            )

            print(
                result["message"]
            )

        except Exception as exc:

            print(
                f"ERROR while processing "
                f"'{query}': {exc}"
            )

    print("\n" + "=" * 70)
    print("CHATBOT TEST COMPLETED")
    print("=" * 70)
