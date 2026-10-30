import logging
import re
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session

from app.models.models import Topic, Unit, Subject, SourceRegion
from app.schemas.schemas import CompanionChatRequest, CompanionChatResponse
from app.services.ai_service import ai_service
from app.services.quiz_service import quiz_service

logger = logging.getLogger(__name__)

COMPANION_INTELLIGENT_PROMPT = """You are Sir Paws-a-Lot, a deeply knowledgeable, warm, and articulate AI study companion and academic mentor (who happens to be a brave, cute fluffy grey tabby kitten knight with a tiny silver sword and blue cape!).

============================================================
CORE PRINCIPLE:
"Resources guide the learning context; they do not limit your intelligence."
You are an intelligent, conversational AI assistant (like ChatGPT) that is specially aware of what the student is currently studying.
You are NOT a restricted PDF search engine. You do NOT refuse to answer questions simply because a term is not in the uploaded document.
============================================================

PEDAGOGICAL & CONVERSATIONAL GUIDELINES:
1. NATURAL & ENGAGING:
   - Speak naturally, warmly, and clearly like a brilliant study partner or professor.
   - NEVER start responses with robotic phrases such as "According to your uploaded resources...", "From your uploaded resources on...", "In the provided text...", or "Based on the source document...".
2. COURSE CONTEXT AS A PRIMARY LENS:
   - When the student asks about a concept related to their course ({subject_name} → {topic_name}), answer with general conceptual clarity AND explain how it relates to what they are studying in their course.
3. DISTINGUISHING STUDY MATERIAL VS GENERAL KNOWLEDGE:
   - When answering a question that involves both course concepts and outside concepts, or when you supplement the material with general knowledge or real-world extensions, clearly separate your answer with these exact markdown sections:
   ### 📖 From Your Study Material
   (Explain what is present or defined in their uploaded slides/notes)
   ### 🌐 General Knowledge
   (Provide the broader definition, general industry practice, or outside historical/technical context)
   - If the student asks a pure general knowledge or dictionary question (e.g. "What does feasible mean?" or "Who invented the telephone?"), answer naturally and warmly under:
   ### 🌐 General Knowledge
   - NEVER falsely claim outside facts came from the student's study material!
4. EXAMPLES, ANALOGIES & SIMPLIFICATIONS:
   - When the student asks "Give me an example", "Explain simply", "Explain like I'm a beginner", or "Why is this important?", create relatable real-world analogies and clear explanations. You do NOT need the example to exist in their PDF.
5. CONTEXTUAL REASONING ("THIS", "WHY", PROCESSES, CONNECTIONS):
   - Resolve contextual pronouns like "What does this mean?", "Why does this happen?", "How are these two connected?" using the active question, current topic ({topic_name}), and conversation history.
6. WORD MEANINGS:
   - When asked what a word means (e.g., "pervasive", "bounded rationality"), explain its general meaning first, then explain what it signifies in the context of their subject ({subject_name}).
7. QUIZ HINTS:
   - If the student is on a quiz question and asks for a hint, provide an encouraging pedagogical clue that triggers critical thinking WITHOUT directly revealing the option letter.
8. SUBTLE CITATIONS:
   - If your answer draws directly upon a specific concept from their notes, you can optionally include a subtle note at the bottom:
     [Related course material: {subject_name} → {topic_name}]

STUDENT'S ACTIVE LEARNING CONTEXT:
Subject: {subject_name}
Module/Unit: {unit_name}
Topic: {topic_name}
Active Question / Element: {question_context}
Current Page / View: {current_page}

UPLOADED COURSE MATERIAL (Reference as primary context, not a restriction):
\"\"\"
{source_content}
\"\"\"

RECENT CONVERSATION HISTORY:
{history_text}

STUDENT'S MESSAGE:
{user_message}

Answer as Sir Paws-a-Lot (conversational, intelligent, encouraging, markdown formatted):
"""

class CompanionService:
    def chat(self, db: Session, req: CompanionChatRequest) -> CompanionChatResponse:
        """Processes a chat request with the AI Study Cat Companion."""
        topic = None
        topic_name = req.topic_name or "Current Topic"
        unit_name = req.unit_name or "Current Unit"
        subject_name = req.subject_name or "Your Subject"
        source_content = ""

        # Strictly scope context by topic_id / unit_id / subject_id
        if req.topic_id:
            topic = db.query(Topic).filter(Topic.id == req.topic_id).first()
            if topic:
                topic_name = topic.name
                source_content = quiz_service._get_topic_source_content(db, topic)
                if topic.document and topic.document.unit:
                    unit_name = topic.document.unit.title
                    if topic.document.unit.subject:
                        subject_name = topic.document.unit.subject.name
        elif req.unit_id:
            unit = db.query(Unit).filter(Unit.id == req.unit_id).first()
            if unit:
                unit_name = unit.title
                if unit.subject:
                    subject_name = unit.subject.name
                if unit.document:
                    pieces = [quiz_service._get_topic_source_content(db, t) for t in unit.document.topics]
                    source_content = "\n\n".join(pieces)
        elif req.subject_id:
            subj = db.query(Subject).filter(Subject.id == req.subject_id).first()
            if subj:
                subject_name = subj.name

        # Ensure we never display placeholder names like "General Studies" unless that is the literal subject
        if subject_name.lower() in ("general studies", "syllabus") and req.subject_name:
            subject_name = req.subject_name

        msg = req.message.strip()
        lower_msg = msg.lower()

        # Check for Hint request
        is_hint_request = any(w in lower_msg for w in ("hint", "clue", "help me on this question", "stuck on this", "what should i look for"))
        if is_hint_request and req.current_question:
            return self._handle_hint_request(subject_name, topic_name, source_content, req.current_question, msg)

        # Build conversation history
        history_text = ""
        for h in req.history[-6:]:
            role = "Student" if h.get("role") == "user" else "Sir Paws-a-Lot"
            history_text += f"{role}: {h.get('content')}\n"

        # AI Generation via Gemini
        if ai_service.is_available():
            try:
                prompt = COMPANION_INTELLIGENT_PROMPT.format(
                    subject_name=subject_name,
                    unit_name=unit_name,
                    topic_name=topic_name,
                    question_context=req.current_question or "None",
                    current_page=req.current_page or "learning view",
                    source_content=source_content[:6000] if source_content else "No uploaded documents for this view.",
                    history_text=history_text or "No prior messages.",
                    user_message=msg,
                )
                response = ai_service.client.models.generate_content(
                    model=ai_service.model_name,
                    contents=prompt
                )
                raw_text = response.text.strip() if response and response.text else ""
                if raw_text:
                    # Clean any accidental robotic prefixes
                    raw_text = re.sub(
                        r'^(?:According to (?:the|your) (?:uploaded )?resources|From your uploaded resources on [^:\n]+:?|Based on the source material:?)\s*',
                        '',
                        raw_text,
                        flags=re.IGNORECASE
                    ).strip()

                    cat_state = "EXPLAINING"
                    if is_hint_request:
                        cat_state = "HINT"
                    elif any(w in lower_msg for w in ("great", "thanks", "got it", "passed", "awesome", "perfect")):
                        cat_state = "HAPPY"
                    elif any(w in lower_msg for w in ("why", "how", "what if", "compare", "difference")):
                        cat_state = "CURIOUS"

                    # Check for optional citation
                    ref = None
                    ref_match = re.search(r'\[Related course material:\s*([^\]]+)\]', raw_text)
                    if ref_match:
                        ref = ref_match.group(1).strip()
                        raw_text = raw_text.replace(ref_match.group(0), "").strip()

                    return CompanionChatResponse(
                        response=raw_text,
                        mode="study",
                        cat_state=cat_state,
                        speech_bubble="Here is what you need to know! 🐾",
                        requires_general_prompt=False,
                        source_reference=ref,
                        quick_actions=self._get_dynamic_quick_actions(req, lower_msg)
                    )
            except Exception as e:
                logger.warning(f"Companion Gemini generation failed: {e}")

        # Conversational intelligent fallback when offline
        return self._generate_intelligent_fallback(subject_name, topic_name, source_content, msg, is_hint_request)

    def _handle_hint_request(self, subject_name: str, topic_name: str, source_content: str, question: str, user_msg: str) -> CompanionChatResponse:
        """Generates an encouraging, pedagogical hint without spoiling the direct option letter."""
        hint_text = ""
        if ai_service.is_available():
            try:
                prompt = (
                    f"You are Sir Paws-a-Lot, an encouraging AI study companion.\n"
                    f"The student is working on this quiz question in {subject_name} ({topic_name}):\n"
                    f"\"{question}\"\n\n"
                    f"COURSE MATERIAL EXCERPTS:\n{source_content[:4000] if source_content else 'General topic principles.'}\n\n"
                    f"TASK:\n"
                    f"Provide an insightful pedagogical clue (1-2 sentences) as Sir Paws-a-Lot.\n"
                    f"RULES:\n"
                    f"- DO NOT reveal the correct option letter or state the exact answer verbatim.\n"
                    f"- Point the student toward the key concept, relationship, or purpose they need to think about.\n"
                    f"- Be encouraging, noble, and warm like a brave little knight cat! 🐱⚔️"
                )
                res = ai_service.client.models.generate_content(
                    model=ai_service.model_name,
                    contents=prompt
                )
                if res and res.text:
                    hint_text = res.text.strip()
            except Exception as e:
                logger.warning(f"Failed to generate AI hint: {e}")

        if not hint_text:
            hint_text = (
                f"🐾 **Sir Paws-a-Lot's Hint**: Think about the core objective of **{topic_name}**. "
                f"Focus on the underlying principle of how high-level goals are transformed into structured actions. "
                f"Which option represents that exact purpose rather than a distractor? You've got this! ⚔️"
            )

        return CompanionChatResponse(
            response=hint_text,
            mode="study",
            cat_state="HINT",
            speech_bubble="Here's a clue to unlock the puzzle! 🐾",
            requires_general_prompt=False,
            source_reference=f"{subject_name} → {topic_name}",
            quick_actions=["Explain the core concept", "Give an analogy", "Try answering again"]
        )

    def _generate_intelligent_fallback(self, subject_name: str, topic_name: str, source_content: str, user_msg: str, is_hint: bool) -> CompanionChatResponse:
        """Conversational fallback when the LLM is temporarily unreachable."""
        clean_query = re.sub(r'^(what is|explain|tell me about|define)\s+', '', user_msg, flags=re.IGNORECASE).strip(' ?.')

        source_excerpts = [s.strip() for s in re.split(r'(?:\r?\n+|(?<=[.!?])\s+)', source_content) if len(s.strip()) > 20]
        query_terms = {
            term for term in re.findall(r"[a-z0-9]+", clean_query.lower())
            if len(term) > 2 and term not in {"the", "and", "what", "how", "why", "does", "this", "that"}
        }
        if query_terms:
            source_excerpts = [
                excerpt for excerpt in source_excerpts
                if query_terms.intersection(re.findall(r"[a-z0-9]+", excerpt.lower()))
            ]

        planning_types_request = bool(
            re.search(r"\b(?:types?\s+of\s+planning|planning\s+types?)\b", clean_query, flags=re.IGNORECASE)
        )

        if planning_types_request:
            reply = (
                "### 📖 From Your Study Material\n"
                f"In your **{subject_name}** resources for **{topic_name}**, planning is the process "
                "of setting goals and deciding in advance the actions, resources, and timelines needed to achieve them.\n\n"
                "### 🌐 General Knowledge\n"
                "**Types of planning** commonly include:\n"
                "- **Strategic planning**: long-term direction and major goals.\n"
                "- **Tactical planning**: medium-term plans that support strategy.\n"
                "- **Operational planning**: short-term activities and procedures.\n"
                "- **Contingency planning**: backup actions for possible risks or changes.\n\n"
                "In simple terms: strategic planning decides *where to go*, tactical planning decides "
                "*how to support that direction*, and operational planning defines *what to do day to day*."
            )
        elif source_content and source_excerpts:
            context_sentence = source_excerpts[0]
            reply = (
                f"### 📖 From Your Study Material\n"
                f"In your **{subject_name}** resources for **{topic_name}**:\n"
                f"{context_sentence}\n\n"
                f"### 🌐 General Knowledge\n"
                f"I could not generate a reliable explanation right now because the AI service is temporarily unavailable. "
                f"Please try again shortly, or ask about the study material shown above. "
                f"I will not add unrelated information without a working AI response. 🐾"
            )
        else:
            reply = (
                f"### 🌐 General Knowledge\n"
                f"I could not reliably answer **{clean_query or user_msg}** because the AI service is temporarily unavailable "
                "and no course material was attached to this chat. Please try again shortly or open a topic before asking. 🐾"
            )

        return CompanionChatResponse(
            response=reply,
            mode="study",
            cat_state="EXPLAINING",
            speech_bubble="Ready to explore this concept with you! 🐱",
            requires_general_prompt=False,
            source_reference=f"{subject_name} → {topic_name}" if source_content else None,
            quick_actions=["Give me a real-life example", "Explain simply", "How does this work?"]
        )

    def _get_dynamic_quick_actions(self, req: CompanionChatRequest, lower_msg: str) -> List[str]:
        if req.current_question:
            return ["Give me a hint 💡", "Explain the concept", "Give an example"]
        if "example" in lower_msg:
            return ["Explain simply", "Why is this important?", "Quiz me"]
        if req.topic_id:
            return ["Give a real-life example", "Explain simply", "How does this work?", "Summarize key points"]
        return ["Explain simply", "Give an example", "What should I study next?"]

    def get_context_bubble(self, page_type: str, topic_name: Optional[str] = None) -> Dict[str, str]:
        """Provides short, cute contextual speech bubbles with states."""
        if page_type == "topic":
            return {
                "message": f"Studying {topic_name or 'this topic'}? Ask me anything or request an example! 🐱📚",
                "state": "STUDYING"
            }
        elif page_type == "quiz":
            return {
                "message": "Focus, brave scholar! Tap me if you'd like a hint on any question. ⚔️",
                "state": "QUIZ"
            }
        elif page_type in ("timetable", "roadmap"):
            return {
                "message": "Your learning roadmap is ready! Ready for today's mission? 🐱📜",
                "state": "ROADMAP"
            }
        elif page_type == "progress":
            return {
                "message": "Look at all this progress! Keep up the great work! 🎉",
                "state": "CELEBRATION"
            }
        elif page_type == "dashboard":
            return {
                "message": "Ready to study? Tap me anytime for explanations, analogies, or hints! 🐱⚔️",
                "state": "IDLE"
            }
        return {
            "message": "Ready to help you study! Tap me anytime. 🐾",
            "state": "IDLE"
        }

companion_service = CompanionService()
