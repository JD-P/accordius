from django.shortcuts import render
from rest_framework import viewsets, filters, generics
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication, BasicAuthentication 
from lw2.models import *
from lw2.serializers import *
# Create your views here.

class CsrfExemptSessionAuthentication(SessionAuthentication):
    """The API doesn't actually communicate with a users browser, so CSRF 
    doesn't make sense."""
    def enforce_csrf(self, request):
        return

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer

class TagViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows tags to be viewed or edited.
    """
    authentication_classes = (CsrfExemptSessionAuthentication,BasicAuthentication)
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    filter_fields = ('user','document_id','text',)

class BanViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows bans to be viewed or edited.
    """
    permission_classes = (DjangoModelPermissions,)
    queryset = Ban.objects.all()
    serializer_class = BanSerializer

class InviteViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows invites to be created or viewed.
    """
    permission_classes = (IsAuthenticated,)
    queryset = Invite.objects.all()
    serializer_class = InviteSerializer

class InviteList(generics.ListAPIView):
    """
    API endpoint that lets a user get a list of their created invite codes.
    """
    serializer_class = RestrictedInviteSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return Invite.objects.filter(creator=user)
    
