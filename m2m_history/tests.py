from django.test import TestCase
from django.db import models

'''
Example from Django docs: https://docs.djangoproject.com/en/dev/topics/db/examples/many_to_many/
'''

class Publication(models.Model):
    title = models.CharField(max_length=30)

    def __str__(self):              # __unicode__ on Python 2
        return self.title

    class Meta:
        ordering = ('title',)

class Article(models.Model):
    headline = models.CharField(max_length=100)
    publications = models.ManyToManyHistoryField(Publication)

    def __str__(self):              # __unicode__ on Python 2
        return self.headline

    class Meta:
        ordering = ('headline',)


'''
Test class
'''

class ManyToManyHistoryTest(TestCase):

    def test_m2m_field(self):
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
        #Adding a second time is OK:
        a2.publications.add(p3)
        #Adding an object of the wrong type raises TypeError:
#        a2.publications.add(a1)
#         Traceback (most recent call last):
#         ...
#         TypeError: 'Publication' instance expected
#         Create and add a Publication to an Article in one step using create():

        p4 = a2.publications.create(title='Highlights for Children')
        Article objects have access to their related Publication objects:

        self.assertItemsEqual(a1.publications.all(), [p1])
        self.assertItemsEqual(a2.publications.all(), [p1])
        self.assertItemsEqual(a1.publications.all(), [p4, p2, p3, p1])
        #Publication objects have access to their related Article objects:

        self.assertItemsEqual(p2.article_set.all(), [a1])
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
