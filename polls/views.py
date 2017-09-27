from django.shortcuts import render
from django.http import HttpResponse

def index(request):
    return HttpResponse("Hello world. Arjun Suresh here")
# Create your views here.
