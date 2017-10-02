from django.conf.urls import url

from . import views

urlpatterns = [
    # ex: /library/
    url(r'^$', views.index, name='index'),
    # ex: /library/user/login/
    url(r'^user/loginoption/$', views.userloginoption, name='userloginoption'),
    # ex: /library/user/signup/
    url(r'^user/signup/$', views.signup, name='signup'),
    # ex: /library/user/checksignup/
    url(r'^user/signup/checksignup/$', views.checksignup, name='checksignup'),    
    # ex: /library/user/login/
    url(r'^user/login/$', views.userlogin, name='userlogin'),
    # ex: /library/user/login/auth
    url(r'^user/login/auth$', views.userauthenticate, name='userauthenticate'),
    # ex: /library/user/home
    url(r'^user/home/$', views.userhome, name='userhome'),
    # ex: /library/user/home/history
    url(r'^user/home/history/$', views.userhistory, name='userhistory'),
    # ex: /library/user/home/recommendation
    url(r'^user/home/recommendation/$', views.userrecommendation, name='userrecommendation'),
    # ex: /library/user/booksearch
    url(r'^user/booksearch/$', views.userbooksearch, name='booksearch'),
    # ex: /library/user/booksearch/isbn
    url(r'^user/booksearch/isbn/$', views.userbooksearchisbn, name='booksearchisbn'),
    # ex: /library/user/booksearch/title
    url(r'^user/booksearch/title/$', views.userbooksearchtitle, name='booksearchtitle'),
    # ex: /library/user/booksearch/isbn/checkisbn
    url(r'^user/booksearch/isbn/checkisbn/$', views.usercheckisbn, name='checkisbn'),
    # ex: /library/user/booksearch/title/checktitle
    url(r'^user/booksearch/title/checktitle/$', views.userchecktitle, name='userchecktitle'),
    # ex: /library/user/booksearch/proceed
    url(r'^user/booksearch/proceed/$', views.booksearchproceed, name='booksearchproceed'),
    # ex: /library/user/authorsearch
    url(r'^user/authorsearch/$', views.userauthorsearch, name='userauthorsearch'),
    # ex: /library/user/booksearch/isbn/checkisbn
    url(r'^user/authorsearch/checkauthor/$', views.usercheckauthor, name='usercheckauthor'),
    # ex: /library/admin/login/
    url(r'^admin/login/$', views.adminlogin, name='adminlogin'),
    # ex: /library/admin/login/auth
    url(r'^admin/login/auth$', views.adminauthenticate, name='adminauthenticate'),
    # ex: /library/admin/home
    url(r'^admin/home/$', views.adminhome, name='adminhome'),
    # ex: /library/logout
    url(r'^logout/$', views.logout, name='logout'),
    # ex: /polls/5/results/
    #url(r'^(?P<question_id>[0-9]+)/results/$', views.results, name='results'),
    # ex: /polls/5/vote/
    #url(r'^(?P<question_id>[0-9]+)/vote/$', views.vote, name='vote'),
]
