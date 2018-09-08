from graphene_django import DjangoObjectType
import graphene
from .models import Test

class TestType(DjangoObjectType):
    class Meta:
        model = Test

class Query(object):
    all_tests = graphene.List(TestType)

    def resolve_all_tests(self, info, **kwargs):
        return Test.objects.all()
