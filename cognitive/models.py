# coding=utf-8
from __future__ import unicode_literals

from django.db import models

# Create your models here.


class Person(models.Model):
    name = models.CharField(blank=True, null=True, max_length=64, unique=True)
    image = models.URLField(blank=True, null=True)
    face_id = models.CharField(max_length=255)

    class META:
        ordering = ['name']

    def __unicode__(self):
        return self.name


class UnknownPerson(models.Model):
    image = models.URLField(blank=True, null=True)
    face_id = models.CharField(max_length=255)
