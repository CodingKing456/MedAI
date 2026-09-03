import base64
import json
from typing import Any
from google import genai
from google.genai import types

MODEL = "gemini-3.7-flash"

def analyze_image(image_bytes: bytes, mime_type: str, api_key: str) -> dict[str, Any]:
    if not api_key:
        raise ValueError("A Gemini API key is required.")

    if mime_type not in {"image/png", "image/jpeg", "image/webp"}:
        raise ValueError("Only PNG, JPEG, and WEBP images are supported.")

    client = genai.Client(api_key=api_key)

    prompt = """
You are MedAI, an experimental medical-imaging research assistant.
Analyze the supplied X-ray and return ONLY valid JSON:
{
  "studyType": "string",
  "findings": ["string"],
  "possibleInterpretations": ["string"],
  "limitations": ["string"],
  "disclaimer": "string"
}
Describe observable features separately from possible interpretations.
Do not provide a confirmed diagnosis, treatment, or medication recommendation. Provide a percentae for a chance of having the disese.
Mention limitations and require qualified clinician/radiologist review.
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=[
            types.Part.from_text(text=prompt),
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.2,
        ),
    )
    try:
        return json.loads(response.text)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Gemini returned invalid JSON.") from exc

def analyze_base64(image_base64: str, mime_type: str, api_key: str) -> dict[str, Any]:
    return analyze_image(base64.b64decode(image_base64), mime_type, api_key)
