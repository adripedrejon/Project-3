import streamlit as st
from questions import generate_mcq, generate_mcq_from_er, generate_mcq_from_gantt
import subprocess
import os
import json
from PIL import Image
import time
import uuid

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
    
