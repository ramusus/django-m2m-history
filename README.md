Django ManyToMany History
========================

[![PyPI version](https://badge.fury.io/py/django-m2m-history.png)](http://badge.fury.io/py/django-m2m-history) [![Build Status](https://travis-ci.org/ramusus/django-m2m-history.png?branch=master)](https://travis-ci.org/ramusus/django-m2m-history) [![Coverage Status](https://coveralls.io/repos/ramusus/django-m2m-history/badge.png?branch=master)](https://coveralls.io/r/ramusus/django-m2m-history)

Django ManyToMany relation field with history of changes. Like usual Django's ManyToManyField, it's generate intermediary join table
to represent the many-to-many relationship, but with two additional columns: 'time_from' and 'time_to'. Using updated interface of field it's
possible to retreive history of all versions of this field's value.

Compatibility
-------------

  * python v2.7, v3.4
  * django >=1.5, <=1.8. **Does not compatible with Django 1.9**
  * postgres

Installation
------------

    pip install django-m2m-history

Add into `settings.py` lines:

    INSTALLED_APPS = (
        ...
        'm2m_history',
    )

Usage example
-------------

Make 2 models with many-to-many relationship:

    class Publication(models.Model):
        title = models.CharField(max_length=30)

        def __str__(self):
            return self.title

    class Article(models.Model):
        headline = models.CharField(max_length=100)
        publications = ManyToManyHistoryField(Publication)

        def __str__(self):
            return self.headline

Create objects and relations betweeen them:

    >>> p1 = Publication.objects.create(title='Pub1')
    >>> p2 = Publication.objects.create(title='Pub2')
    >>> p3 = Publication.objects.create(title='Pub3')

    >>> article = Article.objects.create(headline='Article1')
    >>> state_time1 = datetime.now()

    >>> article.publications = [p1, p2]
    >>> state_time2 = article.publications.last_update_time()
    >>> article.publications.all()
    [<Publication: Pub1>, <Publication: Pub2>]
    >>> article.publications.count()
    2
    >>> article.publications.through.objects.count()
    2

    >>> article.publications = [p3]
    >>> state_time3 = article.publications.last_update_time()
    >>> article.publications.all()
    [<Publication: Pub3>]
    >>> article.publications.count()
    1
    >>> article.publications.through.objects.count()
    3

    >>> article.publications.add(p2, p1)
    >>> state_time4 = article.publications.last_update_time()
    >>> article.publications.all()
    [<Publication: Pub1>, <Publication: Pub2>, <Publication: Pub3>]
    >>> article.publications.count()
    3
    >>> article.publications.through.objects.count()
    5

    >>> article.publications.remove(p2, p1)
    >>> state_time5 = article.publications.last_update_time()
    >>> article.publications.all()
    [<Publication: Pub3>]
    >>> article.publications.count()
    1
    >>> article.publications.through.objects.count()
    5

    >>> article.publications = [p1, p2]
    >>> state_time6 = article.publications.last_update_time()
    >>> article.publications.all()
    [<Publication: Pub1>, <Publication: Pub2>]
    >>> article.publications.count()
    2
    >>> article.publications.through.objects.count()
    7

    >>> article.publications.clear()
    >>> state_time7 = article.publications.last_update_time()
    >>> article.publications.all()
    []
     >>> article.publications.count()
    0
    >>> article.publications.through.objects.count()
    7

Get objects of history states by timestamps:

    >>> article.publications.were_at(state_time1)
    []

    >>> article.publications.were_at(state_time2)
    [<Publication: Pub1>, <Publication: Pub2>]

    >>> article.publications.were_at(state_time3)
    [<Publication: Pub3>]

    >>> article.publications.were_at(state_time4)
    [<Publication: Pub1>, <Publication: Pub2>, <Publication: Pub3>]

    >>> article.publications.were_at(state_time5)
    [<Publication: Pub3>]

    >>> article.publications.were_at(state_time6)
    [<Publication: Pub1>, <Publication: Pub2>]

    >>> article.publications.were_at(state_time7)
    []

Get added and removed objects of history states by timestamps:

    >>> article.publications.added_at(state_time3)
    [<Publication: Pub3>]

    >>> article.publications.removed_at(state_time3)
    [<Publication: Pub1>, <Publication: Pub2>]

    >>> article.publications.added_at(state_time4)
    [<Publication: Pub1>, <Publication: Pub2>]

    >>> article.publications.removed_at(state_time5)
    [<Publication: Pub1>, <Publication: Pub2>]

    >>> article.publications.added_at(state_time6)
    [<Publication: Pub1>, <Publication: Pub2>]

    >>> article.publications.removed_at(state_time6)
    [<Publication: Pub3>]
