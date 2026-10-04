import re
from typing import Any, Dict, List, Optional

import requests

from config import USDA_API_KEY, USDA_BASE_URL


# ============================================================
# CONFIGURATION
# ============================================================

MINIMUM_MATCH_SCORE = 75.0


# ============================================================
# USDA DATA TYPE PRIORITY
# ============================================================

DATA_TYPE_PRIORITY = {
    "foundation": 100,
    "sr legacy": 90,
    "survey (fndds)": 80,
    "sub-ingredients": 60,
    "branded": 50,
    "experimental": 40,
}


# ============================================================
# FOOD MATCHING TERMS
# ============================================================

PREPARED_TERMS = {
    "baked",
    "boiled",
    "fried",
    "deep fried",
    "roasted",
    "grilled",
    "steamed",
    "sauteed",
    "sautéed",
    "cooked",
    "prepared",
    "breaded",
    "battered",
    "microwaved",
    "smoked",
    "dried",
    "dehydrated",
    "candied",
    "pickled",
    "canned",
    "frozen",
    "stewed",
    "braised",
}


COMBINATION_TERMS = {
    "salad",
    "soup",
    "stew",
    "curry",
    "sandwich",
    "pizza",
    "burger",
    "burrito",
    "wrap",
    "casserole",
    "pasta",
    "lasagna",
    "smoothie",
    "parfait",
    "dessert",
    "cake",
    "cookie",
    "cookies",
    "pie",
    "pudding",
    "sauce",
    "dressing",
    "juice",
    "nectar",
    "shake",
    "dish",
}


GENERIC_QUALIFIERS = {
    "raw",
    "fresh",
    "whole",
    "plain",
    "natural",
    "uncooked",
    "unprepared",
}


# These words describe a specific part, subtype, preparation,
# or product form rather than the generic food itself.
SPECIFIC_FOOD_TERMS = {
    "breast",
    "thigh",
    "wing",
    "leg",
    "drumstick",
    "feet",
    "foot",
    "skin",
    "back",
    "neck",
    "tail",
    "ground",
    "liver",
    "heart",
    "gizzard",
    "organ",
    "meatless",
    "spread",
    "patty",
    "nugget",
    "sausage",
    "tender",
    "tenders",
    "fillet",
    "filet",
    "steak",
    "chunks",
    "chunk",
    "strips",
    "strip",
    "minced",
    "powder",
    "flour",
    "milk",
    "cheese",
    "butter",
    "cream",
    "paste",
    "puree",
    "purée",
}


# ============================================================
# USDA API
# ============================================================

def search_food(
    food_name: str,
    page_size: int = 50,
) -> List[Dict[str, Any]]:
    """
    Search USDA FoodData Central for a food.

    The search is completely dynamic. The food does not need
    to exist in a local project dataset.
    """

    url = f"{USDA_BASE_URL}/foods/search"

    params = {
        "api_key": USDA_API_KEY,
        "query": food_name,
        "pageSize": page_size,
    }

    response = requests.get(
        url,
        params=params,
        timeout=20,
    )

    response.raise_for_status()

    data = response.json()

    return data.get(
        "foods",
        [],
    )


def get_food_details(
    fdc_id: int,
) -> Dict[str, Any]:
    """
    Retrieve complete USDA food details.
    """

    url = f"{USDA_BASE_URL}/food/{fdc_id}"

    params = {
        "api_key": USDA_API_KEY,
    }

    response = requests.get(
        url,
        params=params,
        timeout=20,
    )

    response.raise_for_status()

    return response.json()


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_text(
    text: str,
) -> str:
    """
    Normalize text for food matching.
    """

    text = str(text or "").lower()

    text = text.replace(
        "&",
        " and ",
    )

    text = re.sub(
        r"[^a-z0-9\s]",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def tokenize(
    text: str,
) -> List[str]:
    """
    Convert text into normalized tokens.
    """

    normalized = normalize_text(
        text
    )

    if not normalized:
        return []

    return normalized.split()


# ============================================================
# FOOD TYPE CHECKS
# ============================================================

def is_prepared_food(
    description: str,
) -> bool:
    """
    Detect whether a USDA description represents a prepared food.
    """

    text = normalize_text(
        description
    )

    for term in PREPARED_TERMS:

        if term in text:
            return True

    return False


def is_combination_food(
    description: str,
) -> bool:
    """
    Detect combination/dish-type USDA foods.
    """

    text = normalize_text(
        description
    )

    for term in COMBINATION_TERMS:

        if term in text:
            return True

    return False


def is_specific_food_variant(
    description: str,
    query: str,
) -> bool:
    """
    Detect whether a USDA result is a specific subtype/part
    rather than the generic food requested by the user.

    Example:

        query = chicken

        Chicken, breast
        Chicken, ground
        Chicken feet
        Chicken spread

    These are more specific than generic chicken.
    """

    query_tokens = set(
        tokenize(query)
    )

    description_tokens = set(
        tokenize(description)
    )

    extra_words = (
        description_tokens - query_tokens
    )

    return bool(
        extra_words.intersection(
            SPECIFIC_FOOD_TERMS
        )
    )


# ============================================================
# SIMPLE FOOD MATCH
# ============================================================

def is_simple_food_match(
    query: str,
    description: str,
) -> bool:
    """
    Determine whether a USDA description represents a reasonable
    simple-food candidate.
    """

    query_tokens = tokenize(
        query
    )

    description_tokens = tokenize(
        description
    )

    if not query_tokens or not description_tokens:
        return False

    if is_prepared_food(
        description
    ):
        return False

    if is_combination_food(
        description
    ):
        return False

    return True


# ============================================================
# FOOD RESULT SCORING
# ============================================================

def score_food_result(
    query: str,
    food: Dict[str, Any],
) -> float:
    """
    Score a USDA candidate.

    Higher score = better match.

    The ranking strongly prefers the generic food requested by
    the user over specific variants.

    Examples:

        chicken
        CHICKEN
            -> acceptable exact branded match

        chicken
        Chicken, raw
            -> excellent generic match

        chicken
        Chicken, breast
            -> lower score

        chicken
        Chicken spread
            -> much lower score
    """

    query = normalize_text(
        query
    )

    description = normalize_text(
        food.get(
            "description",
            "",
        )
    )

    if not query or not description:
        return 0.0

    data_type = normalize_text(
        food.get(
            "dataType",
            "",
        )
    )

    priority = DATA_TYPE_PRIORITY.get(
        data_type,
        0,
    )

    query_tokens = tokenize(
        query
    )

    description_tokens = tokenize(
        description
    )

    if not query_tokens or not description_tokens:
        return 0.0

    query_set = set(
        query_tokens
    )

    description_set = set(
        description_tokens
    )

    # --------------------------------------------------------
    # 1. EXACT DESCRIPTION
    # --------------------------------------------------------

    if description == query:

        # Exact non-branded generic food.
        if data_type != "branded":
            return round(
                100.0
                + (
                    priority / 1000
                ),
                2,
            )

        # Exact branded food is accepted, but deliberately
        # ranked below generic USDA records.
        return 75.0

    # --------------------------------------------------------
    # 2. REJECT PREPARED FOODS
    # --------------------------------------------------------

    if is_prepared_food(
        description
    ):
        return 0.0

    # --------------------------------------------------------
    # 3. REJECT COMBINATION FOODS
    # --------------------------------------------------------

    if is_combination_food(
        description
    ):
        return 0.0

    # --------------------------------------------------------
    # 4. PRIMARY FOOD-NAME MATCH
    # --------------------------------------------------------

    starts_with_query = (
        len(description_tokens)
        >= len(query_tokens)
        and description_tokens[
            :len(query_tokens)
        ]
        == query_tokens
    )

    if starts_with_query:

        extra_words = (
            description_set - query_set
        )

        # ----------------------------------------------------
        # 4A. ONLY GENERIC QUALIFIERS
        # ----------------------------------------------------

        if extra_words.issubset(
            GENERIC_QUALIFIERS
        ):

            qualifier_penalty = (
                len(extra_words) * 2
            )

            score = (
                96.0
                + (
                    priority / 1000
                )
                - qualifier_penalty
            )

            return round(
                min(
                    99.9,
                    score,
                ),
                2,
            )

        # ----------------------------------------------------
        # 4B. SPECIFIC FOOD VARIANT
        # ----------------------------------------------------

        specific_terms = (
            extra_words.intersection(
                SPECIFIC_FOOD_TERMS
            )
        )

        if specific_terms:

            # Specific variants should remain searchable,
            # but should NOT beat a generic exact food.
            #
            # Example:
            # chicken -> Chicken, ground
            #
            # This receives a score below the exact branded
            # fallback of 75.
            score = (
                68.0
                + (
                    priority / 1000
                )
                - (
                    len(specific_terms) * 4.0
                )
                - (
                    max(
                        0,
                        len(extra_words)
                        - len(specific_terms),
                    )
                    * 2.0
                )
            )

            return round(
                max(
                    0.0,
                    min(
                        74.0,
                        score,
                    ),
                ),
                2,
            )

        # ----------------------------------------------------
        # 4C. OTHER EXTRA DESCRIPTORS
        # ----------------------------------------------------

        extra_count = len(
            extra_words
        )

        score = (
            72.0
            + (
                priority / 1000
            )
            - (
                extra_count * 5.0
            )
        )

        return round(
            max(
                0.0,
                min(
                    74.0,
                    score,
                ),
            ),
            2,
        )

    # --------------------------------------------------------
    # 5. QUERY EXISTS BUT IS NOT PRIMARY FOOD
    # --------------------------------------------------------

    if query_set.issubset(
        description_set
    ):
        return 20.0

    # --------------------------------------------------------
    # 6. PARTIAL OVERLAP
    # --------------------------------------------------------

    common_words = (
        query_set.intersection(
            description_set
        )
    )

    if not common_words:
        return 0.0

    word_match = (
        len(common_words)
        / len(query_set)
    )

    score = (
        word_match * 20.0
    )

    if (
        query_tokens[0]
        == description_tokens[0]
    ):
        score += 10.0

    score += (
        priority / 20.0
    )

    return round(
        max(
            0.0,
            min(
                30.0,
                score,
            ),
        ),
        2,
    )


# ============================================================
# FIND BEST FOOD
# ============================================================

def find_best_food(
    food_name: str,
    page_size: int = 50,
) -> List[Dict[str, Any]]:
    """
    Search USDA and return ranked candidates.

    IMPORTANT:
    This function returns candidates for inspection.

    The final confidence threshold is applied by
    get_food_with_nutrition().
    """

    foods = search_food(
        food_name,
        page_size=page_size,
    )

    ranked = []

    for food in foods:

        score = score_food_result(
            food_name,
            food,
        )

        if score <= 0:
            continue

        candidate = {
            "fdc_id": food.get(
                "fdcId"
            ),
            "description": food.get(
                "description",
                "",
            ),
            "data_type": food.get(
                "dataType",
                "",
            ),
            "score": score,
            "raw": food,
        }

        ranked.append(
            candidate
        )

    ranked.sort(
        key=lambda item: (
            item["score"],
            DATA_TYPE_PRIORITY.get(
                normalize_text(
                    item["data_type"]
                ),
                0,
            ),
        ),
        reverse=True,
    )

    return ranked


# ============================================================
# NUTRIENT MAP
# ============================================================

NUTRIENT_MAP = {
    "energy": "calories",
    "energy atwater general factors": "calories",
    "energy atwater specific factors": "calories",
    "energy converted from macronutrients": "calories",

    "protein": "protein_g",

    "carbohydrate by difference":
        "carbohydrates_g",

    "total carbohydrate":
        "carbohydrates_g",

    "total lipid fat":
        "fat_g",

    "total fat":
        "fat_g",

    "fiber total dietary":
        "fiber_g",

    "dietary fiber":
        "fiber_g",

    "sugars total including nlea":
        "sugar_g",

    "total sugars":
        "sugar_g",

    "calcium ca":
        "calcium_mg",

    "calcium":
        "calcium_mg",

    "iron fe":
        "iron_mg",

    "iron":
        "iron_mg",

    "sodium na":
        "sodium_mg",

    "sodium":
        "sodium_mg",

    "vitamin c total ascorbic acid":
        "vitamin_c_mg",

    "vitamin c":
        "vitamin_c_mg",
}


# ============================================================
# UNIT HELPERS
# ============================================================

def normalize_unit(
    unit: str,
) -> str:
    """
    Normalize USDA nutrient units.
    """

    unit = str(
        unit or ""
    ).strip().lower()

    unit = unit.replace(
        "μ",
        "u",
    )

    unit = unit.replace(
        "µ",
        "u",
    )

    return unit


def convert_energy_to_kcal(
    value: float,
    unit: str,
) -> float:
    """
    Convert USDA energy values to kcal.
    """

    unit = normalize_unit(
        unit
    )

    if unit == "kcal":
        return float(value)

    if unit == "kj":
        return float(value) / 4.184

    if unit == "cal":
        return float(value) / 1000.0

    return float(value)


def convert_nutrient_value(
    value: float,
    unit: str,
    output_name: str,
) -> float:
    """
    Convert nutrient values into the project's standard units.
    """

    unit = normalize_unit(
        unit
    )

    value = float(
        value
    )

    if output_name == "calories":
        return convert_energy_to_kcal(
            value,
            unit,
        )

    # Gram-based nutrients.
    if output_name.endswith(
        "_g"
    ):

        if unit == "g":
            return value

        if unit == "mg":
            return value / 1000.0

        if unit == "ug":
            return value / 1_000_000.0

    # Milligram-based nutrients.
    if output_name.endswith(
        "_mg"
    ):

        if unit == "mg":
            return value

        if unit == "g":
            return value * 1000.0

        if unit == "ug":
            return value / 1000.0

    return value


# ============================================================
# NUTRIENT EXTRACTION
# ============================================================

def extract_nutrients(
    food_details: Dict[str, Any],
) -> Dict[str, float]:
    """
    Extract useful nutrients from USDA food details.
    """

    nutrients = {}

    for nutrient in food_details.get(
        "foodNutrients",
        [],
    ):

        nutrient_data = nutrient.get(
            "nutrient",
            nutrient,
        )

        nutrient_name = normalize_text(
            nutrient_data.get(
                "name",
                "",
            )
        )

        output_name = NUTRIENT_MAP.get(
            nutrient_name
        )

        if not output_name:
            continue

        amount = nutrient.get(
            "amount"
        )

        unit = nutrient_data.get(
            "unitName",
            nutrient.get(
                "unitName",
                "",
            ),
        )

        if amount is None:
            continue

        try:

            converted = convert_nutrient_value(
                float(amount),
                unit,
                output_name,
            )

        except (
            TypeError,
            ValueError,
        ):
            continue

        if (
            output_name not in nutrients
            or nutrients[output_name] is None
        ):
            nutrients[
                output_name
            ] = round(
                converted,
                4,
            )

    return nutrients


# ============================================================
# NUTRITION VALIDATION
# ============================================================

def has_sufficient_nutrition(
    nutrition: Dict[str, float],
) -> bool:
    """
    Verify that the USDA result contains enough nutrition data.
    """

    important_fields = [
        "calories",
        "protein_g",
        "carbohydrates_g",
        "fat_g",
    ]

    available = sum(
        1
        for field in important_fields
        if field in nutrition
        and nutrition[field] is not None
    )

    return available >= 2


# ============================================================
# SERVING INFORMATION
# ============================================================

def extract_serving_information(
    food_details: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Extract USDA serving-size information when available.
    """

    result = {
        "serving_size": food_details.get(
            "servingSize"
        ),
        "serving_unit": food_details.get(
            "servingSizeUnit"
        ),
    }

    return result


def extract_food_portions(
    food_details: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Extract USDA food portion/measure information.
    """

    portions = []

    for portion in food_details.get(
        "foodMeasures",
        [],
    ):

        gram_weight = portion.get(
            "gramWeight"
        )

        if gram_weight is None:
            continue

        portions.append(
            {
                "description": portion.get(
                    "disseminationText"
                )
                or portion.get(
                    "modifier"
                )
                or portion.get(
                    "measureUnitName"
                ),
                "amount": portion.get(
                    "amount"
                ),
                "unit": portion.get(
                    "measureUnitName"
                ),
                "gram_weight": gram_weight,
            }
        )

    return portions


# ============================================================
# NUTRITION BASIS
# ============================================================

def get_nutrition_basis(
    food_details: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Nutrition values used by this project are treated as a
    standardized per-100-g basis for quantity scaling.
    """

    return {
        "basis": "per_100_g",
        "basis_amount": 100.0,
        "basis_unit": "g",
    }


# ============================================================
# CALCULATE NUTRITION FOR GRAMS
# ============================================================

def calculate_nutrition_for_grams(
    nutrition: Dict[str, float],
    grams: float,
) -> Dict[str, float]:
    """
    Scale per-100-g nutrition to the requested number of grams.
    """

    if grams is None:
        return nutrition.copy()

    grams = float(
        grams
    )

    multiplier = (
        grams / 100.0
    )

    result = {}

    for key, value in nutrition.items():

        if value is None:
            continue

        result[key] = round(
            float(value)
            * multiplier,
            4,
        )

    return result


# ============================================================
# CALCULATE NUTRITION FOR SERVING
# ============================================================

def calculate_nutrition_for_serving(
    nutrition: Dict[str, float],
    serving_grams: float,
) -> Dict[str, float]:
    """
    Calculate nutrition for a USDA serving weight.
    """

    return calculate_nutrition_for_grams(
        nutrition,
        serving_grams,
    )


# ============================================================
# GET FOOD WITH NUTRITION
# ============================================================

def get_food_with_nutrition(
    food_name: str,
    page_size: int = 50,
) -> Optional[Dict[str, Any]]:
    """
    Find the best reliable USDA food match and retrieve nutrition.

    A candidate is accepted only when its match score is at least
    MINIMUM_MATCH_SCORE.
    """

    candidates = find_best_food(
        food_name,
        page_size=page_size,
    )

    if not candidates:
        return None

    # --------------------------------------------------------
    # CONFIDENCE CHECK
    # --------------------------------------------------------

    best_candidate = candidates[0]

    if (
        best_candidate["score"]
        < MINIMUM_MATCH_SCORE
    ):
        return None

    # --------------------------------------------------------
    # GET COMPLETE USDA RECORD
    # --------------------------------------------------------

    fdc_id = best_candidate.get(
        "fdc_id"
    )

    if not fdc_id:
        return None

    try:

        food_details = get_food_details(
            int(fdc_id)
        )

    except requests.RequestException:
        return None

    # --------------------------------------------------------
    # EXTRACT NUTRITION
    # --------------------------------------------------------

    nutrition = extract_nutrients(
        food_details
    )

    if not has_sufficient_nutrition(
        nutrition
    ):
        return None

    # --------------------------------------------------------
    # SERVING / PORTION INFORMATION
    # --------------------------------------------------------

    serving_information = (
        extract_serving_information(
            food_details
        )
    )

    food_portions = extract_food_portions(
        food_details
    )

    nutrition_basis = get_nutrition_basis(
        food_details
    )

    # --------------------------------------------------------
    # FINAL RESULT
    # --------------------------------------------------------

    return {
        "matched_food": food_details.get(
            "description",
            best_candidate.get(
                "description",
                food_name,
            ),
        ),

        "fdc_id": food_details.get(
            "fdcId",
            fdc_id,
        ),

        "data_type": food_details.get(
            "dataType",
            best_candidate.get(
                "data_type",
                "",
            ),
        ),

        "match_score": best_candidate[
            "score"
        ],

        "nutrition": nutrition,

        "serving_size": serving_information.get(
            "serving_size"
        ),

        "serving_unit": serving_information.get(
            "serving_unit"
        ),

        "food_portions": food_portions,

        "nutrition_basis": nutrition_basis,

        "raw_food": food_details,
    }


# ============================================================
# COMMAND-LINE TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 70)
    print("DYNAMIC NUTRITION SERVICE TEST")
    print("=" * 70)

    test_foods = [
        "banana",
        "dragon fruit",
        "pomegranate",
        "quinoa",
        "salmon",
        "paneer",
        "tofu",
        "jackfruit",
        "kiwi",
        "cantaloupe",
        "asparagus",
        "chicken",
        "xyzabc food",
    ]

    for food_name in test_foods:

        print()
        print("-" * 70)
        print(
            f"Searching for: {food_name}"
        )
        print("-" * 70)

        try:

            result = get_food_with_nutrition(
                food_name
            )

            if result is None:

                print(
                    "No reliable USDA food match found."
                )

                continue

            print(
                f"Matched food : {result['matched_food']}"
            )

            print(
                f"FDC ID       : {result['fdc_id']}"
            )

            print(
                f"Data Type    : {result['data_type']}"
            )

            print(
                f"Match Score  : {result['match_score']}"
            )

            print()
            print("Nutrition:")
            print("-" * 40)

            for key, value in result[
                "nutrition"
            ].items():

                print(
                    f"{key}: {value}"
                )

        except Exception as exc:

            print(
                f"ERROR: {exc}"
            )