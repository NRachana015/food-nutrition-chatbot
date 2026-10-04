import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from chatbot import chat


# ============================================================
# MOCK USDA DATA
# ============================================================

MOCK_FOOD_DATABASE = {
    "banana": {
        "food": "Banana, raw",
        "fdc_id": 2709224,
        "data_type": "Survey (FNDDS)",
        "match_score": 93.0,
        "nutrition": {
            "calories": 97.0,
            "protein_g": 0.74,
            "carbohydrates_g": 22.70,
            "fat_g": 0.28,
            "fiber_g": 1.70,
            "sugar_g": 15.80,
            "calcium_mg": 5.0,
            "iron_mg": 0.0,
            "sodium_mg": 0.0,
            "vitamin_c_mg": 12.0,
        },
    },

    "broccoli": {
        "food": "Broccoli, raw",
        "fdc_id": 170379,
        "data_type": "SR Legacy",
        "match_score": 93.09,
        "nutrition": {
            "calories": 34.0,
            "protein_g": 2.82,
            "carbohydrates_g": 6.64,
            "fat_g": 0.37,
            "fiber_g": 2.60,
            "sugar_g": 1.70,
            "calcium_mg": 47.0,
            "iron_mg": 0.73,
            "sodium_mg": 33.0,
            "vitamin_c_mg": 89.2,
        },
    },

    "chicken": {
        "food": "Chicken",
        "fdc_id": 2038064,
        "data_type": "Branded",
        "match_score": 75.0,
        "nutrition": {
            "calories": 107.0,
            "protein_g": 21.43,
            "carbohydrates_g": 0.0,
            "fat_g": 1.79,
            "fiber_g": 0.0,
            "sugar_g": 0.0,
            "calcium_mg": 0.0,
            "iron_mg": 0.0,
            "sodium_mg": 179.0,
            "vitamin_c_mg": 0.0,
        },
    },

    "avocado": {
        "food": "Avocado, raw",
        "fdc_id": 171705,
        "data_type": "SR Legacy",
        "match_score": 93.09,
        "nutrition": {
            "calories": 160.0,
            "protein_g": 2.0,
            "carbohydrates_g": 8.53,
            "fat_g": 14.66,
            "fiber_g": 6.70,
            "sugar_g": 0.66,
            "calcium_mg": 12.0,
            "iron_mg": 0.55,
            "sodium_mg": 7.0,
            "vitamin_c_mg": 10.0,
        },
    },

    "quinoa": {
        "food": "Quinoa",
        "fdc_id": 2058561,
        "data_type": "Branded",
        "match_score": 75.0,
        "nutrition": {
            "calories": 333.0,
            "protein_g": 14.29,
            "carbohydrates_g": 66.67,
            "fat_g": 4.76,
            "fiber_g": 9.52,
            "sugar_g": 0.0,
            "calcium_mg": 48.0,
            "iron_mg": 4.29,
            "sodium_mg": 0.0,
            "vitamin_c_mg": 0.0,
        },
    },

    "dragon fruit": {
        "food": "Dragon fruit",
        "fdc_id": 2709234,
        "data_type": "Survey (FNDDS)",
        "match_score": 100.0,
        "nutrition": {
            "calories": 68.0,
            "protein_g": 1.0,
            "carbohydrates_g": 14.0,
            "fat_g": 0.4,
            "fiber_g": 3.0,
            "sugar_g": 7.7,
            "calcium_mg": 10.0,
            "iron_mg": 0.30,
            "sodium_mg": 0.0,
            "vitamin_c_mg": 9.0,
        },
    },

    "pomegranate": {
        "food": "Pomegranate, raw",
        "fdc_id": 2709267,
        "data_type": "Survey (FNDDS)",
        "match_score": 93.0,
        "nutrition": {
            "calories": 83.0,
            "protein_g": 1.67,
            "carbohydrates_g": 18.70,
            "fat_g": 1.17,
            "fiber_g": 4.0,
            "sugar_g": 13.67,
            "calcium_mg": 10.0,
            "iron_mg": 0.30,
            "sodium_mg": 3.0,
            "vitamin_c_mg": 10.2,
        },
    },

    "tofu": {
        "food": "Tofu",
        "fdc_id": 2038883,
        "data_type": "Branded",
        "match_score": 75.0,
        "nutrition": {
            "calories": 94.0,
            "protein_g": 10.0,
            "carbohydrates_g": 2.0,
            "fat_g": 5.0,
            "fiber_g": 1.0,
            "sugar_g": 0.5,
            "calcium_mg": 350.0,
            "iron_mg": 2.0,
            "sodium_mg": 10.0,
            "vitamin_c_mg": 0.0,
        },
    },

    "paneer": {
        "food": "Paneer",
        "fdc_id": 2429587,
        "data_type": "Branded",
        "match_score": 75.0,
        "nutrition": {
            "calories": 321.0,
            "protein_g": 18.0,
            "carbohydrates_g": 3.5,
            "fat_g": 25.0,
            "fiber_g": 0.0,
            "sugar_g": 2.0,
            "calcium_mg": 208.0,
            "iron_mg": 2.16,
            "sodium_mg": 22.0,
            "vitamin_c_mg": 0.0,
        },
    },

    "salmon": {
        "food": "Salmon",
        "fdc_id": 2016166,
        "data_type": "Branded",
        "match_score": 75.0,
        "nutrition": {
            "calories": 139.0,
            "protein_g": 20.0,
            "carbohydrates_g": 0.0,
            "fat_g": 6.0,
            "fiber_g": 0.0,
            "sugar_g": 0.0,
            "calcium_mg": 12.0,
            "iron_mg": 0.40,
            "sodium_mg": 45.0,
            "vitamin_c_mg": 0.0,
        },
    },

    "chicken wings": {
        "food": "Chicken wings",
        "fdc_id": 1906811,
        "data_type": "Branded",
        "match_score": 75.0,
        "nutrition": {
            "calories": 283.0,
            "protein_g": 18.58,
            "carbohydrates_g": 0.0,
            "fat_g": 18.58,
            "fiber_g": 0.0,
            "sugar_g": 0.0,
            "calcium_mg": 0.0,
            "iron_mg": 0.96,
            "sodium_mg": 84.0,
            "vitamin_c_mg": 0.0,
        },
    },

    "chicken breast": {
        "food": "Chicken breast",
        "fdc_id": 171077,
        "data_type": "SR Legacy",
        "match_score": 93.09,
        "nutrition": {
            "calories": 165.0,
            "protein_g": 31.0,
            "carbohydrates_g": 0.0,
            "fat_g": 3.57,
            "fiber_g": 0.0,
            "sugar_g": 0.0,
            "calcium_mg": 15.0,
            "iron_mg": 1.04,
            "sodium_mg": 74.0,
            "vitamin_c_mg": 0.0,
        },
    },

    "sweet potato": {
        "food": "Sweet potato, raw",
        "fdc_id": 168482,
        "data_type": "SR Legacy",
        "match_score": 93.09,
        "nutrition": {
            "calories": 86.0,
            "protein_g": 1.57,
            "carbohydrates_g": 20.12,
            "fat_g": 0.05,
            "fiber_g": 3.0,
            "sugar_g": 4.18,
            "calcium_mg": 30.0,
            "iron_mg": 0.61,
            "sodium_mg": 55.0,
            "vitamin_c_mg": 2.4,
        },
    },

    "jackfruit": {
        "food": "Jackfruit, raw",
        "fdc_id": 174687,
        "data_type": "SR Legacy",
        "match_score": 93.09,
        "nutrition": {
            "calories": 94.8853,
            "protein_g": 1.72,
            "carbohydrates_g": 23.25,
            "fat_g": 0.64,
            "fiber_g": 1.5,
            "sugar_g": 19.08,
            "calcium_mg": 24.0,
            "iron_mg": 0.23,
            "sodium_mg": 3.0,
            "vitamin_c_mg": 13.7,
        },
    },

    "cantaloupe": {
        "food": "Cantaloupe, raw",
        "fdc_id": 2709226,
        "data_type": "Survey (FNDDS)",
        "match_score": 93.0,
        "nutrition": {
            "calories": 38.0,
            "protein_g": 0.82,
            "carbohydrates_g": 8.16,
            "fat_g": 0.18,
            "fiber_g": 0.8,
            "sugar_g": 7.88,
            "calcium_mg": 9.0,
            "iron_mg": 0.38,
            "sodium_mg": 30.0,
            "vitamin_c_mg": 10.9,
        },
    },

    "asparagus": {
        "food": "Asparagus, raw",
        "fdc_id": 168389,
        "data_type": "SR Legacy",
        "match_score": 93.09,
        "nutrition": {
            "calories": 20.0,
            "protein_g": 2.2,
            "carbohydrates_g": 3.88,
            "fat_g": 0.12,
            "fiber_g": 2.1,
            "sugar_g": 1.88,
            "calcium_mg": 24.0,
            "iron_mg": 2.14,
            "sodium_mg": 2.0,
            "vitamin_c_mg": 5.6,
        },
    },
}


# ============================================================
# MOCK USDA LOOKUP
# ============================================================

def mock_get_food_with_nutrition(food_name):
    """
    Mock only the USDA nutrition lookup.

    The real chatbot, NLP parser, quantity handling,
    nutrition calculation, and response generation
    continue to run normally.
    """

    food_name = food_name.lower().strip()

    # Exact match first.
    if food_name in MOCK_FOOD_DATABASE:
        return MOCK_FOOD_DATABASE[food_name].copy()

    # Simple fallback for normalized names.
    for key, data in MOCK_FOOD_DATABASE.items():
        if key in food_name or food_name in key:
            return data.copy()

    return None


# ============================================================
# FIXTURE
# ============================================================

@pytest.fixture
def mocked_usda(mocker):
    """
    Replace only the USDA retrieval layer.

    IMPORTANT:
    We do NOT mock chatbot.chat().
    """

    return mocker.patch(
        "chatbot.get_food_with_nutrition",
        side_effect=mock_get_food_with_nutrition,
    )


# ============================================================
# COMMON FOOD TESTS
# ============================================================

@pytest.mark.parametrize(
    "query",
    [
        "banana",
        "broccoli",
        "chicken",
        "avocado",
        "quinoa",
        "dragon fruit",
        "pomegranate",
        "tofu",
        "paneer",
        "salmon",
    ],
)
def test_common_foods(
    mocked_usda,
    query,
):
    result = chat(query)

    assert result["success"] is True
    assert result["food"]
    assert result["matched_food"]
    assert result["fdc_id"] is not None
    assert result["nutrition"]


# ============================================================
# NATURAL LANGUAGE TESTS
# ============================================================

@pytest.mark.parametrize(
    "query",
    [
        "i ate 200g banana",
        "how much protein is in 150g chicken",
        "nutrition of dragon fruit",
        "what are the calories in 2 bananas",
        "tell me nutrition of broccoli",
        "i had some quinoa",
    ],
)
def test_natural_language_queries(
    mocked_usda,
    query,
):
    result = chat(query)

    assert result["success"] is True
    assert result["food"]
    assert result["nutrition"]


# ============================================================
# TYPO CORRECTION TESTS
# ============================================================

@pytest.mark.parametrize(
    "query",
    [
        "bananna",
        "brocolli",
        "chickwn",
        "avacado",
    ],
)
def test_typo_correction(
    mocked_usda,
    query,
):
    result = chat(query)

    assert result["success"] is True
    assert result["matched_food"]
    assert result["nutrition"]


# ============================================================
# QUANTITY TESTS
# ============================================================

def test_100g_banana(mocked_usda):

    result = chat("100g banana")

    assert result["success"] is True
    assert result["grams"] == pytest.approx(100.0)

    assert result["nutrition"]["calories"] == pytest.approx(
        97.0
    )


def test_200g_banana(mocked_usda):

    result_100 = chat("100g banana")
    result_200 = chat("200g banana")

    assert result_100["success"] is True
    assert result_200["success"] is True

    assert result_200["grams"] == pytest.approx(
        200.0
    )

    calories_100 = result_100["nutrition"]["calories"]
    calories_200 = result_200["nutrition"]["calories"]

    assert calories_200 == pytest.approx(
        calories_100 * 2
    )


def test_1kg_banana(mocked_usda):

    result = chat("1 kg banana")

    assert result["success"] is True
    assert result["grams"] == pytest.approx(
        1000.0
    )

    assert result["nutrition"]["calories"] == pytest.approx(
        970.0
    )


# ============================================================
# SPECIFIC FOOD TESTS
# ============================================================

@pytest.mark.parametrize(
    "query",
    [
        "chicken wings",
        "chicken breast",
        "sweet potato",
        "dragon fruit",
        "jackfruit",
        "cantaloupe",
        "asparagus",
    ],
)
def test_specific_foods(
    mocked_usda,
    query,
):
    result = chat(query)

    assert result["success"] is True
    assert result["matched_food"]
    assert result["nutrition"]


# ============================================================
# TYPO + SPECIFIC FOOD
# ============================================================

def test_typo_with_specific_food(
    mocked_usda,
):

    result = chat(
        "i ate chickwn wings"
    )

    assert result["success"] is True
    assert result["food"] == "chicken wings"
    assert result["matched_food"]
    assert result["nutrition"]


# ============================================================
# NUTRITION FIELD VALIDATION
# ============================================================

def test_nutrition_contains_core_fields(
    mocked_usda,
):

    result = chat("banana")

    assert result["success"] is True

    nutrition = result["nutrition"]

    required_fields = [
        "calories",
        "protein_g",
        "carbohydrates_g",
        "fat_g",
    ]

    for field in required_fields:

        assert field in nutrition
        assert nutrition[field] is not None
        assert nutrition[field] >= 0


# ============================================================
# USDA METADATA
# ============================================================

def test_usda_metadata(
    mocked_usda,
):

    result = chat("banana")

    assert result["success"] is True

    assert result["fdc_id"] is not None
    assert result["data_type"]
    assert result["match_score"] is not None

    assert result["match_score"] >= 75


# ============================================================
# UNKNOWN FOOD SAFETY
# ============================================================

@pytest.mark.parametrize(
    "query",
    [
        "xyzabc food",
        "jh",
        "thisisnotarealfood123",
    ],
)
def test_unknown_food_is_handled_safely(
    mocked_usda,
    query,
):

    result = chat(query)

    assert result["success"] is False
    assert result["message"]

    message = result["message"].lower()

    assert (
        "couldn't find" in message
        or "could not find" in message
    )


# ============================================================
# CHATBOT RESPONSE
# ============================================================

def test_chatbot_returns_user_friendly_message(
    mocked_usda,
):

    result = chat("200g banana")

    assert result["success"] is True
    assert result["message"]

    message = result["message"].lower()

    assert "banana" in message
    assert "calories" in message
    assert "protein" in message
    assert "usda" in message


# ============================================================
# REAL CHAT FUNCTION VERIFICATION
# ============================================================

def test_real_chat_function_is_used(
    mocked_usda,
):

    result = chat("banana")

    assert result["success"] is True

    # Verify that the real chat() called the
    # mocked USDA retrieval layer.
    mocked_usda.assert_called_once_with("banana")


# ============================================================
# USDA IS NEVER CALLED DIRECTLY
# ============================================================

def test_usda_lookup_is_mocked(
    mocked_usda,
):

    chat("banana")

    assert mocked_usda.call_count == 1
    mocked_usda.assert_called_once_with("banana")


# ============================================================
# QUANTITY SCALING VALIDATION
# ============================================================

def test_protein_scales_correctly(
    mocked_usda,
):

    result_100 = chat("100g banana")
    result_200 = chat("200g banana")

    protein_100 = result_100["nutrition"]["protein_g"]
    protein_200 = result_200["nutrition"]["protein_g"]

    assert protein_100 == pytest.approx(
        0.74
    )

    assert protein_200 == pytest.approx(
        1.48
    )


def test_chicken_quantity_scaling(
    mocked_usda,
):

    result = chat("200g chicken")

    assert result["success"] is True
    assert result["grams"] == pytest.approx(
        200.0
    )

    assert result["nutrition"]["calories"] == pytest.approx(
        214.0
    )

    assert result["nutrition"]["protein_g"] == pytest.approx(
        42.86
    )


# ============================================================
# END
# ============================================================
