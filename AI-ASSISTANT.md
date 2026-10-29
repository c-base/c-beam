# Der KI-Assistent in c-beam-droid

Stand 2026-10-29. Diese Datei beschreibt, wie die App mit dem Bordcomputer spricht:
Aufnahme, Spracherkennung, Sprachmodell mit Werkzeugen, Wissensdatenbank und Vorlesen.
Sie ist so geschrieben, dass sich dieselben Funktionen in der Web-Oberfläche von c-beam
nachbauen lassen. Alle Protokolle sind HTTP oder WebSocket und nicht Android-spezifisch;
Android-eigen sind nur Mikrofon und Sprachausgabe. Der Code liegt in
`app/src/main/java/org/c_base/c_beam/voice/`, die Dateinamen stehen jeweils dabei.

## 1. Überblick

Ein Nutzer hält den Mikrofonknopf, spricht einen Satz, lässt los. Die App schickt die
Aufnahme an Whisper, den Text an das Sprachmodell, und das Modell antwortet entweder in
Worten oder ruft ein Werkzeug auf: Stationsdaten abfragen, die Wissensdatenbank
durchsuchen, einloggen, eine Durchsage machen. Die Antwort erscheint in einem kleinen
Terminal im Stil des Activity-Logs und wird auf Wunsch vorgelesen.

Beteiligte Dienste, alle nur aus dem Crew-Netz erreichbar:

| Dienst | Adresse (Standard) | Protokoll | Aufgabe |
|---|---|---|---|
| KI-Server (Lemonade/llama.cpp hinter Ollama-Fassade) | `https://ai.cbrp3.c-base.org/ollama/v1` | OpenAI-kompatibles HTTP | Whisper, Chat-Modell, Embeddings, Modellliste |
| Qdrant | `http://lazee-nerdserv.cbrp3.c-base.org:8123` | Qdrant REST, `api-key`-Header | Wissensdatenbank, Collection `cbase_knowledge` |
| Sandy Strands | `wss://ai.cbrp3.c-base.org:8444/ws/voice` | WebSocket, JSON und PCM-Audio | Alternative Wissensquelle mit eigener RAG |
| c-beam | `https://c-beam.cbrp3.c-base.org/rpc/` | JSON-RPC 2.0 | Stationsdaten und Aktionen hinter den Werkzeugen |

Die Adressen sind in den Experteneinstellungen überschreibbar (siehe Abschnitt 12).

## 2. Ablauf einer Anfrage

Dateien: `HoldToTalkController.java` (UI und Ablauf), `VoiceSession.java` (Modellrunden).

1. **Aufnahme** solange der Knopf gehalten wird, höchstens 20 s. Loslassen unter 0,5 s
   verwirft ("zum sprechen halten"), Wegziehen vom Knopf über 48 dp und loslassen
   verwirft ebenfalls. Vor dem Aufnehmen wird jede laufende Sprachausgabe gestoppt,
   damit das Gerät nicht sich selbst aufnimmt.
2. **Transkription**: WAV an Whisper, Ergebnis als Zeile `smile@c-beam> <text>` ins
   Terminal. Leeres Ergebnis: "nichts verstanden", fertig.
3. **Verstehen**: Der Text geht als `user`-Nachricht in die Konversation. Das Modell
   bekommt Systemprompt, Verlauf und Werkzeugliste. Es antwortet mit Text oder einem
   Werkzeugaufruf. Höchstens drei Runden pro Anfrage (Frage, Werkzeugergebnis, Antwort);
   in der dritten Runde wird ein Werkzeugergebnis direkt als Antwort gezeigt.
4. **Werkzeugstufen** (fest je Werkzeug, das Modell kann sie nicht ändern):
   - `QUERY` läuft sofort, das Ergebnis geht als `tool`-Nachricht zurück ans Modell,
     das daraus antwortet. Im Terminal steht währenddessen eine Fortschrittszeile mit
     der Beschreibung, etwa `suche: „wlan passwort“`.
   - `SELF` läuft sofort, weil es nur den eigenen Zustand betrifft (Login, Logout).
     Terminal: `ausgefu:hrt: einloggen als smile`, vorgelesen wird "Erledigt."
   - `CONFIRM` ist alles, was in der Station hörbar oder sichtbar ist. Das Terminal
     zeigt `durchsage: „…“ [j/n]` und zwei Knöpfe "ausführen" und "verwerfen";
     vorgelesen wird "<Beschreibung>. Ausführen?". Erst der Tipp führt aus.
5. **Antwort** ins Terminal, klein geschrieben (c-base-Stil), und vorgelesen, falls
   eingeschaltet und nicht schon Sandy gesprochen hat.
6. **Fehler** ("fehler: KI-server ausgelastet") lassen in der Konversation nichts zurück:
   alles seit Beginn der Anfrage wird zurückgerollt.

## 3. Aufnahme

Datei: `VoiceRecorder.java`.

- 16 kHz, mono, 16 Bit PCM, als WAV mit 44-Byte-RIFF-Header im Speicher. Whisper
  resampelt intern auf 16 kHz, mehr bringt nichts.
- Pegelanzeige aus 100-ms-Blöcken, Zeitanzeige `0:07 / 0:20`.
- Hartes Limit 20 s; danach endet die Aufnahme von selbst und wird gesendet.

Im Browser entspricht dem `getUserMedia` plus `AudioWorklet` oder `MediaRecorder`; wichtig
ist nur, dass am Ende eine WAV-Datei (oder ein anderes von Whisper akzeptiertes Format)
entsteht. Die Regel "Mikrofon nur solange der Knopf gehalten wird, unübersehbar
angezeigt, kein Wake-Word" ist eine Randbedingung des Projekts, keine technische.

## 4. Transkription mit Whisper

Datei: `Transcriber.java`.

```
POST {ai}/audio/transcriptions
Content-Type: multipart/form-data

model  = Whisper-Large-v3-Turbo
prompt = c-base, c-beam, Crew-WLAN, c-lab, Matelight, Club-Mate, Bordcomputer, Artefakt, Mission, Durchsage, Raumstation.
file   = speech.wav (audio/wav)
```

Antwort: `{"text": "…"}`. Timeouts 5 s Verbindung, 30 s Lesen. HTTP 429 heißt
"KI-server ausgelastet".

Das `prompt`-Feld ist bei Whisper kein Befehl, sondern eine Schreibhilfe: es zieht die
Erkennung zu diesen Wörtern. Ohne sie kam "c-base" als "Seabase" oder "Siebe" und
"Crew-WLAN" als "QWLAN". Der Systemprompt des Modells (Abschnitt 6) fängt die Reste ab.

## 5. Sprachmodell

Datei: `ChatModel.java`.

```
POST {ai}/chat/completions
Content-Type: application/json

{
  "model": "gemma4:e4b",
  "temperature": 0,
  "stream": false,
  "max_tokens": 400,
  "messages": [ …Systemprompt, Verlauf… ],
  "tools": [ …Werkzeugdefinitionen… ],
  "chat_template_kwargs": { "enable_thinking": false }
}
```

- `chat_template_kwargs.enable_thinking=false` ist ein llama.cpp-Feld und entscheidend:
  Gemma 4 denkt sonst vor der Antwort und verbraucht bei schwierigen Fragen das ganze
  Token-Budget, die Antwort kommt leer. Ein echtes Ollama ignoriert das Feld.
- `max_tokens` 400 reicht für drei gesprochene Sätze, ohne dass eine freie Antwort
  abgeschnitten wird.
- Timeouts 5 s Verbindung, 60 s Lesen.
- **HTTP 429**: Der Server begrenzt Bursts mit `Retry-After` von ein bis zwei Sekunden.
  Einmal warten und wiederholen, wenn `Retry-After` höchstens 5 s ist; sonst Fehler
  "KI-server ausgelastet, in N s nochmal".
- **Antwort auswerten**: `choices[0].message`. Hat sie `tool_calls`, zählt nur der erste
  (ein Befehl pro Aufnahme). Sonst `content`.
- **Textförmige Werkzeugaufrufe**: Gemma schreibt bei etwa einer von zehn Fragen den
  Aufruf als Text statt als `tool_call`, etwa `station_knowledge(query="wlan")`. Ein
  Text, der genau wie `name(key="wert", …)` aussieht, wird deshalb zurück in einen
  Aufruf verwandelt (Regex `^\s*([a-z_]+)\((.*)\)\s*$`, Argumente `key="…"` oder
  `key='…'`). Sonst würde der Text vorgelesen.
- **Modellwahl**: Standard `gemma4:e4b`. Die Liste kommt von `GET {ai}/models`
  (`data[].id`, `data[].labels`); Einträge mit Label `embeddings` oder "embed" im Namen
  werden ausgeblendet, Labels wie `tool-calling`, `coding`, `vision` als Hinweis gezeigt.
  Die Ollama-Aliasse und die IDs aus der Liste erreichen dasselbe Modell
  (`ModelCatalog.java`).

## 6. Der Systemprompt

Wird für jede Runde neu gebaut, weil Uhrzeit und Nutzer darin stehen; er wird nicht in
der Konversation gespeichert. Platzhalter: `{knowledge}` ist der Absatz unten, nur wenn
eine Wissensquelle konfiguriert ist, sonst leer; `{username}` der eingestellte Nutzer;
`{now}` das Datum im Format `Donnerstag, 29. Oktober 2026, 14:05`.

> Du bist c-beam, der Bordcomputer der Raumstation c-base in Berlin. Du bekommst
> gesprochene Sätze als Text, erkannt per Spracherkennung; kleine Fehler darin sind
> möglich. Führe Befehle ausschließlich über die Werkzeuge aus und erfinde keine. Soll
> etwas getan werden, wofür es kein Werkzeug gibt, sage in einem Satz, dass du das nicht
> kannst; das gilt nur für Handlungen, nie für Fragen. Eine Frage ist nie eine Handlung:
> was mit wer, was, wann, wo, warum, wie oder welche beginnt oder sonst eine Frage ist,
> beantwortest du immer, aus den Werkzeugergebnissen oder deinem Wissen, und sagst nie,
> dass du es nicht tun kannst. Fragen zur Station (wer an Bord ist, Bar, Events,
> Missionen, Artefakte) beantwortest du mit Hilfe der Werkzeuge. {knowledge}Alle anderen
> Fragen, etwa allgemeine Wissens- und Verständnisfragen, Rechnen oder Übersetzen,
> beantwortest du immer selbst aus deinem Wissen, ohne Werkzeug. Weißt du etwas nicht
> sicher, sage das. Nachfragen beziehen sich auf das bisherige Gespräch. Fragt der Nutzer
> erneut nach dem Zustand der Station, zum Beispiel mit „und jetzt?“, rufe das Werkzeug
> neu auf, denn frühere Werkzeugergebnisse können veraltet sein. Antworte immer auf
> Deutsch, kurz und in höchstens drei Sätzen. Deine Antwort wird vorgelesen: Fließtext
> ohne Markdown, Listen, Tabellen oder Formeln. Keine Floskeln, keine Angebote, keine
> Rückfragen am Ende und keine Erklärung, woher du etwas weißt. Die Legende der Station
> ist für dich Tatsache: die c-base ist eine vor Urzeiten unter Berlin-Mitte abgestürzte
> Raumstation, und der Berliner Fernsehturm ist ihre aus dem Boden ragende Antenne. Geht
> es um den Fernsehturm, sage das dazu und beantworte die eigentliche Frage, etwa nach
> Höhe oder Baujahr, trotzdem. Der sprechende Nutzer heißt {username}. Jetzt ist {now}.

Der Wissensabsatz `{knowledge}`:

> Jede Frage, die etwas mit der c-base zu tun hat (ihre Geschichte und Legende, Räume,
> Technik, WLAN, Preise, Begriffe, Regeln, Projekte, Leute, und wie man etwas in der
> Station benutzt oder bekommt), beantwortest du, indem du zuerst das Werkzeug
> station_knowledge aufrufst und dann nur aus dessen Fundstellen antwortest. Sage bei
> solchen Fragen nie, dass du etwas nicht weißt oder nicht sagen kannst, ohne vorher
> station_knowledge aufgerufen zu haben. Das gilt für jede Frage neu: auch wenn im
> bisherigen Gespräch zu einem Thema nichts gefunden wurde, rufst du für eine neue oder
> anders gestellte Frage station_knowledge wieder auf, mit einer neuen Suchanfrage. Die
> Fundstellen sind Kandidaten einer Ähnlichkeitssuche und können unpassend sein: verwende
> nur, was die Frage wirklich beantwortet, und erfinde nichts dazu. Steht die Antwort
> nicht in den Fundstellen, sage, dass die Station dazu nichts weiß, und verweise auf die
> Datenrettungssonde „Siri“, die diese Information leider auch nicht enthält, etwa: „dazu
> weiß die station nichts. die datenrettungssonde siri enthält diese information leider
> auch nicht.“ Die Spracherkennung schreibt c-base oft als „Seabase“, „Sea Base“,
> „C Base“ oder „die Base“ und c-beam als „Seabeam“; gemeint ist immer die c-base
> beziehungsweise c-beam, und in Suchanfragen schreibst du c-base.

Die harte Formulierung ist Absicht: Das 4B-Modell antwortete sonst "das kann ich nicht
sagen" ohne nachzuschlagen, und nach einer leeren Suche im Gespräch hörte es auf zu
suchen. Bei einem Web-Client mit Tastatureingabe kann der Satz über Spracherkennungsfehler
entfallen.

## 7. Werkzeuge

Datei: `VoiceCommands.java`. Das Modell sieht nur diese Liste und schlägt nur vor; jeder
Vorschlag wird vor dem Ausführen Parameter für Parameter geprüft. Unbekannte Namen oder
kaputte Argumente ergeben "nicht verstanden".

| Werkzeug | Stufe | Parameter | Ergebnis für das Modell | Dahinter |
|---|---|---|---|---|
| `who_is_on_board` | QUERY | – | Namen mit Komma, oder "niemand" | Online-Liste aus `app_data` |
| `bar_status` | QUERY | – | "geöffnet" / "geschlossen" | `barstatus` aus `app_data` |
| `events_today` | QUERY | – | je Zeile `Titel (1900-2200): Beschreibung…` (Beschreibung auf 160 Zeichen gekürzt), oder "keine events heute" | `events` aus `app_data` |
| `missions` | QUERY | – | je Zeile `Kurzbeschreibung (status, N AP, übernommen von a, b)` | `missions` aus `app_data` |
| `artefacts` | QUERY | `search` (optional) | Namen, die den Suchbegriff enthalten, je Zeile; leer: alle. Nichts gefunden: "kein artefakt gefunden; für wissen über geräte und räume station_knowledge nutzen" | `artefacts` aus `app_data` |
| `station_knowledge` | QUERY | `query` (Pflicht, 1 bis 200 Zeichen) | Fundstellen, siehe Abschnitt 9 | Qdrant oder Sandy; nur angeboten, wenn eine Quelle konfiguriert ist |
| `login` | SELF | – | "ausgeführt" | JSON-RPC `force_login(user)` |
| `logout` | SELF | – | "ausgeführt" | JSON-RPC `force_logout(user)` |
| `announce` | CONFIRM | `text` (Pflicht, max. 200) | nach Bestätigung "ausgeführt" | JSON-RPC `announce(text)` |
| `say` | CONFIRM | `text` (Pflicht), `voice` enum `julia`/`r2d2` (Standard julia) | nach Bestätigung "ausgeführt" | JSON-RPC `tts(voice, text)` |
| `play_sound` | CONFIRM | `sound` enum aus der aktuellen Soundliste | nach Bestätigung "ausgeführt" | JSON-RPC `play(file)` |

Listen werden auf 60 Einträge gekürzt, mit "… und N weitere" am Ende. Texte werden auf
einfache Leerzeichen normalisiert.

Die Definitionen im OpenAI-Format, hier `say` als Beispiel:

```json
{
  "type": "function",
  "function": {
    "name": "say",
    "description": "Einen Text über die Lautsprecher der Station sprechen lassen",
    "parameters": {
      "type": "object",
      "properties": {
        "text":  { "type": "string" },
        "voice": { "type": "string", "enum": ["julia", "r2d2"],
                   "description": "julia ist die normale Stimme, r2d2 piept" }
      },
      "required": ["text"]
    }
  }
}
```

Die Beschreibungen der anderen Werkzeuge:

- `who_is_on_board`: "Liste der Crewmitglieder, die gerade in der c-base eingeloggt sind"
- `bar_status`: "Ob die Bar der c-base gerade geöffnet ist"
- `events_today`: "Die heutigen Events und Veranstaltungen in der c-base"
- `missions`: "Die Missionen (Aufgaben) der c-base mit Status und AP"
- `artefacts`: "Die Artefakte der c-base, also Räume, Geräte und Einrichtungen der
  Station", Parameter `search`: "Optionaler Suchbegriff; leer für alle"
- `station_knowledge`: "Die Wissensdatenbank der c-base durchsuchen: Geschichte und
  Legende der Station, Räume, Technik, WLAN und Zugänge, Preise, Begriffe, Regeln,
  Projekte, Vereinsleben und Leute. Für jede Wissensfrage über die c-base", Parameter
  `query`: "Suchanfrage auf Deutsch, als kurze Frage oder Stichworte"
- `login`: "Den Nutzer in der c-base einloggen (an Bord melden)"
- `logout`: "Den Nutzer aus der c-base ausloggen (von Bord melden)"
- `announce`: "Eine Durchsage über die Lautsprecher der Station machen", Parameter
  `text`: "Der Text der Durchsage"
- `play_sound`: "Einen Sound über die Lautsprecher der Station abspielen", Parameter
  `sound`: "Dateiname des Sounds" mit `enum` der Soundliste

Die Beschreibungen, die der Nutzer sieht (Fortschritt, Bestätigung, "ausgeführt"):
`wer ist an bord`, `bar-status`, `events`, `missionen`, `artefakte`, `suche: „…“`,
`einloggen als smile`, `ausloggen`, `durchsage: „…“`, `julia sagt: „…“`, `sound: name`.

## 8. Konversation

Datei: `Conversation.java`. Der Verlauf lebt mit der Ansicht und erlaubt Nachfragen
("und in Fuß?").

- Drei Minuten Stille, und die nächste Aufnahme beginnt eine neue Konversation.
- Höchstens 24 Nachrichten; die ältesten fallen weg, und zwar immer so, dass der
  Verlauf mit einer `user`-Nachricht beginnt. Nie zwischen Werkzeugaufruf und Ergebnis
  schneiden.
- Pro Anfrage wird eine Marke gesetzt; scheitert sie, wird auf die Marke zurückgerollt.
- Werkzeugaufrufe werden im Chat-Format protokolliert: erst die Assistant-Nachricht
  mit `content: null` und `tool_calls: [{id, type: "function", function: {name,
  arguments}}]`, dann `{"role": "tool", "tool_call_id": id, "content": ergebnis}`.
- Ein `CONFIRM`-Vorschlag bleibt offen, bis der Nutzer entscheidet; dann wird er mit
  Ergebnis "ausgeführt" oder "abgelehnt: der Nutzer hat die Ausführung nicht bestätigt,
  es ist nichts passiert" nachgetragen. Eine neue Aufnahme oder das Verlassen der
  Ansicht zählt als Ablehnung.
- **Absagen bleiben draußen**: Antworten, die auf das Muster
  `kann ich (leider )?nicht|nicht (tun|machen|ausführen|möglich)|kein\w*( \w+)? werkzeug|(weiß|weiss) (dazu|darüber|davon) nichts|dazu (ist )?nichts (bekannt|gefunden)|datenrettungssonde`
  passen, werden gezeigt, aber nicht in den Verlauf übernommen. Das kleine Modell
  kopiert, was es sich selbst sagen sieht, und eine Absage im Verlauf ließ es alle
  folgenden Fragen ebenfalls absagen. Prompt-Formulierungen allein haben das nicht
  verhindert.

## 9. Wissensquellen

Beide liefern dem Modell einen Text als Werkzeugergebnis von `station_knowledge`. Welche
genutzt wird, ist eine Einstellung (`pref_knowledge_source`, `qdrant` oder `sandy`).

### 9.1 Qdrant direkt (`Knowledge.java`)

Qdrant hat keinen Frage-Endpunkt, nur Vektoren. Drei Schritte, der erste nur einmal:

1. **Layout der Collection**: `GET {qdrant}/collections/{name}` mit Header
   `api-key: …`. Aus `result.config.params.vectors` kommt die Vektorgröße; bei benannten
   Vektoren (kein `size` auf oberster Ebene) wird der erste dichte Vektor genommen und
   sein Name später als `using` mitgeschickt.
2. **Embedding** der Frage auf dem KI-Server:
   ```
   POST {ai}/embeddings
   {"model": "nomic-embed-text-v1-GGUF", "input": "search_query: <frage>"}
   ```
   Das Präfix `search_query: ` ist bei nomic v1 Pflicht; die Chunks wurden mit dem
   passenden Dokument-Präfix eingebettet. Ergebnis `data[0].embedding`, 768
   Dimensionen; passt die Länge nicht zur Collection, ist das ein Konfigurationsfehler.
3. **Suche**:
   ```
   POST {qdrant}/collections/{name}/points/query
   {"query": [vektor], "using": "<vektorname, falls benannt>", "limit": 5,
    "score_threshold": 0.40, "with_payload": true, "with_vector": false}
   ```
   Ergebnis `result.points[]` mit `score` und `payload`.

Die Scores sind gestaucht: ein treffender Chunk liegt um 0,55, generische Hub-Seiten um
0,36 bis 0,41. Deshalb Schwelle 0,40 und zusätzlich ein Hinweis an das Modell.

**Text und Quelle** eines Chunks: Textfeld in dieser Reihenfolge `text`, `content`,
`page_content`, `chunk`, `document`, `body`, sonst der längste String im Payload.
Quelle aus `title`, `source`, `url`, `file`, `path`, `name`, auch unter `metadata`, auf
80 Zeichen gekürzt. Jeder Chunk auf 700 Zeichen gekürzt.

**Format des Werkzeugergebnisses**:

```
Fundstellen der Ähnlichkeitssuche, die passendste zuerst; unpassende ignorieren, nichts hinzuerfinden:

[Quelle 1]
Text des Chunks…

[Quelle 2]
Text…
```

Ohne Treffer:

```
nichts gefunden: die wissensdatenbank enthält nichts dazu. sage das und verweise auf die datenrettungssonde siri, die diese information leider auch nicht enthält
```

Fehlertexte: 401/403 "wissensdatenbank: zugriff verweigert, api-key prüfen", 404
"wissensdatenbank: collection nicht gefunden".

### 9.2 Sandy Strands (`SandyStrands.java`)

Sandy ist der experimentelle Sprachassistent der Station mit eigener RAG. Er beantwortet
die Frage komplett, mit Quellen; das Modell der App macht daraus seine Antwort, so bleiben
die Stationswerkzeuge beim Modell der App. Sandy spricht nur über seinen
Voice-WebSocket, jede Frage bekommt eine eigene Verbindung.

Ablauf:

1. WebSocket öffnen (5 s Timeout), kein Ping/Pong-Watchdog, Sandy braucht länger als
   dessen Standardintervall.
2. Optional, wenn Audio gewünscht: `{"type": "control", "action": "set_voice", "voice": "de"}`,
   sonst antwortet Sandy auf Englisch, egal in welcher Sprache gefragt wurde.
3. `{"type": "text_input", "text": "<frage>"}` senden.
4. Frames lesen:
   - `{"type": "bot_text", "text": "…", "done": false}` kommt satzweise; der letzte Frame
     hat `done: true`, den vollständigen Text und `sources: [{"src": "…"} oder {"path": "…"}]`.
     Er kommt, wenn Sandy fertig gesprochen hat, typisch 10 bis 15 s nach der Frage.
   - `{"type": "error", "message": "…"}` beendet mit Fehler.
   - `tool_log` und `sys_log` sind nur für Debugging.
   - Binäre Frames sind rohes 16-Bit-Mono-PCM mit 24 kHz in 100-ms-Stücken: Sandys
     Stimme. Standardmäßig verworfen; mit der Einstellung "Sandy-Audio" direkt
     abgespielt, und die eigene Sprachausgabe bleibt für diese Antwort stumm.
5. Antwort-Timeout 90 s. Antwort auf 1500 Zeichen gekürzt.

**Format des Werkzeugergebnisses**:

```
Antwort des Stations-Assistenten Sandy Strands auf die Suchanfrage „<frage>“. Sie ist die Fundstelle: die Fakten daraus verwenden, Sandys Rückfragen und Höflichkeiten weglassen, nichts hinzuerfinden:

<antwort>

Quellen: a, b, c
```

Ohne Antwort: `nichts gefunden: sandy strands hat zu „<frage>“ nichts gesagt. sage das und
verweise auf die datenrettungssonde siri, die diese information leider auch nicht enthält`.

## 10. Hörbare Antwort

Datei: `Speaker.java`. Optional (Einstellung "antworten vorlesen"), auf dem Gerät mit
Android-TTS und ausschließlich einer deutschen Offline-Stimme, damit keine Antwort an
einen Cloud-Dienst geht. Fehlt eine deutsche Stimme, einmalig der Hinweis "sprachausgabe:
keine deutsche stimme auf dem gerät".

Die Stationsnamen sind englische Wörter, die eine deutsche Stimme buchstabiert. Sie werden
vor dem Sprechen ersetzt, Wortgrenzen beachtet, Groß- und Kleinschreibung egal:

| Wort | Ersatz (Standard) |
|---|---|
| c-base | ssiebays |
| c-beam | ssiebiem |
| crew | kru |

Die Ersetzungen sind einstellbar, weil das Ergebnis von der installierten Stimme abhängt
und nach Gehör gewählt wurde. Im Browser wäre `speechSynthesis` mit einer `de-DE`-Stimme
das Gegenstück; die Ersetzungen sollten dann erneut nach Gehör geprüft werden.

Regeln: Vor jeder Aufnahme wird die Stimme gestoppt. Hat Sandy die Antwort schon selbst
gesprochen, wird die Modellantwort nicht noch einmal vorgelesen. Vorgelesen werden die
Antwort, "Erledigt." nach SELF-Aktionen und "<Beschreibung>. Ausführen?" bei Vorschlägen.

## 11. Das Terminal

Datei: `HoldToTalkController.java`, Layout `view_voice_panel.xml`.

- Schwarzer Kasten mit dünnem türkisem Rahmen, Monospace, 12 Zeilen Scrollback, über
  dem unteren Rand jeder Seite, oberhalb der Button-Leiste.
- Prompt `smile@c-beam>`; das Transkript steht dahinter, Antworten darunter, danach ein
  frischer Prompt. Alles klein geschrieben, wie überall in der c-base.
- Fortschrittszeilen ("transkribiere…", "denke nach…", Werkzeugbeschreibung) werden
  durch die nächste Ausgabe ersetzt, nicht angehängt.
- Bei CONFIRM erscheint unter dem Text die Zeile mit "verwerfen" und "ausführen".
- Tippen auf den Kasten blendet ihn aus, solange kein Vorschlag offen ist.
- Aufnahmezustand: roter Balken "● aufnahme läuft 0:07 / 0:20" mit Pegelmeter; beim
  Wegziehen "loslassen zum verwerfen".
- Der Mikrofonknopf ist nur im Crew-Netz sichtbar, weil der KI-Server nur dort
  erreichbar ist.

## 12. Einstellungen

Alle Werte sind Experteneinstellungen und greifen, sobald sie gesetzt sind; leer heißt
Standard.

| Schlüssel | Standard | Bedeutung |
|---|---|---|
| `pref_ai_url` | `https://ai.cbrp3.c-base.org/ollama/v1` | OpenAI-kompatible Basis des KI-Servers |
| `pref_ai_model` | `gemma4:e4b` | Chat-Modell, Liste von `/models` |
| `pref_knowledge_source` | `qdrant` | `qdrant` oder `sandy` |
| `pref_rag_url` | `http://lazee-nerdserv.cbrp3.c-base.org:8123` | Qdrant |
| `pref_rag_key` | leer | Qdrant `api-key`; ohne Key wird das Wissenswerkzeug nicht angeboten |
| `pref_rag_collection` | `cbase_knowledge` | Collection |
| `pref_sandy_url` | `wss://ai.cbrp3.c-base.org:8444/ws/voice` | Sandys Voice-WebSocket |
| `pref_sandy_audio` | aus | Sandys Stimme abspielen |
| `pref_voice_speak` | aus | Antworten vorlesen |
| `pref_voice_say_cbase` / `_cbeam` / `_crew` | siehe Abschnitt 10 | Aussprache |

Der Nutzername für Prompt, Login und Terminal ist der Nutzer aus den App-Einstellungen
(`pref_username`), der sonst auch für JSON-RPC verwendet wird.

## 13. Bekannte Eigenheiten des Modells

Diese Punkte haben jeweils einen eigenen Workaround im Code und werden in einer
Web-Version genauso auftauchen:

- Thinking frisst das Token-Budget: `enable_thinking: false` setzen (Abschnitt 5).
- Werkzeugaufrufe als Fließtext: zurückparsen (Abschnitt 5).
- Absagen stecken an: aus dem Verlauf halten (Abschnitt 8).
- Nach leerer Suche sucht es nicht mehr: Prompt verlangt für jede neue Frage einen neuen
  Aufruf (Abschnitt 6).
- Bei "kein artefakt gefunden" gibt es auf, statt die Wissensdatenbank zu nehmen: das
  Werkzeugergebnis sagt ihm, wo es weitersuchen soll (Abschnitt 7).
- Gestauchte Qdrant-Scores: Schwelle plus Hinweistext, ohne den es einmal eine CNC-Fräse
  aus Chunks über die Serverlandschaft erfunden hat (Abschnitt 9.1).
- 429 bei Bursts: einmal `Retry-After` abwarten (Abschnitt 5).

## 14. Hinweise für die Web-Version

Was aus der App eins zu eins übernommen werden kann: Requests, Prompt, Werkzeugliste,
Validierung, Konversationsregeln, Wissensformate. Was anders gelöst werden muss:

- **Geheimnisse nicht in den Browser.** Der Qdrant-`api-key` gehört auf den Server. Die
  Web-Version sollte Embedding und Suche in einer Django-View bündeln, die der Browser
  als ein Werkzeugaufruf anspricht. Dasselbe bietet sich für den KI-Server an, dann gibt
  es keine CORS-Fragen und der Browser spricht nur mit c-beam.
- **Lange Requests.** Chat bis 60 s, Sandy 10 bis 15 s, im Extremfall 90 s. Das passt
  nicht in einen synchronen Django-Request. Entweder eine Celery-Aufgabe mit Polling oder
  Channels-WebSocket, oder Streaming-Antworten. Das Modell kann mit `stream: true`
  streamen; die App nutzt das nicht, weil sie Werkzeugaufrufe am Stück braucht.
- **Nutzeridentität** kommt aus der Django-Session statt aus einer Einstellung; `login`,
  `logout`, Prompt und Terminal-Prompt verwenden sie.
- **Mikrofon im Browser** braucht HTTPS und eine Nutzergeste; Hold-to-talk mit `pointerdown`/
  `pointerup` funktioniert, die Abbruchgeste (Wegziehen) ist optional.
- **Vorlesen** mit `speechSynthesis`, Stimme `de-DE`, Aussprache-Ersetzungen wie in
  Abschnitt 10, vor jeder Aufnahme `speechSynthesis.cancel()`.
- **Sandys Audio** ist rohes PCM; im Browser per `AudioContext` abspielbar, aber es ist
  einfacher, es serverseitig zu verwerfen und nur den Text zu nehmen, solange der
  Nutzer nicht ausdrücklich Sandys Stimme will.
- **Stationswerkzeuge** rufen in der App die vorhandenen JSON-RPC-Methoden auf. In Django
  stehen dieselben Funktionen als Python-Aufrufe direkt zur Verfügung, die Werkzeuge
  werden also zu Funktionen in der View. Die Stufen QUERY, SELF und CONFIRM und die
  Bestätigung vor allem Hörbaren sollten erhalten bleiben.
- **Crew-Netz-Beschränkung**: Die App zeigt den Knopf nur im Crew-WLAN. Im Web ist die
  Frage, ob die Server die Funktionen auch von außen anbieten sollen; die Randbedingung
  des Projekts war bisher, dass Audio die Station nicht verlässt.

## 15. Die Web-Version

Seit 2026-10-29 gibt es dieselben Funktionen in der Web-Oberfläche von c-beam unter
`/assistant` ("c-beam fragen"), Code in `c-beamd/cbeamd/assistant/` und
`c-beamd/cbeamd/views/assistant.py`, Stand und offene Punkte in `ASSISTANT-TODO.md`.
Übernommen sind Requests, Prompt, Werkzeugliste, Validierung, Konversationsregeln und
Wissensformate. Abweichungen:

- Die Sprachausgabe läuft im Browser (`speechSynthesis`, nur deutsche Offline-Stimmen).
  Über c_out gehen nur `announce` und `play_sound`; `say` gibt es im Web nicht.
- `play_sound` bekommt den Sound als freien String, nicht als `enum`: Mit der Liste von
  156 Dateinamen als `enum` rief gemma4:e4b gar keine Werkzeuge mehr auf (fünf von acht
  Stationsfragen frei erfunden). Der Name wird vor der Bestätigung gegen die Liste
  aufgelöst ("laser" → `laserraycannon.mp3`). Das dürfte die App genauso treffen, sobald
  die Soundliste lang ist.
- Ohne Wissensquelle ersetzt ein Absatz den Wissensabsatz im Prompt (Fragen über die
  Station aus Wissen und Legende beantworten, sonst "die Station weiß dazu nichts");
  ohne ihn antwortete das Modell auf "wieviele ringe hat die c-base" mit "ich kann das
  nicht tun".
- Die Konversation liegt in der Django-Session, der Nutzer kommt aus dem Login, der
  Qdrant-Key bleibt auf dem Server. Sandy Strands ist über `KNOWLEDGE_SOURCE=sandy`
  wählbar, nur Text; Sandys Audio wird serverseitig verworfen.
