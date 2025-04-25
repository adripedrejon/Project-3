import streamlit as st
from utils import generate_mcq, generate_mcq_from_er, generate_mcq_from_gantt, generate_er_diagram, generate_gantt_chart, extract_exam_questions
import subprocess
import os
import json
from PIL import Image
import time
import uuid
import requests
import io
import base64
from io import BytesIO
import datetime

# Set page configuration
st.set_page_config(page_title="pracTICe - Civil Servant Exam Trainer", layout="wide")

# Add custom CSS for styling with new exam container
st.markdown("""
    <style>
        .title {
            color: #2C3E50;
            font-weight: bold;
        }
        .section-title {
            font-size: 22px;
            color: #2980B9;
            font-weight: 600;
            margin-bottom: 10px;
        }
        .button {
            background-color: #2980B9;
            color: white;
            font-weight: bold;
            border-radius: 5px;
        }
        .button:hover {
            background-color: #3498DB;
        }
        .stTextInput>div>div>input {
            background-color: #ecf0f1;
        }
        .stSelectbox>div>div>div {
            background-color: #ecf0f1;
        }
        .stCheckbox>div>div>label {
            color: #2980B9;
        }
        .stMarkdown {
            color: #34495E;
        }
        
        /* Container styles */
        .create-container {
            background-color: #EFF7FA;
            padding: 20px;
            border-radius: 10px;
            border-left: 5px solid #2980B9;
            margin-bottom: 20px;
        }
        .search-container {
            background-color: #F5F9EE;
            padding: 20px;
            border-radius: 10px;
            border-left: 5px solid #27AE60;
            margin-bottom: 20px;
        }
        
        /* New exam container style */
        .exam-container {
            background-color: #FFF8E1;
            padding: 20px;
            border-radius: 10px;
            border-left: 5px solid #F39C12;
            margin-bottom: 20px;
        }
        
        /* Divider style */
        .custom-divider {
            height: 3px;
            background: linear-gradient(to right, #2980B9, transparent);
            margin: 10px 0 20px 0;
        }
        
        .search-divider {
            height: 3px;
            background: linear-gradient(to right, #27AE60, transparent);
            margin: 10px 0 20px 0;
        }
        
        /* New exam divider style */
        .exam-divider {
            height: 3px;
            background: linear-gradient(to right, #F39C12, transparent);
            margin: 10px 0 20px 0;
        }
        
        /* Main app title */
        .app-title {
            text-align: center;
            padding: 15px;
            background: linear-gradient(to right, #2C3E50, #4CA1AF);
            color: white;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        
        .app-subtitle {
            text-align: center;
            color: #34495E;
            margin-bottom: 25px;
            font-style: italic;
        }
        
        /* Question card style */
        .question-card {
            background-color: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            margin-bottom: 15px;
        }
        
        /* Feedback buttons */
        .feedback-container {
            display: flex;
            justify-content: flex-end;
            margin-top: 10px;
        }
        
        .feedback-button {
            background-color: transparent;
            border: none;
            font-size: 24px;
            cursor: pointer;
            margin-left: 10px;
            transition: transform 0.2s;
        }
        
        .feedback-button:hover {
            transform: scale(1.2);
        }
        
        .thumbs-up {
            color: #27AE60;
        }
        
        .thumbs-up.active {
            color: #27AE60;
            animation: pulse 0.5s;
        }
        
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.3); }
            100% { transform: scale(1); }
        }
    </style>
""", unsafe_allow_html=True)


# Title and Slogan with enhanced styling
st.markdown("<div class='app-title'><h1>pracTICe – Your AI-powered Civil Servant Exam Trainer 🎓</h1></div>", unsafe_allow_html=True)
st.markdown("<div class='app-subtitle'>Prepare with AI-generated practice questions from official IT Civil Servant topics. Train smart, practice hard!</div>", unsafe_allow_html=True)

# Initialize session state variables
if 'session_id' not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if 'question_id' not in st.session_state:
    st.session_state.question_id = None
if 'feedback_submitted' not in st.session_state:
    st.session_state.feedback_submitted = False
if 'feedback_message' not in st.session_state:
    st.session_state.feedback_message = ""
if 'current_question' not in st.session_state:
    st.session_state.current_question = None

# Function to handle feedback submission
# Replace the submit_feedback function with this updated version
def submit_feedback(feedback_type):
    try:
        feedback_response = requests.post(
            "http://localhost:5000/question_feedback",
            json={
                "question_id": st.session_state.question_id,
                "feedback": feedback_type,
                "session_id": st.session_state.session_id
            }
        )
        
        # Save feedback to local file
        with open("feedback_log.txt", "a") as f:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"{timestamp} | Question ID: {st.session_state.question_id} | Feedback: {feedback_type} | Session: {st.session_state.session_id} | Topic: {st.session_state.last_topic} | Level: {st.session_state.last_level}\n")
        
        if feedback_response.status_code == 200:
            st.session_state.feedback_submitted = True
            message = "Thanks for your positive feedback!" if feedback_type == "positive" else "Thanks for your feedback. We'll improve our questions!"
            st.session_state.feedback_message = message
            st.rerun()

    except Exception as e:
        st.session_state.feedback_message = f"Error sending feedback: {e}"
        st.rerun()
# Create tabs for different modes
tab1, tab2, tab3 = st.tabs(["Practice Questions", "Real Exam Questions", "Search Questions"])

# Tab 1: Practice Questions
with tab1:
    # Create Question Section with a distinct background
    st.markdown("<div class='create-container'>", unsafe_allow_html=True)
    st.markdown("## <span class='section-title'>Create a Practice Question</span>", unsafe_allow_html=True)
    st.markdown("<div class='custom-divider'></div>", unsafe_allow_html=True)

    # Topic selection
    topic = st.selectbox("Choose a topic", [
        "Spanish Constitution (La Constitución Española)",
        "Law 39/2015 - Administrative Procedure",
        "Law 40/2015 - Legal Regime",
        "Information Systems in Public Administration",
        "Operating Systems",
        "Networks",
        "Databases",
        "Software Engineering",
        "Cybersecurity",
        "ER Diagrams",
        "Project Management (Gantt)"
    ])

    # Difficulty level
    level = st.radio("Select difficulty", ["beginner", "intermediate", "advanced"], horizontal=True)

    # Option for Text-to-Speech
    use_tts = st.checkbox("🔊 Read the question aloud (Text-to-Speech)")

    # Button to generate question with enhanced styling
    if st.button("🎯 Generate Question", key="generate", help="Generate a new question", use_container_width=True):
        # Save the current topic and level for logging
        st.session_state.last_topic = topic
        st.session_state.last_level = level
        
        # Reset feedback state
        st.session_state.feedback_submitted = False
        st.session_state.feedback_message = ""
        
        with st.spinner("Generating question..."):
            try:
                response = requests.post("http://localhost:5000/generate_question", 
                                         json={"topic": topic, "level": level, "tts": use_tts})

                # Check if response is audio (TTS enabled)
                if response.headers.get("Content-Type", "").startswith("audio"):
                    st.audio(response.content, format="audio/wav")
                else:
                    result = response.json()

                    if "error" in result:
                        st.error(result["error"])
                    else:
                        # Store the question data
                        st.session_state.question_id = result.get("question_id")
                        st.session_state.current_question = result
            except requests.exceptions.RequestException as e:
                st.error(f"Connection error: {e}")

    # Display current question if available
    if st.session_state.current_question:
        result = st.session_state.current_question
        
        # Handle image if available (for ER or Gantt diagrams)
        if "image" in result:
            try:
                image_path = result["image"]
                with open(image_path, "rb") as f:
                    img = Image.open(io.BytesIO(f.read()))
                    img = img.resize((800, 600))
                    st.image(img, caption=f"{st.session_state.last_topic} Diagram", width=700)
            except Exception as e:
                st.warning(f"Couldn't load the image: {e}")

        st.markdown("<div class='custom-divider'></div>", unsafe_allow_html=True)
        st.markdown(result["question"], unsafe_allow_html=True)
        
        # Display feedback section only if feedback hasn't been submitted
        if not st.session_state.feedback_submitted:
            st.markdown("<div class='custom-divider'></div>", unsafe_allow_html=True)
            st.markdown("<p>Was this question helpful?</p>", unsafe_allow_html=True)
            
            # Create columns for the buttons
            col1, col2, col3 = st.columns([1, 1, 8])
            
            # Thumbs up button
            with col1:
                if st.button("👍", key="thumbs_up"):
                    submit_feedback("positive")
            
            # Thumbs down button
            with col2:
                if st.button("👎", key="thumbs_down"):
                    submit_feedback("negative")
        
        # Display feedback message if feedback has been submitted
        elif st.session_state.feedback_message:
            st.success(st.session_state.feedback_message)

    st.markdown("</div>", unsafe_allow_html=True)

# Tab 2: Real Exam Questions (code unchanged)
with tab2:
    st.markdown("<div class='exam-container'>", unsafe_allow_html=True)
    st.markdown("## <span class='section-title'>Official Exam Questions</span>", unsafe_allow_html=True)
    st.markdown("<div class='exam-divider'></div>", unsafe_allow_html=True)
    
    st.markdown("Access real questions from previous civil servant exams. Questions are automatically translated from Spanish to English.")
    
    # Exam year selection
    exam_year = st.selectbox("Select Exam Year", ["2020", "2019", "2018", "2017"], key="exam_year")
    
    # Translation option
    translate = st.checkbox("Translate questions to English", value=True)
    
    # Number of questions to show
    num_questions = st.slider("Number of questions to show", 1, 20, 5)
    
    # Button to fetch exam questions
    if st.button("📝 Get Exam Questions", key="get_exam", help="Fetch questions from official exams", use_container_width=True):
        with st.spinner("Extracting and translating exam questions..."):
            try:
                response = requests.post(
                    "http://localhost:5000/get_exam_questions", 
                    json={
                        "year": exam_year,
                        "count": num_questions,
                        "translate": translate  # Include the translation flag
                    }
                )
                
                result = response.json()
                
                if "error" in result:
                    st.error(result["error"])
                elif "questions" in result and result["questions"]:
                    st.success(f"Found {len(result['questions'])} questions from the {exam_year} exam")
                    
                    for i, q in enumerate(result["questions"]):
                        with st.container():
                            st.markdown(f"""
                            <div class="question-card">
                                <p><strong>Question {i+1}:</strong> {q['question']}</p>
                                <p>a) {q['options']['a']}</p>
                                <p>b) {q['options']['b']}</p>
                                <p>c) {q['options']['c']}</p>
                                <p>d) {q['options']['d']}</p>
                                <details>
                                    <summary>View Answer</summary>
                                    <p><strong>Correct Answer:</strong> {q['correct_answer']}</p>
                                </details>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.warning("No questions found for the selected criteria.")
            
            except requests.exceptions.RequestException as e:
                st.error(f"Connection error: {e}")
    
    st.markdown("</div>", unsafe_allow_html=True)

# Tab 3: Search Questions (code unchanged)
with tab3:
    st.markdown("<div class='search-container'>", unsafe_allow_html=True)
    st.markdown("## <span class='section-title'>Search Similar Questions</span>", unsafe_allow_html=True)
    st.markdown("<div class='search-divider'></div>", unsafe_allow_html=True)
    
    st.markdown("Enter your question or topic below to search for similar questions.")
    
    search_query = st.text_input("Enter your question or topic...", key="search_query")

    # Button with green styling
    if st.button("🔍 Search Similar Questions", key="search", help="Search for similar questions based on your query", use_container_width=True):
        with st.spinner("Finding similar questions..."):
            try:
                response = requests.post("http://localhost:5000/semantic_search", json={"query": search_query})
                results = response.json().get("results", [])

                if not results:
                    st.warning("No similar questions found.")
                else:
                    for idx, res in enumerate(results):
                        result_container = st.container()
                        with result_container:
                            st.markdown(f"**Similarity:** {res['similarity']:.2f}")
                            st.markdown(res["text"])
                            meta = res['metadata']
                            st.markdown(f"*Topic: {meta['topic']} | Level: {meta['level']}*")
                            if idx < len(results) - 1:
                                st.markdown("<div class='search-divider'></div>", unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Error: {e}")
    
    st.markdown("</div>", unsafe_allow_html=True)