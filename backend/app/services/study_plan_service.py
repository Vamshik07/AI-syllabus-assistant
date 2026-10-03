from datetime import date, timedelta
from math import ceil
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.models.models import Subject


class StudyPlanService:
    """Builds deterministic, source-grounded study plans from a subject syllabus."""

    @staticmethod
    def _source_material(topic: Any, detailed: bool) -> str:
        lines = [
            region.content_text.strip()
            for region in topic.source_regions
            if region.content_text and region.content_text.strip()
        ]
        if not lines:
            return "Review the original source pages/slides for this topic."

        # Keep the material verbatim; only select a bounded amount for the plan.
        limit = 1400 if detailed else 500
        selected: List[str] = []
        length = 0
        for line in lines:
            addition = line if not selected else f"\n{line}"
            if selected and length + len(addition) > limit:
                break
            selected.append(line)
            length += len(addition)
        return "\n".join(selected)

    def create_plan(
        self,
        db: Session,
        subject: Subject,
        start_date: date,
        end_date: date,
        daily_hours: float,
    ) -> Dict[str, Any]:
        days = (end_date - start_date).days + 1
        topics: List[Any] = []
        for unit in sorted(subject.units, key=lambda item: item.order_index):
            if unit.document:
                topics.extend(sorted(unit.document.topics, key=lambda item: item.order_index))

        if not topics:
            raise ValueError("Upload and process at least one syllabus document before creating a timetable.")

        total_minutes = days * daily_hours * 60
        minutes_per_topic = total_minutes / len(topics)
        detailed = minutes_per_topic >= 45
        topic_minutes = max(15, int(round(minutes_per_topic)))
        schedule: List[Dict[str, Any]] = []

        for index, topic in enumerate(topics):
            day_offset = min(days - 1, int(index * days / len(topics)))
            study_date = start_date + timedelta(days=day_offset)
            unit = topic.document.unit
            schedule.append(
                {
                    "date": study_date.isoformat(),
                    "unit_id": unit.id,
                    "unit_title": unit.title,
                    "topic_id": topic.id,
                    "topic_name": topic.name,
                    "study_minutes": topic_minutes,
                    "material_mode": "detailed" if detailed else "concise",
                    "material": self._source_material(topic, detailed),
                    "source_start": topic.source_start,
                    "source_end": topic.source_end,
                    "tasks": [
                        "Read the source material",
                        "Write a short recall summary",
                        "Attempt the topic quiz" if detailed else "Review the key points",
                    ],
                }
            )

        schedule.sort(key=lambda item: (item["date"], item["unit_title"], item["topic_name"]))
        return {
            "subject_id": subject.id,
            "subject_name": subject.name,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "days": days,
            "daily_hours": daily_hours,
            "total_hours": round(total_minutes / 60, 1),
            "material_mode": "detailed" if detailed else "concise",
            "schedule": schedule,
        }


study_plan_service = StudyPlanService()
