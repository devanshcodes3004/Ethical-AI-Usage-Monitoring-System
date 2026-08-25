import sys


class CustomException(Exception):
    """
    Base custom exception for the project.
    """

    def __init__(self, error_message: str, error_details: sys):
        super().__init__(error_message)

        self.error_message = self.get_detailed_error_message(
            error_message,
            error_details
        )

    @staticmethod
    def get_detailed_error_message(
        error_message: str,
        error_details: sys
    ) -> str:

        _, _, exc_tb = error_details.exc_info()

        if exc_tb is None:
            return error_message

        file_name = exc_tb.tb_frame.f_code.co_filename
        line_number = exc_tb.tb_lineno

        return (
            f"Error occurred in Python script: [{file_name}] "
            f"at line [{line_number}] "
            f"Error message: {error_message}"
        )

    def __str__(self):
        return self.error_message