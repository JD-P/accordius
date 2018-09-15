import graphene
from lw2 import schema

class Query(schema.Query, graphene.ObjectType):
    pass

class Mutations(schema.Mutations, graphene.ObjectType):
    pass

schema = graphene.Schema(query=Query, mutation=Mutations)
