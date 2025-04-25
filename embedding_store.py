# embedding_store.py
import json
import os
import numpy as np

STORE_FILE = "embedding_store.json"

def load_store():
    if os.path.exists(STORE_FILE):
        with open(STORE_FILE, "r") as f:
            return json.load(f)
    return []

def save_store(data):
    with open(STORE_FILE, "w") as f:
        json.dump(data, f)

def add_to_store(question_text, embedding, metadata, options=None, correct_answer=None):
    store = load_store()
    store.append({
        "text": question_text,
        "embedding": embedding.tolist(),
        "metadata": metadata,
        "options": options,  # Guardar las opciones como un diccionario
        "correct_answer": correct_answer
    })
    save_store(store)
