from django.shortcuts import render
from django.forms import ModelForm
from django.forms import fields as ff
from app01 import models
class TestModelForm(ModelForm):

    class Meta:
        model = models.UserInfo
        fields = "__all__"
        labels={
            'username':'sdfsdfsd'
        }
        help_texts = {
            'username': 'hhhhh'
        }
        error_messages = {
            'username':{
                'required': '用户名不能为空'
            }
        }

        field_classes = {
            'username': ff.EmailField
        }

def test(request):
    if request.method == "GET":
        obj = TestModelForm()
    else:
        obj = TestModelForm(data=request.POST,files=request.FILES)
        obj.save()
    return render(request,'test.html',{'obj':obj})