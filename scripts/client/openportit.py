from optparse import OptionParser
import pprint
import subprocess
import sys

if __name__ == '__main__':
	import wx
	app = wx.App(redirect=False)

import os
from sys import argv

working_dir = os.getcwd()
os.chdir(os.path.realpath(os.path.dirname(argv[0])))
from servefile import serve_file_on_port
from openport_win import open_port

def get_open_port():
	import socket
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.bind(("",0))
	s.listen(1)
	port = s.getsockname()[1]
	s.close()
	return port

def open_port_file(path, callback=None, extra_args={}):
	import threading
	serving_port = get_open_port()
	thr = threading.Thread(target=serve_file_on_port, args=(path, serving_port))
	thr.setDaemon(True)
	thr.start()
	
	thr2 = threading.Thread(target=open_port, args=(serving_port,callback, extra_args))
	thr2.setDaemon(True)
	thr2.start()

def start_tray_application():
    #todo: linux/mac
    if sys.argv[0][-3:] == '.py':
        command = ['start', 'python', 'application.py']
    else:
        command = ['start', quote_path(os.path.join(os.path.dirname(sys.argv[0]), 'application.exe'))]
    print command
    subprocess.call(' '.join(command), shell=True)

def quote_path(path):
    split = path.split(os.sep)
    print split
    quoted = ['"%s"' % dir if ' ' in dir else dir for dir in split]
    return os.sep.join(quoted)


if __name__ == '__main__':

#    print quote_path('c:\\hallo\\jan\\hoe ist\\goed.txt')
#    sys.exit(0)

    print 'client pid:%s' % os.getpid()
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--hide-message', action='store_true', help='Do not show the message.')
    parser.add_argument('--no-clipboard', action='store_true', help='Do not copy the link to the clipboard.')
    parser.add_argument('--tray-port', type=int, default=8001, help='Inform the tray app of the new share.')
    parser.add_argument('filename', help='The file you want to openport.')
    args = parser.parse_args()

    def copy_to_clipboard(server_ip, server_port):
        from Tkinter import Tk
        r = Tk()
        r.withdraw()
        r.clipboard_clear()
        file_address = '%s:%s'%(server_ip, server_port)

        r.clipboard_append(file_address.strip())
        r.destroy()

    def show_message_box(server_ip, server_port, extra_args):
        wx.MessageBox('You can now download your file(s) from %s:%s\nThis link has been copied to your clipboard.' %(server_ip, server_port), 'Info', wx.OK | wx.ICON_INFORMATION)

    def inform_tray_app(server_ip, server_port, extra_args, tray_port, account_id, key_id, start_tray=False):
        import urllib, urllib2
        path = os.path.abspath( os.path.join(working_dir,args.filename))
        url = 'http://127.0.0.1:%s' % tray_port

        try:
            data = urllib.urlencode({
                'path' : path,
                'server': server_ip,
                'server_port': server_port,
                'pid': os.getpid(),
                'account_id': account_id,
                'key_id': key_id,
            })
            req = urllib2.Request(url, data)
            response = urllib2.urlopen(req).read()
            if response.strip() != 'ok':
                print response
        except Exception, detail:
            print "An error has occured while informing the tray: ", detail
            if start_tray:
                start_tray_application()
                sleep(3)
                inform_tray_app(server_ip, server_port, extra_args, tray_port, account_id, key_id, start_tray=False)


    def callback(server_ip, server_port, account_id, key_id,  extra_args):
        if args.tray_port > 0:
            inform_tray_app(server_ip, server_port, extra_args, args.tray_port, account_id, key_id, start_tray=True)
        if not args.no_clipboard:
            copy_to_clipboard(server_ip, server_port)
        if not args.hide_message:
            show_message_box(server_ip, server_port, extra_args)

    app.MainLoop()
    open_port_file(os.path.join(working_dir, args.filename), callback)
    from time import sleep
    while True:
       sleep(1000)

	