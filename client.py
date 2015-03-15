from ftplib import FTP
import os

filename = ""
cwd = os.getcwd()

def quit():
	ftp.quit()

def list():
	ftp.retrlines('LIST') #Lists files in current dir
	menu()

def download():

	filename = raw_input("Enter file name: ")
	
	dfile = open(filename, 'wb')
	ftp.retrbinary('RETR ' + filename, dfile.write, 256)
	dfile.close()
	print 'Downloaded', filename, 'to', cwd
	
	menu()
	
def upload():
	dirs = os.listdir(".")
	for file in dirs:
		print file
	filename = raw_input("\nEnter filename to upload: ")
	ftp.storbinary('STOR '+filename, open(filename, 'rb'))
	print '\nUploaded', filename
	
	menu()
	
	
def menu():

	print '\nType U to Upload\nType D to Download\nType L to List files\nType Q to Quit'

	option = raw_input("Choice: ")
	print '\n'
	
	if option == "q":
		quit()
	elif option == "l":
		list()
	elif option == "d":
		download()
	elif option == "u":
		upload()


HOST = '192.168.0.6' #raw_input("Enter FTP IP: ")
PORT = 4095 #raw_input("Enter PORT: ")
ftp = FTP()
ftp.connect(HOST, PORT)

print '\nConnected to', HOST, ':', PORT, '\n'

menu()

raw_input('Enter to end...\n')

