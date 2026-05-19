# -*- coding: utf-8 -*-
"""
Health check and monitoring views.
"""

import json
from django.http import HttpResponse, JsonResponse
from django.utils import timezone


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

    return JsonResponse(health_status)


def readiness_check(request):
    """
    Readiness check - can the application serve requests?
    """
    from django.db import connection

    readiness = {
        'status': 'ready',
        'timestamp': timezone.now().isoformat(),
        'checks': {}
    }

    # Check database connectivity
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        readiness['checks']['database'] = 'ready'
    except Exception as e:
        readiness['checks']['database'] = f'not ready: {str(e)}'
        readiness['status'] = 'not ready'

    status_code = 200 if readiness['status'] == 'ready' else 503
    return JsonResponse(readiness, status=status_code)


def liveness_check(request):
    """
    Liveness check - is the application process alive?
    """
    liveness = {
        'status': 'alive',
        'timestamp': timezone.now().isoformat()
    }

    return JsonResponse(liveness)


def metrics(request):
    """
    Prometheus-style metrics endpoint.
    """
    from .view_helpers import models

    metrics_data = {
        'timestamp': timezone.now().isoformat(),
        'users': {
            'online': models.User.objects.filter(status='online').count(),
            'eta': models.User.objects.filter(status='eta').count(),
            'total': models.User.objects.count(),
        },
        'missions': {
            'open': models.Mission.objects.filter(status='open').count(),
            'assigned': models.Mission.objects.filter(status='assigned').count(),
            'completed': models.Mission.objects.filter(status='completed').count(),
        },
    }

    return HttpResponse(
        json.dumps(metrics_data),
        content_type='application/json'
    )
