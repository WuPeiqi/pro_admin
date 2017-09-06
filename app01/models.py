from django.db import models

class UserGroup(models.Model):
    t1 = models.CharField(max_length=32)

    def __str__(self):
        return self.t1

class Some(models.Model):
    name = models.CharField(max_length=32)


class UserInfo(models.Model):
    username = models.CharField(verbose_name='用户名',max_length=32)
    pwd = models.CharField(verbose_name='密码',max_length=32)
    fk = models.ForeignKey(verbose_name='用户组',to=UserGroup,null=True)

    mm = models.ManyToManyField(verbose_name='选多个',to=Some)

    def __str__(self):
        return self.username

class Test(models.Model):
    ttt = models.CharField(max_length=32)
    kkk = models.ForeignKey(UserInfo,null=True)