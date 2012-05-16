# -*- coding: utf-8 -*-

from jsb.utils.exception import handle_exception
from jsb.lib.commands import cmnds

import random 

quotes = [
    "Allerdings muss ich gleich sagen: Bei mir beginnt die Mathematik, Physik und auch Geologie dort, wo das Hochschulstudium aufhört.",
    "Medizin ist Mathematik, Biologie ist Physik!",
    "Magie ist Physik durch Wollen!",
    "Der Mensch ist eine energetische Matrix.",
    "Der menschliche Zellkern ist gleich pures Licht, sprich: schwarze Sonnen.",
    "Wenn ein Mensch autogen sein Kraftfeld verstärkt, könnte er im Extremfall schweben. Also levitieren.",
    "Die Sonne ist KALT, da staunt ihr, wa?",
    "Wer weis das? ... Wieder keiner!",
    "Im Prinzip brauchen wir nur drei Wissenschaften, um alles zu beschreiben: Physik. Mathematik. Philosophie.",
    "Und die Russen sind ja Waffentechnisch den Amerikanern weit überlegen. MUSS MAN WISSEN!",
    "...und das ist auch die Maschine, die entscheidend ist für Freie-Energie-Maschinen. Die muss man anzapfen entsprechend einem Implosions-Strudel. Das heißt, eine Logarithmische Spirale raum-zeitlich betrachtet nach INNEN.",
    "...und das ist auch die Maschine, die entscheidend ist für Freie-Energie-Maschinen. Die muss man anzapfen entsprechend einem Implosions-Strudel. Das heißt, eine Logarithmische Spirale raum-zeitlich betrachtet nach INNENdrinrein.",
    "Es gibt keine Zufälle, Das Wort 'Zufall' ist aus meinem Wortschatz gestrichen",
    "96 Flugzeuge * 60 Minuten * 14 Stunden * 40 Passagiere ergibt: 3.225.600 Passagiere pro Tag. PRO TAG! Das ist kein Science Fiction.",
    "Das hier ist nichts anderes als ein Strafplanet",
    "Der Selbsterhaltungstrieb der Zelle. Zur Erinnerung: [Die Zelle] ist ein Perpetuum Mobile, wie das Universum auch, ist ja klar.",
    "Wiederholung ist die Mutter der Weisheit",
    "Seit 10 Jahren wird der T-92 hergestellt. Ein modernster Panzer, russische Panzer mit Spitzengeschwindigkeit von 300 km/h",
]



def handle_axel(bot, ievent):
        ievent.reply('"%s"' % random.choice(quotes))
        #bot.say('#c-base', '"%s"' % random.choice(quotes))
        # bot.say('#c-base', '"%s" (Dr. Axel Stoll)' random.choice(quotes))

cmnds.add("axel", handle_axel, ['OPER', 'USER', 'GUEST'])
