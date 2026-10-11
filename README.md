# 🥗 Food Nutrition Chatbot Using NLP — NutriBot

<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=0:11998e,100:38ef7d&height=200&section=header&text=NutriBot&fontSize=65&fontColor=ffffff&animation=fadeIn&fontAlignY=35&desc=AI-Powered%20Nutrition%20Assistant&descAlignY=58&descSize=20" width="100%" alt="NutriBot banner"/>
</p>

<p align="center">
  <b>Ask about any food. Understand its nutrition. Make informed food choices.</b>
</p>

<p align="center">
  <a href="https://food-nutrition-chatbot-4ys8af95qffyeu48wtu6wm.streamlit.app/">
    <img src="https://img.shields.io/badge/🚀_Live_Demo-Open_NutriBot-FF4B4B?style=for-the-badge" alt="Live Demo"/>
  </a>
  <a href="https://github.com/NRachana015/food-nutrition-chatbot">
    <img src="https://img.shields.io/badge/GitHub-Repository-181717?style=for-the-badge&logo=github" alt="GitHub Repository"/>
  </a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/NLP-Natural%20Language%20Processing-8A2BE2?style=flat-square" alt="NLP"/>
  <img src="https://img.shields.io/badge/Streamlit-Web%20Application-FF4B4B?style=flat-square&logo=streamlit&logoColor=white" alt="Streamlit"/>
  <img src="https://img.shields.io/badge/Data-USDA%20FoodData%20Central-228B22?style=flat-square" alt="USDA"/>
  <img src="https://img.shields.io/badge/Testing-Pytest-0A9EDC?style=flat-square&logo=pytest&logoColor=white" alt="Pytest"/>
</p>

---

## 📌 Project Overview

**NutriBot** is an AI-powered nutrition chatbot that uses Natural Language Processing (NLP) and the USDA FoodData Central API to retrieve nutritional information about foods.

Users can ask questions in natural language, specify food quantities, and view nutrition information through an interactive web interface.

Unlike a chatbot restricted to a small hardcoded list of foods, NutriBot searches an external food database dynamically and ranks possible matches to identify a suitable nutrition record.

The application displays calories, macronutrients, additional nutrients, and a graphical macronutrient profile.

## 🌐 Live Application

**Try NutriBot here:**

👉 https://food-nutrition-chatbot-4ys8af95qffyeu48wtu6wm.streamlit.app/

The application is deployed using Streamlit Community Cloud.

---

## ✨ Key Features

- 💬 **Natural Language Queries** — Ask nutrition questions using everyday language.
- 🔎 **Dynamic Food Search** — Retrieve food records from USDA FoodData Central rather than relying on a small predefined nutrition dictionary.
- 🧠 **NLP-Based Processing** — Normalize food names and process user queries.
- ✍️ **Spelling Correction** — Handle supported misspellings, such as `chickwn wings`.
- ⚖️ **Quantity-Based Calculations** — Calculate nutrition values for requested quantities when the quantity can be interpreted.
- 🔥 **Calorie Information** — Display food energy in kilocalories (kcal).
- 💪 **Macronutrient Analysis** — Display protein, carbohydrates, fat, and fiber.
- 🧪 **Additional Nutrients** — Show available information for sugar, calcium, iron, sodium, and vitamin C.
- 📊 **Interactive Nutrition Chart** — Visualize macronutrients using a horizontal bar chart.
- 🛡️ **Reliable-Match Validation** — Apply food matching and scoring rules before displaying nutrition information.
- 🚫 **Safe Unknown-Food Handling** — Inform users when a reliable food match cannot be found.
- ☁️ **Cloud Deployment** — Access the chatbot through a web browser.
- 🧪 **Automated Testing** — Validate important application behaviors using pytest.

---

## 🖥️ Application Screenshots

### 1. NutriBot Dashboard

![NutriBot Dashboard](dashboard.png)

### 2. Nutrition Information

![NutriBot Nutrition Results](result01.png)

### 3. Additional Nutrition Results

![NutriBot Additional Results](result02.png)

---

## 🥑 Nutritional Information Provided

NutriBot can display the following values when they are available in the selected USDA food record.

| Nutrient | Unit |
|---|---|
| Calories | kcal |
| Protein | g |
| Carbohydrates | g |
| Fat | g |
| Dietary Fiber | g |
| Sugar | g |
| Calcium | mg |
| Iron | mg |
| Sodium | mg |
| Vitamin C | mg |

The application also displays food-source metadata, including the USDA data type, FoodData Central ID (FDC ID), and match score.

**Note:** Results depend on the selected USDA food record, available nutrient data, and the requested quantity. Nutrition values are estimates for the matched food, not personalized medical advice.

---

## 🔍 Example Queries

Try asking NutriBot questions such as:

```text
What is the nutrition in 100g banana?

What is the nutrition in 2 eggs?

What is the nutrition in 200g mango?

What is the nutrition in dragon fruit?

What is the nutrition in chickwn wings?

What is the nutrition in xyzabc food?
```

Expected behavior:

- Recognized foods return available nutrition information.
- Supported spelling corrections can help identify the intended food.
- Quantity-based requests calculate nutrition for the interpreted quantity.
- Unknown foods receive a helpful message rather than fabricated nutrition values.

---

## ⚙️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core application logic |
| Natural Language Processing | Query processing and food-name normalization |
| USDA FoodData Central API | External food and nutrition data |
| Requests | HTTP communication with the API |
| RapidFuzz | Fuzzy text matching |
| Streamlit | Interactive web application |
| Plotly | Nutrition data visualization |
| python-dotenv | Local environment configuration |
| Pytest | Automated testing |
| Git and GitHub | Version control and project hosting |
| Streamlit Community Cloud | Application deployment |

---

## 🏗️ System Architecture

```text
        User
         |
         v
  Natural Language Query
         |
         v
    Streamlit UI
         |
         v
   NLP Processing
         |
         v
 Food Name & Quantity
     Identification
         |
         v
 Dynamic USDA API Search
         |
         v
   Food Match Ranking
         |
         v
  Nutrition Extraction
         |
         v
 Quantity-Based Calculation
         |
         v
 Nutrition Summary + Chart
         |
         v
    User Response
```

---

## 🔄 How It Works

1. **User input:** The user enters a food-related question.
2. **NLP processing:** The application processes the query and normalizes the food name.
3. **Quantity interpretation:** The system identifies the requested amount when supported.
4. **Dynamic retrieval:** The nutrition service searches USDA FoodData Central.
5. **Food matching:** Candidate records are evaluated and ranked using the project's matching rules.
6. **Nutrition extraction:** Available nutrient values are extracted from the selected record.
7. **Calculation:** Values are adjusted for the requested quantity when applicable.
8. **Visualization:** The application displays nutrition information and a macronutrient chart.
9. **Safe response:** If no sufficiently reliable match is found, the chatbot reports that it could not find reliable information.

---

## 📂 Project Structure

```text
food-nutrition-chatbot/
│
├── app.py
├── chatbot.py
├── nlp_processor.py
├── nutrition_service.py
├── config.py
├── requirements.txt
├── .env.example
├── .gitignore
│
├── dashboard.png
├── result01.png
├── result02.png
│
└── README.md
```

Additional files, such as tests and configuration files, may also be present in the repository.

---

## 🚀 Run Locally

### Prerequisites

- Python 3.12 recommended
- Git
- A USDA FoodData Central API key

### 1. Clone the repository

```bash
git clone https://github.com/NRachana015/food-nutrition-chatbot.git
```

### 2. Enter the project directory

```bash
cd food-nutrition-chatbot
```

### 3. Create a virtual environment

```bash
python -m venv venv
```

### 4. Activate the environment

**Windows PowerShell:**

```powershell
.\venv\Scripts\Activate.ps1
```

### 5. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 6. Configure the USDA API key

Obtain an API key from the USDA FoodData Central website:

https://fdc.nal.usda.gov/api-guide.html

Create a local `.env` file in the project directory and add:

```env
USDA_API_KEY=your_actual_api_key
```

Replace the placeholder with your own key.

**Security:** Never commit `.env` or publish your real API key. For Streamlit Cloud, configure the key through the application's Secrets settings.

### 7. Start the application

```bash
streamlit run app.py
```

Open the local URL shown in your terminal, usually:

```text
http://localhost:8501
```

---

## 🧪 Running Tests

Activate your virtual environment and run:

```bash
python -m pytest -v
```

The project's previously recorded test run completed with **41 passed**. Run the tests again against the current code to verify the latest repository state.

---

## 🔐 Security and Data Reliability

- API credentials are configured through environment variables or Streamlit Secrets.
- The `.env` file should remain excluded from version control.
- Nutrition values are retrieved from external food records when a reliable match is available.
- Match scoring helps distinguish suitable food records from unsuitable alternatives.
- Unrecognized food queries should not be answered with invented nutrition values.
- USDA data may differ depending on the food description, preparation method, and dataset selected.

---

## 🎯 Project Objectives

- Build an interactive NLP-based nutrition assistant.
- Integrate an external food database through an API.
- Support natural-language food queries.
- Process food names and quantities.
- Apply matching and validation rules to food search results.
- Calculate nutrition for supported quantities.
- Present results in a clear visual format.
- Handle unsupported food queries safely.
- Deploy a Python application to the cloud.

---

## 🔮 Future Enhancements

- 🥗 Meal-level nutrition analysis
- 📅 Daily nutrition tracking
- 👤 Personalized nutrition profiles
- 📈 Nutrition history and analytics
- 🎙️ Voice-based food queries
- 🌐 Multilingual food-name support
- 🔍 Further improvements to semantic food matching
- 📱 Enhanced mobile experience
- 📥 Nutrition report export
- 🧾 Broader food-source integration

---

## 👩‍💻 Author

<p align="center">
  <b>Rachana Nyavanandhi</b><br/>
  B.Tech — Artificial Intelligence and Machine Learning
</p>

<p align="center">
  <a href="https://github.com/NRachana015">
    <img src="https://img.shields.io/badge/GitHub-NRachana015-181717?style=for-the-badge&logo=github" alt="GitHub Profile"/>
  </a>
</p>

**Project Repository:**  
https://github.com/NRachana015/food-nutrition-chatbot

**Live Demo:**  
https://food-nutrition-chatbot-4ys8af95qffyeu48wtu6wm.streamlit.app/

---

<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=0:11998e,100:38ef7d&height=120&section=footer" width="100%" alt="Footer banner"/>
</p>

<p align="center">
  <b>🥗 NutriBot — Natural Language Processing • Dynamic Food Retrieval • Nutrition Visualization</b>
</p>

<p align="center">
  ⭐ If you find this project useful, consider giving the repository a star!
</p>