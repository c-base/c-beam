# -*- coding: utf-8 -*-
"""
REST API ViewSets.
"""

import requests
from rest_framework import permissions, viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action

from .. import models
from ..serializers import UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.

    ## List users
    Returns a list of all users in the system with their current status and activity points.

    ## Retrieve user
    Returns detailed information about a specific user.

    ## Create user
    Creates a new user in the system.

    ## Update user
    Updates an existing user's information.

    ## Delete user
    Removes a user from the system.
    """
    queryset = models.User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class MemberViewSet(viewsets.ViewSet):
    """
    API endpoint for member-related operations.

    ## List members
    Returns a list of currently online members with their online percentage.
    This endpoint provides real-time information about active space station crew.
    """
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        queryset = models.User.objects.filter(status="online").order_by('username')
        serializer = UserSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)


class PriceViewSet(viewsets.ViewSet):
    """
    API endpoint for bar price information.

    ## List prices
    Returns the current price list for bar items including drinks and food.
    Prices are loaded from the CSV file and returned as a structured list.
    """
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        from .helpers import get_prices
        return Response(get_prices())


class EventViewSet(viewsets.ViewSet):
    """
    API endpoint for space station events.

    ## List events
    Returns today's events from the c-base calendar including title, start/end times,
    and descriptions. Events are fetched from the external calendar feed.
    """
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        from .events import event_list
        return Response(event_list(request))


class BarViewSet(viewsets.ViewSet):
    """
    API endpoint for bar status information.

    ## List bar status
    Returns whether the bar is currently open or closed.
    This information is used by crew members to know when bar services are available.
    """
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        from .bar import get_barstatus
        return Response(get_barstatus(request))


class MatelightViewSet(viewsets.ViewSet):
    """
    API endpoint for Matelight display control.

    The Matelight is a LED display system in the space station.

    ## List videos
    Returns a list of available videos that can be played on the Matelight display.

    ## Retrieve video
    Returns detailed information about a specific video.

    ## Play video
    Starts playing a specific video on the Matelight display.

    ## Stop video
    Stops the currently playing video.

    ## Get status
    Returns the current status of the Matelight system.
    """
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        url = "http://matelight.cbrp3.c-base.org/api/getvideos"
        response = requests.get(url=url)
        videos = response.json()
        return Response(videos)

    def retrieve(self, request, **kwargs):
        url = "http://matelight.cbrp3.c-base.org/api/getvideos"
        response = requests.get(url=url)
        videos = response.json()
        video = next((x for x in videos if x['title'] == kwargs['pk']), None)
        if video:
            return Response(video)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['get'])
    def play(self, request, *args, **kwargs):
        """Play a specific video on the Matelight display."""
        url = "http://matelight.cbrp3.c-base.org/api/play/" + kwargs['pk']
        response = requests.get(url=url)
        result = response.json()
        return Response(result)

    @action(detail=True, methods=['get'])
    def image(self, request, *args, **kwargs):
        """Get the thumbnail image for a specific video."""
        url = "http://matelight.cbrp3.c-base.org/api/getvideos"
        response = requests.get(url=url)
        videos = response.json()
        video = next((x for x in videos if x['title'] == kwargs['pk']), None)
        if video:
            url = "http://matelight.cbrp3.c-base.org/assets/thumbs/" + video['thumbnailName']
            response = requests.get(url=url)
            from django.http import HttpResponse
            return HttpResponse(response.content, content_type='image/jpeg')
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'])
    def stop(self, request):
        """Stop the currently playing video."""
        url = "http://matelight.cbrp3.c-base.org/api/stop"
        response = requests.get(url=url)
        result = response.json()
        return Response(result)

    @action(detail=False, methods=['get'])
    def status(self, request):
        """Get the current status of the Matelight system."""
        url = "http://matelight.cbrp3.c-base.org/api/getstatus"
        response = requests.get(url=url)
        status_data = response.json()
        return Response(status_data)
