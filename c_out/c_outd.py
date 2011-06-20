#! /usr/bin/python
# -*- coding: utf-8 -*-

import httplib, urllib, random, re, os, sys, time
from jsonrpclib.SimpleJSONRPCServer import SimpleJSONRPCServer

player = 'mpg123'
sampledir = '/mnt/datengrab/00_audio/c_out'
sampledir = '/tmp/shout'
r2d2path = '/home/smile/projects/c-beam/c_out/r2d2_wav'
password = '0g7znor2aa'

thevoices = ['lucy', 'peter', 'rachel', 'heather', 'kenny', 'laura', 'nelly', 'ryan', 'julia', 'sarah', 'klaus']

def main():
    server = SimpleJSONRPCServer(('0.0.0.0', 1775))
    r2d2("foo der bar!")

    server.register_function(tts, 'tts')
    server.register_function(r2d2, 'r2d2')
    server.register_function(play, 'play')
    server.register_function(volume, 'volume')
    server.register_function(voices, 'voices')
    server.serve_forever()

def voices():
    return thevoices

def mergemp3(mp3s, outfile):
    oFile = open('%s/%s.mp3' % (sampledir, outfile),'wb')
    oFile.close

    for mp3 in mp3s:
        iFile = open("%s/%s" % (r2d2path, mp3), 'r')
        oFile.write(iFile.read())
        iFile.close
    oFile.close

    return "%s/%s" % (sampledir, outfile)


def tts(voice, text):
    if voice in thevoices:
        voice = '%s22k' % voice
    else:
        voice = 'lucy22k'

    pitch = 100
    speed = 180
    if not text.endswith("."): text = "%s." % (text,)
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

def r2d2(text):
    mp3s = []
    #text = text.lower()

    for char in text:
        char = char.replace(" ", "space")
        char = char.replace("\n", "space")
        char = char.replace("/", "slash")
        char = char.replace("-", "minus")
        char = char.replace("?", "ask")
        char = char.replace("ß", "szett")
        char = char.replace("ä", "ae")
        char = char.replace("ö", "oe")
        char = char.replace("ü", "ue")
        char = char.replace("Ä", "AE")
        char = char.replace("Ö", "OE")
        char = char.replace("Ü", "UE")

        mp3s.append("%s/%s.mp3" % (r2d2path, char))
    print mp3s
    #return play(mergemp3(mp3s, "r2d2.mp3"))
    return play(" ".join(mp3s))

def festival(text):
    return "not implemented"

def volume(vol):
    return "not implemented"

def play(filename):
    # TODO: check if filename contains /, otherwise use default directory
    print '%s %s' % (player, filename)
    if player == 'mplayer':
        print 'mplayer -af volume=+10 -really-quiet -ao esd %s >/dev/null' % filename
        os.system('mplayer -af volume=+10 -really-quiet -ao esd %s >/dev/null' % filename)
    else:
        os.system('%s %s' % (player, filename))

if __name__ == "__main__":
    main()

