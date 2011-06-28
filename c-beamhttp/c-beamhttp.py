import time, os
import BaseHTTPServer
HOST_NAME = '10.0.1.27' # !!!REMEMBER TO CHANGE THIS!!!
PORT_NUMBER = 8080 # Maybe set this to 9000.

usermap = '/home/c-beam/usermap'
scriptdir = '/home/smile/projects/c-beam/tageventor/tagEventor/scripts'



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
            return 

        (foo, method, uuid) = urlcomponents
        print "method: %s" % method
        print "uuid: %s" % uuid

   
        # lookup uuid
        userfile = '%s/%s' % (usermap, uuid)
        if os.path.exists(userfile) and os.path.isfile(userfile):
            f = open(userfile, "r")
            username = f.read()
            print username
            if method == 'login':
                #login
                s.wfile.write('hallo %s, willkommen auf der c-base.' % username)
            elif method == 'logout':
                #logout
                s.wfile.write('danke, daC du dich abgemeldet hast.')
            
        else:
            s.wfile.write("invalid tocen.")
            
        # login user
        
   

        #s.wfile.write("<p>You accessed path: %s</p>" % s.path)
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
