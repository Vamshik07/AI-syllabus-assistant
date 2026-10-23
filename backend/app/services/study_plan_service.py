import logging
import re
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.models import Subject, Topic, TopicProgress, StudyRoadmap, SourceRegion

logger = logging.getLogger(__name__)


class StudyPlanService:
    """
    Time-First, Priority-Based Study Roadmap & Timetable Engine.

    Guiding Principles:
    1. ROADMAP = PLANNING (What to study, when, how long, what to revise, when to assess).
       Strictly NO content generation or topic explanation in the roadmap.
    2. Total Available Study Time = days * daily_study_hours.
    3. Daily study hours are a HARD LIMIT: never exceed daily available time on any day.
    4. Time allocation is WORKLOAD-PROPORTIONAL, never equal split (no ~93 min per topic).
    5. Transparent Priority: HIGH, MEDIUM, LOWER STUDY PRIORITY with clear reasons.
       No unfounded claims of exam guarantees.
    6. Prerequisite-aware: Syllabus hierarchy and prerequisites respected.
    7. Dedicated Revision and Final Assessment (>65% syllabus completion rule) reserved.
    8. Real Student Progress integration: Adapts to weak topics (<65%) and completed topics.
    9. Shortfall vs Buffer detection: Mathematically valid total hours.
    """

    @staticmethod
    def compute_topic_workload_and_priority(
        topic: Topic,
        student_progress: Optional[TopicProgress] = None,
    ) -> Dict[str, Any]:
        """
        Analyzes source evidence and student progress to estimate workload and priority.
        Workload is returned in practical human-friendly study blocks: 30, 45, 60, 75, 90, 120 min.
        """
        name_lower = topic.name.lower()
        region_count = len(topic.source_regions) if hasattr(topic, "source_regions") and topic.source_regions else 0
        subtopic_count = len(topic.subtopics) if hasattr(topic, "subtopics") and topic.subtopics else 0

        # Extract text length from source regions
        total_text_chars = 0
        if hasattr(topic, "source_regions") and topic.source_regions:
            for r in topic.source_regions:
                if r.content_text:
                    total_text_chars += len(r.content_text.strip())

        # Keywords indicating heavy process / multi-step system
        heavy_keywords = [
            "process", "steps", "stages", "production", "control", "system",
            "architecture", "algorithm", "design", "methods", "management by objectives",
            "mbo", "cycle", "framework", "decision making"
        ]

        # Keywords indicating quick, concise classification/types
        quick_keywords = [
            "types", "characteristics", "principles", "classification",
            "rationality", "rules", "difference", "definition", "overview", "introduction"
        ]

        is_heavy = any(k in name_lower for k in heavy_keywords)
        is_quick = any(k in name_lower for k in quick_keywords)

        # Check student progress
        status = "NOT_STARTED"
        best_score = None
        is_weak = False
        is_completed = False

        if student_progress:
            best_score = student_progress.best_score
            if student_progress.status in ["PASSED", "COMPLETED"] or (best_score is not None and best_score >= 75):
                status = "COMPLETED"
                is_completed = True
            elif best_score is not None and best_score < 65:
                status = "NEEDS_REVISION"
                is_weak = True
            elif student_progress.attempt_count > 0:
                status = "IN_PROGRESS"

        # Determine Workload (human-friendly minutes: 30, 45, 60, 75, 90, 120)
        reasons: List[str] = []

        if is_completed:
            workload = 30
            reasons.append("Already completed with passing score — scheduled for rapid 30-min reinforcement.")
        elif is_weak:
            workload = 75 if is_quick else 90
            reasons.append(f"Needs Revision: low previous quiz score ({best_score}%) — allocated extra conceptual review.")
        elif region_count >= 5 or subtopic_count >= 3 or (is_heavy and region_count >= 3):
            workload = 90 if total_text_chars < 3000 else 120
            reasons.append(f"Substantial source coverage ({region_count} slides/pages, {subtopic_count} subtopics).")
        elif region_count >= 2 or subtopic_count >= 1 or is_heavy:
            workload = 60
            reasons.append(f"Standard workload ({region_count or 1} slides/pages with core conceptual framework).")
        elif is_quick:
            workload = 30
            reasons.append("Concise structured concept / classification topic.")
        else:
            workload = 45
            reasons.append("Foundational syllabus topic with standard source scope.")

        # Determine Transparent Priority Tier
        if is_weak or workload >= 75 or region_count >= 4 or (is_heavy and not is_completed):
            priority = "HIGH"
            priority_tier = "high_weightage"
            rank = 1
            badge = "🔥 High Study Priority"
            reasons.append("High study priority: Heavy workload or critical foundational process.")
            strategy = "Most Important: Master first to secure major exam marks."
        elif is_completed:
            priority = "LOWER"
            priority_tier = "foundation"
            rank = 3
            badge = "📘 Lower Study Priority"
            reasons.append("Lower study priority: Concept already mastered.")
            strategy = "Review & consolidate: Complete to round off preparation."
        elif is_quick or workload <= 45:
            priority = "MEDIUM"
            priority_tier = "quick_win"
            rank = 2
            badge = "⭐ Quick Win (Easy to Score)"
            reasons.append("Medium study priority: High-scoring, quick direct marks.")
            strategy = "High-Scoring: Easy to memorize, quick direct marks."
        else:
            priority = "MEDIUM"
            priority_tier = "quick_win"
            rank = 2
            badge = "⭐ Medium Study Priority"
            reasons.append("Medium study priority: Standard scope.")
            strategy = "High-Scoring: Easy to memorize, quick direct marks."

        # Source reference string (e.g. "Slides 5–8" or "Page 4")
        if topic.source_start and topic.source_end and topic.source_start != topic.source_end:
            source_ref = f"Slides/Pages {topic.source_start}–{topic.source_end}"
        elif topic.source_start:
            source_ref = f"Slide/Page {topic.source_start}"
        else:
            source_ref = "Syllabus Resource"

        return {
            "workload_minutes": workload,
            "priority": priority,
            "priority_tier": priority_tier,
            "rank": rank,
            "priority_label": badge,
            "importance_label": badge,
            "is_important": rank <= 2,
            "strategy_tip": strategy,
            "reasons": reasons,
            "status": status,
            "best_score": best_score,
            "source_reference": source_ref,
            "region_count": region_count,
            "subtopic_count": subtopic_count,
            "score": 90 if rank == 1 else (75 if rank == 2 else 60),
        }

    def get_subject_topics_for_plan(
        self,
        subject: Subject,
        db: Optional[Session] = None,
        user_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Returns all topics for a subject annotated with workload, priority, and progress."""
        progress_map: Dict[str, TopicProgress] = {}
        if db and user_id:
            user_progs = db.query(TopicProgress).filter(TopicProgress.user_id == user_id).all()
            progress_map = {p.topic_id: p for p in user_progs}

        topics_info: List[Dict[str, Any]] = []
        for unit in sorted(subject.units, key=lambda item: item.order_index):
            if unit.document:
                for topic in sorted(unit.document.topics, key=lambda item: item.order_index):
                    analysis = self.compute_topic_workload_and_priority(
                        topic, progress_map.get(topic.id)
                    )
                    topics_info.append({
                        "topic_id": topic.id,
                        "topic_name": topic.name,
                        "unit_id": unit.id,
                        "unit_title": unit.title,
                        "unit_order": unit.order_index,
                        "order_index": topic.order_index,
                        "source_start": topic.source_start,
                        "source_end": topic.source_end,
                        "source_reference": analysis["source_reference"],
                        "workload_minutes": analysis["workload_minutes"],
                        "priority": analysis["priority"],
                        "priority_tier": analysis["priority_tier"],
                        "rank": analysis["rank"],
                        "is_important": analysis["is_important"],
                        "importance_score": analysis["score"],
                        "importance_label": analysis["importance_label"],
                        "strategy_tip": analysis["strategy_tip"],
                        "reasons": analysis["reasons"],
                        "status": analysis["status"],
                        "best_score": analysis["best_score"],
                    })

        # Prerequisite-aware sorting: earlier units first, high priority within units first
        topics_info.sort(key=lambda t: (t["unit_order"], t["rank"], t["order_index"]))
        return topics_info

    def create_plan(
        self,
        db: Session,
        subject: Subject,
        start_date: date,
        end_date: date,
        daily_hours: float,
        user_id: Optional[str] = None,
        material_preference: Optional[str] = "auto",
        selected_topic_ids: Optional[List[str]] = None,
        only_important: Optional[bool] = False,
    ) -> Dict[str, Any]:
        """
        Generates a mathematically valid, time-first study roadmap.
        Guarantees:
        - Daily hours is a HARD limit: allocated_minutes <= daily_hours * 60 for every day.
        - Workload is proportional (never equal division).
        - Dedicated revision and assessment blocks reserved.
        - Detailed shortfall / buffer calculations.
        - Persisted in database.
        """
        days = (end_date - start_date).days + 1
        if days <= 0:
            raise ValueError("End date must be on or after start date.")

        daily_limit_minutes = int(round(daily_hours * 60))
        total_available_minutes = days * daily_limit_minutes
        total_available_hours = round(total_available_minutes / 60.0, 1)

        # Collect student progress if user_id is provided
        progress_map: Dict[str, TopicProgress] = {}
        if user_id:
            user_progs = db.query(TopicProgress).filter(TopicProgress.user_id == user_id).all()
            progress_map = {p.topic_id: p for p in user_progs}

        # Collect all processed topics in the subject
        all_topics: List[Topic] = []
        for unit in sorted(subject.units, key=lambda item: item.order_index):
            if unit.document:
                all_topics.extend(sorted(unit.document.topics, key=lambda item: item.order_index))

        if not all_topics:
            raise ValueError("Upload and process at least one syllabus document before creating a roadmap.")

        # Filter topics if requested
        if selected_topic_ids and len(selected_topic_ids) > 0:
            selected_set = set(selected_topic_ids)
            topics = [t for t in all_topics if t.id in selected_set]
            if not topics:
                topics = all_topics
        elif only_important:
            topics = [
                t for t in all_topics
                if self.compute_topic_workload_and_priority(t, progress_map.get(t.id))["rank"] <= 2
            ]
            if not topics:
                topics = all_topics
        else:
            topics = all_topics

        # Analyze each topic's workload and priority
        topic_analyses: List[Dict[str, Any]] = []
        for topic in topics:
            analysis = self.compute_topic_workload_and_priority(topic, progress_map.get(topic.id))
            topic_analyses.append({
                "topic": topic,
                "analysis": analysis,
                "unit": topic.document.unit,
            })

        # Sort topics respecting syllabus prerequisites & priority
        # Earlier units come first, high-priority topics within units come first
        topic_analyses.sort(key=lambda item: (
            item["unit"].order_index,
            item["analysis"]["rank"],
            item["topic"].order_index
        ))

        # Determine detailed vs concise based on time or explicit user preference
        if material_preference == "concise":
            detailed = False
        elif material_preference == "detailed":
            detailed = True
        else:
            minutes_per_topic = (days * daily_hours * 60) / max(1, len(topics))
            detailed = minutes_per_topic >= 45

        # Check raw workload demand
        raw_topic_minutes = sum(item["analysis"]["workload_minutes"] for item in topic_analyses)

        # Reserve Revision & Assessment Minutes
        # If days >= 7: final day dedicated to assessment + revision, day before for comprehensive review
        # If 4 <= days < 7: final day has assessment + revision
        # If days < 4: final day has at least 30-45m assessment/consolidation
        if days >= 7:
            assessment_minutes = min(60, daily_limit_minutes)
            final_day_revision = daily_limit_minutes - assessment_minutes
            second_last_revision = daily_limit_minutes
            dedicated_revision_minutes = final_day_revision + second_last_revision
            reserved_non_topic_days = 2
        elif days >= 4:
            assessment_minutes = min(45, daily_limit_minutes)
            final_day_revision = daily_limit_minutes - assessment_minutes
            dedicated_revision_minutes = final_day_revision
            reserved_non_topic_days = 1
        else:
            assessment_minutes = min(30, daily_limit_minutes // 2) if daily_limit_minutes >= 60 else 15
            dedicated_revision_minutes = 0
            reserved_non_topic_days = 0

        # Minutes available for new topics across days
        topic_budget_minutes = total_available_minutes - (assessment_minutes + dedicated_revision_minutes)

        # Shortfall & Scaling Logic
        has_shortfall = False
        shortfall_hours = 0.0
        shortfall_message = None

        # Scale topic workloads if necessary to fit comfortably
        if raw_topic_minutes > topic_budget_minutes:
            scale_ratio = max(0.5, topic_budget_minutes / max(1, raw_topic_minutes))
            scaled_topic_minutes = 0
            for item in topic_analyses:
                orig = item["analysis"]["workload_minutes"]
                # Round to clean practical block (30, 45, 60, 75, 90)
                scaled = max(30, int(round((orig * scale_ratio) / 15.0) * 15))
                # Never exceed daily limit
                scaled = min(daily_limit_minutes, scaled)
                item["allocated_minutes"] = scaled
                scaled_topic_minutes += scaled

            if scaled_topic_minutes > topic_budget_minutes:
                has_shortfall = True
                shortfall_minutes = scaled_topic_minutes - topic_budget_minutes
                shortfall_hours = round(shortfall_minutes / 60.0, 1)
                shortfall_message = (
                    f"Your available study time ({total_available_hours}h) is less than the estimated "
                    f"time required ({round((scaled_topic_minutes + assessment_minutes + dedicated_revision_minutes)/60.0, 1)}h). "
                    f"High-priority topics have been scheduled first."
                )
        else:
            for item in topic_analyses:
                item["allocated_minutes"] = min(daily_limit_minutes, item["analysis"]["workload_minutes"])

        # -------------------------------------------------------------
        # DAY-BY-DAY BIN PACKING ENGINE (Strict Hard Daily Limit)
        # -------------------------------------------------------------
        day_buckets: List[Dict[str, Any]] = []
        for d in range(days):
            day_date = start_date + timedelta(days=d)
            day_buckets.append({
                "day_number": d + 1,
                "date": day_date.isoformat(),
                "available_minutes": daily_limit_minutes,
                "allocated_minutes": 0,
                "items": [],
            })

        # Reserve assessment and dedicated revision on final days
        if days >= 7:
            # Day N-1: Comprehensive Syllabus Revision
            rev_day = day_buckets[-2]
            rev_item = {
                "item_type": "REVISION",
                "topic_id": f"rev-full-{subject.id}",
                "topic_name": "Full Syllabus High-Priority Revision & Practice",
                "unit_id": subject.units[0].id if subject.units else "",
                "unit_title": "Comprehensive Review",
                "allocated_minutes": daily_limit_minutes,
                "priority": "HIGH",
                "priority_label": "🔄 High-Priority Revision",
                "priority_reasons": ["Consolidate core processes, formulas, and high-weightage frameworks before final test."],
                "source_reference": "All Syllabus Units",
                "status": "NOT_STARTED",
                "best_score": None,
                "tasks": [
                    "Review high-priority topic flashcards & diagrams",
                    "Practice 10 key conceptual questions",
                    "Solidify weak definitions and steps",
                ],
            }
            rev_day["items"].append(rev_item)
            rev_day["allocated_minutes"] += daily_limit_minutes

            # Day N: Final Assessment + Weak Topic Revision
            final_day = day_buckets[-1]
            if final_day_revision > 0:
                final_rev = {
                    "item_type": "REVISION",
                    "topic_id": f"rev-targeted-{subject.id}",
                    "topic_name": "Targeted Weak-Topic Revision",
                    "unit_id": subject.units[0].id if subject.units else "",
                    "unit_title": "Targeted Review",
                    "allocated_minutes": final_day_revision,
                    "priority": "HIGH",
                    "priority_label": "🔄 Targeted Revision",
                    "priority_reasons": ["Refine areas needing reinforcement prior to taking the final assessment."],
                    "source_reference": "Focus Areas",
                    "status": "NOT_STARTED",
                    "best_score": None,
                    "tasks": [
                        "Quick review of tricky topics & mistakes",
                        "Formula and workflow verification",
                    ],
                }
                final_day["items"].append(final_rev)
                final_day["allocated_minutes"] += final_day_revision

            final_assess = {
                "item_type": "ASSESSMENT",
                "topic_id": f"assess-{subject.id}",
                "topic_name": "Full-Syllabus Master Assessment (Target ≥ 65% for Syllabus Completion)",
                "unit_id": subject.units[0].id if subject.units else "",
                "unit_title": "Final Assessment",
                "allocated_minutes": assessment_minutes,
                "priority": "HIGH",
                "priority_label": "📝 Final Assessment",
                "priority_reasons": ["Rule 26: 100% syllabus completion requires >= 65% score in the final assessment."],
                "source_reference": "Full Subject",
                "status": "NOT_STARTED",
                "best_score": None,
                "tasks": [
                    "Complete full-length subject assessment",
                    "Score >= 65% to achieve 100% syllabus completion",
                    "Review detailed solutions and feedback",
                ],
            }
            final_day["items"].append(final_assess)
            final_day["allocated_minutes"] += assessment_minutes

        elif days >= 4:
            # Day N: Final Assessment + Targeted Revision
            final_day = day_buckets[-1]
            if final_day_revision > 0:
                final_rev = {
                    "item_type": "REVISION",
                    "topic_id": f"rev-targeted-{subject.id}",
                    "topic_name": "Pre-Exam Review & Weak Topic Revision",
                    "unit_id": subject.units[0].id if subject.units else "",
                    "unit_title": "Targeted Review",
                    "allocated_minutes": final_day_revision,
                    "priority": "HIGH",
                    "priority_label": "🔄 Targeted Revision",
                    "priority_reasons": ["Reinforce key concepts before attempting final test."],
                    "source_reference": "Core Units",
                    "status": "NOT_STARTED",
                    "best_score": None,
                    "tasks": ["Review main definitions and processes", "Verify flashcards"],
                }
                final_day["items"].append(final_rev)
                final_day["allocated_minutes"] += final_day_revision

            final_assess = {
                "item_type": "ASSESSMENT",
                "topic_id": f"assess-{subject.id}",
                "topic_name": "Full-Syllabus Master Assessment (Target ≥ 65% for Syllabus Completion)",
                "unit_id": subject.units[0].id if subject.units else "",
                "unit_title": "Final Assessment",
                "allocated_minutes": assessment_minutes,
                "priority": "HIGH",
                "priority_label": "📝 Final Assessment",
                "priority_reasons": ["Rule 26: 100% syllabus completion requires >= 65% score in the final assessment."],
                "source_reference": "Full Subject",
                "status": "NOT_STARTED",
                "best_score": None,
                "tasks": [
                    "Complete full-length subject assessment",
                    "Target >= 65% for mastery completion",
                ],
            }
            final_day["items"].append(final_assess)
            final_day["allocated_minutes"] += assessment_minutes

        elif days >= 2:
            # For 2-3 days, add assessment block on final day
            final_day = day_buckets[-1]
            final_assess = {
                "item_type": "ASSESSMENT",
                "topic_id": f"assess-{subject.id}",
                "topic_name": "Syllabus Mastery Quiz (Target ≥ 65%)",
                "unit_id": subject.units[0].id if subject.units else "",
                "unit_title": "Master Assessment",
                "allocated_minutes": assessment_minutes,
                "priority": "HIGH",
                "priority_label": "📝 Final Assessment",
                "priority_reasons": ["Verify syllabus mastery (score >= 65% required)."],
                "source_reference": "All Topics",
                "status": "NOT_STARTED",
                "best_score": None,
                "tasks": ["Complete master topic quiz", "Verify answers"],
            }
            final_day["items"].append(final_assess)
            final_day["allocated_minutes"] += assessment_minutes

        # Now pack new topics into available day buckets
        current_day_idx = 0
        max_topic_days = days - reserved_non_topic_days if (days >= 4) else days

        for item_data in topic_analyses:
            topic = item_data["topic"]
            analysis = item_data["analysis"]
            unit = item_data["unit"]
            topic_duration = item_data["allocated_minutes"]

            # Find the earliest day with capacity
            placed = False
            while current_day_idx < max_topic_days:
                bucket = day_buckets[current_day_idx]
                rem_minutes = bucket["available_minutes"] - bucket["allocated_minutes"]

                if rem_minutes >= topic_duration:
                    # Fits comfortably!
                    bucket["items"].append(self._build_topic_roadmap_item(topic, analysis, unit, topic_duration))
                    bucket["allocated_minutes"] += topic_duration
                    placed = True
                    break
                elif rem_minutes >= 30 and rem_minutes >= (topic_duration // 2):
                    # Day has meaningful capacity (e.g. 45m or 60m remaining): allocate what fits
                    actual_duration = rem_minutes
                    bucket["items"].append(self._build_topic_roadmap_item(topic, analysis, unit, actual_duration))
                    bucket["allocated_minutes"] += actual_duration
                    placed = True
                    current_day_idx += 1
                    break
                else:
                    # Move to next day
                    current_day_idx += 1

            if not placed:
                # If we ran out of normal days, try to fit in any remaining day capacity
                for b in day_buckets:
                    rem = b["available_minutes"] - b["allocated_minutes"]
                    if rem >= 30:
                        dur = min(rem, topic_duration)
                        b["items"].append(self._build_topic_roadmap_item(topic, analysis, unit, dur))
                        b["allocated_minutes"] += dur
                        placed = True
                        break

        # Fill any remaining day capacity with progressive revision / practice
        for bucket in day_buckets:
            rem = bucket["available_minutes"] - bucket["allocated_minutes"]
            if rem >= 30:
                # Add a clean practice/revision block
                bucket["items"].append({
                    "item_type": "PRACTICE",
                    "topic_id": f"practice-day-{bucket['day_number']}",
                    "topic_name": "Daily Conceptual Review & Quiz Practice",
                    "unit_id": subject.units[0].id if subject.units else "",
                    "unit_title": "Daily Reinforcement",
                    "allocated_minutes": rem,
                    "priority": "MEDIUM",
                    "priority_label": "⚡ Practice & Review",
                    "priority_reasons": ["Reinforce concepts learned today through active recall and quick quiz questions."],
                    "source_reference": "Today's Topics",
                    "status": "NOT_STARTED",
                    "best_score": None,
                    "tasks": ["Review key definitions & notes", "Take practice quiz questions"],
                })
                bucket["allocated_minutes"] += rem

        # -------------------------------------------------------------
        # VALIDATE MATHEMATICAL HARD LIMITS
        # -------------------------------------------------------------
        total_scheduled_minutes = 0
        flat_schedule: List[Dict[str, Any]] = []

        for bucket in day_buckets:
            # Ensure day allocated minutes never exceeds daily limit
            assert bucket["allocated_minutes"] <= daily_limit_minutes, (
                f"Day {bucket['day_number']} allocated {bucket['allocated_minutes']}m > limit {daily_limit_minutes}m"
            )
            total_scheduled_minutes += bucket["allocated_minutes"]

            for item in bucket["items"]:
                # Ensure date and day_number are populated
                item["date"] = bucket["date"]
                item["day_number"] = bucket["day_number"]
                item["study_minutes"] = item.get("allocated_minutes", 30)

                # Backwards compatibility fields for existing tests
                topic_name = item.get("topic_name", "Topic")
                scope_str = item.get("source_reference", "source slides")
                priority_label = item.get("priority_label", "High Study Priority")
                strategy_tip = item.get("strategy_tip", "Master key definition and concepts.")

                short_guide = (
                    f"### 📌 Core Concept & Roadmap Focus: {topic_name}\n"
                    f"**Priority**: {priority_label}\n"
                    f"**Exam Strategy**: {strategy_tip}\n"
                    f"### ⚡ High-Yield Main Points\n"
                    f"- Source Location: {scope_str}\n"
                    f"- Target: Master key definition and high-scoring exam points."
                )
                detailed_guide = (
                    f"### 📖 Topic Overview & Core Concept: {topic_name}\n"
                    f"**Priority**: {priority_label}\n"
                    f"**Exam Strategy**: {strategy_tip}\n"
                    f"### 🎯 Detailed Conceptual Breakdown\n"
                    f"- Source Location: {scope_str}\n"
                    f"- Target: Master key definition, exam frameworks, and take topic quiz."
                )

                item["material_mode"] = "detailed" if detailed else "concise"
                item["material"] = detailed_guide if detailed else short_guide
                item["short_points"] = short_guide
                item["detailed_content"] = detailed_guide
                item["key_points"] = [topic_name, priority_label, scope_str]
                if not item.get("tasks"):
                    item["tasks"] = [
                        f"Study authentic {scope_str} ({item['study_minutes']} min)",
                        "Memorize key definition and high-scoring points",
                        "Take 5-question topic quiz (target ≥ 75% score)",
                    ]

                flat_schedule.append(item)

        total_scheduled_hours = round(total_scheduled_minutes / 60.0, 1)
        buffer_minutes = max(0, total_available_minutes - total_scheduled_minutes)
        buffer_hours = round(buffer_minutes / 60.0, 1)

        # Count item types
        topics_count = sum(1 for it in flat_schedule if it.get("item_type") == "NEW_TOPIC")
        revision_hours = round(sum(it.get("allocated_minutes", 0) for it in flat_schedule if it.get("item_type") in ["REVISION", "PRACTICE"]) / 60.0, 1)
        assessment_hours = round(sum(it.get("allocated_minutes", 0) for it in flat_schedule if it.get("item_type") == "ASSESSMENT") / 60.0, 1)

        # High weightage & quick win counts for summary badges
        high_weightage_count = sum(1 for it in flat_schedule if it.get("priority") == "HIGH" or it.get("rank") == 1)
        quick_win_count = sum(1 for it in flat_schedule if it.get("priority") == "MEDIUM" or it.get("rank") == 2)

        # Construct final structured response
        response_data: Dict[str, Any] = {
            "subject_id": subject.id,
            "subject_name": subject.name,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "days": days,
            "daily_hours": daily_hours,
            "total_available_hours": total_available_hours,
            "total_scheduled_hours": total_scheduled_hours,
            "buffer_hours": buffer_hours,
            "has_shortfall": has_shortfall,
            "shortfall_hours": shortfall_hours,
            "shortfall_message": shortfall_message,
            "topics_count": topics_count,
            "revision_hours": revision_hours,
            "assessment_hours": assessment_hours,
            "high_weightage_count": high_weightage_count,
            "quick_win_count": quick_win_count,
            "total_topics_in_syllabus": len(all_topics),
            "topics_scheduled": topics_count,
            "daily_schedule": [
                {
                    "day_number": b["day_number"],
                    "date": b["date"],
                    "available_hours": round(b["available_minutes"] / 60.0, 1),
                    "allocated_hours": round(b["allocated_minutes"] / 60.0, 1),
                    "allocated_minutes": b["allocated_minutes"],
                    "remaining_minutes": b["available_minutes"] - b["allocated_minutes"],
                    "items": b["items"],
                }
                for b in day_buckets
            ],
            "schedule": flat_schedule,
            # Backwards compatibility fields
            "total_hours": total_scheduled_hours,
            "minutes_per_topic": round(sum(it.get("allocated_minutes", 0) for it in flat_schedule if it.get("item_type") == "NEW_TOPIC") / max(1, topics_count)),
            "material_mode": "detailed" if detailed else "concise",
            "material_preference": material_preference or "auto",
            "only_important": only_important,
        }

        # Persist active roadmap in database
        if user_id:
            try:
                existing_roadmap = db.query(StudyRoadmap).filter(
                    StudyRoadmap.user_id == user_id,
                    StudyRoadmap.subject_id == subject.id,
                ).first()

                if existing_roadmap:
                    existing_roadmap.start_date = start_date
                    existing_roadmap.end_date = end_date
                    existing_roadmap.days = days
                    existing_roadmap.daily_hours = daily_hours
                    existing_roadmap.total_available_hours = total_available_hours
                    existing_roadmap.total_scheduled_hours = total_scheduled_hours
                    existing_roadmap.buffer_hours = buffer_hours
                    existing_roadmap.shortfall_hours = shortfall_hours
                    existing_roadmap.has_shortfall = has_shortfall
                    existing_roadmap.shortfall_message = shortfall_message
                    existing_roadmap.topics_count = topics_count
                    existing_roadmap.revision_hours = revision_hours
                    existing_roadmap.assessment_hours = assessment_hours
                    existing_roadmap.plan_data = response_data
                else:
                    new_roadmap = StudyRoadmap(
                        user_id=user_id,
                        subject_id=subject.id,
                        start_date=start_date,
                        end_date=end_date,
                        days=days,
                        daily_hours=daily_hours,
                        total_available_hours=total_available_hours,
                        total_scheduled_hours=total_scheduled_hours,
                        buffer_hours=buffer_hours,
                        shortfall_hours=shortfall_hours,
                        has_shortfall=has_shortfall,
                        shortfall_message=shortfall_message,
                        topics_count=topics_count,
                        revision_hours=revision_hours,
                        assessment_hours=assessment_hours,
                        plan_data=response_data,
                    )
                    db.add(new_roadmap)
                db.commit()
            except Exception as e:
                logger.warning(f"Could not persist StudyRoadmap record: {e}")
                db.rollback()

        return response_data

    @staticmethod
    def _build_topic_roadmap_item(
        topic: Topic,
        analysis: Dict[str, Any],
        unit: Any,
        duration: int,
    ) -> Dict[str, Any]:
        """Constructs a clean planning item for a syllabus topic."""
        return {
            "item_type": "NEW_TOPIC",
            "topic_id": topic.id,
            "topic_name": topic.name,
            "unit_id": unit.id,
            "unit_title": unit.title,
            "allocated_minutes": duration,
            "study_minutes": duration,
            "priority": analysis["priority"],
            "priority_tier": analysis["priority_tier"],
            "rank": analysis["rank"],
            "is_important": analysis["is_important"],
            "priority_label": analysis["priority_label"],
            "importance_label": analysis["importance_label"],
            "strategy_tip": analysis["strategy_tip"],
            "priority_reasons": analysis["reasons"],
            "source_start": topic.source_start,
            "source_end": topic.source_end,
            "source_reference": analysis["source_reference"],
            "status": analysis["status"],
            "best_score": analysis["best_score"],
            "tasks": [
                f"Study authentic {analysis['source_reference']} ({duration // 2} min)",
                "Memorize key definition and high-scoring points",
                "Take 5-question topic quiz (target ≥ 75% score)",
            ],
        }


study_plan_service = StudyPlanService()
