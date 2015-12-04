from HTMLParser import HTMLParser

# create a subclass and override the handler methods
class MyHTMLParser(HTMLParser):
    artefacts = {}
    def handle_starttag(self, tag, attrs):
        #print "Encountered a start tag:", tag
        is_artefact = False
        for x,y in attrs:
            if x == 'class' and y == 'artefact':
                is_artefact = True
            if is_artefact and x == 'href':
                self.artefacts[y[10:]] = y

    def handle_endtag(self, tag):
        #print "Encountered an end tag :", tag
        pass
    def handle_data(self, data):
        #print "Encountered some data  :", data
        pass

    def get_artefacts(self):
        return self.artefacts

# instantiate the parser and fed it some HTML
#parser = MyHTMLParser()
#parser.feed(urlopen("http://cbag3.c-base.org/artefact/").read())
#print parser.get_artefacts()
