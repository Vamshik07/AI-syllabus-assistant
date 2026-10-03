QUIZ_GENERATION_PROMPT = """You are an expert university professor creating an authoritative, pedagogical multiple-choice exam based exclusively on the provided educational source material.

CRITICAL TEACHER-QUALITY RULES:
1. Generate EXACTLY {num_questions} high-caliber multiple-choice questions.
2. Frame questions like an experienced university examiner:
   - Ask about definitions, core concepts, classifications, stages of processes, relationships, and distinctions.
   - If the material includes diagrams, hierarchies, or classifications (e.g. Standing vs Single-use plans, stages of production), test the student's understanding of those categories and structures.
3. NEVER generate fill-in-the-blank questions (e.g., NEVER write sentences with "______" masking a word). Every question must be a complete, well-formed question sentence.
4. Ground every question STRICTLY in the provided source material below. Do NOT use outside knowledge or hallucinate details.
5. Provide EXACTLY 4 distinct, plausible options per question. All options must be grammatically consistent and meaningful.
6. Exactly ONE option must be the correct answer.
7. 'correct_answer' must match one of the items in 'options' character-for-character.
8. 'source_reference' MUST be a direct quote or specific sentence from the provided source text supporting the correct answer.
9. 'explanation' must be a clear pedagogical explanation referencing the source material.
10. Return valid JSON ONLY.

SCHEMA:
{{
  "questions": [
    {{
      "question": "Clear, well-framed conceptual or factual question?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_answer": "Option A",
      "source_reference": "Direct verbatim excerpt or sentence from the source text",
      "explanation": "Clear explanation grounded in the cited source reference"
    }}
  ]
}}

TOPIC NAME: {topic_name}

SOURCE CONTENT FOR THIS TOPIC (includes text, tables, and transcribed diagrams/visuals):
{source_content}
"""
