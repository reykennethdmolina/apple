#__author__ = 'reykennethmolina'
from django.db import models
from django.contrib.auth import User

class UserData(User):

    def __unicode__(self):
        return self.get_full_name()