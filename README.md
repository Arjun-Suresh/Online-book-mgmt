# Online-library

Introduction:
This application is an online library application, which helps the user to read a subset of e-books stored in Project Gutenberg's e-book storage site. Project Gutenberg is an initiative to provide access to the world of e-books for all internet users. Currently, all the books stored in this particular application's database point to the corresponding book in Project Gutengerg's site, and I would like to give all due credit to the initiative.


Development platforms:
This application follows the MVC (technically shared-nothing) architecture:
1. HTML 5.5, CSS and Javascript(minimal) for the presentation tier.
2. Python with Django (specific packages used could be checked in the requirements.txt file) for the logic tier.
3. MYSQL database for the persistence tier.


Deployment:
This particular application has been deployed in heroku and is currently running in the url: https://desolate-everglades-70182.herokuapp.com/library


Setting it up on the local system:
1. Clone the repository
2. Ensure you have MYSQL 5.7 or above installed on the system. Import the .sql file into mysql provided under db folder
3. In the __init.py__, set DATABASE_URL_CONSTANT global variable. Format for this global variable is 'mysql://username:password@hostname/databaseName
4. Also, set ALLOWED_HOSTS_CONSTANT to '127.0.0.1'
5. In command prompt, navigate to mysite folder and enter the command 'python manage.py runserver'
6. The app would be hosted at '127.0.0.1:8000/library/'
7. Try admin login with user email: 'arjun.sureshn2000@gmail.com' and password: 'Password'
