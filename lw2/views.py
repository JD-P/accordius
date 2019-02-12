from django.shortcuts import render
from django.views import View
from django.http import HttpResponse
from django.utils.datastructures import MultiValueDictKeyError
from rest_framework import viewsets, filters, generics
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.decorators import action
from lw2.models import *
from lw2.serializers import *
import lw2.search as wl_search
import pdb
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

class PostViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows posts to be viewed or edited.
    """
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    
    
class CommentViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows comments to be viewed or edited.
    """
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication)
    # Figure out later perhaps if there's a better way to ensure deleted content
    # can't be retrieved
    # TODO: Make deleted comments more foolproof
    queryset = Comment.objects.filter(is_deleted=False)
    serializer_class = CommentSerializer
    
    def destroy(self, request, pk=None):
        comment = self.queryset.get(id=pk)
        comment.is_deleted = True
        comment.save()
        return HttpResponse("Test")
    
class TagViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows tags to be viewed or edited.
    """
    authentication_classes = (CsrfExemptSessionAuthentication,BasicAuthentication)
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    filter_fields = ('user','document_id','text',)

#TODO: Add API endpoint here that returns tag validation regex    
    
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

class InviteList(viewsets.ViewSet):
    """
    API endpoint that lets a user get a list of their created invite codes.
    """
    
    def list(self, request):
        user = self.request.user
        invite_serializer = RestrictedInviteSerializer(Invite.objects.filter(creator=user),
                                                       context={'request': request}, many=True)
        if user.is_authenticated:
            return Response(invite_serializer.data)

# TODO: Refactor these to both inherit from one class or use same underlying method
# definition
class PostSearchView(viewsets.ViewSet):
    """Search posts with a query string ?query=

    See search.py for a quick guide to the search syntax rules."""
    def list(self, request):
        try:
            parsed_search = wl_search.parse_search_string(request.GET["query"])
        except MultiValueDictKeyError:
            raise ValueError("Didn't specify a query string. Use ?query=")
        filters = wl_search.mk_search_filters(parsed_search)
        posts = Post.objects.all()
        for _filter in filters:
            if _filter["exclude"]:
                posts = posts.exclude(_filter["Q"])
            else:
                posts = posts.filter(_filter["Q"])
        post_serializer = PostSerializer(posts, context={'request': request}, many=True)
        return HttpResponse(JSONRenderer().render(post_serializer.data),
                            content_type="application/json")
        
class CommentSearchView(viewsets.ViewSet):
    """Search comments with a query string ?query=

    See search.py for a quick guide to the search syntax rules."""
    def list(self, request):
        try:
            parsed_search = wl_search.parse_search_string(request.GET["query"])
        except MultiValueDictKeyError:
            raise ValueError("Didn't specify a query string. Use ?query=")
        filters = wl_search.mk_search_filters(parsed_search)
        comments = Comment.objects.all()
        for _filter in filters:
            if _filter["exclude"]:
                comments = comments.exclude(_filter["Q"])
            else:
                comments = comments.filter(_filter["Q"])
        comment_serializer = CommentSerializer(comments,
                                               context={'request': request},
                                               many=True)
        return HttpResponse(JSONRenderer().render(comment_serializer.data),
                            content_type="application/json")
