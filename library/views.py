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
import requests
import re

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
    sql="SELECT * from users where email=%s"
    with connection.cursor() as cursor:
        cursor.execute(sql,(userEmail))
        returnedVal = cursor.fetchone()
    if returnedVal == None:
        sql="INSERT into users values(%s,%s,%s,'normal')"
        with connection.cursor() as cursor:
            try:
                cursor.execute(sql,(userEmail,userName,Password))
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


def userhistory(request,arg='', context={}):
    if 'userEmail' in request.session and 'Password' in request.session:
        if request.session['userEmail'] == '#' or request.session['Password'] == '#':
            return redirectToPage(request,"Please Login to proceed", '/library/user/loginoption')
        else:
            request.session['visited']='true'
            sql="select b.title, a.authorname, b.isbn, b.link from author a,book b where b.isbn in (select isbn from hasread where email = %s) and a.id = (select authorid from haswritten where isbn=b.isbn)"
            with connection.cursor() as cursor:
                cursor.execute(sql,(request.session['userEmail']))
                returnedVal=cursor.fetchall()
            return render(request,"library/user/displaybookstitle.html", {'book':returnedVal})
    else:
        return redirectToPage(request,"Please Login to proceed", '/library/user/loginoption')


def userrecommendation(request,arg='', context={}):
    if 'userEmail' in request.session and 'Password' in request.session:
        if request.session['userEmail'] == '#' or request.session['Password'] == '#':
            return redirectToPage(request,"Please Login to proceed", '/library/user/loginoption')
        else:
            request.session['visited']='true'
            bookList=['#']
            
            sql="select b.title, a.authorname, b.isbn, b.link,b.deleted from author a,book b where b.isbn not in (select isbn from hasread where email = %s) and a.id in (select authorid from likes where email = %s) and a.id = (select authorid from haswritten where isbn=b.isbn) and b.deleted='false' limit 4"
            with connection.cursor() as cursor:
                cursor.execute(sql,(request.session['userEmail'],request.session['userEmail']))
                returnedVal1=cursor.fetchall()
            for val in returnedVal1:
                bookList.append(val)
            valToShow = int((10-len(returnedVal1))/3+0.5)
            sql="select authorid from likes group by authorid order by sum(visits) desc limit 3"
            with connection.cursor() as cursor:
                cursor.execute(sql)
                popId=cursor.fetchall()

            for autId in popId:
                sql="select  b.title, a.authorname, b.isbn, b.link from author a,book b where b.isbn not in (select isbn from hasread where email = %s) and b.isbn in (select isbn from haswritten where id="+str(autId[0])+") and a.id=(select authorid from haswritten where isbn=b.isbn) and b.deleted='false' limit "+str(valToShow)
                with connection.cursor() as cursor:
                    cursor.execute(sql,(request.session['userEmail']))
                    returnedVal2=cursor.fetchall()
                for r in returnedVal2:
                    flag=0
                    for b in bookList:
                        if b is not '#':
                            if b[2] == r[2]:
                                flag=1

                    if flag is 0:        
                        bookList.append(r)
                    
            bookList.remove('#')
            return render(request,"library/user/displaybookstitle.html", {'book':bookList})
    else:
        return redirectToPage(request,"Please Login to proceed", '/library/user/loginoption')


def userauthenticate(request,arg=''):
    userEmail=request.POST.get("User_Email")
    Password=request.POST.get("User_Password")
    if userEmail == None or Password == None:
        raise Http404
    sql="SELECT userpassword,userType from users where email=%s"
    with connection.cursor() as cursor:
        cursor.execute(sql,(userEmail))
        returnParam = cursor.fetchone()
    if returnParam != None and returnParam[0] == Password:
        request.session['userEmail']=userEmail
        request.session['Password']=Password
        request.session['userType']=returnParam[1]
        
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
            sql="select b.title, a.authorname, b.link from author a,book b where id = (select authorid from haswritten where isbn='"+isbn+"') and b.isbn = '"+isbn+"' and b.deleted='false'"
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
            sql="select b.title, a.authorname, b.isbn, b.link from book b, author a, haswritten h where b.title= %s and b.isbn=h.isbn and h.authorid=a.id and b.deleted='false'"
            with connection.cursor() as cursor:
                cursor.execute(sql,(title))
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
            sql="select a.authorname, b.title, b.link, b.deleted from author a,book b where id = (select authorid from haswritten where isbn='"+isbn+"') and b.isbn = '"+isbn+"'"
            with connection.cursor() as cursor:
                cursor.execute(sql)
                returnedVal = cursor.fetchone()
            deleted=returnedVal[3]
            author=returnedVal[0]
            title=returnedVal[1]
            link=returnedVal[2]
            if request.session['visited']=='true':
                request.session['visited']='false'
                if deleted == 'true':
                    return render(request,"library/user/InvalidBook.html")
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
                sql="select visits from likes where email = %s and authorid="+str(authorid)
                with connection.cursor() as cursor:
                        cursor.execute(sql,(request.session['userEmail']))
                        visits=cursor.fetchone()
                if visits == None or len(visits)==0:
                    sql="insert into likes values(%s,"+str(authorid)+",1)"
                    try:
                        with connection.cursor() as cursor:
                            cursor.execute(sql,(request.session['userEmail']))
                        connection.commit()
                    except:
                        print("Error inserting into likes table\n")
                else:
                    sql="update likes set visits='"+str(int(visits[0])+1)+"' where email= %s and authorid="+str(authorid)
                    with connection.cursor() as cursor:
                        cursor.execute(sql,(request.session['userEmail']))
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
            sql="select b.title, a.authorname, b.isbn, b.link from book b, author a, haswritten h where b.isbn=h.isbn and h.authorid=a.id and a.authorname=%s and b.deleted ='false'"
            with connection.cursor() as cursor:
                cursor.execute(sql,(author))
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
    sql="SELECT userpassword,userType from users where email=%s"
    with connection.cursor() as cursor:
        cursor.execute(sql,(userEmail))
        returnedParam = cursor.fetchone()
    if returnedParam != None and returnedParam[0] == Password:
        request.session['userEmail']=userEmail
        request.session['Password']=Password
        request.session['userType']=returnedParam[1]
        return redirect("/library/user/home")
    else:
        return redirectToPage(request, "Login failure. Please try again", '/library/user/login')


        
def adminauthenticate(request,arg=''):
    userEmail=request.POST.get("User_Email")
    Password=request.POST.get("User_Password")
    if userEmail == None or Password == None:
        raise Http404
    sql="SELECT userpassword,usertype from users where email=%s"
    with connection.cursor() as cursor:
        cursor.execute(sql,(userEmail))
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


def userrecord(request,arg='', context={}):
    if 'userEmail' in request.session and 'Password' in request.session and 'userType' in request.session:
        if request.session['userEmail'] == '#' or request.session['Password'] == '#' or request.session['userType'] == '#':
            return redirectToAdminLoginpage(request,"Please Login to proceed")
        if request.session['userType'] != 'admin':
            return HttpResponseForbidden()
        else:
            return render(request, 'library/admin/UserRecordHome.html', context)
    else:
        return redirectToPage(request,"Please Login to proceed", '/library/admin/login')


def bookrecord(request,arg='', context={}):
    if 'userEmail' in request.session and 'Password' in request.session and 'userType' in request.session:
        if request.session['userEmail'] == '#' or request.session['Password'] == '#' or request.session['userType'] == '#':
            return redirectToAdminLoginpage(request,"Please Login to proceed")
        if request.session['userType'] != 'admin':
            return HttpResponseForbidden()
        else:
            return render(request, 'library/admin/BookRecordHome.html', context)
    else:
        return redirectToPage(request,"Please Login to proceed", '/library/admin/login')


def addbook(request,arg='', context={}):
    if 'userEmail' in request.session and 'Password' in request.session and 'userType' in request.session:
        if request.session['userEmail'] == '#' or request.session['Password'] == '#' or request.session['userType'] == '#':
            return redirectToAdminLoginpage(request,"Please Login to proceed")
        if request.session['userType'] != 'admin':
            return HttpResponseForbidden()
        else:
            return render(request, 'library/admin/InsertBook.html', context)
    else:
        return redirectToPage(request,"Please Login to proceed", '/library/admin/login')


def checknewbook(request,arg=''):
    isbn=request.POST.get("isbn")
    title=request.POST.get("title")
    author=request.POST.get("author")
    gutid=request.POST.get("gutid")
    link=request.POST.get("link")
    if isbn == None or title == None or author == None:
        return redirect('/library/admin/BookRecord/add/')
    sql="SELECT * from book where isbn='"+isbn+"'"
    with connection.cursor() as cursor:
        cursor.execute(sql)
        returnedVal = cursor.fetchone()
    if returnedVal == None or returnedVal[4] == "true":
        if returnedVal!= None and returnedVal[4] == "true":
            sql="delete from book where isbn='"+isbn+"'"
            with connection.cursor() as cursor:
                cursor.execute(sql)
            connection.commit()
        if link == None or link=="":
            base='http://aleph.gutenberg.org/'
            for i in range(len(gutid)-1):
                base=base+gutid[i]+'/'
            base=base+gutid
            r=requests.get(base)
            htmlText=r.text
            m=re.search('[0-9]-?[0-9]?-?[0-9]?-?[0-9]?-?[0-9]?-?[0-9]?-?[0-9]?-?[0-9]?-?[0-9]?-?[0-9]?-?[0-9]?-?.txt',htmlText)
            print(base)
            if m != None:
                link=base+'/'+m.group(0)
                sql="INSERT into book (isbn,title,gutid,link) values(%s,%s,%s,%s)"
                with connection.cursor() as cursor:
                    try:
                        cursor.execute(sql,(isbn,title,gutid,link))
                    except:
                        return redirectToPage(request, "Please fill the details again", '/library/admin/BookRecord/add')
                connection.commit()
        else:
            sql="INSERT into book (isbn,title,gutid,link) values(%s,%s,%s,%s)"
            with connection.cursor() as cursor:
                try:
                    cursor.execute(sql,(isbn,title,"#",link))
                except:
                    return redirectToPage(request, "Please fill the details again", '/library/admin/BookRecord/add')
            connection.commit()
        sql="select id from author where authorname=%s"
        with connection.cursor() as cursor:
            cursor.execute(sql,(author))
            authorList=cursor.fetchone()
        if authorList == None:
            sql="select id from author order by ID desc limit 1"
            with connection.cursor() as cursor:
                cursor.execute(sql)
                latestId=cursor.fetchone()
            curId=latestId[0]+1
            sql="INSERT into author values("+str(curId)+",%s)"
            with connection.cursor() as cursor:
                try:
                    cursor.execute(sql,(author))
                except:
                    return redirectToPage(request, "Author not inserted", "/library/admin/home")
        sql="select id from author where authorname=%s"
        with connection.cursor() as cursor:
            cursor.execute(sql,(author))
            authorList=cursor.fetchone()
        sql="INSERT into haswritten values('"+isbn+"',"+str(authorList[0])+")"
        with connection.cursor() as cursor:
            try:
                cursor.execute(sql)
            except:
                return redirectToPage(request, "Internal error", "/library/admin/home/")
        return redirectToPage(request, "Successful insertion", "/library/admin/home/")
    else:
        return redirectToPage(request, "ISBN already present", '/library/admin/BookRecord/add')



def updatebook(request,arg='', context={}):
    if 'userEmail' in request.session and 'Password' in request.session and 'userType' in request.session:
        if request.session['userEmail'] == '#' or request.session['Password'] == '#' or request.session['userType'] == '#':
            return redirectToAdminLoginpage(request,"Please Login to proceed")
        if request.session['userType'] != 'admin':
            return HttpResponseForbidden()
        else:
            sql="select b.title, a.authorname, b.isbn, b.link from author a,book b where a.id = (select authorid from haswritten where isbn=b.isbn) and b.deleted='false'"
            with connection.cursor() as cursor:
                cursor.execute(sql)
                returnedVal=cursor.fetchall()
            return render(request,"library/admin/UpdateBookList.html", {'book':returnedVal})
    else:
        return redirectToPage(request,"Please Login to proceed", '/library/admin/login')


def bookUpdateForm(request,arg=''):
    isbn=request.POST.get("isbn")
    if isbn == None:
        return redirect('/library/admin/BookRecord/update')
    if 'userEmail' in request.session and 'Password' in request.session and 'userType' in request.session:
        if request.session['userEmail'] == '#' or request.session['Password'] == '#' or request.session['userType'] == '#':
            return redirectToAdminLoginpage(request,"Please Login to proceed")
        if request.session['userType'] != 'admin':
            return HttpResponseForbidden()        
        else:
            sql="select a.authorname, b.title, b.gutid, b.link from author a,book b where id = (select authorid from haswritten where isbn='"+isbn+"') and b.isbn = '"+isbn+"'"
            with connection.cursor() as cursor:
                cursor.execute(sql)
                returnedVal = cursor.fetchone()
            author=returnedVal[0]
            title=returnedVal[1]
            gutid=returnedVal[2]
            link=returnedVal[3]
            return render(request,"library/admin/updateFormDisplay.html", {'title':title,'author':author,'isbn':isbn,'gutid':gutid,'link':link})

    else:
        return redirectToPage(request,"Please Login to proceed", '/library/admin/login')



def performBookUpdate(request,arg=''):
    isbn=request.POST.get("isbn")
    title=request.POST.get("title")
    author=request.POST.get("author")
    gutid=request.POST.get("gutid")
    link=request.POST.get("link")
    if isbn == None or title == None or author == None:
        return redirect('/library/admin/BookRecord/update/')
    sql="SELECT * from book where isbn='"+isbn+"'"
    with connection.cursor() as cursor:
        cursor.execute(sql)
        returnedVal = cursor.fetchone()
    existingGutId=returnedVal[2]
    existingLink=returnedVal[3]
    if existingGutId != gutid:
        base='http://aleph.gutenberg.org/'
        for i in range(len(gutid)-1):
            base=base+gutid[i]+'/'
        base=base+gutid
        r=requests.get(base)
        htmlText=r.text
        m=re.search('[0-9]-?[0-9]?-?[0-9]?-?[0-9]?-?[0-9]?-?[0-9]?-?[0-9]?-?[0-9]?-?[0-9]?-?[0-9]?-?[0-9]?-?.txt',htmlText)
        print(base)
        if m != None:
            link=base+'/'+m.group(0)
    elif link!=existingLink:
        gutid='#'
    sql="select authorname from author where id=(select authorid from haswritten where isbn='"+isbn+"')"
    with connection.cursor() as cursor:
        cursor.execute(sql)
        existingAuthorName = cursor.fetchone()[0]
    if existingAuthorName!=author :
        sql="select id from author order by ID desc limit 1"
        with connection.cursor() as cursor:
            cursor.execute(sql)
            latestId=cursor.fetchone()
        curId=latestId[0]+1
        sql="INSERT into author values("+str(curId)+",%s)"
        with connection.cursor() as cursor:
            try:
                cursor.execute(sql,(author))
            except:
                return redirectToPage(request, "Author not updated", "/library/admin/home")
        connection.commit()
        sql="select id from author where authorname=%s"
        with connection.cursor() as cursor:
            cursor.execute(sql,(existingAuthorName))
            authorList=cursor.fetchone()
        sql="INSERT into haswritten values('"+isbn+"',"+str(authorList[0])+")"
        with connection.cursor() as cursor:
            try:
                cursor.execute(sql)
            except:
                return redirectToPage(request, "Internal error", "/library/admin/home/")
        connection.commit()
    sql="update book set title=%s, gutid=%s, link=%s where isbn='"+isbn+"'"
    print(sql,(title,gutid,link))
    with connection.cursor() as cursor:
        try:
            cursor.execute(sql,(title,gutid,link))
        except:
            return redirectToPage(request, "Please fill the details again", '/library/admin/BookRecord/update/updateForm')
    connection.commit()
    return redirectToPage(request, "Successful updation", "/library/admin/home/")


def deletebook(request,arg='', context={}):
    if 'userEmail' in request.session and 'Password' in request.session and 'userType' in request.session:
        if request.session['userEmail'] == '#' or request.session['Password'] == '#' or request.session['userType'] == '#':
            return redirectToAdminLoginpage(request,"Please Login to proceed")
        if request.session['userType'] != 'admin':
            return HttpResponseForbidden()
        else:
            sql="select b.title, a.authorname, b.isbn, b.link from author a,book b where a.id = (select authorid from haswritten where isbn=b.isbn)and b.deleted='false'"
            with connection.cursor() as cursor:
                cursor.execute(sql)
                returnedVal=cursor.fetchall()
            return render(request,"library/admin/DeleteBookList.html", {'book':returnedVal})
    else:
        return redirectToPage(request,"Please Login to proceed", '/library/admin/login')


def performBookDelete(request,arg=''):
    isbn=request.POST.get("isbn")
    if isbn == None:
        return redirect('/library/admin/BookRecord/delete')
    sql="update book set deleted='true' where isbn='"+isbn+"'"
    with connection.cursor() as cursor:
        cursor.execute(sql)
    connection.commit()            
    return redirectToPage(request, "Successful deletion", "/library/admin/home/")




def userrecord(request,arg='', context={}):
    if 'userEmail' in request.session and 'Password' in request.session and 'userType' in request.session:
        if request.session['userEmail'] == '#' or request.session['Password'] == '#' or request.session['userType'] == '#':
            return redirectToAdminLoginpage(request,"Please Login to proceed")
        if request.session['userType'] != 'admin':
            return HttpResponseForbidden()
        else:
            return render(request, 'library/admin/UserRecordHome.html', context)
    else:
        return redirectToPage(request,"Please Login to proceed", '/library/admin/login')


def adduser(request,arg='', context={}):
    if 'userEmail' in request.session and 'Password' in request.session and 'userType' in request.session:
        if request.session['userEmail'] == '#' or request.session['Password'] == '#' or request.session['userType'] == '#':
            return redirectToAdminLoginpage(request,"Please Login to proceed")
        if request.session['userType'] != 'admin':
            return HttpResponseForbidden()
        else:
            return render(request, 'library/admin/InsertUser.html', context)
    else:
        return redirectToPage(request,"Please Login to proceed", '/library/admin/login')


def checknewuser(request,arg=''):
    email=request.POST.get("useremail")
    userName=request.POST.get("username")
    password=request.POST.get("password")
    if email == None or userName == None or password == None:
        return redirect('/library/admin/UserRecord/add/')
    sql="SELECT * from users where email='"+email+"'"
    with connection.cursor() as cursor:
        cursor.execute(sql)
        returnedVal = cursor.fetchone()
    if returnedVal == None:
        sql="INSERT into users (email,username, userpassword,userType) values(%s,%s,%s,'normal')"
        with connection.cursor() as cursor:
            try:
                cursor.execute(sql,(email,userName,password))
            except:
                return redirectToPage(request, "Please fill the details again", '/library/admin/UserRecord/add')
        connection.commit()
        return redirectToPage(request, "Successful insertion", "/library/admin/home/")
    else:
        return redirectToPage(request, "email already present", '/library/admin/BookRecord/add')



def updateuser(request,arg='', context={}):
    if 'userEmail' in request.session and 'Password' in request.session and 'userType' in request.session:
        if request.session['userEmail'] == '#' or request.session['Password'] == '#' or request.session['userType'] == '#':
            return redirectToAdminLoginpage(request,"Please Login to proceed")
        if request.session['userType'] != 'admin':
            return HttpResponseForbidden()
        else:
            sql="select username, email from users where userType='normal'"
            with connection.cursor() as cursor:
                cursor.execute(sql)
                returnedVal=cursor.fetchall()
            return render(request,"library/admin/UpdateUserList.html", {'users':returnedVal})
    else:
        return redirectToPage(request,"Please Login to proceed", '/library/admin/login')


def userUpdateForm(request,arg=''):
    email=request.POST.get("useremail")
    if email == None:
        return redirect('/library/admin/UserRecord/update')
    if 'userEmail' in request.session and 'Password' in request.session and 'userType' in request.session:
        if request.session['userEmail'] == '#' or request.session['Password'] == '#' or request.session['userType'] == '#':
            return redirectToAdminLoginpage(request,"Please Login to proceed")
        if request.session['userType'] != 'admin':
            return HttpResponseForbidden()        
        else:
            sql="select username, email, userpassword from users where email=%s"
            with connection.cursor() as cursor:
                cursor.execute(sql,(email))
                returnedVal = cursor.fetchone()
            username=returnedVal[0]
            password=returnedVal[2]
            request.session['emailEntry']=email
            return render(request,"library/admin/updateFormUserDisplay.html", {'email':email,'username':username,'password':password})

    else:
        return redirectToPage(request,"Please Login to proceed", '/library/admin/login')



def performUserUpdate(request,arg=''):
    email=request.POST.get("useremail")
    username=request.POST.get("username")
    password=request.POST.get("password")
    if email == None or username == None or password == None or request.session['emailEntry'] == '#':
        return redirect('/library/admin/UserRecord/update/')
    oldEmailId = request.session['emailEntry']
    request.session['emailEntry']='#'
    sql = "update users set email=%s,username=%s,userpassword=%s where email=%s"
    with connection.cursor() as cursor:
        cursor.execute(sql,(email,username,password,oldEmailId))
    connection.commit()
    return redirectToPage(request, "Successful updation", "/library/admin/home/")



def deleteuser(request,arg='', context={}):
    if 'userEmail' in request.session and 'Password' in request.session and 'userType' in request.session:
        if request.session['userEmail'] == '#' or request.session['Password'] == '#' or request.session['userType'] == '#':
            return redirectToAdminLoginpage(request,"Please Login to proceed")
        if request.session['userType'] != 'admin':
            return HttpResponseForbidden()
        else:
            sql="select username, email from users where userType='normal'"
            with connection.cursor() as cursor:
                cursor.execute(sql)
                returnedVal=cursor.fetchall()
            return render(request,"library/admin/DeleteUserList.html", {'users':returnedVal})
    else:
        return redirectToPage(request,"Please Login to proceed", '/library/admin/login')


def performUserDelete(request,arg=''):
    email=request.POST.get("useremail")
    if email == None:
        return redirect('/library/admin/Userecord/delete')
    sql="delete from users where email=%s"
    with connection.cursor() as cursor:
        cursor.execute(sql,(email))
    connection.commit()            
    return redirectToPage(request, "Successful deletion", "/library/admin/home/")



def updateauthor(request,arg='', context={}):
    if 'userEmail' in request.session and 'Password' in request.session and 'userType' in request.session:
        if request.session['userEmail'] == '#' or request.session['Password'] == '#' or request.session['userType'] == '#':
            return redirectToAdminLoginpage(request,"Please Login to proceed")
        if request.session['userType'] != 'admin':
            return HttpResponseForbidden()
        else:
            sql="select authorname,id from author"
            with connection.cursor() as cursor:
                cursor.execute(sql)
                returnedVal=cursor.fetchall()
            return render(request,"library/admin/UpdateAuthorList.html", {'authors':returnedVal})
    else:
        return redirectToPage(request,"Please Login to proceed", '/library/admin/login')



def authorUpdateForm(request,arg=''):
    authorid=request.POST.get("authorid")
    if authorid == None:
        return redirect('/library/admin/AuthorUpdate')
    if 'userEmail' in request.session and 'Password' in request.session and 'userType' in request.session:
        if request.session['userEmail'] == '#' or request.session['Password'] == '#' or request.session['userType'] == '#':
            return redirectToAdminLoginpage(request,"Please Login to proceed")
        if request.session['userType'] != 'admin':
            return HttpResponseForbidden()        
        else:
            sql="select authorname from author where id="+str(authorid)
            with connection.cursor() as cursor:
                cursor.execute(sql)
                returnedVal = cursor.fetchone()
            authorname=returnedVal[0]
            request.session['authorEntry']=authorid
            return render(request,"library/admin/updateFormAuthorDisplay.html", {'authorname':authorname})

    else:
        return redirectToPage(request,"Please Login to proceed", '/library/admin/login')



def performAuthorUpdate(request,arg=''):
    authorname=request.POST.get("authorname")
    if authorname == None or request.session['authorEntry'] == -1:
        return redirect('/library/admin/AuthorUpdate/')
    authorid=request.session['authorEntry']
    request.session['authorEntry']=-1
    sql = "update author set authorname=%s where id="+authorid
    with connection.cursor() as cursor:
        cursor.execute(sql,(authorname))
    connection.commit()
    return redirectToPage(request, "Successful updation", "/library/admin/home/")



def topReads(request,arg='', context={}):
    if 'userEmail' in request.session and 'Password' in request.session and 'userType' in request.session:
        if request.session['userEmail'] == '#' or request.session['Password'] == '#' or request.session['userType'] == '#':
            return redirectToAdminLoginpage(request,"Please Login to proceed")
        if request.session['userType'] != 'admin':
            return HttpResponseForbidden()
        else:
            bookList=['#']
            sql="select isbn from hasread group by isbn order by count(*) desc limit 8"
            with connection.cursor() as cursor:
                cursor.execute(sql)
                isbnList=cursor.fetchall()

            for isbn in isbnList:
                sql="select b.title, a.authorname, b.isbn, b.link from author a,book b where id = (select authorid from haswritten where isbn='"+isbn[0]+"') and b.isbn = '"+isbn[0]+"'"
                with connection.cursor() as cursor:
                    cursor.execute(sql)
                    returnedVal2=cursor.fetchall()
                for r in returnedVal2:
                    bookList.append(r)
                    
            bookList.remove('#')
            return render(request,"library/admin/TopReads.html", {'book':bookList})
    else:
        return redirectToPage(request,"Please Login to proceed", '/library/admin/login')


def viewdetails(request,arg=''):
    isbn=request.POST.get("isbn")
    if isbn == None:
        return redirect('/library/admin/topReads')
    if 'userEmail' in request.session and 'Password' in request.session and 'userType' in request.session:
        if request.session['userEmail'] == '#' or request.session['Password'] == '#' or request.session['userType'] == '#':
            return redirectToAdminLoginpage(request,"Please Login to proceed")
        if request.session['userType'] != 'admin':
            return HttpResponseForbidden()        
        else:
            sql="select a.authorname, b.title, b.link, b.deleted from author a,book b where id = (select authorid from haswritten where isbn='"+isbn+"') and b.isbn = '"+isbn+"'"
            with connection.cursor() as cursor:
                cursor.execute(sql)
                returnedVal = cursor.fetchone()
            author=returnedVal[0]
            title=returnedVal[1]
            link=returnedVal[2]
            deleted=returnedVal[3]
            if deleted == 'true':
                return render(request,"library/admin/InvalidBook.html")
            return render(request,"library/admin/displaybookdetails.html", {'title':title,'author':author,'isbn':isbn,'link':link})

    else:
        return redirectToPage(request,"Please Login to proceed", '/library/admin/login')



def logout(request,arg='',context={}):
    return redirect('/library/')
    
