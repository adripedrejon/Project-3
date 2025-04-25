from openai import OpenAI
import streamlit as st
import urllib.parse
import pytesseract
import traceback
import re
import subprocess
import os
import json
from PIL import Image
import time
import uuid
from dotenv import load_dotenv
import openai
import fitz
import random

# Set the Tesseract executable path
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# Assign the API key directly
api_key = "" # Insert your API key

# Set the OpenAI API key
openai.api_key = api_key


def generate_er_diagram():
    try:
        # Create a unique filename for this session to avoid conflicts
        unique_id = str(uuid.uuid4())[:8]
        output_dir = os.getcwd()
        output_image_path = os.path.join(output_dir, f"generated_er_diagram_{unique_id}.png")
        json_path = os.path.join(output_dir, f"generated_er_diagram_{unique_id}.json")
        
        # Path to the Blender executable and Blender script
        blender_executable = r"C:\Program Files\Blender Foundation\Blender 4.4\blender.exe"
        blender_script = os.path.join(os.getcwd(), "er_diagram_script.py")
        
        st.info("Generating ER diagram using Blender (this may take a few seconds)...")
        
        # Run Blender command to generate ER diagram
        cmd = [
            blender_executable,
            "-b",  # Run Blender in background mode (no UI)
            "--python", blender_script,  # Blender script path
            "--",  # Separate Blender arguments from script arguments
            "--output", output_image_path  # Pass the output image path as an argument
        ]
        
        # For debugging
        #st.write(f"Running command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            check=True, 
            capture_output=True, 
            text=True
        )
        
        # Check if the file was created
        if os.path.exists(output_image_path):
            #st.success("ER diagram generated successfully!")
            # Check if the JSON file was created
            if os.path.exists(json_path):
                return output_image_path, json_path
            else:
                st.warning("JSON data not found, will use OCR to extract diagram information.")
                return output_image_path, None
        else:
            st.error(f"Blender execution successful but output file not found at {output_image_path}")
            st.text(f"Blender output: {result.stdout}")
            st.text(f"Blender errors: {result.stderr}")
            return None, None
            
    except subprocess.CalledProcessError as e:
        st.error(f"Error running Blender: {e}")
        st.text(f"Command output: {e.stdout}")
        st.text(f"Error output: {e.stderr}")
        return None, None
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        return None, None

def generate_gantt_chart():
    try:
        # Create a unique filename for this session to avoid conflicts
        unique_id = str(uuid.uuid4())[:8]
        output_dir = os.getcwd()
        output_image_path = os.path.join(output_dir, f"generated_gantt_diagram_{unique_id}.png")
        json_path = os.path.join(output_dir, f"generated_gantt_diagram_{unique_id}.json")
        
        # Path to the Blender executable and Blender script
        blender_executable = r"C:\Program Files\Blender Foundation\Blender 4.4\blender.exe"
        blender_script = os.path.join(os.getcwd(), "gantt_diagram_script.py")
        
        st.info("Generating Gantt chart using Blender (this may take a few seconds)...")
        
        # Run Blender command to generate Gantt chart
        cmd = [
            blender_executable,
            "-b",  # Run Blender in background mode (no UI)
            "--python", blender_script,  # Blender script path
            "--",  # Separate Blender arguments from script arguments
            "--output", output_image_path  # Pass the output image path as an argument
        ]
        
        result = subprocess.run(
            cmd,
            check=True, 
            capture_output=True, 
            text=True
        )
        
        # Check if the file was created
        if os.path.exists(output_image_path):
            # Check if the JSON file was created
            if os.path.exists(json_path):
                return output_image_path, json_path
            else:
                st.warning("JSON data not found, will use OCR to extract Gantt chart information.")
                return output_image_path, None
        else:
            st.error(f"Blender execution successful but output file not found at {output_image_path}")
            st.text(f"Blender output: {result.stdout}")
            st.text(f"Blender errors: {result.stderr}")
            return None, None
            
    except subprocess.CalledProcessError as e:
        st.error(f"Error running Blender: {e}")
        st.text(f"Command output: {e.stdout}")
        st.text(f"Error output: {e.stderr}")
        return None, None
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        return None, None
    

def generate_mcq(topic: str, level: str = "intermediate"):
    prompt = f"""
    You are an expert civil servant IT trainer in Spain.
    Create one multiple-choice question on the topic: "{topic}".
    The difficulty level should be: {level}.
    
    Format:
    Question: ...\n
    A) ...\n
    B) ...\n
    C) ...\n
    D) ...\n
    Correct Answer: ...\n
    Explanation: ...
    
    Here you have an example: 
    Question: What is the primary function of a router in a network?\n
    A) To connect computers within the same local area network (LAN)\n
    B) To direct data between different networks\n
    C) To provide wireless connectivity to devices\n
    D) To store data in a cloud server\n

    Correct Answer: B) To direct data between different networks
    Explanation: A router forwards data packets between different networks, ensuring that data can travel across the internet or between local networks.
    """

    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",  # Correct chat model
        messages=[{"role": "user", "content": prompt}]  # Use 'messages' with role
    )
    
    # Return the AI-generated content
    initial_question = response.choices[0].message.content.strip()

    refined_question = refine_mcq(initial_question)

    return refined_question


def refine_mcq(initial_question: str):
    prompt = f"""
    The following multiple-choice question was generated by another AI model:
    {initial_question}
    
    Please review and improve it. Make sure the question is clear, the answer choices are plausible, and the question is appropriately challenging. You should also improve the explanation if necessary.

    Format:
    Question: ...\n
    A) ...\n
    B) ...\n
    C) ...\n
    D) ...\n
    Correct Answer: ...\n
    Explanation: ...
    """

    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    refined_question = response.choices[0].message.content.strip()

    return refined_question

    

# Updated function for generating a question from the ER diagram
def generate_mcq_from_er(er_image_path: str, json_path: str = None):
    try:
        diagram_data = None
        
        # First try to use the JSON data if available
        if json_path and os.path.exists(json_path):
            try:
                with open(json_path, 'r') as f:
                    diagram_data = json.load(f)
                print("Successfully loaded diagram data from JSON")
            except Exception as e:
                print(f"Error loading JSON data: {e}")
                diagram_data = None
        
        # If JSON data is not available or couldn't be loaded, fall back to OCR
        if not diagram_data:
            print("Using OCR to extract diagram information")
            # Open and preprocess the ER diagram image
            er_image = Image.open(er_image_path)
            
            # Optional: Preprocess image to improve OCR accuracy
            er_image = er_image.convert('L')  # Convert to grayscale
            # Apply a threshold to improve text extraction
            er_image = er_image.point(lambda p: p > 180 and 255)
            
            # Use pytesseract to extract text content from the image
            diagram_text = pytesseract.image_to_string(er_image)
            
            # Print extracted text for debugging
            print("Extracted text from the diagram:")
            print(diagram_text)
            
            # Extract potential entities and relationships from the OCR text
            entities = re.findall(r'\b[A-Za-z0-9_]+\b', diagram_text)
            entities = [e for e in entities if len(e) > 2 and e.lower() not in [
                'the', 'and', 'box', 'line', 'label', 'rel', 'curve'
            ]]
            
            # Construct structured data from OCR
            diagram_data = {
                "entities": [{"name": entity} for entity in set(entities) if entity],
                "relationships": []  # Hard to extract relationships reliably with OCR
            }
        
        # Construct a prompt for the AI to generate a question
        prompt = f"""
        You are an expert civil servant IT trainer in Spain specializing in database design.
        
        I have an Entity-Relationship (ER) diagram with the following elements:
        
        Entities: {', '.join(e["name"] for e in diagram_data["entities"])}
        
        Relationships:
        {json.dumps(diagram_data.get("relationships", []), indent=2)}
        
        Create one multiple-choice question about this ER diagram. The question should test understanding of entities, relationships, cardinality, or database design principles based on this diagram.
        
        The question should be challenging but fair, and should require analyzing the diagram to answer correctly.
        
        Format:
        Question: ...\n
        A) ...\n
        B) ...\n
        C) ...\n
        D) ...\n
        Correct Answer: ...\n
        Explanation: ...
        """
        
        # Make the API call to OpenAI for question generation
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",  # Correct chat model
            messages=[{"role": "user", "content": prompt}]  # Use 'messages' with role
        )
        
        # Return the AI-generated content
        initial_question = response.choices[0].message.content.strip()

        refined_question = refine_mcq(initial_question)

        return refined_question
    
    except Exception as e:
        st.error(f"Failed to generate question from ER diagram: {e}")
        import traceback
        st.text(traceback.format_exc())
        return None

# New function for generating a question from a Gantt diagram
def generate_mcq_from_gantt(gantt_image_path: str, json_path: str = None):
    try:
        gantt_data = None

        # Load JSON if available
        if json_path and os.path.exists(json_path):
            with open(json_path, 'r') as f:
                gantt_data = json.load(f)

        # Fallback to OCR if no JSON data
        if not gantt_data:
            gantt_image = Image.open(gantt_image_path).convert('L')
            gantt_image = gantt_image.point(lambda p: p > 180 and 255)
            diagram_text = pytesseract.image_to_string(gantt_image)

            # Basic text parsing
            tasks = []
            for line in diagram_text.split('\n'):
                task_match = re.search(r'(\d+)\.\s*([A-Za-z\s]+)', line)
                duration_match = re.search(r'(\d+)\s*days', line)
                if task_match:
                    task_id = int(task_match.group(1))
                    task_name = task_match.group(2).strip()
                    duration = int(duration_match.group(1)) if duration_match else None
                    tasks.append({
                        "id": task_id,
                        "name": task_name,
                        "duration": duration,
                        "start_day": None,
                        "depends_on": []
                    })
            gantt_data = {
                "tasks": tasks,
                "project_duration": None
            }

        # No tasks? Exit early
        if not gantt_data or "tasks" not in gantt_data or not gantt_data["tasks"]:
            return "Error: No task data found in the Gantt chart."

        # Prepare tasks in a simple format for the question
        task_summaries = [f"{task['name']}: {task['duration']} days" for task in gantt_data["tasks"]]
        formatted_tasks = "\n".join(task_summaries)

        # Simpler prompt for the API call
        prompt = f"""
        You are an expert civil servant IT trainer in Spain specializing in project management.

        Create one multiple-choice question that tests knowledge of project scheduling based on these specific tasks {formatted_tasks}. The question should be challenging but fair, with one clearly correct answer and three plausible distractors.

        Your response must follow this exact format:

        Question: [Write a clear, concise question related to project scheduling techniques, critical path analysis, resource allocation, or scheduling conflicts relevant to the tasks provided]

        Format:
        Question: ...\n
        A) ...\n
        B) ...\n
        C) ...\n
        D) ...\n
        Correct Answer: ...\n
        Explanation: ...
        """
        

        # API call with a clear and simple prompt
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",  # Correct chat model
            messages=[{"role": "user", "content": prompt}]  # Use 'messages' with role
        )
        
        # Return the AI-generated content
        initial_question = response.choices[0].message.content.strip()

        refined_question = refine_mcq(initial_question)
        return refined_question

        if not result:
            return "❌ Error: The model returned an empty result."

        return result

    except Exception as e:
        return f"❌ Failed to generate question: {e}"

def extract_exam_questions(pdf_path, topic=None, count=5):
    doc = fitz.open(pdf_path)
    questions = []
    
    # Regex patterns for question and options
    question_pattern = re.compile(r"^\d+\.\s*(.*)")  # Matches question starting with a number (e.g., 1. Question text)
    option_pattern = re.compile(r"\s*([a-d])\)\s*(.*)")  # Matches options like "a) Option text"
    
    # Iterate through the PDF pages
    for page in doc:
        text_instances = []
        blocks = page.get_text("dict")["blocks"]
        
        # Parse the text into blocks
        for block in blocks:
            if block["type"] == 0:  # Text block
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"]
                        text_instances.append(text.strip())
        
        # Start extracting questions and options
        current_question = ""
        options = {}
        current_option_label = None
        current_option_text = ""
        
        # Iterating through the text to find questions and options
        for text in text_instances:
            text = text.strip()
            
            # Detect the question format: "number. Question text"
            question_match = question_pattern.match(text)
            if question_match:
                # If there's an existing question, save it
                if current_question:
                    # Ensure all options are added, even if one is missing
                    for option_label in ['a', 'b', 'c', 'd']:
                        if option_label not in options:
                            options[option_label] = None  # Set missing options to None
                    questions.append({
                        "question": current_question.strip(),
                        "options": options,
                        "correct_answer": None,  # Assuming the correct answer is not marked yet
                        "topic": topic
                    })
                    options = {}  # Reset for next question
                
                # Start a new question
                current_question = question_match.group(1).strip()
                current_option_label = None
                current_option_text = ""
            
            # Detect options (e.g., "a) Option text")
            option_match = option_pattern.match(text)
            if option_match:
                option_label = option_match.group(1).lower()  # Option label (a, b, c, d)
                option_text = option_match.group(2).strip()  # Option text
                options[option_label] = option_text  # Add option to dictionary
            
            elif current_question and text:  # If it's part of the question (if text exists and is not part of an option)
                current_question += " " + text  # Concatenate multi-line question text
        
        # Append the last question if it exists
        if current_question:
            # Ensure all options are added, even if one is missing
            for option_label in ['a', 'b', 'c', 'd']:
                if option_label not in options:
                    options[option_label] = None  # Set missing options to None
            questions.append({
                "question": current_question.strip(),
                "options": options,
                "correct_answer": None,  # Assuming the correct answer is not marked yet
                "topic": topic
            })
        
    return questions


def guess_correct_answer(question_text, options_dict):
    

    prompt = f"""
Given the following multiple choice question, choose the most appropriate answer. Respond ONLY with the letter (a, b, c, or d).

Question:
{question_text}

Options:
a) {options_dict.get('a', '')}
b) {options_dict.get('b', '')}
c) {options_dict.get('c', '')}
d) {options_dict.get('d', '')}

Answer:"""

    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",  # or "gpt-4"
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=5,
        )
        answer = response.choices[0].message.content.strip().lower()
        
        return(answer)
    except Exception as e:
        print(f"LLM guessing failed: {e}")
    
    #return None









