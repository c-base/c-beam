#! /usr/bin/python


import time, os, datetime
import BaseHTTPServer
import logging

HOST_NAME = '10.0.1.27' # !!!REMEMBER TO CHANGE THIS!!!
PORT_NUMBER = 8080 # Maybe set this to 9000.

usermap = '/home/c-beam/usermap'
scriptdir = '/home/smile/projects/c-beam/tageventor/tagEventor/scripts'
userpath = '/home/c-beam/users'
logfile = '/var/log/c-beam/c-beamhttp.log'
logindelta = 30
timeoutdelta = 600

logger = logging.getLogger('c-beamhttp')
hdlr = logging.FileHandler(logfile)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr) 
logger.setLevel(logging.INFO)


class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_HEAD(s):
        s.send_response(200)
        s.send_header("Content-type", "text/html")
        s.end_headers()
    def do_GET(s):
        """Respond to a GET request."""
        s.send_response(200)
        s.send_header("Content-type", "text/html")
        s.end_headers()
        s.wfile.write("<html><head><title>c-beam user interface</title></head>")
        s.wfile.write("<body>")

        urlcomponents = s.path.split('/')
        if len(urlcomponents) != 3:
            s.wfile.write("invalid URL.<body><html>")
            logger.warn("invalid url: %s" % s.path)
            return 

        (foo, method, uuid) = urlcomponents
        logger.info("method: %s uuid: %s" % (method, uuid))
   
        # lookup uuid
        userfile = '%s/%s' % (usermap, uuid)
        if os.path.exists(userfile) and os.path.isfile(userfile):
            f = open(userfile, "r")
            username = f.read()
            username = username.rstrip('\n')
            f.close()
            
            logger.info("%s: %s" % (method, username))
            if method == 'login':
                userloginfile = '%s/%s' % (userpath, username)
                logints = datetime.datetime.now() + datetime.timedelta(seconds=logindelta)
                timeoutts = datetime.datetime.now() + datetime.timedelta(minutes=timeoutdelta)
                expire = [int(logints.strftime("%Y%m%d%H%M%S")), int(timeoutts.strftime("%Y%m%d%H%M%S"))]
                f = open(userloginfile, 'w')
                f.write(str(expire))
                f.close()
                s.wfile.write('<h1>hallo %s, willkommen auf der c-base.</h1>' % username)
            elif method == 'logout':
                if os.path.exists('%s/%s' % (userpath, username)):
                    os.remove('%s/%s' % (userpath, username))
                s.wfile.write('danke, daC du dich abgemeldet hast.')
            
        else:
            logger.warn("invalid tocen: %s" % uuid)
            s.wfile.write("invalid tocen.")

        s.wfile.write("</body></html>")

if __name__ == '__main__':
    server_class = BaseHTTPServer.HTTPServer
    httpd = server_class((HOST_NAME, PORT_NUMBER), MyHandler)
    print time.asctime(), "Server Starts - %s:%s" % (HOST_NAME, PORT_NUMBER)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print time.asctime(), "Server Stops - %s:%s" % (HOST_NAME, PORT_NUMBER)
