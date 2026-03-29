from typing import List, Optional
from uuid import UUID
from datetime import datetime
from app.core.database import supabase_client
from app.schemas import NotificationCreate, NotificationOut, NotificationType, KNECScore
from app.services.knowledge_graph import knowledge_graph_service

class NotificationService:
    def __init__(self):
        self.client = supabase_client

    def create_notification(self, notification: NotificationCreate) -> NotificationOut:
        data = notification.model_dump()
        data["learner_id"] = str(data["learner_id"])
        data["type"] = data["type"].value
        
        response = self.client.table("notifications").insert(data).execute()
        return NotificationOut(**response.data[0])

    def get_learner_notifications(self, learner_id: UUID, unread_only: bool = False) -> List[NotificationOut]:
        query = self.client.table("notifications")\
            .select("*")\
            .eq("learner_id", str(learner_id))\
            .order("created_at", desc=True)
            
        if unread_only:
            query = query.eq("is_read", False)
            
        response = query.execute()
        return [NotificationOut(**item) for item in response.data]

    def mark_as_read(self, notification_id: UUID) -> bool:
        response = self.client.table("notifications")\
            .update({"is_read": True})\
            .eq("id", str(notification_id))\
            .execute()
        return len(response.data) > 0

    def check_intervention_trigger(self, learner_id: UUID, learning_outcome_id: UUID, current_score: str, outcome_description: str, mastery_probability: Optional[float] = None):
        """
        Check if the learner needs intervention based on:
        1. Repeated failures (2+ times in last 5 attempts).
        2. Low mastery probability (< 50%).
        """
        # 1. Define Failure Scores
        failing_scores = ["AE1", "AE2", "BE1", "BE2"]
        
        should_trigger = False
        trigger_reason = ""
        
        # Check Mastery Probability (< 50%)
        if mastery_probability is not None and mastery_probability < 0.5:
            should_trigger = True
            trigger_reason = f"Mastery probability dropped to {int(mastery_probability * 100)}%."

        # Check Repeated Failures (only if not already triggered, or to add context)
        if not should_trigger and current_score in failing_scores:
            # Fetch recent history for this outcome
            response = self.client.table("sba_records")\
                .select("score, recorded_at")\
                .eq("learner_id", str(learner_id))\
                .eq("learning_outcome_id", str(learning_outcome_id))\
                .order("recorded_at", desc=True)\
                .limit(5)\
                .execute()
                
            history = response.data
            failure_count = 0
            for record in history:
                if record["score"] in failing_scores:
                    failure_count += 1
            
            if failure_count >= 2:
                should_trigger = True
                trigger_reason = f"Failed {failure_count} times recently."
        
        if should_trigger:
            # Check if we already sent a notification recently for this outcome to avoid spamming
            # (Simple check: look for unread notifications with this outcome_id in metadata)
            existing = self.client.table("notifications")\
                .select("id")\
                .eq("learner_id", str(learner_id))\
                .eq("is_read", False)\
                .contains("metadata", {"outcome_id": str(learning_outcome_id)})\
                .execute()
                
            if existing.data:
                return # Already have an active alert

            # 4. Generate Remedial Suggestions
            prerequisites = knowledge_graph_service.get_prerequisites(outcome_description)
            
            suggestion_text = ""
            if prerequisites:
                topics = [p.get("source_topic") for p in prerequisites]
                suggestion_text = f"We suggest reviewing these foundational topics: {', '.join(topics)}."
            else:
                suggestion_text = "We suggest reviewing the previous lessons on this topic or scheduling a consultation with the teacher."

            # 5. Create Notification
            message = f"Intervention Needed: {trigger_reason} {suggestion_text}"
            
            notification = NotificationCreate(
                learner_id=learner_id,
                title=f"Intervention Needed: {outcome_description}",
                message=message,
                type=NotificationType.INTERVENTION,
                metadata={
                    "outcome_id": str(learning_outcome_id),
                    "reason": trigger_reason,
                    "latest_score": current_score,
                    "mastery": mastery_probability
                }
            )
            
            self.create_notification(notification)
            print(f"Intervention triggered for learner {learner_id} on {outcome_description}")

notification_service = NotificationService()
