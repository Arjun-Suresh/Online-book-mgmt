import pymysql
pymysql.install_as_MySQLdb()
#Format for this global variable is 'mysql://username:password@hostname/databaseName
DATABASE_URL_CONSTANT = 'mysql://root:password@127.0.0.1/onlinelibrary'
ALLOWED_HOSTS_CONSTANT = '127.0.0.1'
#DATABASE_URL_CONSTANT = 'mysql://bccdb0b58a9802:7ee543ed@us-cdbr-iron-east-05.cleardb.net/heroku_e9cedb276cb7f86'
#ALLOWED_HOSTS_CONSTANT = 'desolate-everglades-70182.herokuapp.com'
