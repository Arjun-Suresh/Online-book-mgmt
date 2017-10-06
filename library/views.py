import pymysql
from django.http import HttpResponse
from django.template import loader
from django.shortcuts import render
from django.contrib import messages
from django.shortcuts import redirect
from django.http import Http404
from django.conf import settings
from django.http import HttpResponseForbidden
import requests
import re


#Connect to the database settings provided in settings.py file
connection = pymysql.connect(host=settings.DATABASES['default']['HOST'],
                             user=settings.DATABASES['default']['USER'],
                             password=settings.DATABASES['default']['PASSWORD'],
                             db=settings.DATABASES['default']['NAME'])
connection.ping(True)

def executeQuery(sql,connection, *arg):    
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql,arg)
        except pymysql.err.OperationalError:
            connection = pymysql.connect(host=settings.DATABASES['default']['HOST'],
                                 user=settings.DATABASES['default']['USER'],
                                 password=settings.DATABASES['default']['PASSWORD'],
                                 db=settings.DATABASES['default']['NAME'])
            with connection.cursor() as cursor:
                cursor.execute(sql,arg)
        return cursor


#Generic function to redirect to any view wiith a message to be displayed on the html element
def redirectToPage(request,message,url):
    messages.add_message(request, messages.INFO, message)
    return redirect(url)


#index page of the application
def index(request,arg='',context={}):
    request.session['userEmail']='#'
    request.session['Password']='#'
    request.session['userType']='#'
    return render(request, 'library/index.html', context)


#Template which asks the user to login or signup  
def userloginoption(request,arg='',context={}):
    return render(request, 'library/user/loginoption.html', context)


#render user login page. Missing the feature 'forgot password'
def userlogin(request,arg='',context={}):
    return render(request, 'library/user/login.html', context)


#Authenticate the user login
def userauthenticate(request,arg=''):
    userEmail=request.POST.get("User_Email")
    Password=request.POST.get("User_Password")
    if userEmail == None or Password == None:
        raise Http404
    sql="SELECT userpassword,userType from users where email=%s"
    cursor= executeQuery(sql,connection,userEmail)
    returnParam = cursor.fetchone()
    cursor.close()
    if returnParam != None and returnParam[0] == Password:
        request.session['userEmail']=userEmail
        request.session['Password']=Password
        request.session['userType']=returnParam[1]
        
        return redirect("/library/user/home")
    else:
        return redirectToPage(request, "Login failure. Please try again", '/library/user/login')

    
#render the user signup form
def signup(request,arg='',context={}):
    return render(request, 'library/user/signup.html', context)


#validate form parameters provided by user while signing up and insert it into the database
def checksignup(request,arg=''):
    userEmail=request.POST.get("email")
    userName=request.POST.get("username")
    Password=request.POST.get("password")
    if userEmail == None or Password == None or userName == None:
        raise Http404
    sql="SELECT * from users where email=%s"
    cursor=executeQuery(sql,connection,userEmail)
    returnedVal = cursor.fetchone()
    cursor.close()
    if returnedVal == None:
        sql="INSERT into users values(%s,%s,%s,'normal')"
        try:
            cursor=executeQuery(sql,connection,userEmail,userName,Password)
        except:
            return redirectToUserLoginPage(request, "Please fill the details again", '/library/user/signup')
        cursor.close()
        connection.commit()
        request.session['userEmail']=userEmail
        request.session['Password']=Password
        request.session['userType']='normal'
        return redirect("/library/user/home")
    else:
        return redirectToPage(request, "Email already present. Try with a different one.", '/library/user/signup')



#User home with options to search book, author, view history and recommendations
def userhome(request,arg='', context={}):
    if 'userEmail' in request.session and 'Password' in request.session:
        if request.session['userEmail'] == '#' or request.session['Password'] == '#':
            return redirectToPage(request,"Please Login to proceed", '/library/user/loginoption')
        else:
            return render(request, 'library/user/home.html', context)
    else:
        return redirectToPage(request,"Please Login to proceed", '/library/user/loginoption')


#Display user book visit history
def userhistory(request,arg='', context={}):
    if 'userEmail' in request.session and 'Password' in request.session:
        if request.session['userEmail'] == '#' or request.session['Password'] == '#':
            return redirectToPage(request,"Please Login to proceed", '/library/user/loginoption')
        else:
            request.session['visited']='true'
            sql="select b.title, a.authorname, b.isbn, b.link from author a,book b where b.isbn in (select isbn from hasread where email = %s) and a.id = (select authorid from haswritten where isbn=b.isbn)"
            cursor=executeQuery(sql,connection,request.session['userEmail'])
            returnedVal=cursor.fetchall()
            cursor.close()
            return render(request,"library/user/displaybookstitle.html", {'book':returnedVal})
    else:
        return redirectToPage(request,"Please Login to proceed", '/library/user/loginoption')



#Display recommended books. This view gets data of books written by authors whose other book has been read by the user,
#and other top reads from the bunch of users (Upto 4 of the first kind and remaining of the second kind). Special care to avoid displaying books which the user has already read previously
def userrecommendation(request,arg='', context={}):
    if 'userEmail' in request.session and 'Password' in request.session:
        if request.session['userEmail'] == '#' or request.session['Password'] == '#':
            return redirectToPage(request,"Please Login to proceed", '/library/user/loginoption')
        else:
            request.session['visited']='true'
            bookList=['#'] #booklist.append doesn't allow appending to empty list. Appending a dummy variable. Need to change this.
            
            sql="select b.title, a.authorname, b.isbn, b.link,b.deleted from author a,book b where b.isbn not in (select isbn from hasread where email = %s) and a.id in (select authorid from likes where email = %s) and a.id = (select authorid from haswritten where isbn=b.isbn) and b.deleted='false' limit 4"
            cursor=executeQuery(sql,connection, request.session['userEmail'],request.session['userEmail'])
            returnedVal1=cursor.fetchall()
            cursor.close()
            for val in returnedVal1:
                bookList.append(val)
            valToShow = int((10-len(returnedVal1))/3+0.5)
            sql="select authorid from likes group by authorid order by sum(visits) desc limit 3"
            cursor=executeQuery(sql,connection)
            popId=cursor.fetchall()
            cursor.close()
            for autId in popId:
                sql="select  b.title, a.authorname, b.isbn, b.link from author a,book b where b.isbn not in (select isbn from hasread where email = %s) and b.isbn in (select isbn from haswritten where id="+str(autId[0])+") and a.id=(select authorid from haswritten where isbn=b.isbn) and b.deleted='false' limit "+str(valToShow)
            
                cursor=executeQuery(sql,connection,request.session['userEmail'])
                returnedVal2=cursor.fetchall()
                cursor.close()
                for r in returnedVal2:
                    flag=0
                    for b in bookList:
                        if b is not '#':
                            if b[2] == r[2]:
                                flag=1

                    if flag is 0:        
                        bookList.append(r)
                    
            bookList.remove('#') #Removing the dummy variable.You don't want to display this.
            return render(request,"library/user/displaybookstitle.html", {'book':bookList})
    else:
        return redirectToPage(request,"Please Login to proceed", '/library/user/loginoption')


#render the book search options template - By ISBN or by Title
def userbooksearch(request,arg='',context={}):
    if 'userEmail' in request.session and 'Password' in request.session:
        if request.session['userEmail'] == '#' or request.session['Password'] == '#':
            return redirectToPage(request,"Please Login to proceed", '/library/user/loginoption')
        else:
            request.session['visited']='true'
            return render(request, 'library/user/booksearch.html', context)
    else:
        return redirectToPage(request,"Please Login to proceed", '/library/user/loginoption')


#render the search by isbn page which has a search bar to get the ISBN
def userbooksearchisbn(request,arg='',context={}):
    if 'userEmail' in request.session and 'Password' in request.session:
        if request.session['userEmail'] == '#' or request.session['Password'] == '#':
            return redirectToPage(request,"Please Login to proceed", '/library/user/loginoption')
        else:
            return render(request, 'library/user/booksearchbyisbn.html', context)
    else:
        return redirectToPage(request,"Please Login to proceed", '/library/user/loginoption')


#Check isbn and search the isbn in books table and get back the book details to the results page. Meanwhile, store these details in the session,
#so that the display book details view can use these details to render them onto the display page 
def usercheckisbn(request,arg=''):
    isbn=request.POST.get("isbn")
    if 'userEmail' in request.session and 'Password' in request.session:
        if isbn == None or request.session['userEmail'] == '#' or request.session['Password'] == '#':
            raise Http404        
        else:
            sql="select b.title, a.authorname, b.link from author a,book b where id = (select authorid from haswritten where isbn='"+isbn+"') and b.isbn = '"+isbn+"' and b.deleted='false'"

            cursor=executeQuery(sql,connection)
            returnedVal = cursor.fetchone()
            cursor.close()
            if returnedVal == None:
                return redirectToPage(request,"ISBN Not found.Please try again", '/library/user/booksearch/isbn/')
            else:                
                return render(request,"library/user/displaybooksisbn.html", {'book':returnedVal,'isbn':isbn})

    else:
        return redirectToPage(request,"Please Login to proceed", '/library/user/loginoption')



#Render page which displays a title search bar
def userbooksearchtitle(request,arg='',context={}):
    if 'userEmail' in request.session and 'Password' in request.session:
        if request.session['userEmail'] == '#' or request.session['Password'] == '#':
            return redirectToPage(request,"Please Login to proceed", '/library/user/loginoption')
        else:
            return render(request, 'library/user/booksearchbytitle.html', context)
    else:
        return redirectToPage(request,"Please Login to proceed", '/library/user/loginoption')



#Check isbn and search the title in books table and get back the book details to the results page. Meanwhile, store these details in the session,
#so that the display book details view can use these details to render them onto the display page
def userchecktitle(request,arg=''):
    title=request.POST.get("title")
    if 'userEmail' in request.session and 'Password' in request.session:
        if title == None or request.session['userEmail'] == '#' or request.session['Password'] == '#':
            raise Http404        
        else:
            sql="select b.title, a.authorname, b.isbn, b.link from book b, author a, haswritten h where b.title= %s and b.isbn=h.isbn and h.authorid=a.id and b.deleted='false'"
    
            cursor=executeQuery(sql,connection,title)
            returnedVal = cursor.fetchall()
            cursor.close()
            if returnedVal == None or len(returnedVal) == 0:
                return redirectToPage(request,"Title Not found.Please try again", '/library/user/booksearch/title/')
            else:
                return render(request,"library/user/displaybookstitle.html", {'book':returnedVal})

    else:
        return redirectToPage(request,"Please Login to proceed", '/library/user/loginoption')

    

#Common function used to render the book details of a particular book like isbn, author, title and link.
#Also, updates the hasread and the likes table(to increase number of visits)
def booksearchproceed(request,arg=''):
    isbn=request.POST.get("isbn")
    if isbn == None:
        return redirect('/library/user/booksearch/isbn/checkisbn')
    if 'userEmail' in request.session and 'Password' in request.session:
        if isbn == None or request.session['userEmail'] == '#' or request.session['Password'] == '#':
            raise Http404        
        else:
            sql="select a.authorname, b.title, b.link, b.deleted from author a,book b where id = (select authorid from haswritten where isbn='"+isbn+"') and b.isbn = '"+isbn+"'"
    
            cursor=executeQuery(sql,connection)
            returnedVal = cursor.fetchone()
            cursor.close()
            deleted=returnedVal[3]
            author=returnedVal[0]
            title=returnedVal[1]
            link=returnedVal[2]
            if request.session['visited']=='true':
                request.session['visited']='false'
                if deleted == 'true':
                    return render(request,"library/user/InvalidBook.html")
                sql="insert into hasread values(%s,'"+isbn+"')"
                try:

                    cursor=executeQuery(sql,connection,request.session['userEmail'])
                    cursor.close()
                    connection.commit()
                except:
                    print(isbn+' already present\n')
                sql="select authorid from haswritten where isbn='"+isbn+"'"
            
                cursor=executeQuery(sql,connection)
                returnedVal = cursor.fetchone()
                cursor.close()
                authorid=returnedVal[0]
                sql="select visits from likes where email = %s and authorid="+str(authorid)
            
                cursor=executeQuery(sql,connection,request.session['userEmail'])
                visits=cursor.fetchone()
                cursor.close()
                if visits == None or len(visits)==0:
                    sql="insert into likes values(%s,"+str(authorid)+",1)"
                    try:

                        cursor=executeQuery(sql,connection,request.session['userEmail'])
                        cursor.close()
                        connection.commit()
                    except:
                        print("Error inserting into likes table\n")   #Internal error. Shouldn't be displayed to user
                else:
                    sql="update likes set visits='"+str(int(visits[0])+1)+"' where email= %s and authorid="+str(authorid)

                    cursor=executeQuery(sql,connection,request.session['userEmail'] )
                    cursor.close()
                    connection.commit()
            return render(request,"library/user/displaybookdetails.html", {'title':title,'author':author,'isbn':isbn,'link':link})

    else:
        return redirectToPage(request,"Please Login to proceed", '/library/user/loginoption')


#Render page which has an author search bar
def userauthorsearch(request,arg='',context={}):
    if 'userEmail' in request.session and 'Password' in request.session:
        if request.session['userEmail'] == '#' or request.session['Password'] == '#':
            return redirectToPage(request,"Please Login to proceed", '/library/user/loginoption')
        else:
            request.session['visited']='true'
            return render(request, 'library/user/authorsearch.html', context)
    else:
        return redirectToPage(request,"Please Login to proceed", '/library/user/loginoption')


#Searches for the author on the author list and returns all the books written by the same
def usercheckauthor(request,arg=''):
    author=request.POST.get("author")
    if 'userEmail' in request.session and 'Password' in request.session:
        if author == None or request.session['userEmail'] == '#' or request.session['Password'] == '#':
            raise Http404        
        else:
            sql="select b.title, a.authorname, b.isbn, b.link from book b, author a, haswritten h where b.isbn=h.isbn and h.authorid=a.id and a.authorname=%s and b.deleted ='false'"

            cursor=executeQuery(sql,connection,author)
            returnedVal = cursor.fetchall()
            cursor.close()
            if returnedVal == None or len(returnedVal) == 0:
                return redirectToPage(request,"Author not found.Please try again", '/library/user/authorsearch')
            else:
                return render(request,"library/user/displaybookstitle.html", {'book':returnedVal})

    else:
        return redirectToPage(request,"Please Login to proceed", '/library/user/loginoption')
 


#render the admin login page
def adminlogin(request,arg='',context={}):
    return render(request, 'library/admin/login.html', context)


#Validates the admin login details 
def adminauthenticate(request,arg=''):
    userEmail=request.POST.get("User_Email")
    Password=request.POST.get("User_Password")
    if userEmail == None or Password == None:
        raise Http404
    sql="SELECT userpassword,usertype from users where email=%s"

    cursor=executeQuery(sql,connection,userEmail)
    returnedList = cursor.fetchone()
    cursor.close()
    if returnedList != None and returnedList[0] == Password and returnedList[1]=='admin':
        request.session['userEmail']=userEmail
        request.session['Password']=Password
        request.session['userType']='admin'
        return redirect("/library/admin/home")
    else:
        return redirectToPage(request,"Login failure. Please try again", '/library/admin/login')


#Admin home page contains book record, user record, author update and top reads
def adminhome(request,arg='', context={}):
    if 'userEmail' in request.session and 'Password' in request.session and 'userType' in request.session:
        if request.session['userEmail'] == '#' or request.session['Password'] == '#' or request.session['userType'] == '#':
            return redirectToPage(request,"Please Login to proceed", '/library/admin/login')
        if request.session['userType'] != 'admin':
            return HttpResponseForbidden()
        else:
            return render(request, 'library/admin/home.html', context)
    else:
        return redirectToPage(request,"Please Login to proceed", '/library/admin/login')



#Book record page has add, delete and update book options
def bookrecord(request,arg='', context={}):
    if 'userEmail' in request.session and 'Password' in request.session and 'userType' in request.session:
        if request.session['userEmail'] == '#' or request.session['Password'] == '#' or request.session['userType'] == '#':
            return redirectToPage(request,"Please Login to proceed", '/library/admin/login')
        if request.session['userType'] != 'admin':
            return HttpResponseForbidden()
        else:
            return render(request, 'library/admin/BookRecordHome.html', context)
    else:
        return redirectToPage(request,"Please Login to proceed", '/library/admin/login')


#Renders a form which takes isbn, title, author and gutenberg ID or link to the e-book
def addbook(request,arg='', context={}):
    if 'userEmail' in request.session and 'Password' in request.session and 'userType' in request.session:
        if request.session['userEmail'] == '#' or request.session['Password'] == '#' or request.session['userType'] == '#':
            return redirectToPage(request,"Please Login to proceed", '/library/admin/login')
        if request.session['userType'] != 'admin':
            return HttpResponseForbidden()
        else:
            return render(request, 'library/admin/InsertBook.html', context)
    else:
        return redirectToPage(request,"Please Login to proceed", '/library/admin/login')


#Takes the data from the new book form. If gutenberg id is provided, compute the link, else link is present and initialize gutenberg id to '#'
#Insert these 4 values to books table. Check if the author is present on the author table and if not add it there
#Insert author id and isbn to haswritten table
def checknewbook(request,arg=''):
    isbn=request.POST.get("isbn")
    title=request.POST.get("title")
    author=request.POST.get("author")
    gutid=request.POST.get("gutid")
    link=request.POST.get("link")
    if isbn == None or title == None or author == None:
        return redirect('/library/admin/BookRecord/add/')
    sql="SELECT * from book where isbn='"+isbn+"'"

    cursor=executeQuery(sql,connection)
    returnedVal = cursor.fetchone()
    cursor.close()
    if returnedVal == None or returnedVal[4] == "true":
        if returnedVal!= None and returnedVal[4] == "true":
            sql="delete from book where isbn='"+isbn+"'"
        
            cursor=executeQuery(sql,connection)
            cursor.close()
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
            
                try:
                    cursor=executeQuery(sql,connection,isbn,title,gutid,link)
                except:
                    return redirectToPage(request, "Please fill the details again", '/library/admin/BookRecord/add')
                    cursor.close()
                connection.commit()
        else:
            sql="INSERT into book (isbn,title,gutid,link) values(%s,%s,%s,%s)"
            
            try:
                cursor=executeQuery(sql,connection,isbn,title,"#",link)
            except:
                return redirectToPage(request, "Please fill the details again", '/library/admin/BookRecord/add')
                cursor.close()
            connection.commit()
        sql="select id from author where authorname=%s"
    
        cursor=executeQuery(sql,connection,author)
        authorList=cursor.fetchone()
        cursor.close()
        if authorList == None:
            sql="select id from author order by ID desc limit 1"
        
            cursor=executeQuery(sql,connection)
            latestId=cursor.fetchone()
            cursor.close()
            curId=latestId[0]+1
            sql="INSERT into author values("+str(curId)+",%s)"
            
            try:
                cursor=executeQuery(sql,connection,author)
            except:
                return redirectToPage(request, "Author not inserted", "/library/admin/home")
                cursor.close()
        sql="select id from author where authorname=%s"
    
        cursor=executeQuery(sql,connection,author)
        authorList=cursor.fetchone()
        cursor.close()
        sql="INSERT into haswritten values('"+isbn+"',"+str(authorList[0])+")"
        
        try:
            cursor=executeQuery(sql,connection)
        except:
            return redirectToPage(request, "Internal error", "/library/admin/home/")
            cursor.close()
        return redirectToPage(request, "Successful insertion", "/library/admin/home/")
    else:
        return redirectToPage(request, "ISBN already present", '/library/admin/BookRecord/add')



#Renders the update book page which shows all the books available with a select option
def updatebook(request,arg='', context={}):
    if 'userEmail' in request.session and 'Password' in request.session and 'userType' in request.session:
        if request.session['userEmail'] == '#' or request.session['Password'] == '#' or request.session['userType'] == '#':
            return redirectToPage(request,"Please Login to proceed", '/library/admin/login')
        if request.session['userType'] != 'admin':
            return HttpResponseForbidden()
        else:
            sql="select b.title, a.authorname, b.isbn, b.link from author a,book b where a.id = (select authorid from haswritten where isbn=b.isbn) and b.deleted='false'"
        
            cursor=executeQuery(sql,connection)
            returnedVal=cursor.fetchall()
            cursor.close()
            return render(request,"library/admin/UpdateBookList.html", {'book':returnedVal})
    else:
        return redirectToPage(request,"Please Login to proceed", '/library/admin/login')


#Renders a prepopulated book update form based on the book selected
def bookUpdateForm(request,arg=''):
    isbn=request.POST.get("isbn")
    if isbn == None:
        return redirect('/library/admin/BookRecord/update')
    if 'userEmail' in request.session and 'Password' in request.session and 'userType' in request.session:
        if request.session['userEmail'] == '#' or request.session['Password'] == '#' or request.session['userType'] == '#':
            return redirectToPage(request,"Please Login to proceed", '/library/admin/login')
        if request.session['userType'] != 'admin':
            return HttpResponseForbidden()        
        else:
            sql="select a.authorname, b.title, b.gutid, b.link from author a,book b where id = (select authorid from haswritten where isbn='"+isbn+"') and b.isbn = '"+isbn+"'"
            
            cursor=executeQuery(sql,connection)
            returnedVal = cursor.fetchone()
            cursor.close()
            author=returnedVal[0]
            title=returnedVal[1]
            gutid=returnedVal[2]
            link=returnedVal[3]
            return render(request,"library/admin/updateFormDisplay.html", {'title':title,'author':author,'isbn':isbn,'gutid':gutid,'link':link})

    else:
        return redirectToPage(request,"Please Login to proceed", '/library/admin/login')


#Get the details from the form and update the book. If the author is changed, create a new entry in the author table and update haswritten
def performBookUpdate(request,arg=''):
    isbn=request.POST.get("isbn")
    title=request.POST.get("title")
    author=request.POST.get("author")
    gutid=request.POST.get("gutid")
    link=request.POST.get("link")
    if isbn == None or title == None or author == None:
        return redirect('/library/admin/BookRecord/update/')
    sql="SELECT * from book where isbn='"+isbn+"'"

    cursor=executeQuery(sql,connection)
    returnedVal = cursor.fetchone()
    cursor.close()
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

    cursor=executeQuery(sql,connection)
    existingAuthorName = cursor.fetchone()[0]
    cursor.close()
    if existingAuthorName!=author :
        sql="select id from author order by ID desc limit 1"
    
        cursor=executeQuery(sql,connection)
        latestId=cursor.fetchone()
        cursor.close()
        curId=latestId[0]+1
        sql="INSERT into author values("+str(curId)+",%s)"
    
        try:
            cursor=executeQuery(sql,connection,author)
        except:
            return redirectToPage(request, "Author not updated", "/library/admin/home")
        cursor.close()
        connection.commit()
        sql="select id from author where authorname=%s"
    
        cursor=executeQuery(sql,connection,existingAuthorName)
        authorList=cursor.fetchone()
        cursor.close()
        sql="INSERT into haswritten values('"+isbn+"',"+str(authorList[0])+")"
    
        try:
            cursor=executeQuery(sql,connection)
        except:
            return redirectToPage(request, "Internal error", "/library/admin/home/")
        cursor.close()
        connection.commit()
    sql="update book set title=%s, gutid=%s, link=%s where isbn='"+isbn+"'"
    print(sql,(title,gutid,link))

    try:
        cursor=executeQuery(sql,connection,title,gutid,link)
    except:
        return redirectToPage(request, "Please fill the details again", '/library/admin/BookRecord/update/updateForm')
    cursor.close()
    connection.commit()
    return redirectToPage(request, "Successful updation", "/library/admin/home/")


#Renders the delete book page which displays all the books available, with a select option.
def deletebook(request,arg='', context={}):
    if 'userEmail' in request.session and 'Password' in request.session and 'userType' in request.session:
        if request.session['userEmail'] == '#' or request.session['Password'] == '#' or request.session['userType'] == '#':
            return redirectToPage(request,"Please Login to proceed", '/library/admin/login')
        if request.session['userType'] != 'admin':
            return HttpResponseForbidden()
        else:
            sql="select b.title, a.authorname, b.isbn, b.link from author a,book b where a.id = (select authorid from haswritten where isbn=b.isbn)and b.deleted='false'"
        
            cursor=executeQuery(sql,connection)
            returnedVal=cursor.fetchall()
            cursor.close()
            return render(request,"library/admin/DeleteBookList.html", {'book':returnedVal})
    else:
        return redirectToPage(request,"Please Login to proceed", '/library/admin/login')


#Delete the selected book from the book table. This is done by updating the book deleted colum as 'true' in the book table instead of physical deletion
def performBookDelete(request,arg=''):
    isbn=request.POST.get("isbn")
    if isbn == None:
        return redirect('/library/admin/BookRecord/delete')
    sql="update book set deleted='true' where isbn='"+isbn+"'"

    cursor=executeQuery(sql,connection)
    cursor.close()
    connection.commit()            
    return redirectToPage(request, "Successful deletion", "/library/admin/home/")



#Renders the user record page containing add user, update user and delete user 
def userrecord(request,arg='', context={}):
    if 'userEmail' in request.session and 'Password' in request.session and 'userType' in request.session:
        if request.session['userEmail'] == '#' or request.session['Password'] == '#' or request.session['userType'] == '#':
            return redirectToPage(request,"Please Login to proceed", '/library/admin/login')
        if request.session['userType'] != 'admin':
            return HttpResponseForbidden()
        else:
            return render(request, 'library/admin/UserRecordHome.html', context)
    else:
        return redirectToPage(request,"Please Login to proceed", '/library/admin/login')


#Renders form to add new user
def adduser(request,arg='', context={}):
    if 'userEmail' in request.session and 'Password' in request.session and 'userType' in request.session:
        if request.session['userEmail'] == '#' or request.session['Password'] == '#' or request.session['userType'] == '#':
            return redirectToPage(request,"Please Login to proceed", '/library/admin/login')
        if request.session['userType'] != 'admin':
            return HttpResponseForbidden()
        else:
            return render(request, 'library/admin/InsertUser.html', context)
    else:
        return redirectToPage(request,"Please Login to proceed", '/library/admin/login')


#Checks the new user form details and insert the user into users table
def checknewuser(request,arg=''):
    email=request.POST.get("useremail")
    userName=request.POST.get("username")
    password=request.POST.get("password")
    if email == None or userName == None or password == None:
        return redirect('/library/admin/UserRecord/add/')
    sql="SELECT * from users where email='"+email+"'"

    cursor=executeQuery(sql,connection)
    returnedVal = cursor.fetchone()
    cursor.close()
    if returnedVal == None:
        sql="INSERT into users (email,username, userpassword,userType) values(%s,%s,%s,'normal')"
    
        try:
            cursor=executeQuery(sql,connection,email,userName,password)
        except:
            return redirectToPage(request, "Please fill the details again", '/library/admin/UserRecord/add')
        cursor.close()
        connection.commit()
        return redirectToPage(request, "Successful insertion", "/library/admin/home/")
    else:
        return redirectToPage(request, "email already present", '/library/admin/UserRecord/add')


#Displays list of users, with a select option
def updateuser(request,arg='', context={}):
    if 'userEmail' in request.session and 'Password' in request.session and 'userType' in request.session:
        if request.session['userEmail'] == '#' or request.session['Password'] == '#' or request.session['userType'] == '#':
            return redirectToPage(request,"Please Login to proceed", '/library/admin/login')
        if request.session['userType'] != 'admin':
            return HttpResponseForbidden()
        else:
            sql="select username, email from users where userType='normal'"
        
            cursor=executeQuery(sql,connection)
            returnedVal=cursor.fetchall()
            cursor.close()
            return render(request,"library/admin/UpdateUserList.html", {'users':returnedVal})
    else:
        return redirectToPage(request,"Please Login to proceed", '/library/admin/login')


#Returns a prepopulated user update form
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
        
            cursor=executeQuery(sql,connection,email)
            returnedVal = cursor.fetchone()
            cursor.close()
            username=returnedVal[0]
            password=returnedVal[2]
            request.session['emailEntry']=email
            return render(request,"library/admin/updateFormUserDisplay.html", {'email':email,'username':username,'password':password})

    else:
        return redirectToPage(request,"Please Login to proceed", '/library/admin/login')


#Updates the user update based on the form details
def performUserUpdate(request,arg=''):
    email=request.POST.get("useremail")
    username=request.POST.get("username")
    password=request.POST.get("password")
    if email == None or username == None or password == None or request.session['emailEntry'] == '#':
        return redirect('/library/admin/UserRecord/update/')
    oldEmailId = request.session['emailEntry']
    request.session['emailEntry']='#'
    sql = "update users set email=%s,username=%s,userpassword=%s where email=%s"
    
    cursor=executeQuery(sql,connection,email,username,password,oldEmailId)
    cursor.close()
    connection.commit()
    return redirectToPage(request, "Successful updation", "/library/admin/home/")


#Displays list of users available, with a select option
def deleteuser(request,arg='', context={}):
    if 'userEmail' in request.session and 'Password' in request.session and 'userType' in request.session:
        if request.session['userEmail'] == '#' or request.session['Password'] == '#' or request.session['userType'] == '#':
            return redirectToPage(request,"Please Login to proceed", '/library/admin/login')
        if request.session['userType'] != 'admin':
            return HttpResponseForbidden()
        else:
            sql="select username, email from users where userType='normal'"
        
            cursor=executeQuery(sql,connection)
            returnedVal=cursor.fetchall()
            cursor.close()
            return render(request,"library/admin/DeleteUserList.html", {'users':returnedVal})
    else:
        return redirectToPage(request,"Please Login to proceed", '/library/admin/login')


#Deletes the selected user from the users table
def performUserDelete(request,arg=''):
    email=request.POST.get("useremail")
    if email == None:
        return redirect('/library/admin/Userecord/delete')
    sql="delete from users where email=%s"

    cursor=executeQuery(sql,connection,email)
    cursor.close()
    connection.commit()            
    return redirectToPage(request, "Successful deletion", "/library/admin/home/")


#Displays a list of authors, with the select option
def updateauthor(request,arg='', context={}):
    if 'userEmail' in request.session and 'Password' in request.session and 'userType' in request.session:
        if request.session['userEmail'] == '#' or request.session['Password'] == '#' or request.session['userType'] == '#':
            return redirectToPage(request,"Please Login to proceed", '/library/admin/login')
        if request.session['userType'] != 'admin':
            return HttpResponseForbidden()
        else:
            sql="select authorname,id from author"
        
            cursor=executeQuery(sql,connection)
            returnedVal=cursor.fetchall()
            cursor.close()
            return render(request,"library/admin/UpdateAuthorList.html", {'authors':returnedVal})
    else:
        return redirectToPage(request,"Please Login to proceed", '/library/admin/login')


#Returns a prepopulated author update form
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
        
            cursor=executeQuery(sql,connection)
            returnedVal = cursor.fetchone()
            cursor.close()
            authorname=returnedVal[0]
            request.session['authorEntry']=authorid
            return render(request,"library/admin/updateFormAuthorDisplay.html", {'authorname':authorname})

    else:
        return redirectToPage(request,"Please Login to proceed", '/library/admin/login')


#Updates the selected author
def performAuthorUpdate(request,arg=''):
    authorname=request.POST.get("authorname")
    if authorname == None or request.session['authorEntry'] == -1:
        return redirect('/library/admin/AuthorUpdate/')
    authorid=request.session['authorEntry']
    request.session['authorEntry']=-1
    sql = "update author set authorname=%s where id="+authorid

    cursor=executeQuery(sql,connection %(authorname))
    cursor.close()
    connection.commit()
    return redirectToPage(request, "Successful updation", "/library/admin/home/")


#Returns a list of books which have been popularly read among the users
def topReads(request,arg='', context={}):
    if 'userEmail' in request.session and 'Password' in request.session and 'userType' in request.session:
        if request.session['userEmail'] == '#' or request.session['Password'] == '#' or request.session['userType'] == '#':
            return redirectToPage(request,"Please Login to proceed", '/library/admin/login')
        if request.session['userType'] != 'admin':
            return HttpResponseForbidden()
        else:
            bookList=['#']
            sql="select isbn from hasread group by isbn order by count(*) desc limit 8"
        
            cursor=executeQuery(sql,connection)
            isbnList=cursor.fetchall()
            cursor.close()

            for isbn in isbnList:
                sql="select b.title, a.authorname, b.isbn, b.link from author a,book b where id = (select authorid from haswritten where isbn='"+isbn[0]+"') and b.isbn = '"+isbn[0]+"'"
            
                cursor=executeQuery(sql,connection)
                returnedVal2=cursor.fetchall()
                cursor.close()
                for r in returnedVal2:
                    bookList.append(r)
                    
            bookList.remove('#')
            return render(request,"library/admin/TopReads.html", {'book':bookList})
    else:
        return redirectToPage(request,"Please Login to proceed", '/library/admin/login')

#Renders a page with the book details and the link to read it
def viewdetails(request,arg=''):
    isbn=request.POST.get("isbn")
    if isbn == None:
        return redirect('/library/admin/topReads')
    if 'userEmail' in request.session and 'Password' in request.session and 'userType' in request.session:
        if request.session['userEmail'] == '#' or request.session['Password'] == '#' or request.session['userType'] == '#':
            return redirectToPage(request,"Please Login to proceed", '/library/admin/login')
        if request.session['userType'] != 'admin':
            return HttpResponseForbidden()        
        else:
            sql="select a.authorname, b.title, b.link, b.deleted from author a,book b where id = (select authorid from haswritten where isbn='"+isbn+"') and b.isbn = '"+isbn+"'"
        
            cursor=executeQuery(sql,connection)
            returnedVal = cursor.fetchone()
            cursor.close()
            author=returnedVal[0]
            title=returnedVal[1]
            link=returnedVal[2]
            deleted=returnedVal[3]
            if deleted == 'true':
                return render(request,"library/admin/InvalidBook.html")
            return render(request,"library/admin/displaybookdetails.html", {'title':title,'author':author,'isbn':isbn,'link':link})

    else:
        return redirectToPage(request,"Please Login to proceed", '/library/admin/login')


#Logout from the application
def logout(request,arg='',context={}):
    return redirect('/library/')
    
