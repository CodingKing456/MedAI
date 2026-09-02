import { GoogleGenAI } from "@google/genai";

const MODEL = "gemini-3.7-flash";

export default async (request) => {
  if (request.method !== "POST") {
    return new Response(JSON.stringify({ error: "Method not allowed." }), {
      status: 405,
      headers: { "Content-Type": "application/json" }
    });
  }

  try {
    const body = await request.json();
    const { apiKey, imageBase64, mimeType } = body || {};

    if (!apiKey || typeof apiKey !== "string" || !apiKey.trim()) {
      return new Response(JSON.stringify({ error: "A Gemini API key is required. Enter your API key in MedAI first." }), {
        status: 400,
        headers: { "Content-Type": "application/json" }
      });
    }

    if (!imageBase64 || !mimeType) {
      return new Response(JSON.stringify({ error: "An X-ray image is required." }), {
        status: 400,
        headers: { "Content-Type": "application/json" }
      });
    }

    if (!["image/png", "image/jpeg", "image/webp"].includes(mimeType)) {
      return new Response(JSON.stringify({ error: "Only PNG, JPEG, and WEBP images are supported." }), {
        status: 400,
        headers: { "Content-Type": "application/json" }
      });
    }

    const ai = new GoogleGenAI({ apiKey: apiKey.trim() });
    const prompt = `You are MedAI, an experimental medical-imaging research assistant.
Analyze the supplied X-ray and return ONLY valid JSON:
{
  "studyType": "string",
  "findings": ["string"],
  "possibleInterpretations": ["string"],
  "limitations": ["string"],
  "disclaimer": "string"
}
Describe observable features separately from possible interpretations.
Do not provide a confirmed diagnosis, treatment, or medication recommendation.
Mention limitations and require qualified clinician/radiologist review.`;

    const response = await ai.models.generateContent({
      model: MODEL,
      contents: [
        {
          role: "user",
          parts: [
            { text: prompt },
            { inlineData: { data: imageBase64, mimeType } }
          ]
        }
      ],
      config: {
        responseMimeType: "application/json",
        temperature: 0.2
      }
    });

    let result;
    try {
      result = JSON.parse(response.text);
    } catch {
      return new Response(JSON.stringify({ error: "Gemini returned invalid JSON." }), {
        status: 502,
        headers: { "Content-Type": "application/json" }
      });
    }

    return new Response(JSON.stringify(result), {
      status: 200,
      headers: { "Content-Type": "application/json" }
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Analysis failed.";
    return new Response(JSON.stringify({ error: message }), {
      status: 500,
      headers: { "Content-Type": "application/json" }
    });
  }
};
