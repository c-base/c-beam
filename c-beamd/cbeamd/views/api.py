"""
Django REST Framework viewsets.

Split out of the original views.py; function bodies are unchanged.
"""


import requests
from django.http import HttpResponse
from rest_framework import permissions, viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action

from ..models import Device, User
from ..serializers import DeviceSerializer, UserSerializer
from ..devices import DeviceAuthentication, IsRegisteredDevice, assign_key

from .auth import tagevent
from .bar import get_barstatus
from .events import event_list
from .helpers import get_prices
from cbeamd.tools.ldapRfid import LdapRfidCheck


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
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class UserTagViewSet(viewsets.ViewSet):
    """
    tag events from the rfid readers at the airlock.

    only registered devices may post here: the reader authenticates with
    `Authorization: Device <device_id>:<key>` (see cbeamd/devices.py and the
    devices endpoint). session and bearer authentication are deliberately not
    accepted — a crew member is not a reader.
    """
    authentication_classes = [DeviceAuthentication]
    permission_classes = [IsRegisteredDevice]

    @action(detail=False, methods=['post'])
    def seen(self, request, *args, **kwargs):
        rfid = request.data.get('rfid')
        if not rfid:
            return Response({'error': 'rfid missing'}, status=status.HTTP_400_BAD_REQUEST)
        # lookup user by tag
        f = LdapRfidCheck("ldaps://lea.cbrp3.c-base.org", 'ou=crew,dc=c-base,dc=org', '', '', 'rfid', '(memberOf=cn=crew,ou=groups,dc=c-base,dc=org)')
        try:
            dn = f.getUserForRfid(rfid)
        finally:
            f.cleanup()
        if dn is None:
            return Response({'error': 'unknown rfid'}, status=status.HTTP_404_NOT_FOUND)
        # the lookup returns the DN (uid=<nick>,ou=crew,...), tagevent wants the nick
        username = dn.split(',')[0].split('=', 1)[1]
        result = tagevent(request, username)
        if isinstance(result, HttpResponse):
            result = result.content.decode()
        return Response({'user': username, 'result': result, 'device': request.auth.device_id})


class DeviceViewSet(viewsets.ModelViewSet):
    """
    registration of rfid readers, for admins (staff accounts) only.

    ## Create device
    Registers a reader and answers with its key — the only time the key is
    readable. Flash it into the device together with the device_id.

    ## Rotate key
    POST to `/devices/<id>/rotate_key/` issues a new key and invalidates the
    old one; the response carries the new key once.
    """
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    permission_classes = [permissions.IsAdminUser]

    def perform_create(self, serializer):
        device = Device(**serializer.validated_data)
        device.plain_key = assign_key(device)
        device.save()
        serializer.instance = device

    @action(detail=True, methods=['post'])
    def rotate_key(self, request, *args, **kwargs):
        device = self.get_object()
        device.plain_key = assign_key(device)
        device.save(update_fields=['key_hash'])
        return Response(self.get_serializer(device).data)


class MemberViewSet(viewsets.ViewSet):
    """
    API endpoint for member-related operations.

    ## List members
    Returns a list of currently online members with their online percentage.
    This endpoint provides real-time information about active space station crew.
    """
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        queryset = User.objects.filter(status="online").order_by('username')
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
