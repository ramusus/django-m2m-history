from django.db import models

from ..fields import ManyToManyHistoryField


class Publication(models.Model):
    title = models.CharField(max_length=30)


class Article(models.Model):
    headline = models.CharField(max_length=100)
    publications = ManyToManyHistoryField(Publication, versions=True)
    publications_no_versions = ManyToManyHistoryField(Publication, related_name='articles_no_versions')
