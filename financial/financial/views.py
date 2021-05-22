#__author__ = 'reykennethmolina'

from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import auth
from django.http import HttpResponseRedirect, Http404
from module.models import Activitylogs

def logout(request):
    print ('log out')
    # Save Activity Logs
    Activitylogs.objects.create(
        user_id=request.user.id,
        username=request.user,
        remarks='Log-out'
    )
    auth.logout(request)

    return HttpResponseRedirect('/login')


@login_required
def index(request):
    context_dict = {}

    print ('log in')
    # Save Activity Logs
    Activitylogs.objects.create(
        user_id=request.user.id,
        username=request.user,
        remarks='Log-in'
    )

    return render(request, 'base-layout.html', context_dict)
    #return render(request, 'base-form.html', context_dict)
    #return HttpResponse("Welcome to Inquirer Enterprise Solutions - Financial System")

@login_required
def index2(request):
    context_dict = {}
    return render(request, 'base-form.html', context_dict)
