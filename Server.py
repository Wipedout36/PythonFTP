import os
import socket
import threading
import time
 
allow_delete = False
local_ip = socket.gethostbyname(socket.gethostname())
local_port = 4095
currdir=os.path.abspath('.')
 
class FTPserverThread(threading.Thread):
    def __init__(self,(conn,addr)):
        self.conn=conn
        self.addr=addr
        self.basewd=currdir
        self.cwd=self.basewd
        self.rest=False
        self.pasv_mode=False
        threading.Thread.__init__(self)
 
    def run(self):
        self.conn.send('220 Welcome!\r\n')
        while True:
            cmd=self.conn.recv(256)
            if not cmd: break
            else:
                print 'Recieved:',cmd
                try:
                    func=getattr(self,cmd[:4].strip().upper())
                    func(cmd)
                except Exception,e:
                    print 'ERROR:',e
                    self.conn.send('500 Sorry.\r\n')

    def USER(self,cmd):
        self.conn.send('331 OK.\r\n')
    def PASS(self,cmd):
        self.conn.send('230 OK.\r\n')
    def QUIT(self,cmd):
        self.conn.send('221 Goodbye.\r\n')
    def TYPE(self,cmd):
        self.mode=cmd[5]
        self.conn.send('200 Binary mode.\r\n')
 
    def PWD(self,cmd):
        cwd=os.path.relpath(self.cwd,self.basewd)
        if cwd=='.':
            cwd='/'
        else:
            cwd='/'+cwd
        self.conn.send('257 \"%s\"\r\n' % cwd)
 
    def PORT(self,cmd):
        if self.pasv_mode:
            self.servsock.close()
            self.pasv_mode = False
        l=cmd[5:].split(',')
        self.dataAddr='.'.join(l[:4])
        self.dataPort=(int(l[4])<<8)+int(l[5])
        self.conn.send('200 Get port.\r\n')
 
    def PASV(self,cmd):
        self.pasv_mode = True
        self.servsock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.servsock.bind((local_ip,0))
        self.servsock.listen(1)
        ip, port = self.servsock.getsockname()
        print 'open', ip, port
        self.conn.send('227 Entering Passive Mode (%s,%u,%u).\r\n' %
                (','.join(ip.split('.')), port>>8&0xFF, port&0xFF))
 
    def start_datasock(self):
        if self.pasv_mode:
            self.datasock, addr = self.servsock.accept()
            print 'connect:', addr
        else:
            self.datasock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            self.datasock.connect((self.dataAddr,self.dataPort))
 
    def stop_datasock(self):
        self.datasock.close()
        if self.pasv_mode:
            self.servsock.close()
 
    def LIST(self,cmd):
        self.conn.send('150 Here comes the directory listing.\r\n')
        print 'list:', self.cwd
        self.start_datasock()
        for t in os.listdir(self.cwd):
            k=self.toListItem(os.path.join(self.cwd,t))
            self.datasock.send(k+'\r\n')
        self.stop_datasock()
        self.conn.send('226 Directory send OK.\r\n')
 
    def toListItem(self,fn):
        st=os.stat(fn)
        return ' '+os.path.basename(fn).ljust(30)+str(st.st_size)+' bytes'
 
    def REST(self,cmd):
        self.pos=int(cmd[5:-2])
        self.rest=True
        self.conn.send('250 File position reseted.\r\n')
 
    def RETR(self,cmd):
        fn=os.path.join(self.cwd,cmd[5:-2])
        print 'Downloading:',fn
        if self.mode=='I':
            fi=open(fn,'rb')
        else:
            fi=open(fn,'r')
        self.conn.send('150 Opening data connection.\r\n')
        if self.rest:
            fi.seek(self.pos)
            self.rest=False
        data= fi.read(1024)
        self.start_datasock()
        while data:
            self.datasock.send(data)
            data=fi.read(1024)
        fi.close()
        self.stop_datasock()
        self.conn.send('226 Transfer complete.\r\n')
 
    def STOR(self,cmd):
        fn=os.path.join(self.cwd,cmd[5:-2])
        print 'Uploading:',fn
        if self.mode=='I':
            fo=open(fn,'wb')
        else:
            fo=open(fn,'w')
        self.conn.send('150 Opening data connection.\r\n')
        self.start_datasock()
        while True:
            data=self.datasock.recv(1024)
            if not data: break
            fo.write(data)
        fo.close()
        self.stop_datasock()
        self.conn.send('226 Transfer complete.\r\n')
 
class FTPserver(threading.Thread):
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((local_ip,local_port))
        threading.Thread.__init__(self)
 
    def run(self):
        self.sock.listen(5)
        while True:
            th=FTPserverThread(self.sock.accept())
            th.daemon=True
            th.start()
 
    def stop(self):
        self.sock.close()
 
if __name__=='__main__':
    ftp=FTPserver()
    ftp.daemon=True
    ftp.start()
    print 'On', local_ip, ':', local_port
    raw_input('Enter to end...\n') #Provides server termination condition.
    ftp.stop()