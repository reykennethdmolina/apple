#__author__ = 'reykennethmolina'

from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

@login_required
def index(request):
    context_dict = {}
    return render(request, 'base-layout.html', context_dict)
    #return render(request, 'base-form.html', context_dict)
    #return HttpResponse("Welcome to Inquirer Enterprise Solutions - Financial System")

@login_required
def index2(request):
    context_dict = {}
    return render(request, 'base-form.html', context_dict)
