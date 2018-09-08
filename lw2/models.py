from django.db import models

# Create your models here.

class Test(models.Model):
    testfield = models.CharField(max_length=50)
