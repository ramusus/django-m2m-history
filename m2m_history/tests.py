# -*- coding: utf-8 -*-
from django.test import TestCase
from django.db import models
from models import ManyToManyHistoryField
from datetime import datetime

'''
Example model from Django docs: https://docs.djangoproject.com/en/dev/topics/db/examples/many_to_many/
'''


class Publication(models.Model):
    title = models.CharField(max_length=30)

    def __str__(self):              # __unicode__ on Python 2
        return self.title

    class Meta:
        ordering = ('title',)


class Article(models.Model):
    headline = models.CharField(max_length=100)
    publications = ManyToManyHistoryField(Publication)

    def __str__(self):              # __unicode__ on Python 2
        return self.headline

    class Meta:
        ordering = ('headline',)


'''
Test class
'''


class ManyToManyHistoryTest(TestCase):

    def test_m2m_fields_and_methods(self):
        self.assertItemsEqual([field.name for field in Article._meta.get_field('publications').rel.through._meta.local_fields], [u'id', 'time_from', 'time_to', 'article', 'publication'])

    def test_m2m_field_history(self):

        p1 = Publication.objects.create(title='Pub1')
        p2 = Publication.objects.create(title='Pub2')
        p3 = Publication.objects.create(title='Pub3')

        article = Article.objects.create(headline='Article1')
        state_time1 = datetime.now()

        article.publications = [p1, p2]
        state_time2 = article.publications.last_update_time()
        self.assertItemsEqual(article.publications.all(), [p1, p2])
        self.assertEqual(article.publications.through.objects.count(), 2)

        article.publications = [p3]
        state_time3 = article.publications.last_update_time()
        self.assertItemsEqual(article.publications.all(), [p3])
        self.assertEqual(article.publications.through.objects.count(), 3)

        article.publications = [p2, p3]
        state_time4 = article.publications.last_update_time()
        self.assertItemsEqual(article.publications.all(), [p2, p3])
        self.assertEqual(article.publications.through.objects.count(), 4)

        article.publications = [p1, p2]
        state_time5 = article.publications.last_update_time()
        self.assertItemsEqual(article.publications.all(), [p1, p2])
        self.assertEqual(article.publications.through.objects.count(), 5)

        article.publications.clear()
        state_time6 = article.publications.last_update_time()
        self.assertItemsEqual(article.publications.all(), [])
        self.assertEqual(article.publications.through.objects.count(), 5)

        # test of history
        self.assertItemsEqual(article.publications.all(state_time1), [])
        self.assertItemsEqual(article.publications.all(state_time2), [p1, p2])
        self.assertItemsEqual(article.publications.all(state_time3), [p3])
        self.assertItemsEqual(article.publications.all(state_time4), [p2, p3])
        self.assertItemsEqual(article.publications.all(state_time5), [p1, p2])
        self.assertItemsEqual(article.publications.all(state_time6), [])

        # test of added and removed
        self.assertItemsEqual(article.publications.added(state_time2), [p1, p2])
        self.assertItemsEqual(article.publications.removed(state_time2), [])
        self.assertItemsEqual(article.publications.added(state_time3), [p3])
        self.assertItemsEqual(article.publications.removed(state_time3), [p1, p2])
        self.assertItemsEqual(article.publications.added(state_time4), [p2])
        self.assertItemsEqual(article.publications.removed(state_time4), [])
        self.assertItemsEqual(article.publications.added(state_time5), [p1])
        self.assertItemsEqual(article.publications.removed(state_time5), [p3])
        self.assertItemsEqual(article.publications.added(state_time6), [])
        self.assertItemsEqual(article.publications.removed(state_time6), [p1, p2])


    def test_m2m_field_build_in(self):
        '''
        Build-in test from https://docs.djangoproject.com/en/dev/topics/db/examples/many_to_many/
        '''
        p1 = Publication(title='The Python Journal')
        p1.save()
        p2 = Publication(title='Science News')
        p2.save()
        p3 = Publication(title='Science Weekly')
        p3.save()

        a1 = Article(headline='Django lets you build Web apps easily')
        a1.save()
        a1.publications.add(p1)

        a2 = Article(headline='NASA uses Python')
        a2.save()
        a2.publications.add(p1, p2)
        a2.publications.add(p3)
        a2.publications.add(p3)
        with self.assertRaises(TypeError):
            a2.publications.add(a1)

        p4 = a2.publications.create(title='Highlights for Children')

        self.assertItemsEqual(a1.publications.all(), [p1])
        self.assertItemsEqual(a2.publications.all(), [p4, p2, p3, p1])

        self.assertItemsEqual(p2.article_set.all(), [a2])
        self.assertItemsEqual(p1.article_set.all(), [a1, a2])
        self.assertItemsEqual(Publication.objects.get(id=4).article_set.all(), [a2])


#         >>> Article.objects.filter(publications__id=1)
#         [<Article: Django lets you build Web apps easily>, <Article: NASA uses Python>]
#         >>> Article.objects.filter(publications__pk=1)
#         [<Article: Django lets you build Web apps easily>, <Article: NASA uses Python>]
#         >>> Article.objects.filter(publications=1)
#         [<Article: Django lets you build Web apps easily>, <Article: NASA uses Python>]
#         >>> Article.objects.filter(publications=p1)
#         [<Article: Django lets you build Web apps easily>, <Article: NASA uses Python>]
#
#         >>> Article.objects.filter(publications__title__startswith="Science")
#         [<Article: NASA uses Python>, <Article: NASA uses Python>]
#
#         >>> Article.objects.filter(publications__title__startswith="Science").distinct()
#         [<Article: NASA uses Python>]
#         The count() function respects distinct() as well:
#
#         >>> Article.objects.filter(publications__title__startswith="Science").count()
#         2
#
#         >>> Article.objects.filter(publications__title__startswith="Science").distinct().count()
#         1
#
#         >>> Article.objects.filter(publications__in=[1,2]).distinct()
#         [<Article: Django lets you build Web apps easily>, <Article: NASA uses Python>]
#         >>> Article.objects.filter(publications__in=[p1,p2]).distinct()
#         [<Article: Django lets you build Web apps easily>, <Article: NASA uses Python>]
#         Reverse m2m queries are supported (i.e., starting at the table that doesn’t have a ManyToManyField):
#
#         >>> Publication.objects.filter(id=1)
#         [<Publication: The Python Journal>]
#         >>> Publication.objects.filter(pk=1)
#         [<Publication: The Python Journal>]
#
#         >>> Publication.objects.filter(article__headline__startswith="NASA")
#         [<Publication: Highlights for Children>, <Publication: Science News>, <Publication: Science Weekly>, <Publication: The Python Journal>]
#
#         >>> Publication.objects.filter(article__id=1)
#         [<Publication: The Python Journal>]
#         >>> Publication.objects.filter(article__pk=1)
#         [<Publication: The Python Journal>]
#         >>> Publication.objects.filter(article=1)
#         [<Publication: The Python Journal>]
#         >>> Publication.objects.filter(article=a1)
#         [<Publication: The Python Journal>]
#
#         >>> Publication.objects.filter(article__in=[1,2]).distinct()
#         [<Publication: Highlights for Children>, <Publication: Science News>, <Publication: Science Weekly>, <Publication: The Python Journal>]
#         >>> Publication.objects.filter(article__in=[a1,a2]).distinct()
#         [<Publication: Highlights for Children>, <Publication: Science News>, <Publication: Science Weekly>, <Publication: The Python Journal>]
#         Excluding a related item works as you would expect, too (although the SQL involved is a little complex):
#
#         >>> Article.objects.exclude(publications=p2)
#         [<Article: Django lets you build Web apps easily>]
#         If we delete a Publication, its Articles won’t be able to access it:
#
#         >>> p1.delete()
#         >>> Publication.objects.all()
#         [<Publication: Highlights for Children>, <Publication: Science News>, <Publication: Science Weekly>]
#         >>> a1 = Article.objects.get(pk=1)
#         >>> a1.publications.all()
#         []
#         If we delete an Article, its Publications won’t be able to access it:
#
#         >>> a2.delete()
#         >>> Article.objects.all()
#         [<Article: Django lets you build Web apps easily>]
#         >>> p2.article_set.all()
#         []
#         Adding via the ‘other’ end of an m2m:
#
#         >>> a4 = Article(headline='NASA finds intelligent life on Earth')
#         >>> a4.save()
#         >>> p2.article_set.add(a4)
#         >>> p2.article_set.all()
#         [<Article: NASA finds intelligent life on Earth>]
#         >>> a4.publications.all()
#         [<Publication: Science News>]
#         Adding via the other end using keywords:
#
#         >>> new_article = p2.article_set.create(headline='Oxygen-free diet works wonders')
#         >>> p2.article_set.all()
#         [<Article: NASA finds intelligent life on Earth>, <Article: Oxygen-free diet works wonders>]
#         >>> a5 = p2.article_set.all()[1]
#         >>> a5.publications.all()
#         [<Publication: Science News>]
#         Removing Publication from an Article:
#
#         >>> a4.publications.remove(p2)
#         >>> p2.article_set.all()
#         [<Article: Oxygen-free diet works wonders>]
#         >>> a4.publications.all()
#         []
#         And from the other end:
#
#         >>> p2.article_set.remove(a5)
#         >>> p2.article_set.all()
#         []
#         >>> a5.publications.all()
#         []
#         Relation sets can be assigned. Assignment clears any existing set members:
#
#         >>> a4.publications.all()
#         [<Publication: Science News>]
#         >>> a4.publications = [p3]
#         >>> a4.publications.all()
#         [<Publication: Science Weekly>]
#         Relation sets can be cleared:
#
#         >>> p2.article_set.clear()
#         >>> p2.article_set.all()
#         []
#         And you can clear from the other end:
#
#         >>> p2.article_set.add(a4, a5)
#         >>> p2.article_set.all()
#         [<Article: NASA finds intelligent life on Earth>, <Article: Oxygen-free diet works wonders>]
#         >>> a4.publications.all()
#         [<Publication: Science News>, <Publication: Science Weekly>]
#         >>> a4.publications.clear()
#         >>> a4.publications.all()
#         []
#         >>> p2.article_set.all()
#         [<Article: Oxygen-free diet works wonders>]
#         Recreate the Article and Publication we have deleted:
#
#         >>> p1 = Publication(title='The Python Journal')
#         >>> p1.save()
#         >>> a2 = Article(headline='NASA uses Python')
#         >>> a2.save()
#         >>> a2.publications.add(p1, p2, p3)
#         Bulk delete some Publications - references to deleted publications should go:
#
#         >>> Publication.objects.filter(title__startswith='Science').delete()
#         >>> Publication.objects.all()
#         [<Publication: Highlights for Children>, <Publication: The Python Journal>]
#         >>> Article.objects.all()
#         [<Article: Django lets you build Web apps easily>, <Article: NASA finds intelligent life on Earth>, <Article: NASA uses Python>, <Article: Oxygen-free diet works wonders>]
#         >>> a2.publications.all()
#         [<Publication: The Python Journal>]
#         Bulk delete some articles - references to deleted objects should go:
#
#         >>> q = Article.objects.filter(headline__startswith='Django')
#         >>> print(q)
#         [<Article: Django lets you build Web apps easily>]
#         >>> q.delete()
#         After the delete(), the QuerySet cache needs to be cleared, and the referenced objects should be gone:
#
#         >>> print(q)
#         []
#         >>> p1.article_set.all()
#         [<Article: NASA uses Python>]
#         An alternate to calling clear() is to assign the empty set:
#
#         >>> p1.article_set = []
#         >>> p1.article_set.all()
#         []
#
#         >>> a2.publications = [p1, new_publication]
#         >>> a2.publications.all()
#         [<Publication: Highlights for Children>, <Publication: The Python Journal>]
#         >>> a2.publications = []
#         >>> a2.publications.all()
#         []
