#! /usr/bin/python
import httplib, urllib, random, re, os, sys
from jsonrpclib.SimpleJSONRPCServer import SimpleJSONRPCServer

player = 'mpg123'
sampledir = '/home/mirror/samples/tts'
password = '0g7znor2aa'

def main():
    server = SimpleJSONRPCServer(('0.0.0.0', 1775))

    server.register_function(tts, 'tts')
    server.serve_forever()

def tts(voice, text):
    if voice in ['lucy', 'peter', 'rachel', 'heather', 'kenny', 'laura', 'nelly', 'ryan', 'julia', 'sarah', 'klaus']:
        voice = '%s22k' % voice
    else:
        voice = 'lucy22k'

    pitch = 100
    speed = 180
    filename = '%s/%s_%s_%d_%d.mp3' % (sampledir, urllib.quote(text.lower()), voice, pitch, speed)
    textparam = '\\vct=%d\\ \\spd=%d\\ %s' % (pitch, speed, text)

    # check whether we have a cached version of the the file
    if os.path.isfile(filename):
        play(filename)
    else:
        params = urllib.urlencode({
            'cl_env': 'FLASH_AS_3.0',
            'req_asw_type': 'INFO',
            'req_voice': voice,
            'req_timeout': '120',
            'cl_vers': '1-30',
            'req_snd_type': '',
            'req_text': textparam,
            'cl_app': 'PROD',
            'cl_login': 'ACAPELA_BOX',
            'prot_vers': '2',
            'req_snd_id': '0_0_84%s88' % random.randint(0, 32767),
            'cl_pwd': password
        })

        headers = {"Content-type": "application/x-www-form-urlencoded",
                  "Accept": "text/plain"}
        conn = httplib.HTTPConnection("vaassl3.acapela-group.com")
        conn.request("POST", "/Services/AcapelaBOX/0/Synthesizer", params, headers)
        response = conn.getresponse()
        data = response.read()
        conn.close()

        url = re.compile('http://.*\.mp3').search(data).group()

        mysock = urllib.urlopen(url)
        fileToSave = mysock.read()
        oFile = open('%s' % filename,'wb')
        oFile.write(fileToSave)
        oFile.close

        play(filename)

def play(filename):
    print '%s %s' % (player, filename)
    os.system('%s %s' % (player, filename))
    
if __name__ == "__main__":
    main()
