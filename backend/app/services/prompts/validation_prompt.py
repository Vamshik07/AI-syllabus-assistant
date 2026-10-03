QUESTION_VALIDATION_PROMPT = """You are a rigorous QA validator for source-grounded educational questions.
Verify whether the following question is 100% supported by the topic source text.

QUESTION:
{question}

OPTIONS:
{options}

CORRECT ANSWER:
{correct_answer}

TOPIC SOURCE TEXT:
{source_content}

Return JSON:
{{
  "is_valid": true,
  "confidence": 0.95,
  "reason": "Brief explanation"
}}
"""
