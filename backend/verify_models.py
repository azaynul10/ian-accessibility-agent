import os
import urllib.request
import json
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")

url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
try:
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode("utf-8"))
        print("Models with bidiGenerateContent support:")
        count = 0
        for model in data.get("models", []):
            methods = model.get("supportedGenerationMethods", [])
            if "bidiGenerateContent" in methods:
                print(f" - {model.get('name')}")
                count += 1
        if count == 0:
            print(" - None found!")
except Exception as e:
    print(f"Error querying API: {e}")
