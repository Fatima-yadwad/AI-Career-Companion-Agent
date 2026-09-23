import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.services.llm_service import llm_service

try:
    data = llm_service.generate_structured("Return a JSON with key 'greeting' and value 'Hello World'")
    print("SUCCESS GENERATING STRUCTURED JSON:")
    print(data)
except Exception as e:
    print("ERROR:", e)
