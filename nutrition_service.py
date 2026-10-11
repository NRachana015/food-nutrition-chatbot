
"""
NutriBot - USDA FoodData Central Nutrition Service

Provides dynamic USDA food search, food matching, nutrition extraction,
per-100-gram nutrition values, and quantity scaling.
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
    "grilled", "steamed", "poached", "sauteed", "broiled",
    "smoked", "dried", "toasted", "scrambled", "microwaved",
    "braised", "stewed", "barbecued", "barbequed", "pickled",
    "frozen",
}

COMBINATION_TERMS = {
    "casserole", "sandwich", "salad", "pizza", "burger",
    "hamburger", "soup", "stew", "curry", "lasagna",
    "pasta dish", "fried rice", "burrito", "taco", "pie",
    "cake", "cookie", "smoothie", "shake", "mixed dish",
    "chicken kiev", "orange chicken", "almond chicken",
    "sesame chicken", "fajita", "nachos", "tamale",
    "barbecue chicken", "barbeque chicken", "taquito",
    "enchilada", "quesadilla", "biryani", "chimichanga",
    "kung pao", "general tso", "teriyaki",
}

GENERIC_WORDS = {
    "whole", "fresh", "raw", "cooked", "uncooked", "meat",
    "flesh", "without", "with", "skin", "boneless", "bone",
    "lean", "only", "including", "excluding", "piece", "pieces",
    "large", "small", "medium", "ripe", "unripe", "common",
    "standard", "food", "foods", "edible", "portion", "product",
    "products", "broiler", "broilers", "fryer", "fryers",
    "young", "roasting", "stewing", "grade", "type", "style",
    "commercial", "or", "and",
}

FOOD_VARIANT_TERMS = {
    "fat", "feet", "foot", "skin", "liver", "heart", "gizzard",
    "kidney", "intestine", "bone", "bones", "broth", "stock",
    "extract", "powder", "flour", "juice", "syrup", "candy",
    "chips", "snack", "spread", "sauce", "supplement", "formula",
    "meatless", "imitation", "substitute", "sausage", "frankfurter",
    "nugget", "nuggets", "patty", "patties", "jerky", "baby",
    "dehydrated", "concentrate", "cracker", "crackers", "tail",
    "tails", "ground", "back", "backs", "neck", "necks", "wing",
    "wings", "breast", "thigh", "thighs", "drumstick", "drumsticks",
    "leg", "legs", "tenderloin", "breaded", "battered", "fajita",
    "enchilada", "quesadilla", "biryani", "chimichanga", "taquito",
    "empanada", "cornbread", "gravy", "sesame", "almond", "orange",
    "teriyaki", "kung", "tso", "barbecue", "barbeque", "curry",
}

NUTRIENT_NAMES = {
    "calories": {
        "energy", "energy kcal", "calories",
    },
    "protein_g": {
        "protein",
    },
    "carbohydrates_g": {
        "carbohydrate by difference", "carbohydrates",
        "carbohydrate total", "total carbohydrate",
    },
    "fat_g": {
        "total lipid fat", "total fat", "fat",
    },
    "fiber_g": {
        "fiber total dietary", "total dietary fiber",
    },
    "sugar_g": {
        "sugars total including nlea", "total sugars",
        "sugars total",
    },
    "calcium_mg": {
        "calcium ca", "calcium",
    },
    "iron_mg": {
        "iron fe", "iron",
    },
    "sodium_mg": {
        "sodium na", "sodium",
    },
    "vitamin_c_mg": {
        "vitamin c total ascorbic acid", "vitamin c",
    },
}


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_text(text: Any) -> str:
    """Normalize text for consistent matching."""
    if text is None:
        return ""
    text = str(text).lower().strip()
    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def singularize_token(token: str) -> str:
    """Convert common plural words to singular form."""
    token = normalize_text(token)

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
        "chickens": "chicken",
        "crackers": "cracker",
        "chips": "chip",
    }

    if token in irregular:
        return irregular[token]

    if len(token) > 4 and token.endswith("ies"):
        return token[:-3] + "y"

    if len(token) > 4 and token.endswith("oes"):
        return token[:-2]

    if (
        len(token) > 3
        and token.endswith("s")
        and not token.endswith(("ss", "us", "is"))
    ):
        return token[:-1]

    return token


def tokenize(text: Any) -> list[str]:
    """Return normalized, singularized tokens."""
    return [
        singularize_token(word)
        for word in normalize_text(text).split()
        if word
    ]


def _core_query(query: str) -> str:
    """Remove preparation words to create an additional search query."""
    tokens = normalize_text(query).split()
    remaining = [
        token for token in tokens
        if token not in PREPARATION_WORDS
    ]
    return " ".join(remaining) if remaining else normalize_text(query)


def _term_tokens(terms: set[str]) -> set[str]:
    return {
        token
        for term in terms
        for token in tokenize(term)
    }


# ============================================================
# USDA API CONNECTION
# ============================================================

class USDAConnectionError(RuntimeError):
    """Raised when USDA data cannot be retrieved."""


def _get_api_key() -> str:
    key = str(USDA_API_KEY or "").strip()
    if not key:
        raise RuntimeError(
            "USDA API key is missing. Check your configuration."
        )
    return key


def _get_base_url() -> str:
    return str(USDA_BASE_URL).rstrip("/")


def _request_json(
    url: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    """Make a USDA request with retries for temporary failures."""
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
                    "USDA returned an unexpected response."
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

            retryable = (
                isinstance(
                    exc,
                    (requests.ConnectionError, requests.Timeout),
                )
                or status in {429, 500, 502, 503, 504}
            )

            if not retryable:
                raise USDAConnectionError(
                    f"USDA request failed: {exc}"
                ) from exc

            if attempt < MAX_RETRIES - 1:
                delay = 2 ** attempt
                logger.warning(
                    "USDA request failed; retrying in %s seconds.",
                    delay,
                )
                time.sleep(delay)

        except ValueError as exc:
            raise USDAConnectionError(
                "USDA returned invalid JSON."
            ) from exc

    raise USDAConnectionError(
        "Could not retrieve USDA data after retries. "
        "Check your internet connection or DNS settings. "
        f"Last error: {last_error}"
    ) from last_error


def search_food(
    food_name: str,
    page_size: int = 50,
) -> list[dict[str, Any]]:
    """Search the live USDA FoodData Central database."""
    if not normalize_text(food_name):
        return []

    payload = _request_json(
        f"{_get_base_url()}/foods/search",
        {
            "api_key": _get_api_key(),
            "query": str(food_name).strip(),
            "pageSize": max(1, min(int(page_size), 200)),
            "pageNumber": 1,
        },
    )

    foods = payload.get("foods", [])
    return foods if isinstance(foods, list) else []


def get_food_details(fdc_id: int) -> dict[str, Any]:
    """Retrieve the full nutrition record for a USDA food ID."""
    return _request_json(
        f"{_get_base_url()}/food/{int(fdc_id)}",
        {"api_key": _get_api_key()},
    )


# ============================================================
# FOOD CLASSIFICATION
# ============================================================

def is_combination_food(description: str) -> bool:
    """Identify foods that are combinations or prepared dishes."""
    normalized = normalize_text(description)
    return any(
        normalize_text(term) in normalized
        for term in COMBINATION_TERMS
    )


def is_specific_food_variant(
    description: str,
    query: str,
) -> bool:
    """Reject unrequested food cuts and variants."""
    query_tokens = set(tokenize(query))
    description_tokens = set(tokenize(description))

    if not query_tokens or not description_tokens:
        return False

    extra_tokens = description_tokens - query_tokens
    variant_tokens = _term_tokens(FOOD_VARIANT_TERMS)
    unrequested_variants = extra_tokens & variant_tokens

    if (
        "skin" in unrequested_variants
        and "meat" in description_tokens
    ):
        unrequested_variants.discard("skin")

    return bool(unrequested_variants)


def is_simple_food_match(
    query: str,
    description: str,
) -> bool:
    """Check whether the query's core words appear in the description."""
    core_tokens = set(tokenize(_core_query(query)))
    description_tokens = set(tokenize(description))
    return bool(core_tokens) and core_tokens.issubset(description_tokens)


# ============================================================
# FOOD MATCH SCORING
# ============================================================

def score_food_result(
    query: str,
    food: dict[str, Any],
) -> float:
    """Score a USDA food result against the user's query."""
    description = str(food.get("description") or "")
    data_type = str(
        food.get("dataType") or food.get("data_type") or ""
    ).strip().lower()

    normalized_query = normalize_text(query)
    normalized_description = normalize_text(description)

    query_tokens = set(tokenize(normalized_query))
    description_tokens = set(tokenize(normalized_description))

    if not query_tokens or not description_tokens:
        return 0.0

    core_tokens = set(tokenize(_core_query(normalized_query)))
    if not core_tokens:
        core_tokens = query_tokens

    if not core_tokens.issubset(description_tokens):
        return 0.0

    if is_specific_food_variant(description, query):
        return 0.0

    if is_combination_food(description):
        requested = any(
            normalize_text(term) in normalized_query
            for term in COMBINATION_TERMS
        )
        if not requested:
            return 0.0

    score = 75.0

    if normalized_query == normalized_description:
        score += 15.0
    else:
        generic_tokens = _term_tokens(GENERIC_WORDS)
        preparation_tokens = _term_tokens(PREPARATION_WORDS)

        query_identity = query_tokens - preparation_tokens
        description_identity = (
            description_tokens
            - preparation_tokens
            - generic_tokens
        )

        if query_identity == description_identity:
            score += 12.0
        else:
            score += 8.0

    priority = DATA_TYPE_PRIORITY.get(data_type, 65)
    score += (priority - 65) * 0.25

    query_preparations = (
        set(normalized_query.split()) & PREPARATION_WORDS
    )
    description_preparations = (
        set(normalized_description.split()) & PREPARATION_WORDS
    )

    if query_preparations:
        if query_preparations.issubset(description_preparations):
            score += 5.0
        else:
            score -= 8.0
    elif description_preparations & (
        PREPARATION_WORDS - {"raw", "cooked", "frozen"}
    ):
        score -= 6.0

    extra_tokens = description_tokens - query_tokens
    extra_tokens -= _term_tokens(GENERIC_WORDS)
    extra_tokens -= _term_tokens(PREPARATION_WORDS)

    if len(core_tokens) == 1:
        cuts = {
            "breast", "thigh", "wing", "drumstick", "leg",
            "tender", "tenderloin", "quarter", "half", "back",
        }
        extra_tokens -= cuts
        if description_tokens & cuts:
            score -= 10.0

    score -= min(35.0, 4.0 * len(extra_tokens))

    if data_type == "branded":
        score -= 25.0

    return round(max(0.0, min(100.0, score)), 2)


# ============================================================
# USDA SEARCH AND RANKING
# ============================================================

def find_best_food(
    food_name: str,
    page_size: int = 50,
) -> list[dict[str, Any]]:
    """Search, deduplicate, score, and rank USDA food records."""
    original_query = normalize_text(food_name)

    if not original_query:
        return []

    core_query = normalize_text(_core_query(original_query))
    query_variants = []

    for variant in (original_query, core_query):
        if variant and variant not in query_variants:
            query_variants.append(variant)

    generic_chicken = original_query in {
        "chicken", "chicken meat",
    }

    if generic_chicken:
        for variant in (
            "chicken meat raw",
            "broiler chicken raw",
        ):
            if variant not in query_variants:
                query_variants.append(variant)

    unique_foods: dict[int, dict[str, Any]] = {}
    successful_searches = 0
    errors = []

    for variant in query_variants:
        try:
            foods = search_food(variant, page_size=page_size)
            successful_searches += 1
        except (USDAConnectionError, RuntimeError, ValueError) as exc:
            logger.warning(
                "Search failed for %r: %s", variant, exc
            )
            errors.append(str(exc))
            continue

        for food in foods:
            fdc_id = food.get("fdcId", food.get("fdc_id"))
            if fdc_id is None:
                continue

            try:
                fdc_id = int(fdc_id)
            except (TypeError, ValueError):
                continue

            unique_foods.setdefault(fdc_id, food)

    if successful_searches == 0 and errors:
        raise USDAConnectionError(
            "Could not reach USDA FoodData Central. "
            "The food has not been confirmed missing. "
            "Check your internet connection and retry. "
            + " | ".join(errors)
        )

    ranked = []

    for fdc_id, food in unique_foods.items():
        description = str(food.get("description") or "")
        score = score_food_result(original_query, food)

        if generic_chicken:
            tokens = set(tokenize(description))

            forbidden_parts = {
                "tail", "back", "neck", "foot", "wing", "breast",
                "thigh", "drumstick", "leg", "ground", "liver",
                "heart", "gizzard", "sausage", "nugget", "tender",
                "tenderloin", "kiev", "fajita", "enchilada",
                "quesadilla", "biryani", "chimichanga", "taquito",
                "empanada", "cornbread", "gravy", "sesame",
                "almond", "orange", "teriyaki", "curry", "spread",
                "frankfurter", "meatless", "soup", "stew", "salad",
                "sandwich", "pizza", "burger", "casserole",
            }

            generic_record = (
                "chicken" in tokens
                and not (tokens & forbidden_parts)
                and not is_combination_food(description)
            )

            if generic_record and (
                "raw" in tokens
                or "roasting" in tokens
                or "broiler" in tokens
                or "fryer" in tokens
                or "stewing" in tokens
            ):
                descriptive_scores = [
                    score_food_result("chicken meat raw", food),
                    score_food_result("broiler chicken raw", food),
                ]
                score = max([score] + descriptive_scores)

        if score < MINIMUM_MATCH_SCORE:
            continue

        item = dict(food)
        item["fdc_id"] = fdc_id
        item["description"] = description
        item["data_type"] = str(
            food.get("dataType") or food.get("data_type") or ""
        )
        item["score"] = round(score, 2)
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
# NUTRIENT EXTRACTION
# ============================================================

def _normalize_unit(unit: Any) -> str:
    value = str(unit or "").strip().lower()

    aliases = {
        "kilocalories": "kcal",
        "kilocalorie": "kcal",
        "calories": "cal",
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
        "kilojoule": "kj",
        "kilojoules": "kj",
    }

    return aliases.get(value, value)


def _convert_value(
    value: float,
    source_unit: str,
    target_unit: str,
) -> Optional[float]:
    source = _normalize_unit(source_unit)
    target = _normalize_unit(target_unit)

    if source == target:
        return value

    factors = {
        ("g", "mg"): 1000.0,
        ("mg", "g"): 0.001,
        ("mg", "µg"): 1000.0,
        ("µg", "mg"): 0.001,
        ("g", "µg"): 1_000_000.0,
        ("µg", "g"): 0.000001,
    }

    factor = factors.get((source, target))
    if factor is None:
        return None

    return value * factor


def extract_nutrients(
    food_data: dict[str, Any],
) -> dict[str, float]:
    """Extract supported nutrients from a USDA food-detail response."""
    result = {key: 0.0 for key in NUTRIENT_NAMES}
    nutrients = food_data.get("foodNutrients", [])

    if not isinstance(nutrients, list):
        return result

    energy_candidates = []

    for item in nutrients:
        if not isinstance(item, dict):
            continue

        nutrient_info = item.get("nutrient", {})
        if not isinstance(nutrient_info, dict):
            nutrient_info = {}

        name = normalize_text(
            nutrient_info.get("name")
            or item.get("nutrientName")
            or item.get("name")
            or ""
        )

        unit = (
            nutrient_info.get("unitName")
            or item.get("unitName")
            or item.get("unit")
            or ""
        )

        value = item.get("amount")
        if value is None:
            value = item.get("value")

        try:
            value = float(value)
        except (TypeError, ValueError):
            continue

        if value < 0:
            continue

        if name.startswith("energy") or "calorie" in name:
            normalized_unit = _normalize_unit(unit)

            if normalized_unit == "kj":
                kcal = value / 4.184
            elif normalized_unit == "kcal":
                kcal = value
            elif normalized_unit == "cal":
                kcal = value / 1000.0
            else:
                continue

            priority = 2 if name == "energy" else 1
            energy_candidates.append((priority, kcal))
            continue

        for key, accepted_names in NUTRIENT_NAMES.items():
            if key == "calories":
                continue

            normalized_names = {
                normalize_text(accepted)
                for accepted in accepted_names
            }

            if name not in normalized_names:
                continue

            target_unit = (
                "g" if key.endswith("_g")
                else "mg"
            )

            converted = _convert_value(
                value,
                str(unit),
                target_unit,
            )

            if converted is not None:
                result[key] = round(converted, 4)
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
    """Check whether the record contains useful macronutrient data."""
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
# SERVING INFORMATION
# ============================================================

def extract_serving_information(
    food_data: dict[str, Any],
) -> dict[str, Any]:
    """Extract USDA serving-size metadata."""
    result = {}

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
    """Extract portion weights where USDA provides them."""
    portions = food_data.get("foodPortions", [])

    if not isinstance(portions, list):
        return []

    result = []

    for portion in portions:
        if not isinstance(portion, dict):
            continue

        try:
            grams = float(portion.get("gramWeight"))
        except (TypeError, ValueError):
            continue

        if grams <= 0:
            continue

        measure_unit = portion.get("measureUnit", {})
        if not isinstance(measure_unit, dict):
            measure_unit = {}

        result.append({
            "gram_weight": grams,
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
    """Describe the reference quantity used by USDA."""
    return {
        "basis_grams": 100.0,
        "basis_description": "per 100 g",
        "serving_information": extract_serving_information(food_data),
        "portions": extract_food_portions(food_data),
    }


# ============================================================
# NUTRITION SCALING
# ============================================================

def calculate_nutrition_for_grams(
    nutrients: dict[str, Any],
    grams: float,
) -> dict[str, float]:
    """Scale nutrition values from 100 g to a requested quantity."""
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
            result[key] = round(float(value) * factor, 4)
        except (TypeError, ValueError):
            continue

    return result


def calculate_nutrition_for_serving(
    nutrients: dict[str, Any],
    portions: list[dict[str, Any]],
    serving_count: float = 1.0,
    serving_name: Optional[str] = None,
) -> dict[str, Any]:
    """Calculate nutrition for a USDA serving portion."""
    try:
        serving_count = float(serving_count)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "Serving count must be a valid number."
        ) from exc

    if serving_count < 0:
        raise ValueError("Serving count cannot be negative.")

    if not portions:
        raise ValueError(
            "No USDA serving weight is available. "
            "Please specify the quantity in grams."
        )

    selected = None

    if serving_name:
        requested = normalize_text(serving_name)

        for portion in portions:
            description = normalize_text(
                portion.get("description", "")
            )
            if requested in description or description in requested:
                selected = portion
                break

    if selected is None:
        selected = portions[0]

    grams = float(selected["gram_weight"]) * serving_count

    return {
        "nutrition": calculate_nutrition_for_grams(
            nutrients, grams
        ),
        "grams": round(grams, 4),
        "serving_count": serving_count,
        "serving_description": selected.get(
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
    """Find a matching food and retrieve its complete nutrition data."""
    matches = find_best_food(food_name, page_size=page_size)

    if not matches:
        return None

    errors = []

    for match in matches:
        try:
            details = get_food_details(match["fdc_id"])
        except (USDAConnectionError, RuntimeError, ValueError) as exc:
            logger.warning(
                "Could not retrieve details for %s: %s",
                match.get("description"),
                exc,
            )
            errors.append(str(exc))
            continue

        nutrients = extract_nutrients(details)

        if not has_sufficient_nutrition(nutrients):
            continue

        portions = extract_food_portions(details)

        return {
            "fdc_id": match["fdc_id"],
            "description": details.get(
                "description", match["description"]
            ),
            "data_type": details.get(
                "dataType", match["data_type"]
            ),
            "score": match["score"],
            "match_score": match["score"],
            "nutrition": nutrients,
            "nutrients": nutrients,
            "food_data": details,
            "serving_information": extract_serving_information(
                details
            ),
            "portions": portions,
            "nutrition_basis": get_nutrition_basis(details),
        }

    if errors:
        raise USDAConnectionError(
            "USDA search succeeded, but nutrition details could "
            "not be retrieved. Please try again. " + " | ".join(errors)
        )

    return None


def get_first_food(
    food_name: str,
) -> Optional[dict[str, Any]]:
    """Return the highest-ranked matching USDA search result."""
    matches = find_best_food(food_name, page_size=50)
    return matches[0] if matches else None


# ============================================================
# MANUAL TEST
# ============================================================

if __name__ == "__main__":
    queries = [
        "banana",
        "chicken",
        "chicken wings",
        "chicken breast",
        "boiled egg",
    ]

    for query in queries:
        print(f"\nQUERY: {query}")

        try:
            matches = find_best_food(query)

            if not matches:
                print("No reliable matching food found.")
                continue

            for food in matches[:5]:
                print(
                    f"Score: {food['score']} | "
                    f"Type: {food['data_type']} | "
                    f"Food: {food['description']} | "
                    f"FDC: {food['fdc_id']}"
                )

        except USDAConnectionError as exc:
            print(f"USDA connection error: {exc}")
        except Exception as exc:
            print(f"Unexpected error: {exc}")
