"""
NutriBot - USDA FoodData Central Nutrition Service

Features:
- Dynamic USDA food search
- Automatic retries for temporary network errors
- Food-name matching and ranking
- Nutrition extraction and unit conversion
- Quantity and serving calculations
- No hardcoded nutrition database
"""

import logging
import re
import time
from typing import Any, Optional

import requests

from config import USDA_API_KEY, USDA_BASE_URL

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 20
MAX_RETRIES = 3
MINIMUM_MATCH_SCORE = 75

DATA_TYPE_PRIORITY = {
    "foundation": 100,
    "sr legacy": 90,
    "survey (fndds)": 80,
    "survey": 80,
    "experimental foods": 70,
    "branded": 50,
}

PREPARATION_WORDS = {
    "raw", "cooked", "boiled", "baked", "fried", "roasted",
    "grilled", "steamed", "poached", "sauteed", "sautéed",
    "broiled", "smoked", "dried", "toasted", "scrambled",
    "microwaved", "braised", "stewed", "barbecued",
    "barbequed", "pickled", "frozen",
}

COMBINATION_TERMS = {
    "casserole", "sandwich", "salad", "pizza", "burger",
    "hamburger", "soup", "stew", "curry", "lasagna",
    "pasta dish", "fried rice", "burrito", "taco",
    "pie", "cake", "cookie", "smoothie", "shake",
    "mixed dish", "baby food dinner",
}

GENERIC_WORDS = {
    "whole", "fresh", "raw", "cooked", "uncooked",
    "meat", "flesh", "without", "with", "skin",
    "boneless", "bone", "bone-in", "lean", "only",
    "including", "excluding", "piece", "pieces",
    "large", "small", "medium", "ripe", "unripe",
    "common", "standard", "food", "foods", "edible",
    "edible portion", "product", "products",
    "broiler", "broilers", "fryer", "fryers",
    "young", "roasting", "stewing", "grade",
    "type", "style", "commercial",
}

FOOD_VARIANT_TERMS = {
    "fat", "feet", "foot", "skin", "liver", "heart",
    "gizzard", "kidney", "intestine", "bone", "bones",
    "broth", "stock", "extract", "powder", "flour",
    "juice", "syrup", "candy", "chips", "snack",
    "spread", "sauce", "supplement", "formula",
    "meatless", "imitation", "substitute", "protein",
    "sausage", "frankfurter", "nugget", "nuggets",
    "patty", "patties", "jerky", "baby", "dehydrated",
    "freeze", "concentrate", "cracker", "crackers",
}

NUTRIENT_MAP = {
    "calories": {
        "names": {"energy", "energy kcal", "calories"},
        "unit": "kcal",
    },
    "protein_g": {
        "names": {"protein", "protein g"},
        "unit": "g",
    },
    "carbohydrates_g": {
        "names": {
            "carbohydrate by difference", "carbohydrates",
            "carbohydrate total", "total carbohydrate",
        },
        "unit": "g",
    },
    "fat_g": {
        "names": {"total lipid fat", "total fat", "fat"},
        "unit": "g",
    },
    "fiber_g": {
        "names": {"fiber total dietary", "total dietary fiber"},
        "unit": "g",
    },
    "sugar_g": {
        "names": {
            "sugars total including nlea", "total sugars",
            "sugars total",
        },
        "unit": "g",
    },
    "calcium_mg": {
        "names": {"calcium ca", "calcium"},
        "unit": "mg",
    },
    "iron_mg": {
        "names": {"iron fe", "iron"},
        "unit": "mg",
    },
    "sodium_mg": {
        "names": {"sodium na", "sodium"},
        "unit": "mg",
    },
    "vitamin_c_mg": {
        "names": {
            "vitamin c total ascorbic acid", "vitamin c",
        },
        "unit": "mg",
    },
}


# ============================================================
# ERRORS AND API REQUESTS
# ============================================================

class USDAConnectionError(RuntimeError):
    """USDA could not be reached or returned an invalid response."""


def _api_key() -> str:
    key = str(USDA_API_KEY or "").strip()
    if not key:
        raise RuntimeError(
            "USDA_API_KEY is missing. Check your local .env configuration."
        )
    return key


def _base_url() -> str:
    return str(USDA_BASE_URL).rstrip("/")


def _request_json(
    url: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    """Request USDA JSON with retries for transient connection errors."""
    last_error = None

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(
                url,
                params=params,
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()

            payload = response.json()
            if not isinstance(payload, dict):
                raise USDAConnectionError(
                    "USDA returned an invalid response."
                )

            return payload

        except requests.RequestException as exc:
            last_error = exc

            status = (
                exc.response.status_code
                if isinstance(exc, requests.HTTPError)
                and exc.response is not None
                else None
            )

            retryable_status = status in {429, 500, 502, 503, 504}
            retryable_connection = isinstance(
                exc,
                (requests.ConnectionError, requests.Timeout),
            )

            if not (retryable_connection or retryable_status):
                raise USDAConnectionError(
                    f"USDA request failed (HTTP {status}): {exc}"
                ) from exc

            if attempt < MAX_RETRIES - 1:
                delay = 1 * (2 ** attempt)
                logger.warning(
                    "USDA request failed (attempt %s/%s). "
                    "Retrying in %s seconds: %s",
                    attempt + 1,
                    MAX_RETRIES,
                    delay,
                    exc,
                )
                time.sleep(delay)

        except ValueError as exc:
            raise USDAConnectionError(
                "USDA returned invalid JSON."
            ) from exc

    raise USDAConnectionError(
        "Could not connect to USDA after "
        f"{MAX_RETRIES} attempts. Check your internet/DNS "
        f"connection and try again. Last error: {last_error}"
    ) from last_error


def search_food(
    food_name: str,
    page_size: int = 50,
) -> list[dict[str, Any]]:
    """Search USDA FoodData Central dynamically."""
    if not normalize_text(food_name):
        return []

    payload = _request_json(
        f"{_base_url()}/foods/search",
        {
            "api_key": _api_key(),
            "query": str(food_name).strip(),
            "pageSize": max(1, min(int(page_size), 200)),
            "pageNumber": 1,
        },
    )

    foods = payload.get("foods", [])
    return foods if isinstance(foods, list) else []


def get_food_details(fdc_id: int) -> dict[str, Any]:
    """Retrieve a complete USDA food record."""
    return _request_json(
        f"{_base_url()}/food/{int(fdc_id)}",
        {"api_key": _api_key()},
    )


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_text(text: Any) -> str:
    if text is None:
        return ""

    value = str(text).lower().strip()
    value = value.replace("&", " and ")
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def singularize_token(token: str) -> str:
    token = normalize_text(token)

    if len(token) <= 3:
        return token

    irregular = {
        "bananas": "banana",
        "tomatoes": "tomato",
        "potatoes": "potato",
        "berries": "berry",
        "strawberries": "strawberry",
        "blueberries": "blueberry",
        "cherries": "cherry",
        "leaves": "leaf",
        "loaves": "loaf",
        "teeth": "tooth",
        "feet": "foot",
        "children": "child",
        "eggs": "egg",
        "wings": "wing",
        "peanuts": "peanut",
        "carrots": "carrot",
        "apples": "apple",
        "oranges": "orange",
        "grapes": "grape",
        "mangoes": "mango",
        "mangos": "mango",
        "stews": "stew",
        "chickens": "chicken",
        "crackers": "cracker",
        "chips": "chip",
    }

    if token in irregular:
        return irregular[token]

    if token.endswith("ies") and len(token) > 4:
        return token[:-3] + "y"

    if token.endswith("oes") and len(token) > 4:
        return token[:-2]

    if token.endswith("s") and not token.endswith(
        ("ss", "us", "is")
    ):
        return token[:-1]

    return token


def tokenize(text: Any) -> list[str]:
    return [
        singularize_token(word)
        for word in normalize_text(text).split()
        if word
    ]


def _preparation_tokens() -> set[str]:
    return {singularize_token(word) for word in PREPARATION_WORDS}


def _core_query(query: str) -> str:
    tokens = normalize_text(query).split()
    remaining = [
        token for token in tokens
        if token not in PREPARATION_WORDS
    ]
    return " ".join(remaining) if remaining else normalize_text(query)


def _normalized_term_set(terms: set[str]) -> set[str]:
    return {
        token
        for term in terms
        for token in tokenize(term)
    }


# ============================================================
# FOOD CLASSIFICATION
# ============================================================

def is_prepared_food(description: str) -> bool:
    words = set(normalize_text(description).split())
    return bool(words & PREPARATION_WORDS)


def is_combination_food(description: str) -> bool:
    normalized = normalize_text(description)
    return any(
        normalize_text(term) in normalized
        for term in COMBINATION_TERMS
    )


def is_specific_food_variant(
    description: str,
    query: str,
) -> bool:
    query_tokens = set(tokenize(query))
    description_tokens = set(tokenize(description))

    if not query_tokens or not description_tokens:
        return False

    extra_words = description_tokens - query_tokens
    variant_terms = _normalized_term_set(FOOD_VARIANT_TERMS)

    explicitly_requested = query_tokens & variant_terms
    unrequested_variants = extra_words & variant_terms
    unrequested_variants -= explicitly_requested

    if "skin" in unrequested_variants:
        if "meat" in description_tokens:
            unrequested_variants.discard("skin")

    return bool(unrequested_variants)


def is_simple_food_match(
    query: str,
    description: str,
) -> bool:
    query_core = set(tokenize(_core_query(query)))
    description_tokens = set(tokenize(description))
    return bool(query_core) and query_core.issubset(description_tokens)


# ============================================================
# MATCH SCORING AND RANKING
# ============================================================

def score_food_result(
    query: str,
    food: dict[str, Any],
) -> float:
    description = str(food.get("description") or "")
    data_type = str(
        food.get("dataType") or food.get("data_type") or ""
    ).strip().lower()

    query_normalized = normalize_text(query)
    description_normalized = normalize_text(description)
    query_tokens = set(tokenize(query_normalized))
    description_tokens = set(tokenize(description_normalized))

    if not query_tokens or not description_tokens:
        return 0.0

    query_core = set(tokenize(_core_query(query_normalized)))
    if not query_core:
        query_core = query_tokens

    if not query_core.issubset(description_tokens):
        return 0.0

    # Reject clearly different forms of the requested food.
    # Example: boiled rice must not match rice crackers.
    query_words = set(query_normalized.split())
    description_words = set(description_normalized.split())

    if "rice" in query_words:
        if description_words & {
            "cracker", "crackers", "chips", "chip",
        }:
            return 0.0

    if is_specific_food_variant(description, query):
        return 0.0

    if is_combination_food(description):
        requested_combination = any(
            normalize_text(term) in query_normalized
            for term in COMBINATION_TERMS
        )
        if not requested_combination:
            return 0.0

    score = 75.0

    if query_normalized == description_normalized:
        score += 15.0
    else:
        preparation_words = _preparation_tokens()
        query_identity = query_tokens - preparation_words
        description_identity = description_tokens - preparation_words
        description_identity -= _normalized_term_set(GENERIC_WORDS)

        if query_identity == description_identity:
            score += 12.0
        else:
            score += 8.0

    priority = DATA_TYPE_PRIORITY.get(data_type, 65)
    score += (priority - 65) * 0.25

    query_preparation = (
        set(query_normalized.split()) & PREPARATION_WORDS
    )
    description_preparation = (
        set(description_normalized.split()) & PREPARATION_WORDS
    )

    if query_preparation:
        if query_preparation.issubset(description_preparation):
            score += 5.0
        else:
            score -= 8.0
    else:
        non_neutral = PREPARATION_WORDS - {
            "raw", "cooked", "frozen",
        }
        if description_preparation & non_neutral:
            score -= 6.0

    extra_words = description_tokens - query_tokens
    extra_words -= _preparation_tokens()
    extra_words -= _normalized_term_set(GENERIC_WORDS)

    if len(query_core) == 1:
        cut_terms = {
            "breast", "thigh", "wing", "drumstick",
            "leg", "tender", "tenderloin", "quarter",
            "half", "back",
        }
        extra_words -= cut_terms

        if description_tokens & cut_terms:
            score -= 10.0

    if extra_words:
        score -= min(35.0, 4.0 * len(extra_words))

    if data_type == "branded":
        score -= 25.0
        if description_tokens.issubset(query_tokens):
            score -= 10.0

    return round(max(0.0, min(100.0, score)), 2)


def find_best_food(
    food_name: str,
    page_size: int = 50,
) -> list[dict[str, Any]]:
    """Search and rank USDA results; raise if every request fails."""
    original_query = normalize_text(food_name)

    if not original_query:
        return []

    core_query = normalize_text(_core_query(original_query))
    query_variants = []

    for variant in (original_query, core_query):
        if variant and variant not in query_variants:
            query_variants.append(variant)

    unique_foods: dict[int, dict[str, Any]] = {}
    successful_searches = 0
    search_errors = []

    for variant in query_variants:
        try:
            results = search_food(variant, page_size=page_size)
            successful_searches += 1

        except (USDAConnectionError, RuntimeError, ValueError) as exc:
            logger.warning("USDA search failed for %r: %s", variant, exc)
            search_errors.append(str(exc))
            continue

        for food in results:
            fdc_id = food.get("fdcId", food.get("fdc_id"))
            if fdc_id is None:
                continue

            try:
                numeric_id = int(fdc_id)
            except (TypeError, ValueError):
                continue

            unique_foods.setdefault(numeric_id, food)

    if successful_searches == 0 and search_errors:
        raise USDAConnectionError(
            "NutriBot could not reach USDA after retrying. "
            "The food has not been confirmed missing. "
            "Check your internet/DNS connection and try again. "
            + " | ".join(search_errors)
        )

    ranked = []

    for fdc_id, food in unique_foods.items():
        score = score_food_result(original_query, food)

        if score < MINIMUM_MATCH_SCORE:
            continue

        item = dict(food)
        item["fdc_id"] = fdc_id
        item["description"] = str(food.get("description") or "")
        item["data_type"] = str(
            food.get("dataType") or food.get("data_type") or ""
        )
        item["score"] = score
        item["data_type_priority"] = DATA_TYPE_PRIORITY.get(
            item["data_type"].strip().lower(), 65
        )
        ranked.append(item)

    ranked.sort(
        key=lambda item: (
            item["score"],
            item["data_type_priority"],
            -len(item["description"]),
        ),
        reverse=True,
    )

    return ranked


# ============================================================
# NUTRIENT EXTRACTION AND UNIT CONVERSION
# ============================================================

def normalize_unit(unit: Any) -> str:
    value = str(unit or "").strip().lower()

    aliases = {
        "kilocalories": "kcal",
        "kilocalorie": "kcal",
        "calories": "kcal",
        "calorie": "cal",
        "grams": "g",
        "gram": "g",
        "milligrams": "mg",
        "milligram": "mg",
        "micrograms": "µg",
        "microgram": "µg",
        "ug": "µg",
        "mcg": "µg",
        "μg": "µg",
        "milliliters": "ml",
        "milliliter": "ml",
        "kilojoule": "kj",
        "kilojoules": "kj",
    }
    return aliases.get(value, value)


def convert_energy_to_kcal(value: float, unit: Any) -> float:
    normalized_unit = normalize_unit(unit)

    if normalized_unit == "kj":
        return value / 4.184
    if normalized_unit == "cal":
        return value / 1000.0
    return value


def convert_nutrient_value(
    value: Any,
    unit: Any,
    target_unit: str,
) -> Optional[float]:
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return None

    if numeric_value < 0:
        return None

    source = normalize_unit(unit)
    target = normalize_unit(target_unit)

    if source == target:
        return numeric_value

    conversions = {
        ("g", "mg"): 1000.0,
        ("mg", "g"): 0.001,
        ("mg", "µg"): 1000.0,
        ("µg", "mg"): 0.001,
        ("g", "µg"): 1_000_000.0,
        ("µg", "g"): 0.000001,
    }

    factor = conversions.get((source, target))
    return numeric_value * factor if factor is not None else None


def extract_nutrients(
    food_data: dict[str, Any],
) -> dict[str, float]:
    """
    Extract nutrients from a complete USDA food-detail response.

    Recognizes Energy, Energy (Atwater General Factors), and other
    Energy variants. Direct Energy is preferred over alternate
    energy calculations when both are present.
    """
    result = {key: 0.0 for key in NUTRIENT_MAP}
    nutrients = food_data.get("foodNutrients", [])

    if not isinstance(nutrients, list):
        return result

    energy_candidates = []

    for nutrient in nutrients:
        if not isinstance(nutrient, dict):
            continue

        nutrient_info = nutrient.get("nutrient", {})
        if not isinstance(nutrient_info, dict):
            nutrient_info = {}

        name = normalize_text(
            nutrient_info.get("name")
            or nutrient.get("nutrientName")
            or nutrient.get("name")
            or ""
        )

        unit = (
            nutrient_info.get("unitName")
            or nutrient.get("unitName")
            or nutrient.get("unit")
            or ""
        )

        value = nutrient.get("amount")
        if value is None:
            value = nutrient.get("value")

        if value is None or not name:
            continue

        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            continue

        if numeric_value < 0:
            continue

        is_energy = (
            name == "energy"
            or name.startswith("energy ")
            or "calorie" in name
        )

        if is_energy:
            normalized_unit = normalize_unit(unit)

            if normalized_unit == "kj":
                kcal = numeric_value / 4.184
            elif normalized_unit == "kcal":
                kcal = numeric_value
            elif normalized_unit == "cal":
                kcal = numeric_value / 1000.0
            else:
                continue

            priority = 2 if name == "energy" else 1
            energy_candidates.append((priority, kcal))
            continue

        for output_key, specification in NUTRIENT_MAP.items():
            if output_key == "calories":
                continue

            accepted_names = {
                normalize_text(item)
                for item in specification["names"]
            }

            if name not in accepted_names:
                continue

            converted = convert_nutrient_value(
                numeric_value,
                unit,
                specification["unit"],
            )

            if converted is not None:
                result[output_key] = round(converted, 4)
            break

    if energy_candidates:
        energy_candidates.sort(
            key=lambda candidate: candidate[0],
            reverse=True,
        )
        result["calories"] = round(energy_candidates[0][1], 4)

    return result


def has_sufficient_nutrition(
    nutrients: dict[str, Any],
) -> bool:
    if not isinstance(nutrients, dict):
        return False

    return any(
        float(nutrients.get(key) or 0) > 0
        for key in (
            "calories",
            "protein_g",
            "carbohydrates_g",
            "fat_g",
        )
    )


# ============================================================
# SERVING AND PORTION INFORMATION
# ============================================================

def extract_serving_information(
    food_data: dict[str, Any],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    serving_size = food_data.get("servingSize")
    serving_unit = food_data.get("servingSizeUnit")

    if serving_size is not None:
        try:
            result["serving_size"] = float(serving_size)
        except (TypeError, ValueError):
            pass

    if serving_unit:
        result["serving_unit"] = str(serving_unit)

    return result


def extract_food_portions(
    food_data: dict[str, Any],
) -> list[dict[str, Any]]:
    portions = food_data.get("foodPortions", [])
    if not isinstance(portions, list):
        return []

    result = []

    for portion in portions:
        if not isinstance(portion, dict):
            continue

        try:
            gram_weight = float(portion.get("gramWeight"))
        except (TypeError, ValueError):
            continue

        if gram_weight <= 0:
            continue

        measure_unit = portion.get("measureUnit", {})
        if not isinstance(measure_unit, dict):
            measure_unit = {}

        result.append({
            "gram_weight": gram_weight,
            "description": str(
                portion.get("portionDescription")
                or portion.get("modifier")
                or measure_unit.get("name")
                or "serving"
            ),
            "amount": portion.get("amount"),
        })

    return result


def get_nutrition_basis(
    food_data: dict[str, Any],
) -> dict[str, Any]:
    return {
        "basis_grams": 100.0,
        "basis_description": "per 100 g",
        "serving_information": extract_serving_information(food_data),
        "portions": extract_food_portions(food_data),
    }


# ============================================================
# QUANTITY CALCULATIONS
# ============================================================

def calculate_nutrition_for_grams(
    nutrients: dict[str, Any],
    grams: float,
) -> dict[str, float]:
    try:
        grams = float(grams)
    except (TypeError, ValueError) as exc:
        raise ValueError("Quantity must be a valid number.") from exc

    if grams < 0:
        raise ValueError("Quantity cannot be negative.")

    factor = grams / 100.0
    result = {}

    for key, value in nutrients.items():
        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            continue

        result[key] = round(numeric_value * factor, 4)

    return result


def calculate_nutrition_for_serving(
    nutrients: dict[str, Any],
    portions: list[dict[str, Any]],
    serving_count: float = 1.0,
    serving_name: Optional[str] = None,
) -> dict[str, Any]:
    try:
        serving_count = float(serving_count)
    except (TypeError, ValueError) as exc:
        raise ValueError("Serving count must be a valid number.") from exc

    if serving_count < 0:
        raise ValueError("Serving count cannot be negative.")

    if not portions:
        raise ValueError(
            "USDA does not provide serving-weight information "
            "for this food. Please specify the quantity in grams."
        )

    selected_portion = None

    if serving_name:
        requested = normalize_text(serving_name)
        for portion in portions:
            description = normalize_text(
                portion.get("description", "")
            )
            if requested in description or description in requested:
                selected_portion = portion
                break

    if selected_portion is None:
        selected_portion = portions[0]

    grams = float(selected_portion["gram_weight"]) * serving_count

    return {
        "nutrition": calculate_nutrition_for_grams(nutrients, grams),
        "grams": round(grams, 4),
        "serving_count": serving_count,
        "serving_description": selected_portion.get(
            "description", "serving"
        ),
    }


# ============================================================
# COMPLETE FOOD LOOKUP
# ============================================================

def get_food_with_nutrition(
    food_name: str,
    page_size: int = 50,
) -> Optional[dict[str, Any]]:
    """Find a USDA record and retrieve its nutrition information."""
    matches = find_best_food(food_name, page_size=page_size)

    if not matches:
        return None

    detail_errors = []

    for match in matches:
        try:
            details = get_food_details(match["fdc_id"])
        except (USDAConnectionError, RuntimeError, ValueError) as exc:
            logger.warning(
                "Could not retrieve USDA details for %s: %s",
                match.get("description"),
                exc,
            )
            detail_errors.append(str(exc))
            continue

        nutrients = extract_nutrients(details)

        if not has_sufficient_nutrition(nutrients):
            continue

        portions = extract_food_portions(details)
        match_score = match["score"]

        return {
            "fdc_id": match["fdc_id"],
            "description": details.get(
                "description", match["description"]
            ),
            "data_type": details.get(
                "dataType", match["data_type"]
            ),
            "score": match_score,
            "match_score": match_score,
            "nutrition": nutrients,
            "nutrients": nutrients,
            "food_data": details,
            "serving_information": extract_serving_information(details),
            "portions": portions,
            "nutrition_basis": get_nutrition_basis(details),
        }

    if detail_errors:
        raise USDAConnectionError(
            "USDA search succeeded, but food details could not be "
            "retrieved. Please retry. " + " | ".join(detail_errors)
        )

    return None


def get_first_food(
    food_name: str,
) -> Optional[dict[str, Any]]:
    matches = find_best_food(food_name, page_size=50)
    return matches[0] if matches else None


# ============================================================
# MANUAL SEARCH TEST
# ============================================================

if __name__ == "__main__":
    test_queries = [
        "boiled egg",
        "banana",
        "chicken",
        "chicken wings",
        "boiled rice",
    ]

    for query in test_queries:
        print(f"\nQUERY: {query}")

        try:
            matches = find_best_food(query)

            if not matches:
                print("No reliable matches found.")
                continue

            for item in matches[:5]:
                print(
                    item["description"],
                    "|", item["data_type"],
                    "|", item["score"],
                    "| FDC:", item["fdc_id"],
                )

        except USDAConnectionError as exc:
            print(f"USDA CONNECTION ERROR: {exc}")
        except Exception as exc:
            print(f"Lookup failed: {exc}")