import pandas as pd
import streamlit as st

from chatbot import chat


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Food Nutrition Chatbot",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    /* ======================================================
       GLOBAL
       ====================================================== */

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }

    /* ======================================================
       HEADER
       ====================================================== */

    .main-title {
        font-size: 2.6rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        margin-bottom: 0.15rem;
    }

    .subtitle {
        color: #6b7280;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }

    /* ======================================================
       SIDEBAR BRAND
       ====================================================== */

    .sidebar-brand {
        padding: 0.5rem 0 1rem 0;
    }

    .sidebar-brand-title {
        font-size: 1.55rem;
        font-weight: 800;
        margin-bottom: 0.15rem;
    }

    .sidebar-brand-subtitle {
        color: #6b7280;
        font-size: 0.85rem;
    }

    /* ======================================================
       SIDEBAR SECTION
       ====================================================== */

    .sidebar-section-title {
        font-size: 0.78rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        margin-top: 1rem;
        margin-bottom: 0.55rem;
        color: #6b7280;
    }

    .sidebar-description {
        font-size: 0.9rem;
        line-height: 1.55;
        color: #4b5563;
    }

    /* ======================================================
       STATUS CARD
       ====================================================== */

    .status-card {
        border: 1px solid rgba(128, 128, 128, 0.25);
        border-radius: 12px;
        padding: 0.8rem;
        margin-top: 0.8rem;
    }

    .status-title {
        font-weight: 700;
        font-size: 0.9rem;
    }

    .status-text {
        color: #6b7280;
        font-size: 0.78rem;
        margin-top: 0.2rem;
    }

    /* ======================================================
       RESULT HEADER
       ====================================================== */

    .result-title {
        font-size: 1.35rem;
        font-weight: 800;
        margin-bottom: 0.1rem;
    }

    .result-food {
        font-size: 1.05rem;
        font-weight: 600;
    }

    .result-amount {
        color: #6b7280;
        font-size: 0.9rem;
        margin-bottom: 1rem;
    }

    /* ======================================================
       NUTRITION CARDS
       ====================================================== */

    .nutrition-card {
        border: 1px solid rgba(128, 128, 128, 0.22);
        border-radius: 14px;
        padding: 1rem;
        min-height: 115px;
    }

    .nutrition-label {
        color: #6b7280;
        font-size: 0.82rem;
        font-weight: 600;
    }

    .nutrition-value {
        font-size: 1.45rem;
        font-weight: 800;
        margin-top: 0.3rem;
    }

    /* ======================================================
       USDA CARD
       ====================================================== */

    .usda-note {
        color: #6b7280;
        font-size: 0.82rem;
        margin-top: 0.4rem;
    }

    /* ======================================================
       FOOTER
       ====================================================== */

    .app-footer {
        text-align: center;
        color: #9ca3af;
        font-size: 0.78rem;
        padding-top: 2rem;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    # --------------------------------------------------------
    # BRAND
    # --------------------------------------------------------

    st.markdown(
        """
        <div class="sidebar-brand">
            <div class="sidebar-brand-title">
                🥗 NutriBot
            </div>
            <div class="sidebar-brand-subtitle">
                AI Nutrition Assistant
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    # --------------------------------------------------------
    # ABOUT
    # --------------------------------------------------------

    st.markdown(
        '<div class="sidebar-section-title">ℹ️ ABOUT</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="sidebar-description">
            Your intelligent nutrition assistant powered by
            Natural Language Processing and USDA FoodData Central.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # QUICK EXAMPLES
    # --------------------------------------------------------

    st.markdown(
        '<div class="sidebar-section-title">⚡ QUICK EXAMPLES</div>',
        unsafe_allow_html=True,
    )

    example_queries = [
        (
            "🔥",
            "Banana — Calories",
            "how many calories are in a banana",
        ),
        (
            "💪",
            "Chicken — Protein",
            "how much protein is in 200g chicken",
        ),
        (
            "🥦",
            "Broccoli — Vitamins & Minerals",
            "what vitamins and minerals are in 150g broccoli",
        ),
        (
            "🌾",
            "Oats — Fiber",
            "how much fiber is in 100g oats",
        ),
        (
            "🥑",
            "Avocado — Healthy Fats",
            "how much fat is in 100g avocado",
        ),
        (
            "🥛",
            "Milk — Calcium",
            "how much calcium is in 250ml milk",
        ),
    ]

    for emoji, label, query in example_queries:

        if st.button(
            f"{emoji}  {label}",
            key=f"example_{label}",
            use_container_width=True,
        ):
            st.session_state.pending_prompt = query
            st.rerun()

    # --------------------------------------------------------
    # WHAT I CAN DO
    # --------------------------------------------------------

    st.markdown(
        '<div class="sidebar-section-title">🔍 WHAT I CAN DO</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="sidebar-description">
            ✓ Understand natural language<br>
            ✓ Detect food and quantity<br>
            ✓ Correct common spelling mistakes<br>
            ✓ Search foods dynamically<br>
            ✓ Calculate nutrition for requested amounts
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # NUTRIENTS TRACKED
    # --------------------------------------------------------

    st.markdown(
        '<div class="sidebar-section-title">📊 NUTRIENTS TRACKED</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="sidebar-description">
            🔥 Calories<br>
            💪 Protein<br>
            🍞 Carbohydrates<br>
            🥑 Fat<br>
            🌾 Fiber<br>
            🍬 Sugar<br>
            🧂 Sodium<br>
            🍊 Vitamin C
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    # --------------------------------------------------------
    # CLEAR CHAT
    # --------------------------------------------------------

    if st.button(
        "🗑️ Clear Conversation",
        use_container_width=True,
    ):
        st.session_state.messages = []
        st.session_state.pending_prompt = None
        st.rerun()

    # --------------------------------------------------------
    # USDA STATUS
    # --------------------------------------------------------

    st.markdown(
        """
        <div class="status-card">
            <div class="status-title">
                🟢 USDA Connected
            </div>
            <div class="status-text">
                Dynamic nutrition data from USDA FoodData Central
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# MAIN HEADER
# ============================================================

st.markdown(
    '<div class="main-title">🥗 FOOD NUTRITION CHATBOT</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    "AI-powered nutrition assistant — ask about any food in natural language."
    "</div>",
    unsafe_allow_html=True,
)


# ============================================================
# HOW IT WORKS
# ============================================================

with st.expander("🔎 How it works", expanded=False):

    col1, col2, col3, col4, col5 = st.columns(5)

    steps = [
        ("1", "💬", "Ask", "Enter a food-related question."),
        ("2", "🧠", "NLP", "Food and quantity are detected."),
        ("3", "🔎", "Search", "USDA is searched dynamically."),
        ("4", "✅", "Match", "The best reliable match is selected."),
        ("5", "📊", "Calculate", "Nutrition is calculated."),
    ]

    for column, (number, icon, title, description) in zip(
        [col1, col2, col3, col4, col5],
        steps,
    ):
        with column:
            st.markdown(f"### {icon}")
            st.markdown(f"**{number}. {title}**")
            st.caption(description)


# ============================================================
# DISPLAY NUTRITION RESULT
# ============================================================

def display_nutrition_result(result: dict):
    """
    Display a professional nutrition result.
    """

    nutrition = result.get(
        "nutrition",
        {},
    )

    # --------------------------------------------------------
    # FOOD + AMOUNT
    # --------------------------------------------------------

    matched_food = result.get(
        "matched_food",
        result.get(
            "food",
            "Unknown",
        ),
    )

    grams = result.get("grams")
    quantity = result.get("quantity")
    unit = result.get("unit")

    if grams is not None and quantity is not None and unit:
        amount_text = f"{quantity:g} {unit}"
    elif grams is not None:
        amount_text = f"{grams:g} g"
    else:
        amount_text = "Per 100 g"

    st.markdown(
        '<div class="result-title">🍎 Nutrition Information</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div class="result-food">{matched_food}</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<div class="result-amount">{amount_text}</div>',
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # MAIN NUTRIENTS
    # --------------------------------------------------------

    calories = nutrition.get(
        "calories",
        0,
    )

    protein = nutrition.get(
        "protein_g",
        0,
    )

    carbohydrates = nutrition.get(
        "carbohydrates_g",
        0,
    )

    fat = nutrition.get(
        "fat_g",
        0,
    )

    st.markdown(
        "#### 📊 Nutrition Summary"
    )

    col1, col2, col3, col4 = st.columns(4)

    nutrient_cards = [
        (
            col1,
            "🔥 Calories",
            f"{calories:.2f} kcal",
        ),
        (
            col2,
            "💪 Protein",
            f"{protein:.2f} g",
        ),
        (
            col3,
            "🍞 Carbohydrates",
            f"{carbohydrates:.2f} g",
        ),
        (
            col4,
            "🥑 Fat",
            f"{fat:.2f} g",
        ),
    ]

    for column, label, value in nutrient_cards:

        with column:

            st.markdown(
                f"""
                <div class="nutrition-card">
                    <div class="nutrition-label">
                        {label}
                    </div>
                    <div class="nutrition-value">
                        {value}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # --------------------------------------------------------
    # ADDITIONAL NUTRIENTS
    # --------------------------------------------------------

    additional_items = []

    if "fiber_g" in nutrition:
        additional_items.append(
            (
                "🌾 Fiber",
                f"{nutrition['fiber_g']:.2f} g",
            )
        )

    if "sugar_g" in nutrition:
        additional_items.append(
            (
                "🍬 Sugar",
                f"{nutrition['sugar_g']:.2f} g",
            )
        )

    if "sodium_mg" in nutrition:
        additional_items.append(
            (
                "🧂 Sodium",
                f"{nutrition['sodium_mg']:.2f} mg",
            )
        )

    if "vitamin_c_mg" in nutrition:
        additional_items.append(
            (
                "🍊 Vitamin C",
                f"{nutrition['vitamin_c_mg']:.2f} mg",
            )
        )

    if additional_items:

        st.markdown(
            "#### 🧪 Additional Nutrients"
        )

        columns = st.columns(
            len(additional_items)
        )

        for column, (label, value) in zip(
            columns,
            additional_items,
        ):

            with column:

                st.metric(
                    label,
                    value,
                )

    # --------------------------------------------------------
    # MACRONUTRIENT CHART
    # --------------------------------------------------------

    st.markdown(
        "#### 📈 Macronutrient Profile"
    )

    chart_data = pd.DataFrame(
        {
            "Nutrient": [
                "Carbohydrates",
                "Fat",
                "Fiber",
                "Protein",
            ],
            "Grams": [
                carbohydrates,
                fat,
                nutrition.get(
                    "fiber_g",
                    0,
                ),
                protein,
            ],
        }
    )

    st.bar_chart(
        chart_data,
        x="Nutrient",
        y="Grams",
        horizontal=True,
        height=300,
    )

    # --------------------------------------------------------
    # USDA INFORMATION
    # --------------------------------------------------------

    st.markdown(
        "#### 🔎 USDA Information"
    )

    data_type = result.get(
        "data_type",
        "Unknown",
    )

    fdc_id = result.get(
        "fdc_id",
        "Unknown",
    )

    match_score = result.get(
        "match_score"
    )

    with st.container(
        border=True
    ):

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**Data type**")
            st.write(data_type)

        with col2:
            st.markdown("**FDC ID**")
            st.write(fdc_id)

        with col3:
            st.markdown("**Match score**")

            if match_score is not None:
                st.write(
                    f"{match_score:.2f}"
                )
            else:
                st.write("N/A")

        st.caption(
            "✓ Nutrition data retrieved dynamically from "
            "USDA FoodData Central."
        )


# ============================================================
# DISPLAY PREVIOUS CHAT
# ============================================================

for message in st.session_state.messages:

    with st.chat_message(
        message["role"]
    ):

        # ----------------------------------------------------
        # PREVIOUS SUCCESSFUL NUTRITION RESULT
        # ----------------------------------------------------

        if message.get("result") is not None:

            display_nutrition_result(
                message["result"]
            )

        # ----------------------------------------------------
        # NORMAL TEXT MESSAGE
        # ----------------------------------------------------

        else:

            st.markdown(
                message["content"]
            )


# ============================================================
# PROCESS PENDING SIDEBAR EXAMPLE
# ============================================================

prompt = st.chat_input(
    "Ask about any food...  e.g.  200g banana"
)

if st.session_state.pending_prompt:

    prompt = st.session_state.pending_prompt

    st.session_state.pending_prompt = None


# ============================================================
# PROCESS USER QUERY
# ============================================================

if prompt:

    # --------------------------------------------------------
    # SAVE USER MESSAGE
    # --------------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    # --------------------------------------------------------
    # DISPLAY USER MESSAGE
    # --------------------------------------------------------

    with st.chat_message(
        "user"
    ):

        st.markdown(
            prompt
        )

    # --------------------------------------------------------
    # ASSISTANT
    # --------------------------------------------------------

    with st.chat_message(
        "assistant"
    ):

        with st.spinner(
            "🔎 Searching USDA nutrition data..."
        ):

            try:

                result = chat(
                    prompt
                )

            except Exception as exc:

                result = {
                    "success": False,
                    "message": (
                        "Sorry, something went wrong "
                        "while processing your request: "
                        f"{exc}"
                    ),
                }

        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        if result.get(
            "success",
            False,
        ):

            display_nutrition_result(
                result
            )

            assistant_message = result.get(
                "message",
                "Nutrition information found.",
            )

        # ----------------------------------------------------
        # NO MATCH / ERROR
        # ----------------------------------------------------

        else:

            assistant_message = result.get(
                "message",
                "Sorry, I could not find reliable nutrition information.",
            )

            st.warning(
                assistant_message
            )

    # --------------------------------------------------------
    # SAVE ASSISTANT RESPONSE
    # --------------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": assistant_message,
            "result": (
                result
                if result.get(
                    "success",
                    False,
                )
                else None
            ),
        }
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="app-footer">
        Food Nutrition Chatbot • NLP + USDA FoodData Central
    </div>
    """,
    unsafe_allow_html=True,
)