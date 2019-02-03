from django.conf.urls import url, include
from django.views.decorators.csrf import csrf_exempt
from graphene_django.views import GraphQLView
from rest_framework import routers
from lw2.models import Tag
from lw2 import views

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'posts', views.PostViewSet)
router.register(r'comments', views.CommentViewSet)
router.register(r'tags', views.TagViewSet)
router.register(r'bans', views.BanViewSet)
router.register(r'invites', views.InviteViewSet)

urlpatterns = [
    url(r'^graphql', csrf_exempt(GraphQLView.as_view())),
    url(r'^graphiql', csrf_exempt(GraphQLView.as_view(graphiql=True))),
    url(r'^api/', include(router.urls)),
    url(r'^api/my_invites/', views.InviteList.as_view()),
    url(r'^api/post_search/', views.PostSearchView.as_view()),
    url(r'^api/comment_search/', views.CommentSearchView.as_view()),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]
