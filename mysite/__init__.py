import pymysql
pymysql.install_as_MySQLdb()
#Format for this global variable is 'mysql://username:password@hostname/databaseName
username=''
password=''
hostname=''
databasename=''
conFile=open('DatabaseConnection.txt','r')
lines=conFile.readlines()
for line in lines:
    if 'UserName' in line:
        username=(line.split(':')[1]).replace('\n','')
    elif 'Password' in line:
        password=(line.split(':')[1]).replace('\n','')
    elif 'HostName' in line:
        hostname=(line.split(':')[1]).replace('\n','')
    elif 'DatabaseName' in line:
        databasename=(line.split(':')[1]).replace('\n','')
                          
DATABASE_URL_CONSTANT = 'mysql://'+username+':'+password+'@'+hostname+'/'+databasename
ALLOWED_HOSTS_CONSTANT = '127.0.0.1'
