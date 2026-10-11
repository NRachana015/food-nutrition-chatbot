
import pandas as pd
import streamlit as st
import plotly.express as px

from chatbot import chat


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="NutriBot | Food Nutrition Chatbot",
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
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }

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
        color: #6b7280;
    }

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

    st.markdown(
        """
        <div class="sidebar-brand">
            <div class="sidebar-brand-title">🥗 NutriBot</div>
            <div class="sidebar-brand-subtitle">
                AI Nutrition Assistant
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

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

    st.markdown(
        '<div class="sidebar-section-title">⚡ QUICK EXAMPLES</div>',
        unsafe_allow_html=True,
    )

    example_queries = [
        ("🔥", "Banana — Calories",
         "how many calories are in a banana"),
        ("💪", "Chicken — Protein",
         "how much protein is in 200g chicken"),
        ("🥦", "Broccoli — Vitamins & Minerals",
         "what vitamins and minerals are in 150g broccoli"),
        ("🌾", "Oats — Fiber",
         "how much fiber is in 100g oats"),
        ("🥑", "Avocado — Healthy Fats",
         "how much fat is in 100g avocado"),
        ("🥛", "Milk — Calcium",
         "how much calcium is in 250ml milk"),
    ]

    for emoji, label, query in example_queries:
        if st.button(
            f"{emoji}  {label}",
            key=f"example_{label}",
            use_container_width=True,
        ):
            st.session_state.pending_prompt = query
            st.rerun()

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
            🦴 Calcium<br>
            🩸 Iron<br>
            🧂 Sodium<br>
            🍊 Vitamin C
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.pending_prompt = None
        st.rerun()

    st.markdown(
        """
        <div class="status-card">
            <div class="status-title">
                🌐 USDA FoodData Central
            </div>
            <div class="status-text">
                Nutrition data is retrieved dynamically when available.
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

    columns = st.columns(5)

    steps = [
        ("💬", "1. Ask", "Enter a food-related question."),
        ("🧠", "2. NLP", "Food and quantity are detected."),
        ("🔎", "3. Search", "USDA is searched dynamically."),
        ("✅", "4. Match", "A suitable food record is selected."),
        ("📊", "5. Calculate", "Nutrition is calculated."),
    ]

    for column, (emoji, title, description) in zip(columns, steps):
        with column:
            st.markdown(f"### {emoji}")
            st.markdown(f"**{title}**")
            st.caption(description)


# ============================================================
# DISPLAY NUTRITION RESULT
# ============================================================

def display_nutrition_result(result: dict):
    nutrition = result.get("nutrition") or {}

    matched_food = result.get(
        "matched_food",
        result.get("food", "Unknown"),
    )

    grams = result.get("grams")
    quantity = result.get("quantity")
    unit = result.get("unit")

    if quantity is not None and unit:
        amount_text = f"{quantity:g} {unit}"
        if grams is not None:
            amount_text += f" (approximately {grams:g} g)"
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

    # Main nutrients
    calories = float(nutrition.get("calories") or 0)
    protein = float(nutrition.get("protein_g") or 0)
    carbohydrates = float(nutrition.get("carbohydrates_g") or 0)
    fat = float(nutrition.get("fat_g") or 0)

    st.markdown("#### 📊 Nutrition Summary")

    columns = st.columns(4)

    cards = [
        (columns[0], "🔥 Calories", f"{calories:.2f} kcal"),
        (columns[1], "💪 Protein", f"{protein:.2f} g"),
        (columns[2], "🍞 Carbohydrates", f"{carbohydrates:.2f} g"),
        (columns[3], "🥑 Fat", f"{fat:.2f} g"),
    ]

    for column, label, value in cards:
        with column:
            st.markdown(
                f"""
                <div class="nutrition-card">
                    <div class="nutrition-label">{label}</div>
                    <div class="nutrition-value">{value}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Additional nutrients
    additional_nutrients = [
        ("🌾 Fiber", "fiber_g", "g"),
        ("🍬 Sugar", "sugar_g", "g"),
        ("🦴 Calcium", "calcium_mg", "mg"),
        ("🩸 Iron", "iron_mg", "mg"),
        ("🧂 Sodium", "sodium_mg", "mg"),
        ("🍊 Vitamin C", "vitamin_c_mg", "mg"),
    ]

    available = [
        (label, float(nutrition[key]), unit_name)
        for label, key, unit_name in additional_nutrients
        if nutrition.get(key) is not None
    ]

    if available:
        st.markdown("#### 🧪 Additional Nutrients")
        columns = st.columns(min(3, len(available)))

        for index, (label, value, unit_name) in enumerate(available):
            with columns[index % len(columns)]:
                st.metric(label, f"{value:.2f} {unit_name}")

    # Improved macronutrient chart
    st.markdown("#### 📈 Macronutrient Profile")

    chart_data = pd.DataFrame(
        {
            "Nutrient": [
                "Carbohydrates",
                "Protein",
                "Fat",
                "Fiber",
            ],
            "Grams": [
                carbohydrates,
                protein,
                fat,
                float(nutrition.get("fiber_g") or 0),
            ],
        }
    )

    chart_data = chart_data[chart_data["Grams"] > 0].sort_values(
        "Grams",
        ascending=True,
    )

    if not chart_data.empty:
        fig = px.bar(
            chart_data,
            x="Grams",
            y="Nutrient",
            orientation="h",
            text="Grams",
            labels={
                "Grams": "Amount (grams)",
                "Nutrient": "",
            },
            title="Macronutrients by weight",
        )

        fig.update_traces(
            texttemplate="%{text:.2f} g",
            textposition="outside",
            cliponaxis=False,
        )

        fig.update_layout(
            height=320,
            showlegend=False,
            margin=dict(l=20, r=80, t=60, b=45),
            xaxis=dict(
                rangemode="tozero",
                title="Amount (grams)",
            ),
            yaxis=dict(
                title="",
                automargin=True,
            ),
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )
    else:
        st.info("No macronutrient values are available to plot.")

    # USDA information
    st.markdown("#### 🔎 USDA Information")

    with st.container(border=True):
        columns = st.columns(3)

        with columns[0]:
            st.markdown("**Data type**")
            st.write(result.get("data_type") or "Unknown")

        with columns[1]:
            st.markdown("**FDC ID**")
            st.write(result.get("fdc_id") or "Unknown")

        with columns[2]:
            st.markdown("**Match score**")
            score = result.get("match_score")
            st.write(f"{score:.2f}" if score is not None else "N/A")

        st.caption(
            "Nutrition data retrieved from USDA FoodData Central "
            "when a reliable match is available."
        )


# ============================================================
# DISPLAY PREVIOUS CHAT
# ============================================================

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message.get("result") is not None:
            display_nutrition_result(message["result"])
        else:
            st.markdown(message["content"])


# ============================================================
# USER INPUT
# ============================================================

prompt = st.chat_input(
    "Ask about any food... e.g. 200g banana"
)

if st.session_state.pending_prompt:
    prompt = st.session_state.pending_prompt
    st.session_state.pending_prompt = None


# ============================================================
# PROCESS USER QUERY
# ============================================================

if prompt:
    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("🔎 Searching nutrition data..."):
            try:
                result = chat(prompt)
            except Exception:
                st.error(
                    "Something went wrong while processing your request. "
                    "Please check your connection and try again."
                )
                result = {
                    "success": False,
                    "message": (
                        "The request could not be processed. "
                        "Please try again."
                    ),
                }

        if result.get("success", False):
            display_nutrition_result(result)
            assistant_message = result.get(
                "message",
                "Nutrition information found.",
            )
        else:
            assistant_message = result.get(
                "message",
                "I couldn't find reliable nutrition information.",
            )
            st.warning(assistant_message)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": assistant_message,
            "result": result if result.get("success", False) else None,
        }
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="app-footer">
        NutriBot • Natural Language Processing + USDA FoodData Central
    </div>
    """,
    unsafe_allow_html=True,
)
