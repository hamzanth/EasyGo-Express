from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework import status

def custom_exception_handler(exc, context):
    # Call DRF's standard handler first
    response = exception_handler(exc, context)

    # Check if it's a validation error
    if isinstance(exc, ValidationError):
        custom_errors = {}
        
        # Source the raw error dictionary directly from the exception
        raw_errors = exc.detail if hasattr(exc, 'detail') else {}
        
        for field, errors in raw_errors.items():
            if isinstance(errors, list) and len(errors) > 0:
                # Extracts just the first string message out of the ErrorDetail list
                custom_errors[field] = str(errors[0])
            else:
                custom_errors[field] = str(errors)

        # Force build a brand new JSON response to override any HTML defaults
        response = Response(
            {"errors": custom_errors}, 
            status=status.HTTP_400_BAD_REQUEST
        )
        # Ensure it renders explicitly as JSON
        response.accepted_renderer = JSONRenderer()
        response.accepted_media_type = "application/json"
        response.renderer_context = {}

    return response
