import pymysql
from django.http import HttpResponse
from django.template import loader
from django.shortcuts import render
from django.contrib import messages
from django.shortcuts import redirect
from django.http import Http404
from .models import Users
from django.conf import settings
from django.http import HttpResponseForbidden

connection = pymysql.connect(host=settings.DATABASES['default']['HOST'],
                             user=settings.DATABASES['default']['USER'],
                             password=settings.DATABASES['default']['PASSWORD'],
                             db=settings.DATABASES['default']['NAME'])




def redirectToPage(request,message,url):
    messages.add_message(request, messages.INFO, message)
    return redirect(url)

    
def index(request,arg='',context={}):
    request.session['userEmail']='#'
    request.session['Password']='#'
    request.session['userType']='#'
    return render(request, 'library/index.html', context)


def checksignup(request,arg=''):
    userEmail=request.POST.get("User_email")
    userName=request.POST.get("User_name")
    Password=request.POST.get("password")
    if userEmail == None or Password == None or userName == None:
        raise Http404
    sql="SELECT * from users where email='"+userEmail+"'"
    with connection.cursor() as cursor:
        cursor.execute(sql)
        returnedVal = cursor.fetchone()
    if returnedVal == None:
        sql="INSERT into users values('"+userEmail+"','"+userName+"','"+Password+"','normal')"
        with connection.cursor() as cursor:
            try:
                cursor.execute(sql)
            except:
                return redirectToUserLoginPage(request, "Please fill the details again", '/library/user/signup')
        connection.commit()
        request.session['userEmail']=userEmail
        request.session['Password']=Password
        request.session['userType']='normal'
        return redirect("/library/user/home")
    else:
        return redirectToPage(request, "Email already present. Try with a different one.", '/library/user/signup')

    
def userloginoption(request,arg='',context={}):
    return render(request, 'library/user/loginoption.html', context)


def userlogin(request,arg='',context={}):
    return render(request, 'library/user/login.html', context)

def signup(request,arg='',context={}):
    return render(request, 'library/user/signup.html', context)

def adminlogin(request,arg='',context={}):
    return render(request, 'library/admin/login.html', context)

def userhome(request,arg='', context={}):
    if 'userEmail' in request.session and 'Password' in request.session:
        if request.session['userEmail'] == '#' or request.session['Password'] == '#':
            return redirectToPage(request,"Please Login to proceed", '/library/user/loginoption')
        else:
            return render(request, 'library/user/home.html', context)
    else:
        return redirectToPage(request,"Please Login to proceed", '/library/user/loginoption')
    

def userauthenticate(request,arg=''):
    userEmail=request.POST.get("User_Email")
    Password=request.POST.get("User_Password")
    if userEmail == None or Password == None:
        raise Http404
    sql="SELECT userpassword from users where email='"+userEmail+"'"
    with connection.cursor() as cursor:
        cursor.execute(sql)
        returnedPassword = cursor.fetchone()
    if returnedPassword != None and returnedPassword[0] == Password:
        request.session['userEmail']=userEmail
        request.session['Password']=Password
        request.session['userType']='normal'
        return redirect("/library/user/home")
    else:
        return redirectToPage(request, "Login failure. Please try again", '/library/user/login')

def userbooksearch(request,arg='',context={}):
    if 'userEmail' in request.session and 'Password' in request.session:
        if request.session['userEmail'] == '#' or request.session['Password'] == '#':
            return redirectToPage(request,"Please Login to proceed", '/library/user/loginoption')
        else:
            request.session['visited']='true'
            return render(request, 'library/user/booksearch.html', context)
    else:
        return redirectToPage(request,"Please Login to proceed", '/library/user/loginoption')


def userbooksearchisbn(request,arg='',context={}):
    if 'userEmail' in request.session and 'Password' in request.session:
        if request.session['userEmail'] == '#' or request.session['Password'] == '#':
            return redirectToPage(request,"Please Login to proceed", '/library/user/loginoption')
        else:
            return render(request, 'library/user/booksearchbyisbn.html', context)
    else:
        return redirectToPage(request,"Please Login to proceed", '/library/user/loginoption')



def usercheckisbn(request,arg=''):
    isbn=request.POST.get("isbn")
    if 'userEmail' in request.session and 'Password' in request.session:
        if isbn == None or request.session['userEmail'] == '#' or request.session['Password'] == '#':
            raise Http404        
        else:
            sql="select a.authorname, b.title, b.link from author a,book b where id = (select authorid from haswritten where isbn='"+isbn+"') and b.isbn = '"+isbn+"'"
            with connection.cursor() as cursor:
                cursor.execute(sql)
                returnedVal = cursor.fetchone()
            if returnedVal == None:
                request.session['author']='#'
                request.session['title']='#'
                request.session['link']='#'
                return redirectToPage(request,"ISBN Not found.Please try again", '/library/user/booksearch/isbn/')
            else:
                request.session['author']=returnedVal[0]
                request.session['title']=returnedVal[1]
                request.session['link']=returnedVal[2]
                
                return render(request,"library/user/displaybooksisbn.html", {'book':returnedVal,'isbn':isbn})

    else:
        return redirectToPage(request,"Please Login to proceed", '/library/user/loginoption')



def userbooksearchtitle(request,arg='',context={}):
    if 'userEmail' in request.session and 'Password' in request.session:
        if request.session['userEmail'] == '#' or request.session['Password'] == '#':
            return redirectToPage(request,"Please Login to proceed", '/library/user/loginoption')
        else:
            return render(request, 'library/user/booksearchbytitle.html', context)
    else:
        return redirectToPage(request,"Please Login to proceed", '/library/user/loginoption')



def userchecktitle(request,arg=''):
    title=request.POST.get("title")
    if 'userEmail' in request.session and 'Password' in request.session:
        if title == None or request.session['userEmail'] == '#' or request.session['Password'] == '#':
            raise Http404        
        else:
            sql="select b.title, a.authorname, b.isbn, b.link from book b, author a, haswritten h where b.title='"+title+"' and b.isbn=h.isbn and h.authorid=a.id"
            with connection.cursor() as cursor:
                cursor.execute(sql)
                returnedVal = cursor.fetchall()
            if returnedVal == None or len(returnedVal) == 0:
                request.session['author']='#'
                request.session['title']='#'
                request.session['link']='#'
                return redirectToPage(request,"Title Not found.Please try again", '/library/user/booksearch/title/')
            else:
                request.session['author']='blah'
                request.session['title']='blah'
                request.session['link']='blah'
                return render(request,"library/user/displaybookstitle.html", {'book':returnedVal,'title':title})

    else:
        return redirectToPage(request,"Please Login to proceed", '/library/user/loginoption')

    

def booksearchproceed(request,arg=''):
    isbn=request.POST.get("isbn")
    if isbn == None:
        return redirect('/library/user/booksearch/isbn/checkisbn')
    if 'userEmail' in request.session and 'Password' in request.session:
        if isbn == None or request.session['userEmail'] == '#' or request.session['Password'] == '#':
            raise Http404        
        else:
            sql="select a.authorname, b.title, b.link from author a,book b where id = (select authorid from haswritten where isbn='"+isbn+"') and b.isbn = '"+isbn+"'"
            with connection.cursor() as cursor:
                cursor.execute(sql)
                returnedVal = cursor.fetchone()
            author=returnedVal[0]
            title=returnedVal[1]
            link=returnedVal[2]
            if request.session['visited']=='true':
                request.session['visited']='false'
                sql="insert into hasread values('"+request.session['userEmail']+"','"+isbn+"')"
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(sql)
                    connection.commit()
                except:
                    print(isbn+' already present\n')
                sql="select authorid from haswritten where isbn='"+isbn+"'"
                with connection.cursor() as cursor:
                    cursor.execute(sql)
                    returnedVal = cursor.fetchone()
                authorid=returnedVal[0]
                sql="select visits from likes where email='"+request.session['userEmail']+"' and authorid="+str(authorid)
                print(sql)
                with connection.cursor() as cursor:
                        cursor.execute(sql)
                        visits=cursor.fetchone()
                if visits == None or len(visits)==0:
                    sql="insert into likes values('"+request.session['userEmail']+"',"+str(authorid)+",1)"
                    try:
                        with connection.cursor() as cursor:
                            cursor.execute(sql)
                        connection.commit()
                    except:
                        print("Error inserting into likes table\n")
                else:
                    sql="update likes set visits='"+str(int(visits[0])+1)+"' where email='"+request.session['userEmail']+"' and authorid="+str(authorid)
                    with connection.cursor() as cursor:
                        cursor.execute(sql)
                    connection.commit()
            return render(request,"library/user/displaybookdetails.html", {'title':title,'author':author,'isbn':isbn,'link':link})

    else:
        return redirectToPage(request,"Please Login to proceed", '/library/user/loginoption')


def userauthorsearch(request,arg='',context={}):
    if 'userEmail' in request.session and 'Password' in request.session:
        if request.session['userEmail'] == '#' or request.session['Password'] == '#':
            return redirectToPage(request,"Please Login to proceed", '/library/user/loginoption')
        else:
            request.session['visited']='true'
            return render(request, 'library/user/authorsearch.html', context)
    else:
        return redirectToPage(request,"Please Login to proceed", '/library/user/loginoption')


def usercheckauthor(request,arg=''):
    author=request.POST.get("author")
    if 'userEmail' in request.session and 'Password' in request.session:
        if author == None or request.session['userEmail'] == '#' or request.session['Password'] == '#':
            raise Http404        
        else:
            sql="select b.title, a.authorname, b.isbn, b.link from book b, author a, haswritten h where b.isbn=h.isbn and h.authorid=a.id and a.authorname='"+author+"'"
            with connection.cursor() as cursor:
                cursor.execute(sql)
                returnedVal = cursor.fetchall()
            if returnedVal == None or len(returnedVal) == 0:
                request.session['author']='#'
                request.session['title']='#'
                request.session['link']='#'
                return redirectToPage(request,"Author not found.Please try again", '/library/user/authorsearch')
            else:
                request.session['author']='blah'
                request.session['title']='blah'
                request.session['link']='blah'
                return render(request,"library/user/displaybookstitle.html", {'book':returnedVal})

    else:
        return redirectToPage(request,"Please Login to proceed", '/library/user/loginoption')
    
    
def userauthenticate(request,arg=''):
    userEmail=request.POST.get("User_Email")
    Password=request.POST.get("User_Password")
    if userEmail == None or Password == None:
        raise Http404
    sql="SELECT userpassword from users where email='"+userEmail+"'"
    with connection.cursor() as cursor:
        cursor.execute(sql)
        returnedPassword = cursor.fetchone()
    if returnedPassword != None and returnedPassword[0] == Password:
        request.session['userEmail']=userEmail
        request.session['Password']=Password
        request.session['userType']='normal'
        return redirect("/library/user/home")
    else:
        return redirectToPage(request, "Login failure. Please try again", '/library/user/login')


        
def adminauthenticate(request,arg=''):
    userEmail=request.POST.get("User_Email")
    Password=request.POST.get("User_Password")
    if userEmail == None or Password == None:
        raise Http404
    sql="SELECT userpassword,usertype from users where email='"+userEmail+"'"
    with connection.cursor() as cursor:
        cursor.execute(sql)
        returnedList = cursor.fetchone()
    if returnedList != None and returnedList[0] == Password and returnedList[1]=='admin':
        request.session['userEmail']=userEmail
        request.session['Password']=Password
        request.session['userType']='admin'
        return redirect("/library/admin/home")
    else:
        return redirectToPage(request,"Login failure. Please try again", '/library/admin/login')


def adminhome(request,arg='', context={}):
    if 'userEmail' in request.session and 'Password' in request.session and 'userType' in request.session:
        if request.session['userEmail'] == '#' or request.session['Password'] == '#' or request.session['userType'] == '#':
            return redirectToAdminLoginpage(request,"Please Login to proceed")
        if request.session['userType'] != 'admin':
            return HttpResponseForbidden()
        else:
            return render(request, 'library/admin/home.html', context)
    else:
        return redirectToPage(request,"Please Login to proceed", '/library/admin/login')


def logout(request,arg='',context={}):
    return redirect('/library/')
    
