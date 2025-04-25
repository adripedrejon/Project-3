from utils import generate_mcq_from_er, generate_mcq_from_gantt, generate_mcq
import subprocess

class ERDiagramAgent:
    def __init__(self, blender_executable, blender_script, output_image_path):
        self.blender_executable = blender_executable
        self.blender_script = blender_script
        self.output_image_path = output_image_path

    def generate_er_diagram(self):
        # Run Blender with the script
        subprocess.run([
            self.blender_executable,
            "--background",
            "--python", self.blender_script
        ])

        # Return the image path
        return self.output_image_path, "generated_er_diagram.json"

class GanttDiagramAgent:
    def __init__(self, blender_executable, blender_script, output_image_path):
        self.blender_executable = blender_executable
        self.blender_script = blender_script
        self.output_image_path = output_image_path

    def generate_gantt_diagram(self):
        # Run Blender with the script
        subprocess.run([
            self.blender_executable,
            "--background",
            "--python", self.blender_script
        ])

        # Return the image path
        return self.output_image_path, "generated_gantt_diagram.json"


class QuestionGenerationAgent:
    def __init__(self):
        pass

    def generate_mcq(self, topic, level):
        # This method generates MCQs for topics other than ER diagrams or Gantt charts
        return generate_mcq(topic, level)

    def generate_mcq_from_gantt(self, gantt_image_path, json_path):
        # Generate MCQ from Gantt chart (similar to how it's done for ER diagrams)
        return generate_mcq_from_gantt(gantt_image_path, json_path)

    def generate_mcq_from_er(self, er_image_path, json_path):
        # Generate MCQ from ER diagram (uses the same function as ERDiagramAgent)
        return generate_mcq_from_er(er_image_path, json_path)
