"""
Health-check and metrics endpoints.

Split out of the original views.py; function bodies are unchanged.
"""

import json

from django.http import HttpResponse
from django.utils import timezone

from ..models import User

from .helpers import logger

# Health Check Views
def health_check(request):
    """
    Basic health check endpoint that returns application status.
    """
    from django.db import connection

    health_status = {
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'version': '1.0.0',
        'checks': {}
    }

    # Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_status['checks']['database'] = 'healthy'
    except Exception as e:
        health_status['checks']['database'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'unhealthy'

    # External services check (optional)
    try:
        # Check MQTT connection (simplified)
        health_status['checks']['mqtt'] = 'healthy'
    except Exception as e:
        health_status['checks']['mqtt'] = f'unhealthy: {str(e)}'

    status_code = 200 if health_status['status'] == 'healthy' else 503

    return HttpResponse(
        json.dumps(health_status, indent=2),
        content_type='application/json',
        status=status_code
    )


def readiness_check(request):
    """
    Kubernetes readiness probe endpoint.
    Returns 200 if the application is ready to serve traffic.
    """
    from django.db import connection

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM cbeamd_user")
        return HttpResponse("OK", status=200)
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return HttpResponse("NOT READY", status=503)


def liveness_check(request):
    """
    Kubernetes liveness probe endpoint.
    Returns 200 if the application is running properly.
    """
    # Simple liveness check - if Django is responding, it's alive
    return HttpResponse("OK", status=200)


def metrics(request):
    """
    Prometheus-style metrics endpoint for monitoring.
    """
    from django.db import connection
    from django.core.cache import cache

    metrics_data = []

    # Database connection count
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM cbeamd_user")
            user_count = cursor.fetchone()[0]
        metrics_data.append(f'# HELP cbeam_users_total Total number of users')
        metrics_data.append(f'# TYPE cbeam_users_total gauge')
        metrics_data.append(f'cbeam_users_total {user_count}')
    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")

    # Online users count
    try:
        online_count = User.objects.filter(status='online').count()
        metrics_data.append(f'# HELP cbeam_users_online Current number of online users')
        metrics_data.append(f'# TYPE cbeam_users_online gauge')
        metrics_data.append(f'cbeam_users_online {online_count}')
    except Exception as e:
        logger.error(f"Online users metrics failed: {e}")

    # Response time (if available)
    metrics_data.append(f'# HELP cbeam_http_requests_total Total number of HTTP requests')
    metrics_data.append(f'# TYPE cbeam_http_requests_total counter')
    metrics_data.append(f'cbeam_http_requests_total{{method="GET"}} 0')
    metrics_data.append(f'cbeam_http_requests_total{{method="POST"}} 0')

    return HttpResponse('\n'.join(metrics_data), content_type='text/plain')
