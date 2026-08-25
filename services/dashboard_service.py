"""
dashboard_service.py

Provides business logic for dashboard statistics.
"""

import sys

from database.dashboard_repository import DashboardRepository

from exception import CustomException


class DashboardService:

    def __init__(self):

        self.dashboard_repository = DashboardRepository()

    def get_dashboard_statistics(self):

        try:

            model_usage = self.dashboard_repository.get_model_usage()

            gemini_count = 0
            ollama_count = 0

            for model in model_usage:

                if model["_id"] == "Gemini":
                    gemini_count = model["count"]

                elif model["_id"] == "Ollama":
                    ollama_count = model["count"]

            return {
                "total_sessions":
                    self.dashboard_repository.get_total_sessions(),

                "total_messages":
                    self.dashboard_repository.get_total_messages(),

                "allowed_requests":
                    self.dashboard_repository.get_allowed_requests(),

                "blocked_requests":
                    self.dashboard_repository.get_blocked_requests(),

                "average_risk_score":
                    self.dashboard_repository.get_average_risk_score(),

                "highest_risk_score":
                    self.dashboard_repository.get_highest_risk_score(),

                "gemini_count":
                    gemini_count,

                "ollama_count":
                    ollama_count,

                "top_categories":
                    self.dashboard_repository.get_top_categories(),

                "recent_blocked_requests":
                    self.dashboard_repository.get_recent_blocked_requests()
            }

        except Exception as e:
            raise CustomException(e, sys)