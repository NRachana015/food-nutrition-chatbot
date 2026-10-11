
"""
NutriBot - USDA FoodData Central Nutrition Chatbot

Features:
- Natural-language food queries
- Dynamic USDA FoodData Central lookup
- Nutrition calculations by weight
- USDA portion-based piece calculations
- Match scores and food-source information
- Typo correction through the NLP processor
- Clear handling of missing foods and connection errors
"""

import logging
from typing import Any, Dict, Optional

from nlp_processor import parse_query, quantity_to_grams
from nutrition_service import (
    USDAConnectionError,
    get_food_with_nutrition,
    calculate_nutrition_for_grams,
)

logger = logging.getLogger(__name__)


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


def format_nutrition(nutrition: Dict[str, Any]) -> str:
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
        if key not in nutrition or nutrition[key] is None:
            continue

        lines.append(
            f"{label}: {format_number(nutrition[key])} {unit}"
        )

    return "\n".join(lines) if lines else (
        "No nutrition values were available."
    )


# ============================================================
# ERROR RESPONSES
# ============================================================

def build_not_found_response(food: Optional[str]) -> str:
    """Respond when no reliable food match is available."""
    if food:
        return (
            f"❌ I couldn't find reliable nutrition information "
            f"for **{food}** in the current food database.\n\n"
            "Try another food name or provide a more specific "
            "description, such as raw, boiled, or roasted."
        )

    return (
        "❌ I couldn't identify a food in your message.\n\n"
        "Try a query such as **banana**, **mango**, "
        "**paneer**, or **dragon fruit**."
    )


def build_connection_error_response() -> str:
    """Distinguish an API outage from an unknown food."""
    return (
        "⚠️ I couldn't retrieve nutrition data from USDA "
        "FoodData Central right now.\n\n"
        "Please check your internet connection and try again. "
        "The food has not been confirmed as missing."
    )


# ============================================================
# USDA PORTION HELPERS
# ============================================================

def find_piece_portion(
    portions: Any,
    food_name: str,
) -> Optional[Dict[str, Any]]:
    """
    Find a plausible USDA portion representing one piece.

    Prefer portions explicitly described as one item. For eggs,
    prefer a size-specific egg portion when USDA provides one.
    Never invent a gram weight.
    """
    if not isinstance(portions, list) or not portions:
        return None

    food = str(food_name or "").lower()
    candidates = []

    for portion in portions:
        if not isinstance(portion, dict):
            continue

        try:
            weight = float(portion.get("gram_weight"))
        except (TypeError, ValueError):
            continue

        if weight <= 0:
            continue

        description = str(
            portion.get("description") or ""
        ).strip().lower()

        amount = portion.get("amount")

        try:
            amount_is_one = (
                amount is not None and float(amount) == 1.0
            )
        except (TypeError, ValueError):
            amount_is_one = False

        # A portion explicitly described as one item is preferred.
        explicitly_one = (
            description.startswith("1 ")
            or description.startswith("one ")
            or description == "1"
            or description == "one"
        )

        score = 0

        if explicitly_one:
            score += 5

        if amount_is_one:
            score += 2

        if any(word in description for word in (
            "piece", "whole", "fruit", "egg"
        )):
            score += 1

        # For egg queries, a named egg size is especially useful.
        if "egg" in food and any(word in description for word in (
            "large", "medium", "small", "extra large"
        )):
            score += 5

        # Avoid selecting a generic cup, tablespoon, or ounce
        # when the user asked for a count of individual pieces.
        if any(word in description for word in (
            "cup", "tablespoon", "teaspoon", "fluid ounce"
        )):
            score -= 5

        if score > 0:
            candidates.append((score, portion))

    if not candidates:
        return None

    candidates.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    return candidates[0][1]


# ============================================================
# MAIN CHAT FUNCTION
# ============================================================

def chat(user_message: str) -> Dict[str, Any]:
    """
    Process a food nutrition query.

    Examples:
        banana
        What is the nutrition in 200g apple?
        I ate chickwn wings
        What is the nutrition in 2 eggs?
    """

    # STEP 1: Parse the user's natural-language query.
    parsed = parse_query(user_message)

    if not parsed.food:
        return {
            "success": False,
            "message": build_not_found_response(None),
            "food": None,
            "quantity": parsed.quantity,
            "unit": parsed.unit,
            "grams": None,
            "nutrition": None,
            "matched_food": None,
            "fdc_id": None,
            "match_score": None,
        }

    # STEP 2: Search USDA and retrieve nutrition information.
    try:
        food_data = get_food_with_nutrition(parsed.food)

    except USDAConnectionError as exc:
        logger.warning("USDA connection error: %s", exc)

        return {
            "success": False,
            "message": build_connection_error_response(),
            "food": parsed.food,
            "quantity": parsed.quantity,
            "unit": parsed.unit,
            "grams": None,
            "nutrition": None,
            "matched_food": None,
            "fdc_id": None,
            "match_score": None,
            "error_type": "usda_connection_error",
        }

    except Exception:
        logger.exception("Unexpected nutrition lookup error")

        return {
            "success": False,
            "message": (
                "⚠️ An unexpected error occurred while retrieving "
                "nutrition information. Please try again."
            ),
            "food": parsed.food,
            "quantity": parsed.quantity,
            "unit": parsed.unit,
            "grams": None,
            "nutrition": None,
            "matched_food": None,
            "fdc_id": None,
            "match_score": None,
            "error_type": "lookup_error",
        }

    # STEP 3: No reliable food match.
    if not food_data:
        return {
            "success": False,
            "message": build_not_found_response(parsed.food),
            "food": parsed.food,
            "quantity": parsed.quantity,
            "unit": parsed.unit,
            "grams": None,
            "nutrition": None,
            "matched_food": None,
            "fdc_id": None,
            "match_score": None,
        }

    # STEP 4: Extract the selected USDA record.
    matched_food = (
        food_data.get("description")
        or food_data.get("food")
        or parsed.food
    )

    fdc_id = food_data.get("fdc_id")
    data_type = food_data.get("data_type")
    match_score = food_data.get(
        "match_score",
        food_data.get("score"),
    )

    nutrition = food_data.get("nutrition") or {}
    portions = food_data.get(
        "portions",
        food_data.get("food_portions", []),
    )

    # STEP 5: Determine quantity.
    grams = None
    calculated_nutrition = dict(nutrition)
    quantity_description = "per 100 g"
    quantity_unit = str(parsed.unit or "").strip().lower()

    if parsed.quantity is not None:
        try:
            grams = quantity_to_grams(
                parsed.quantity,
                parsed.unit,
            )
        except (TypeError, ValueError):
            grams = None

    # STEP 6: Calculate nutrition for a known weight.
    if grams is not None:
        calculated_nutrition = calculate_nutrition_for_grams(
            nutrition,
            grams,
        )
        quantity_description = f"for {format_number(grams)} g"

    # STEP 7: Calculate piece-based quantities using USDA portions.
    # This path runs when the NLP parser identifies a piece/count
    # but cannot convert it directly into grams.
    elif (
        parsed.quantity is not None
        and quantity_unit in {
            "piece", "pieces", "item", "items", "egg", "eggs"
        }
    ):
        portion = find_piece_portion(
            portions,
            f"{parsed.food} {matched_food}",
        )

        if portion is not None:
            try:
                portion_grams = float(portion["gram_weight"])
                count = float(parsed.quantity)

                if count < 0:
                    raise ValueError("Quantity cannot be negative.")

                total_grams = count * portion_grams

                calculated_nutrition = (
                    calculate_nutrition_for_grams(
                        nutrition,
                        total_grams,
                    )
                )

                grams = total_grams

                portion_description = str(
                    portion.get("description") or "USDA portion"
                )

                quantity_description = (
                    f"for {format_number(count)} item(s), "
                    f"approximately {format_number(total_grams)} g "
                    f"({format_number(portion_grams)} g each; "
                    f"USDA portion: {portion_description})"
                )

            except (TypeError, ValueError, KeyError):
                calculated_nutrition = dict(nutrition)
                quantity_description = (
                    "per 100 g; a reliable piece weight "
                    "could not be calculated"
                )

        else:
            # Do not invent a portion weight.
            calculated_nutrition = dict(nutrition)
            quantity_description = (
                "per 100 g; USDA did not provide a suitable "
                "piece weight, so the count could not be calculated"
            )

    elif parsed.quantity is not None:
        quantity_description = (
            f"per 100 g; quantity unit '{parsed.unit}' "
            "could not be converted reliably"
        )

    # STEP 8: Format the result.
    nutrition_text = format_nutrition(calculated_nutrition)

    message = (
        "### 🍎 Nutrition Information\n\n"
        f"**Food:** {matched_food}\n\n"
        f"**Amount:** {quantity_description}\n\n"
        f"{nutrition_text}\n\n"
        "**Data source:** USDA FoodData Central\n\n"
        f"**Data type:** {data_type or 'Not provided'}\n\n"
        f"**USDA FDC ID:** {fdc_id or 'Not provided'}"
    )

    if match_score is not None:
        message += (
            f"\n\n**Match score:** {format_number(match_score)}"
        )

    # STEP 9: Return a structured response for Streamlit or CLI.
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
        "quantity_description": quantity_description,
    }


# ============================================================
# COMMAND-LINE TEST
# ============================================================

if __name__ == "__main__":
    test_queries = [
        "banana",
        "200g banana",
        "What is the nutrition in 200g apple?",
        "I ate 50 g almonds",
        "100 grams paneer",
        "What is the nutrition in 2 eggs?",
        "What is the nutrition in 100g boiled rice?",
        "I ate chickwn wings",
        "tell me nutrition of dragon fruit",
        "one apple",
        "What is the nutrition in xyzabc food?",
    ]

    for query in test_queries:
        print("\n" + "=" * 70)
        print(f"USER: {query}")
        print("=" * 70)

        result = chat(query)
        print(result["message"])
