from django.db import models

class UserGroup(models.Model):
    t1 = models.CharField(max_length=32)

class UserInfo(models.Model):
    username = models.CharField(max_length=32)
    pwd = models.CharField(max_length=32)
    fk = models.ForeignKey(UserGroup,null=True)

class Test(models.Model):
    ttt = models.CharField(max_length=32)
    kkk = models.ForeignKey(UserInfo,null=True)