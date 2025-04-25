from flask import Flask, jsonify, request, send_file
from agents import ERDiagramAgent, GanttDiagramAgent, QuestionGenerationAgent
from utils import extract_exam_questions, guess_correct_answer
import io
import os
import openai
from embedding_store import add_to_store, load_store
import numpy as np
import requests
from gradio_client import Client
import fitz
import re
import random
import json
import os.path
import uuid
import datetime

app = Flask(__name__)

client = Client("UNESCO/nllb")

# Agents initialization (you can also refactor this into a config or init function)
er_agent = ERDiagramAgent(
    blender_executable="C:/Program Files/Blender Foundation/Blender 4.4/blender.exe",
    blender_script="er_diagram_script.py",
    output_image_path="generated_er_diagram.png"
)

gantt_agent = GanttDiagramAgent(
    blender_executable="C:/Program Files/Blender Foundation/Blender 4.4/blender.exe",
    blender_script="gantt_diagram_script.py",
    output_image_path="generated_gantt_diagram.png"
)

question_agent = QuestionGenerationAgent()


HF_API_TOKEN = ""  # Get from huggingface.co/settings/tokens
TTS_API_URL = "https://huggingface.co/spaces/k2-fsa/text-to-speech"

client = Client("k2-fsa/text-to-speech")

# Path for storing feedback data
FEEDBACK_DIR = "feedback"
os.makedirs(FEEDBACK_DIR, exist_ok=True)
FEEDBACK_FILE = os.path.join(FEEDBACK_DIR, "question_feedback.jsonl")

def get_embedding(text, model="text-embedding-3-small"):
    response = openai.embeddings.create(input=[text], model=model)
    return np.array(response.data[0].embedding)

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def text_to_speech_hf(text):

    # Call the Gradio client predict method with necessary parameters
    result = client.predict(
        language="English",  # Language for TTS
        repo_id="csukuangfj/kokoro-en-v0_19|11 speakers",  # Model identifier
        text=text,  # Text input
        sid="0",  # Speaker ID (you can modify this if needed)
        speed=1,  # Speed of the speech
        api_name="/process"  # API endpoint for processing
    )

    # Gradio returns a file path to the generated audio
    # You can return this file content directly or use send_file to serve it
    if result:
        return result[0]  # result is expected to be a list where the first element is the audio file path
    else:
        raise Exception("TTS API error: No result returned from Gradio")
    
def extract_questions_from_pdf(pdf_path):
    # Check if we have a cached version of the extracted questions
    cache_path = pdf_path.replace('.pdf', '_cache.json')
    if os.path.exists(cache_path):
        with open(cache_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    # No cache found, extract questions from PDF
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    
    # Use OpenAI to extract and structure the questions
    prompt = f"""
    The following text contains exam questions in Spanish from a Civil Servant IT exam. 
    Please extract the multiple choice questions, and format them as a JSON array of question objects.
    Each question object should have:
    1. The question text (in both Spanish and translated to English)
    2. The options A, B, C, D (in both Spanish and translated to English)
    3. The correct answer
    4. A brief explanation in English
    5. The topic category (e.g., "Databases", "Networks", etc.)

    Here's a short excerpt of the text:
    {text[:3000]}...
    
    Return only valid JSON.
    """
    
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    
    try:
        # Extract just the JSON part from the response
        result_text = response.choices[0].message.content
        # Find JSON content (anything between first { and last })
        json_match = re.search(r'(\[.*\])', result_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
            questions = json.loads(json_str)
        else:
            questions = json.loads(result_text)
        
        # Cache the results for future use
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(questions, f, ensure_ascii=False, indent=2)
            
        return questions
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        print(f"Response: {result_text}")
        return []
    
@app.route("/")
def index():
    return jsonify({"message": "Welcome to the Civil Exam AI API"})

@app.route("/generate_question", methods=["POST"])
def generate_question():
    data = request.json
    topic = data.get("topic")
    level = data.get("level", "beginner")
    tts = data.get("tts", False)

    if not topic:
        return jsonify({"error": "Missing 'topic' in request"}), 400

    # Generate a unique ID for the question
    question_id = str(uuid.uuid4())

    def process_question_and_store(question):
        embedding = get_embedding(question)
        add_to_store(
            question_text=question,
            embedding=embedding,
            metadata={"topic": topic, "level": level, "question_id": question_id}
        )
        return question

    try:
        if topic == "ER Diagrams":
            er_image_path, json_path = er_agent.generate_er_diagram()
            question = question_agent.generate_mcq_from_er(er_image_path, json_path)
            process_question_and_store(question)

            if tts:
                audio_data = text_to_speech_hf(question)
                return send_file(audio_data, mimetype="audio/wav")
            else:
                return jsonify({"image": er_image_path, "question": question, "question_id": question_id})

        elif topic == "Project Management (Gantt)":
            gantt_image_path, json_path = gantt_agent.generate_gantt_diagram()
            question = question_agent.generate_mcq_from_gantt(gantt_image_path, json_path)
            process_question_and_store(question)

            if tts:
                audio_data = text_to_speech_hf(question)
                return send_file(audio_data, mimetype="audio/wav")
            else:
                return jsonify({"image": gantt_image_path, "question": question, "question_id": question_id})

        else:
            question = question_agent.generate_mcq(topic, level)
            process_question_and_store(question)

            if tts:
                audio_data = text_to_speech_hf(question)
                return send_file(audio_data, mimetype="audio/wav")
            else:
                return jsonify({"question": question, "question_id": question_id})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/question_feedback", methods=["POST"])
def question_feedback():
    """Endpoint to receive feedback on generated questions"""
    data = request.json
    question_id = data.get("question_id")
    feedback = data.get("feedback")  # "positive" for thumbs up
    session_id = data.get("session_id")
    
    if not all([question_id, feedback, session_id]):
        return jsonify({"error": "Missing required feedback data"}), 400
    
    # Record the feedback
    feedback_entry = {
        "question_id": question_id,
        "feedback": feedback,
        "session_id": session_id,
        "timestamp": datetime.datetime.now().isoformat()
    }
    
    # Append to the feedback file
    with open(FEEDBACK_FILE, "a") as f:
        f.write(json.dumps(feedback_entry) + "\n")
    
    return jsonify({"status": "success", "message": "Feedback recorded"})

@app.route("/get_exam_questions", methods=["POST"])
def get_exam_questions():
    data = request.json
    year = data.get("year", "2020")
    topic = data.get("topic")
    count = data.get("count", 5)
    translate = data.get("translate", False)  # <- properly get the flag from frontend

    try:
        pdf_path = f"Exams/{year}.pdf"
        if not os.path.exists(pdf_path):
            return jsonify({"error": f"Exam for year {year} not found"}), 404

        all_questions = extract_exam_questions(pdf_path, topic)
        if not all_questions:
            return jsonify({"error": "No questions found in the PDF"}), 404

        filtered_questions = [q for q in all_questions if topic.lower() in q.get("topic", "").lower()] if topic else all_questions
        selected_questions = random.sample(filtered_questions, min(count, len(filtered_questions)))
        # Add guessed correct answer to each question

        for q in selected_questions:
            guessed_answer = guess_correct_answer(q["question"], q["options"])
            print(f"Guessed answer: {guessed_answer}")
            
            # Extract guessed letter (like 'c') from 'c) las variables en...'
            match = re.match(r"([a-dA-D])\)", guessed_answer.strip())
            if match:
                guessed_letter = match.group(1).lower()
                index = ord(guessed_letter) - 97  # 'a' -> 0, 'b' -> 1, etc.
                if 0 <= index < len(q["options"]):
                    q["correct_answer"] = f"{guessed_letter})"
                else:
                    q["correct_answer"] = "?"
            else:
                q["correct_answer"] = "?"
            
            question_with_options = q["question"] + "\n"
            for key, value in q["options"].items():
                question_with_options += f"{key}) {value}\n"

            embedding = get_embedding(question_with_options)

            add_to_store(
                question_text=question_with_options,
                embedding = embedding,
                metadata={
                    "topic": topic or "General",
                    "source": f"Exam {year}",
                    "level": "exam"
                },
                correct_answer=q["correct_answer"]
            )

        # Translate if requested
        if translate:
            translated_questions = []
            for q in selected_questions:
                translation_response = requests.post(
                    "http://localhost:5000/translate_question",
                    json={
                        "question": q["question"],
                        "options": q["options"],
                        "src_lang": "Spanish",
                        "tgt_lang": "English"
                    }
                )

                if translation_response.status_code == 200:
                    translated_data = translation_response.json()
                    translated_questions.append({
                        "question": translated_data["question"],
                        "options": translated_data["options"],
                        "correct_answer": q["correct_answer"]
                    })
                else:
                    # If translation fails, just fallback to original
                    translated_questions.append(q)

            return jsonify({"questions": translated_questions})
        else:
            return jsonify({"questions": selected_questions})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/translate_question", methods=["POST"])
def translate_question():
    try:
        data = request.json
        question_text = data.get("question")
        options = data.get("options", {})
        src_lang = data.get("src_lang", "Spanish")
        tgt_lang = data.get("tgt_lang", "English")

        if not question_text:
            return jsonify({"error": "Missing question text"}), 400

        client = Client("UNESCO/nllb")

        # Translate the main question
        translated_question = client.predict(
            text=question_text,
            src_lang=src_lang,
            tgt_lang=tgt_lang,
            api_name="/translate"
        )

        # Translate options
        translated_options = {}
        for key, value in options.items():
            translated_value = client.predict(
                text=value,
                src_lang=src_lang,
                tgt_lang=tgt_lang,
                api_name="/translate"
            )
            translated_options[key] = translated_value

        return jsonify({
            "question": translated_question,
            "options": translated_options
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/semantic_search", methods=["POST"])
def semantic_search():
    data = request.json
    query = data.get("query")

    if not query:
        return jsonify({"error": "Missing 'query'"}), 400

    query_emb = get_embedding(query)
    store = load_store()

    results = []
    for item in store:
        emb = np.array(item["embedding"])
        sim = cosine_similarity(query_emb, emb)
        results.append((sim, item))

    results.sort(key=lambda x: x[0], reverse=True)
    top3 = results[:3]

    formatted_results = []
    for sim, item in top3:
        is_exam_question = 'source' in item.get('metadata', {}) and 'Exam' in item['metadata'].get('source', '')

        if is_exam_question and 'correct_answer' in item:
            text = item['text']
            question_text = text
            options = {}

            # Extract options like a) ..., b) ..., etc.
            option_matches = re.findall(r'([a-dA-D])\)\s*(.*?)(?=\n[a-dA-D]\)|$)', text, re.DOTALL)

            if option_matches:
                first_option = f"{option_matches[0][0]})"
                question_parts = text.split(first_option)
                if len(question_parts) > 0:
                    question_text = question_parts[0].strip()

                for opt_letter, opt_text in option_matches:
                    options[opt_letter.lower()] = opt_text.strip()

            # Format the output
            formatted_text = f"Question: {question_text}\n"
            for letter in ['a', 'b', 'c', 'd']:
                if letter in options:
                    formatted_text += f"{letter}) {options[letter]}\n"

            if item.get('correct_answer'):
                formatted_text += f"Correct Answer: {item['correct_answer']}\n"

            formatted_results.append({
                "similarity": round(float(sim), 3),
                "text": formatted_text,
                "metadata": item["metadata"],
                "correct_answer": item.get("correct_answer", "?")
            })
        else:
            formatted_results.append({
                "similarity": round(float(sim), 3),
                "text": item["text"],
                "metadata": item["metadata"],
                "correct_answer": item.get("correct_answer", "?")
            })

    return jsonify({"results": formatted_results})


@app.route("/get_feedback_stats", methods=["GET"])
def get_feedback_stats():
    """Endpoint to get feedback statistics (for admin use)"""
    if not os.path.exists(FEEDBACK_FILE):
        return jsonify({"total_feedback": 0, "positive_feedback": 0})
    
    try:
        feedback_entries = []
        with open(FEEDBACK_FILE, "r") as f:
            for line in f:
                if line.strip():
                    feedback_entries.append(json.loads(line))
        
        total_feedback = len(feedback_entries)
        positive_feedback = sum(1 for entry in feedback_entries if entry.get("feedback") == "positive")
        
        return jsonify({
            "total_feedback": total_feedback,
            "positive_feedback": positive_feedback,
            "positive_percentage": (positive_feedback / total_feedback * 100) if total_feedback > 0 else 0,
            "recent_feedback": feedback_entries[-10:] if total_feedback > 0 else []
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)