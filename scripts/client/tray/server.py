import cgi, urlparse
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import threading
import traceback
import wx
from common.session import Session
from dbhandler import DBHandler
from globals import Globals
from common.share import Share
from services.logger_service import get_logger

logger = get_logger('server')

onNewShare = None

shares = {}

class ShareRequestHandler(BaseHTTPRequestHandler):

    def do_POST(self):
        logger.debug('got post on path:%s'%self.path)
        try:
            ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
            if ctype == 'multipart/form-data':
                postvars = cgi.parse_multipart(self.rfile, pdict)
            elif ctype == 'application/x-www-form-urlencoded':
                length = int(self.headers.getheader('content-length'))
                postvars = urlparse.parse_qs(self.rfile.read(length), keep_blank_values=1)
            else:
                postvars = {}

            dict = {}
            for key in postvars:
                dict[key] = postvars[key][0]

            logger.debug('got dict %s on path %s' % (dict, self.path))
            logger.debug('known shares: %s' %shares)

            if self.path.endswith('newShare'):
                if dict['local_port'] in shares:
                    #update existing share
                    share = shares[dict['local_port']]
                    share.from_dict(dict)
                else:
                    if dict['type'] == 'Share':
                        share = Share()
                    else:
                        share = Session()
                    share.from_dict(dict)

                    globals = Globals()
                    globals.account_id = share.account_id
                    globals.key_id = share.key_id
#                    logger.debug( 'path: <%s>' % share.filePath )

                    save_request(share)
                    if onNewShare:
                        wx.CallAfter(onNewShare, share)
                    global shares
                    shares[share.local_port] = share
                    logger.debug('added new share')
                    logger.debug(shares)
                self.write_response('ok')
            elif self.path.endswith('successShare'):
                logger.debug('success')
                if not dict['local_port'] in shares:
                    logger.error('unknown key: %s in shares %s' % (dict['local_port'], shares))
                    self.write_response('unknown')
                else:
                    shares[dict['local_port']].notify_success()
                    self.write_response('ok')

            elif self.path.endswith('errorShare'):
                logger.debug('error')
                if not dict['local_port'] in shares:
                    logger.error('unknown key: %s in shares %s' % (dict['local_port'], shares))
                    self.write_response('unknown')
                else:
                    shares[dict['local_port']].notify_error()
                    self.write_response('ok')

        except Exception, e:
            logger.exception(e)
            self.write_response('an error has occurred')

    def write_response(self, text):
        try:
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.send_header("Content-Length", str(len(text)))
            self.end_headers()
            self.wfile.write(text)
            self.wfile.close()
        except Exception, e:
            traceback.print_stack()
            logger.error( e )

def start_server(onNewShareFunc=None):
    try:
        server = HTTPServer(('', 8001), ShareRequestHandler)
        global onNewShare
        onNewShare=onNewShareFunc
        logger.info( 'Starting server' )
        server.serve_forever()
    except KeyboardInterrupt:
        server.socket.close()

def save_request(share):
    db_handler = DBHandler()
    return db_handler.add_share(share)

def start_server_thread(onNewShare=None):
    t = threading.Thread(target=start_server, args=[onNewShare])
    t.setDaemon(True)
    t.start()

if __name__ == '__main__':
    start_server()