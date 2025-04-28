# pracTICe

**pracTICe** is an AI-powered application designed to help students pass the first exam of the **TIC Civil Servant Corps** in Spain.  
It offers interactive study tools, including random quizzes, real exam simulations, and semantic search for questions, with features like text-to-speech and translation support.

---

## Features

### 1. Topic Practice
- Select a topic and generate **random multiple-choice questions**.
- View the **correct answer** and a detailed **explanation**.
- Listen to the question via **text-to-speech**.
- Submit **feedback** if you believe the question or answer needs revision.

### 2. Exam Simulation
- Choose the number of questions (1–20).
- Select a real exam from **2017 to 2020**.
- **Translate** responses into **English** if needed.

### 3. Semantic Search
- Search by **topic** or **keyword**.
- Get **similar related questions** to deepen understanding.

---

## How to Run the App

1. **Clone the repository**:

    ```bash
    git clone https://github.com/your-username/practice.git
    cd practice
    ```

2. **Install the required packages**:
    ```text
    Flask==3.1.0
    streamlit==1.44.1
    openai==1.72.0
    huggingface-hub==0.30.2
    deep-translator==1.11.4
    requests==2.32.3
    python-dotenv==1.1.0
    ```

4. **Set up your API keys**:

    - In `utils.py`, assign your OpenAI API key:

      ```python
      # utils.py
      api_key = "sk-your-openai-api-key"
      openai.api_key = api_key
      ```

    - In `flask_api.py`, assign your Hugging Face API token:

      ```python
      # flask_api.py
      HF_API_TOKEN = "hf-your-huggingface-api-token"
      TTS_API_URL = "https://huggingface.co/spaces/k2-fsa/text-to-speech"
      ```

5. **Start the Flask server**:

    ```bash
    python flask_api.py
    ```

6. **In another terminal, run the Streamlit app**:

    ```bash
    streamlit run app.py
    ```

7. **Open your browser** and interact with **pracTICe**!
