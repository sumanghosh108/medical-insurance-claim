import sys
import traceback

def error_message_details(error,error_details):
    if error_details:
        tb=traceback.extract_tb(sys.exc_info()[2])
        
        if not tb:
            return str(error)
        
        last_trace=tb[-1]
        file_name=last_trace.filename
        line_number=last_trace.lineno
        
        return (
            f"Error in script [{file_name}]"
            f"line no [{line_number}]"
            f"error [{str(error)}]"
        )

class CustomException(Exception):
    def __init__(self,error_message,error_detail):
        super().__init__(error_message)
        self.error_message=error_message_details(error_message,error_details=error_detail)
    
    def __str__(self):
        return self.error_message