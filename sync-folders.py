#!/usr/bin/python
# user-assisted syncing
# posix only
import sys,os,curses
from time import sleep
#from shutil import copytree as cp
from filecmp import dircmp,cmp

cp="cp -fLpr" #the command to use when copying
t=0
KB=1024
MB=1024*KB
GB=1024*MB
TB=1024*GB

compare_mtime=True

def key(a):
	if compare_mtime:
		return (a.st_size, a.st_mtime)
		#size, modification time
	else:
		return a.st_size

def different_heads(a,b):
	da=''
	db=''
	i=-1
	while(a[i]==b[i]):
		i-=1
	i+=1
	return a[:i],b[:i]

def w(s):
	t.scroll()
	my,mx=t.getmaxyx()
	t.addstr(my-1,0, s)#somehow, mx, my, -1 lead to an error.
	t.refresh()

def wnr(s):
	w(s)
	return t.getkey()

def safeexit():
	w('exiting in 30 seconds! To exit now, press any key!')
	t.timeout(30*1000)
	i=t.getch()
	curses.putp("\n")
	curses.nocbreak()
	curses.endwin()
	exit()

def syncmissing(a, b, onlyina):
	for i in onlyina:
		if a+'/'+i in ignorelist:
			continue
		if os.stat(a+'/'+i).st_size > 10*MB:
			w('skipped '+a+'/'+i+' due to file size > 10MB')
		c=wnr(i+" not in "+b+". [c]opy [d]elete [s]kip [a]bort [i]gnore list ")
		if(c=='c'):
			s=cp+" '"+a+'/'+i+"' '"+b+"'"
			w(s)
			os.system(s)
		elif(c=='d'):
			s="rm -r '"+a+'/'+i+"'"
			w(s)
			os.system(s)
		elif(c=='a'):
			safeexit()
		elif(c=='i'):
			ignorefile.write(a+'/'+i+'\n')
		elif(c!='s'):
			w("try pressing [s] or [a] next time!")
			safeexit()

#TODO: add exclusion list. for a pair of directories.
def sync(a, b):
	da,db=different_heads(a,b)
	w("syncing "+a+" and "+b)
	d=dircmp(a,b)
	#3 stages
	
	#find missing in a or in b
	syncmissing(b, a, d.right_only)
	syncmissing(a, b, d.left_only)

	#check the common files. same=same modification time.
	for i in d.common_files:
		ta=os.stat(a+'/'+i)
		tb=os.stat(b+'/'+i)
		if(key(ta)!=key(tb)):
			if(ta.st_size==tb.st_size and abs(round(ta.st_mtime)-round(tb.st_mtime))<=2):
				#this is a FAT 2-second resolution problem.
				continue
			w("Files "+a+"/"+i+" and "+b+"/"+i+" seem to differ.")
			l=sorted([[a+"/"+i,ta], [b+"/"+i,tb]],key=lambda t:t[1].st_mtime)
			for x in l:
				w(x[0]+' size '+'{:,d}'.format(x[1].st_size)+' mtime '+str(x[1].st_mtime)+' ')
				os.system('date -d "1970-01-01 UTC '+str(x[1].st_mtime)+' seconds" +"%Y-%m-%d %T %z"')
				t.scroll(-1)
			c=wnr('[1] use '+da+' version [2] use '+db+' version [s]kip [a]bort ')
			if(c=='1'):
				s=cp+" '"+a+'/'+i+"' '"+b+"'"
				w(s)
				os.system(s)
			elif(c=='2'):
				s=cp+" '"+b+'/'+i+"' '"+a+"'"
				w(s)
				os.system(s)
			elif(c=='a'):
				safeexit()
			elif(c!='s'):
				w("try pressing [s] or [a] next time!")
				safeexit()

	#check the subdirs
	for i in d.common_dirs:
		w('syncing '+i)
		sync(a+'/'+i, b+'/'+i)
	return

ignorelist=open('.sync_ignore_list','r').read().splitlines()
ignorefile=open('.sync_ignore_list','a')
t = curses.initscr()
curses.cbreak()
t.idlok(1)
t.scrollok(1)
try:
	w('User-assisted syncing tool. Check the keyboard language!')
	#mx,my=t.getmaxyx()
	#x0,y0=t.getbegyx()
	if len(sys.argv)>3:
		if sys.argv[3]=='-m':
			compare_mtime=False
	sync(sys.argv[1], sys.argv[2])
except KeyboardInterrupt:
	pass
#except :
#	w('exception! '+str(sys.exc_info()[0]))
ignorefile.close()
safeexit()

#print(x0,y0,mx,my)
