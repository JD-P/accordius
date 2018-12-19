from django.shortcuts import render
from rest_framework import viewsets, filters
from rest_framework.permissions import DjangoModelPermissions
from lw2.models import *
from lw2.serializers import *
# Create your views here.

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
