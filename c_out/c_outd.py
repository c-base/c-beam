#! /usr/bin/python
# -*- coding: utf-8 -*-

import httplib, urllib, random, re, os, sys, time, subprocess
import logging
from jsonrpclib.SimpleJSONRPCServer import SimpleJSONRPCServer

player = 'mpg123'

c_outlimit = 5
suppressiontimeout = 300
cpamdelta = 90

sampledir = '/mnt/datengrab/00_audio/c_out'
sampledir = '/usr/local/sounds/loop'
sampledir = '/usr/local/sounds/samples'
tmpdir = '/tmp/shout'

r2d2path = '/home/smile/projects/c-beam/c_out/r2d2_wav'
txt2phopath = "/var/www/c_out.c-base.org/txt2speech/txt2pho"

acapelapassword = '0g7znor2aa'

thevoices = ['lucy', 'peter', 'rachel', 'heather', 'kenny', 'laura', 'nelly', 'ryan', 'julia', 'sarah', 'klaus', 'r2d2']
acapelavoices = ['lucy', 'peter', 'rachel', 'heather', 'kenny', 'laura', 'nelly', 'ryan', 'julia', 'sarah', 'klaus']
txt2phovoices = ['de5']

coutcount = 0
suppressuntil = 0
lastcpamcheck = 0

logfile = '/home/smile/c_out.log'

logger = logging.getLogger('c_out')
hdlr = logging.FileHandler(logfile)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr) 
logger.setLevel(logging.INFO)

def main():

    #tts("julia", "c")

    server = SimpleJSONRPCServer(('0.0.0.0', 1775))

    server.register_function(tts, 'tts')
    server.register_function(r2d2, 'r2d2')
    server.register_function(play, 'play')
    server.register_function(setvolume, 'setvolume')
    server.register_function(getvolume, 'getvolume')
    server.register_function(voices, 'voices')
    server.register_function(sounds, 'sounds')
    server.register_function(c_out, 'c_out')
    server.register_function(announce, 'announce')
    server.serve_forever()

def voices():
    return thevoices

def listFiles(dir):
    ls = []
    for item in os.listdir(dir):
        if os.path.isdir("%s/%s" % (dir, item)):
            ls.extend(listFiles("%s/%s" % (dir, item)))
        else:
            ls.append(item)
    return ls

def findFile(dir, filename):
    for item in os.listdir(dir):
        if os.path.isfile("%s/%s" % (dir, item)):
            if item.find(filename) != -1:
                return "%s/%s" % (dir, item)
        elif os.path.isdir("%s/%s" % (dir, item)):
            res = findFile("%s/%s" % (dir, item), filename)
            if res != "":
               return res
    return ""

def mergemp3(mp3s, outfile):
    oFile = open('%s/%s.mp3' % (tmpdir, outfile),'wb')
    oFile.close

    for mp3 in mp3s:
        iFile = open("%s/%s" % (r2d2path, mp3), 'r')
        oFile.write(iFile.read())
        iFile.close
    oFile.close

    return "%s/%s" % (tmpdir, outfile)


def tts(voice, text):
    if voice in acapelavoices:
        return acapela(voice, text)
    if voice in txt2phovoices:
        return txt2pho(voice, text)
    elif voice == 'r2d2':
        return r2d2(text)
    else:
        return acapela('julia', text)

def acapela(voice, text):
    if voice.find('22k') == -1:
        voice = '%s22k' % voice

    pitch = 100
    speed = 180
    if not text.endswith("."): text = "%s." % (text,)
    filename = '%s/%s_%s_%d_%d.mp3' % (tmpdir, urllib.quote(text.lower()), voice, pitch, speed)
    textparam = '\\vct=%d\\ \\spd=%d\\ %s' % (pitch, speed, text)

    # check whether we have a cached version of the the file
    if os.path.isfile(filename):
        return play(filename)
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
            'cl_pwd': acapelapassword
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

        return play(filename)
    

def r2d2(text):
    #c_outcount += 1
    if iscpam():
        return "cpam alarm. bitte beachten sie die sicherheitshinweise. (%d)" % (suppressuntil - int(time.time()))
    mp3s = []
    #text = text.lower()

    for char in text:
        char = char.replace(" ", "space")
        char = char.replace("\n", "space")
        char = char.replace("/", "slash")
        char = char.replace("-", "minus")
        char = char.replace("?", "ask")
        char = char.replace(unicode('\xc3\xa4', 'utf8'), "ae")
        char = char.replace(unicode('\xc3\x9e', 'utf8'), "szett")
        char = char.replace(unicode('\xc3\xb6', 'utf8'), "oe")
        char = char.replace(unicode('\xc3\xbc', 'utf8'), "ue")
        char = char.replace(unicode('\xc3\x84', 'utf8'), "AE")
        char = char.replace(unicode('\xc3\x96', 'utf8'), "OE")
        char = char.replace(unicode('\xc3\x9c', 'utf8'), "UE")

        mp3s.append("%s/%s.mp3" % (r2d2path, char))
    return playfile(" ".join(mp3s))

def txt2pho(voice, text):
    filenamemp3 = '%s/%s_%s.mp3' % (tmpdir, urllib.quote(text.lower()), voice)
    filenamewav = '%s/%s_%s.wav' % (tmpdir, urllib.quote(text.lower()), voice)
    os.system('echo "%s" | %s/txt2pho | %s/mbrola -v 2.5 %s/data/%s/%s - %s' % (text, txt2phopath, txt2phopath, txt2phopath, voice, voice, filenamewav))
    os.system('lame %s %s' % (filenamewav, filenamemp3))
    return play(filenamemp3)

def getvolume():
    res = subprocess.Popen(['amixer', 'get', 'Master'],  stdout=subprocess.PIPE).stdout.read()
    m = re.search('\[(\d+)\%\]', res)
    try:
        curvol = m.group(1)
    except:
        curvol = -1

    #curvol = subprocess.Popen('/usr/local/bin/getvol', stdout=subprocess.PIPE).stdout.read()
    return curvol

def setvolume(vol):
    os.system('amixer set Master %s%%' % vol)
    return getvolume()

def c_out():
    return play(random.choice(sounds()))

#def c_out(sound):
#    return play(sound)

def sounds():
#    return os.listdir(sampledir)
    return listFiles(sampledir)


def iscpam():
    global coutcount
    global suppressuntil
    global lastcpamcheck
    now = int(time.time())
    if lastcpamcheck + cpamdelta > now:
        coutcount += 1
    else:
        coutcount = 1
    lastcpamcheck = now
    if coutcount > c_outlimit:
        if suppressuntil == 0:
            suppressuntil = now + suppressiontimeout
            return True
        elif now > suppressuntil:
            coutcount = 1
            suppressuntil = 0
            return False
        else:
            return True
    else:
        return False

def play(filename):
    if iscpam():
        return "cpam alarm. bitte beachten sie die sicherheitshinweise. (%d)" % (suppressuntil - int(time.time()))
    else:
        return playfile(filename)

def playfile(filename):
    if filename.find(".") == -1:
        filename = "%s.mp3" % filename
    if filename.find("/") == -1:
        #filename = "%s/%s" % (sampledir, filename)
        filename = findFile(sampledir, filename)
#    print '%s %s' % (player, filename)
    if player == 'mplayer':
        print 'mplayer -af volume=+10 -really-quiet -ao esd %s >/dev/null' % filename
        os.system('mplayer -af volume=+10 -really-quiet -ao esd %s >/dev/null' % filename)
    else:
        os.system('%s %s' % (player, filename))
    return "aye"

if __name__ == "__main__":
    main()

def announce(text):
    """Plays a ringing sound, says an announcement and then repeats it."""
    playfile('announce.mp3')
    tts('julia', 
        "Achtung! Eine Durchsage: %s. Ich wiederhole: %s. Vielen Dank!" % (text, text))