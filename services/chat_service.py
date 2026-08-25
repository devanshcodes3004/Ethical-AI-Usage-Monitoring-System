"""
chat_service.py

Coordinates the complete chat pipeline.
"""

from langchain_core.messages import AIMessage, HumanMessage

from database.audit_repository import AuditRepository
from database.message_repository import MessageRepository
from database.models import AuditLogDocument, MessageDocument

from router.router import Router
from services.governance_service import GovernanceService


class ChatService:

    def __init__(self):

        self.router = Router()
        self.governance = GovernanceService()
        self.message_repository = MessageRepository()
        self.audit_repository = AuditRepository()

    def get_chat_history(
        self,
        session_id: str
    ):

        try:

            messages = self.message_repository.get_session_messages(
                session_id
            )

            history = []

            for message in messages:

                history.append(
                    {
                        "role": message.role,
                        "content": message.content
                    }
                )

            return history

        except Exception:

            return []

    def chat(
        self,
        session_id: str,
        user_id: str,
        prompt: str
    ):

        # =====================================================
        # Governance Analysis
        # =====================================================

        decision = self.governance.analyze_prompt(prompt)

        # =====================================================
        # Save User Message
        # =====================================================

        user_message = MessageDocument(
            session_id=session_id,
            user_id=user_id,
            role="user",
            content=prompt
        )

        self.message_repository.save_message(
            user_message
        )

        # =====================================================
        # BLOCK REQUEST
        # =====================================================

        if decision.decision.value == "BLOCK":

            blocked_response = (
                "🚫 **Request Blocked by AI Governance Engine**\n\n"
                f"**Reason:** {decision.reason}\n\n"
                f"**Risk Score:** {decision.risk_score}\n"
                f"**Risk Level:** {decision.risk_level.value}\n\n"
                f"**Categories:** "
                f"{', '.join(decision.categories) if decision.categories else 'None'}"
            )

            assistant_message = MessageDocument(
                session_id=session_id,
                user_id=user_id,
                role="assistant",
                content=blocked_response,
                model=decision.selected_model.value
            )

            self.message_repository.save_message(
                assistant_message
            )

            audit = AuditLogDocument(
                session_id=session_id,
                user_id=user_id,
                message_id="",
                risk_score=decision.risk_score,
                risk_level=decision.risk_level.value,
                decision=decision.decision.value,
                categories=decision.categories,
                reason=decision.reason,
                confidence=decision.confidence,
                selected_model=decision.selected_model.value
            )

            self.audit_repository.save_log(
                audit
            )

            return {
                "success": False,
                "response": blocked_response,
                "decision": decision
            }

        # =====================================================
        # Load Conversation History
        # =====================================================

        db_messages = self.message_repository.get_session_messages(
            session_id
        )

        history = []

        for message in db_messages:

            if message.role == "user":

                history.append(
                    HumanMessage(
                        content=message.content
                    )
                )

            else:

                history.append(
                    AIMessage(
                        content=message.content
                    )
                )

        # =====================================================
        # Select Model
        # =====================================================

        model = self.router.get_model(
            decision.selected_model.value
        )

        result = model.invoke(history)

        response = result["response"]

        # =====================================================
        # Save Assistant Response
        # =====================================================

        assistant_message = MessageDocument(
            session_id=session_id,
            user_id=user_id,
            role="assistant",
            content=response,
            model=decision.selected_model.value
        )

        self.message_repository.save_message(
            assistant_message
        )

        # =====================================================
        # Save Audit Log
        # =====================================================

        audit = AuditLogDocument(
            session_id=session_id,
            user_id=user_id,
            message_id="",
            risk_score=decision.risk_score,
            risk_level=decision.risk_level.value,
            decision=decision.decision.value,
            categories=decision.categories,
            reason=decision.reason,
            confidence=decision.confidence,
            selected_model=decision.selected_model.value
        )

        self.audit_repository.save_log(
            audit
        )

        # =====================================================
        # Return Response
        # =====================================================

        return {
            "success": True,
            "response": response,
            "decision": decision
        }