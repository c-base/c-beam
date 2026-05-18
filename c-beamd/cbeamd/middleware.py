import logging
import time
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log HTTP requests and responses for monitoring purposes.
    """

    def process_request(self, request):
        """Log incoming requests."""
        request.start_time = time.time()

        # Skip logging for static files and media
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            return

        logger.info(
            f"REQUEST: {request.method} {request.path} "
            f"from {self._get_client_ip(request)} "
            f"user={request.user.username if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous'}"
        )

    def process_response(self, request, response):
        """Log outgoing responses."""
        # Skip logging for static files and media
        if hasattr(request, 'path') and (
            request.path.startswith('/static/') or request.path.startswith('/media/')
        ):
            return response

        # Calculate response time
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
        else:
            duration = 0

        logger.info(
            f"RESPONSE: {request.method} {request.path} "
            f"status={response.status_code} "
            f"duration={duration:.3f}s "
            f"user={request.user.username if hasattr(request, 'user') and hasattr(request.user, 'is_authenticated') and request.user.is_authenticated else 'anonymous'}"
        )

        return response

    def process_exception(self, request, exception):
        """Log exceptions that occur during request processing."""
        logger.error(
            f"EXCEPTION: {request.method} {request.path} "
            f"exception={type(exception).__name__}: {str(exception)} "
            f"user={request.user.username if hasattr(request, 'user') and hasattr(request.user, 'is_authenticated') and request.user.is_authenticated else 'anonymous'}",
            exc_info=True
        )

    def _get_client_ip(self, request):
        """Get the client IP address from the request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SecurityLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log security-related events.
    """

    def process_request(self, request):
        """Log potential security issues."""
        # Log suspicious requests
        suspicious_patterns = [
            '../../',  # Directory traversal
            '<script',  # XSS attempts
            'union select',  # SQL injection attempts
            'eval(',  # Code injection attempts
        ]

        request_path = request.path.lower()
        request_get = str(request.GET).lower()

        for pattern in suspicious_patterns:
            if pattern in request_path or pattern in request_get:
                logger.warning(
                    f"SECURITY: Suspicious request detected: {request.method} {request.path} "
                    f"from {self._get_client_ip(request)} "
                    f"GET={dict(request.GET)} "
                    f"user={request.user.username if hasattr(request, 'user') and hasattr(request.user, 'is_authenticated') and request.user.is_authenticated else 'anonymous'}"
                )
                break

    def _get_client_ip(self, request):
        """Get the client IP address from the request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
