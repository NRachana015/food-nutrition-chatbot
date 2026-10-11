import html

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
        padding-top: 1.8rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }

    .app-header {
        padding: 1.5rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        background: linear-gradient(120deg, #e7f8ed, #e8f3ff);
        color: #183b2a;
    }

    .app-header h1 {
        margin-bottom: 0.3rem;
    }

    .app-footer {
        text-align: center;
        color: #808080;
        font-size: 0.85rem;
        padding: 1.5rem 0 0.5rem;
    }

    [data-testid="stMetric"] {
        border: 1px solid rgba(128, 128, 128, 0.2);
        padding: 14px;
        border-radius: 12px;
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
    st.markdown("# 🥗 NutriBot")
    st.caption("AI Nutrition Assistant")

    st.success("USDA FoodData Central")

    st.markdown("---")
    st.markdown("### 💡 Try these examples")

    examples = [
        "What is the nutrition in 100g banana?",
        "Nutrition in 100g apple",
        "What is the nutrition in 100g chicken?",
        "Nutrition in 200g rice",
        "What is the nutrition in 100g egg?",
    ]

    for example in examples:
        if st.button(example, key=f"example_{example}", use_container_width=True):
            st.session_state.pending_prompt = example
            st.rerun()

    st.markdown("---")

    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.pending_prompt = None
        st.rerun()

    st.markdown("---")
    st.caption("Nutrition information is retrieved from USDA FoodData Central when a reliable match is available.")


# ============================================================
# MAIN HEADER
# ============================================================

st.markdown(
    """
    <div class="app-header">
        <h1>🥗 NutriBot — Food Nutrition Chatbot</h1>
        <p>
            Discover nutritional information for different foods
            using natural language and USDA FoodData Central.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    "Ask about a food and its quantity to explore its calories, "
    "macronutrients, vitamins, and minerals."
)


# ============================================================
# DISPLAY NUTRITION RESULTS
# ============================================================

def display_nutrition_result(result):
    """Display nutrition information and an interactive chart."""

    nutrition = result.get("nutrition") or {}
    food_name = result.get("food") or result.get("description") or "Food"
    quantity = result.get("quantity_g", 100)

    st.markdown(f"### 🍎 Nutrition Information: {html.escape(str(food_name))}")

    if quantity is not None:
        st.caption(f"Serving size: {quantity} g")

    # Primary nutrition values
    calories = float(nutrition.get("calories") or 0)
    protein = float(nutrition.get("protein_g") or 0)
    carbohydrates = float(nutrition.get("carbohydrates_g") or 0)
    fat = float(nutrition.get("fat_g") or 0)

    columns = st.columns(4)

    with columns[0]:
        st.metric("🔥 Calories", f"{calories:.2f} kcal")

    with columns[1]:
        st.metric("💪 Protein", f"{protein:.2f} g")

    with columns[2]:
        st.metric("🍞 Carbohydrates", f"{carbohydrates:.2f} g")

    with columns[3]:
        st.metric("🥑 Fat", f"{fat:.2f} g")

    # Additional nutrients
    st.markdown("#### 🧪 Additional Nutrients")

    additional_nutrients = [
        ("Fiber", "fiber_g", "g"),
        ("Sugar", "sugar_g", "g"),
        ("Calcium", "calcium_mg", "mg"),
        ("Iron", "iron_mg", "mg"),
        ("Sodium", "sodium_mg", "mg"),
        ("Vitamin C", "vitamin_c_mg", "mg"),
    ]

    available = []

    for label, key, unit_name in additional_nutrients:
        value = nutrition.get(key)

        if value is not None:
            try:
                available.append((label, float(value), unit_name))
            except (TypeError, ValueError):
                continue

    if available:
        columns = st.columns(min(3, len(available)))

        for index, (label, value, unit_name) in enumerate(available):
            with columns[index % len(columns)]:
                st.metric(label, f"{value:.2f} {unit_name}")
    else:
        st.info("No additional nutrient values are available.")

    # Macronutrient chart
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

    chart_data = (
        chart_data[chart_data["Grams"] > 0]
        .sort_values("Grams", ascending=True)
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

        # Interactive chart only — no download buttons.
        st.plotly_chart(
            fig,
            use_container_width=True,
            key="nutrition_macronutrient_profile",
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

            if score is not None:
                try:
                    st.write(f"{float(score):.2f}")
                except (TypeError, ValueError):
                    st.write(score)
            else:
                st.write("N/A")

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
