# KI-Assistent in der Web-Oberfläche: Checkliste

Stand 2026-10-29. Vorlage ist `AI-ASSISTANT.md` (die Android-App). Die Schritte sind so
geschnitten, dass nach jedem ein lauffähiger Zwischenstand existiert und die Tests grün
bleiben (`make test`).

Grundentscheidungen:

- Der Browser spricht nur mit c-beam. KI-Server und Qdrant werden von Django angesprochen,
  der Qdrant-Key bleibt in der `.env`.
- **Sprachausgabe läuft lokal im Browser** (`speechSynthesis`), wie in der App auf dem
  Gerät. `c_out` / `cbeamd/views/audio.py` ist für die Stationslautsprecher und wird nur von
  den Werkzeugen `announce` und `play_sound` benutzt. Das Werkzeug `say` aus der App
  entfällt.
- Keine Celery- oder Channels-Infrastruktur: synchrone Views, Konversation in der Session.
  Der gthread-Worker von gunicorn verträgt die langen Requests.
- Erste Version als eigene Seite `/assistant`; ein Panel auf allen Seiten kommt später.
- Lokaler Test: Dev-Server mit `MQTT_ENABLED=False DEBUG=True` und Nutzer in der
  SQLite-DB; KI-Server und shout sind von außerhalb des Containers erreichbar. Der
  Dev-Lauf publiziert nichts per MQTT, `announce` erreicht shout aber direkt, deshalb
  Durchsagen beim Testen verwerfen.

## 0. Vorbereitung

- [ ] Timeout des Reverse-Proxys vor c-beam prüfen: mindestens 90 s für `/assistant/`.
- [ ] Prüfen, dass der c-beam-Container `https://ai.cbrp3.c-base.org/ollama/v1` und
      `http://lazee-nerdserv.cbrp3.c-base.org:8123` erreicht (Compose läuft mit
      `network_mode: host`, sollte also gehen).
- [x] Qdrant-`api-key` besorgen und in die `.env` eintragen (nicht ins Repo). Suche gegen
      die echte Collection geprüft am 2026-10-29 (768 Dimensionen, unbenannter Vektor).

## 1. Konfiguration und Modellclient

- [x] `cbeamdcfg.py`: `AI_URL`, `AI_MODEL` (Standard `gemma4:e4b`), `AI_WHISPER_MODEL`
      (`Whisper-Large-v3-Turbo`), `AI_EMBED_MODEL` (`nomic-embed-text-v1-GGUF`),
      `AI_CONNECT_TIMEOUT` 5, `AI_READ_TIMEOUT` 60, `RAG_URL`, `RAG_KEY`,
      `RAG_COLLECTION` (`cbase_knowledge`), `SANDY_URL`. Leer heißt aus.
- [x] `.env.example` um die Schlüssel ergänzen, mit Kommentar.
- [x] Paket `cbeamd/assistant/` anlegen mit `chat.py` (Modellclient); `tools.py`,
      `prompt.py`, `conversation.py`, `knowledge.py` folgen in ihren Blöcken. Die Views
      kommen nach `cbeamd/views/assistant.py`.
- [x] `chat.py`: `POST {ai}/chat/completions` mit `temperature 0`, `stream false`,
      `max_tokens 400`, `chat_template_kwargs.enable_thinking false`, Timeouts 5/60 s.
- [x] HTTP 429: einmal `Retry-After` abwarten, wenn höchstens 5 s, sonst Fehler
      "KI-server ausgelastet, in N s nochmal".
- [x] Antwort auswerten: `choices[0].message`, nur der erste `tool_call` zählt, sonst
      `content`.
- [x] Textförmige Werkzeugaufrufe `name(key="wert")` per Regex
      `^\s*([a-z_]+)\((.*)\)\s*$` in einen Aufruf zurückverwandeln.
- [x] Tests mit gemocktem `requests.post` (`unittest.mock.patch`): normale Antwort,
      Tool-Call, textförmiger Tool-Call, 429 mit kurzem und langem Retry-After, Timeout.

## 2. Werkzeuge

- [x] `tools.py`: Registry mit Stufen `QUERY`, `SELF`, `CONFIRM`; je Werkzeug Definition im
      OpenAI-Format, Parameterprüfung, Nutzerbeschreibung (`wer ist an bord`, `suche: „…“`,
      `einloggen als smile`, `durchsage: „…“`) und Ausführungsfunktion. Unbekannter Name
      oder kaputte Argumente ergeben "nicht verstanden".
- [x] `who_is_on_board` (QUERY): Nutzer mit Status online aus `User.objects`, Namen mit
      Komma, sonst "niemand".
- [x] `bar_status` (QUERY): `get_barstatus` → "geöffnet" / "geschlossen".
- [x] `events_today` (QUERY): `event_list`, je Zeile `Titel (1900-2200): Beschreibung…`
      (160 Zeichen), sonst "keine events heute".
- [x] `missions` (QUERY): `Mission.objects`, je Zeile
      `Kurzbeschreibung (status, N AP, übernommen von a, b)`.
- [x] `artefacts` (QUERY, `search` optional): `artefact_list`, Treffer je Zeile; leer:
      "kein artefakt gefunden; für wissen über geräte und räume station_knowledge nutzen".
- [x] Listen auf 60 Einträge kürzen ("… und N weitere"), Texte auf einfache Leerzeichen
      normalisieren.
- [x] `login` / `logout` (SELF): `force_login` / `force_logout` mit
      `request.user.username`, Ergebnis "ausgeführt".
- [x] `announce` (CONFIRM, `text` max. 200): `announce(request, text)` aus `audio.py`,
      erst nach Bestätigung, Ergebnis "ausgeführt".
- [x] `play_sound` (CONFIRM, `sound` als freier String, **nicht** als `enum`): Mit der
      Liste von 156 Dateinamen als `enum` rief gemma4:e4b gar keine Werkzeuge mehr auf
      (fünf von acht Stationsfragen frei erfunden, geprüft am 2026-10-29). Der Name wird
      vor der Bestätigung gegen `sounds(request)` aufgelöst: exakt, ohne Endung, sonst
      Teilstring („laser“ → `laserraycannon.mp3`). Kein Treffer: "sound „x“ nicht
      gefunden". Liste eine Minute gecacht; leer heißt Werkzeug nicht angeboten.
- [x] `station_knowledge` (QUERY, `query` 1 bis 200 Zeichen) nur in die Werkzeugliste
      aufnehmen, wenn `RAG_URL` und `RAG_KEY` gesetzt sind (`knowledge.configured()`).
- [x] Tests je Werkzeug mit Datenbank-Fixtures, inklusive Validierung und Kürzung.

## 3. Systemprompt und Konversation

- [x] `prompt.py`: Prompt aus Abschnitt 6 der App-Doku, Platzhalter `{knowledge}`
      (nur mit Wissensquelle), `{username}`, `{now}` im Format
      `Donnerstag, 29. Oktober 2026, 14:05` in Europe/Berlin. Für jede Runde neu gebaut,
      nicht im Verlauf gespeichert.
- [x] Zwei Varianten: mit Spracherkennungs-Sätzen (Eingabe per Mikrofon) und ohne
      (Eingabe per Tastatur).
- [x] Ohne Wissensquelle ersetzt ein Absatz den Wissensabsatz: Fragen über die Station
      aus Wissen und Legende beantworten, sonst "die Station weiß dazu nichts". Ohne ihn
      antwortete das Modell auf "wieviele ringe hat die c-base" mit "ich kann das nicht
      tun" (geprüft am 2026-10-29).
- [x] `conversation.py`: Verlauf in `request.session` als Liste von Chat-Nachrichten.
      Höchstens 24 Nachrichten, ältere fallen so weg, dass der Verlauf mit einer
      `user`-Nachricht beginnt und nie zwischen `tool_calls` und `tool` geschnitten wird.
- [x] Drei Minuten ohne Anfrage: nächste Anfrage beginnt eine neue Konversation.
- [x] Marke pro Anfrage; bei Fehler Rollback auf die Marke.
- [x] Werkzeugaufrufe im Chat-Format protokollieren: Assistant-Nachricht mit
      `content: null` und `tool_calls`, dann `{"role": "tool", "tool_call_id", "content"}`.
- [x] Absagen (Regex aus Abschnitt 8) anzeigen, aber nicht in den Verlauf übernehmen.
- [x] Offener CONFIRM-Vorschlag in der Session; neue Anfrage oder Verwerfen trägt
      "abgelehnt: der Nutzer hat die Ausführung nicht bestätigt, es ist nichts passiert"
      nach.
- [x] Tests: Kürzung, Rollback, Timeout, Absage-Filter, offener Vorschlag.

## 4. Views und Seite

- [x] `POST /assistant/ask` (JSON `{text, voice: bool}`, `login_required`, CSRF):
      höchstens drei Runden (Frage, Werkzeugergebnis, Antwort); in der dritten Runde wird
      ein Werkzeugergebnis direkt als Antwort gezeigt. Antwort als JSON mit
      `lines` (Terminalzeilen), `answer`, `speak` (Text zum Vorlesen) und bei CONFIRM
      `confirm: {id, description}`.
- [x] `POST /assistant/confirm` (JSON `{id, accept}`): ausführen oder ablehnen, Ergebnis
      in den Verlauf, Antwort wie oben.
- [x] `GET /assistant`: Seite rendern, nur eingeloggt. Template steht mit Terminal-Kasten,
      Eingabezeile, Vorlese-Schalter und Mikrofonknopf (versteckt); `static/assistant.js`
      ist bis Block 6 ein Platzhalter. Ablaufsteuerung in `assistant/engine.py`.
- [x] Fehlertexte wie in der App: "fehler: KI-server ausgelastet", Timeout, "nicht
      verstanden"; in allen Fehlerfällen Rollback.
- [x] URLs in `cbeamd/urls.py`, Menüeintrag in `base.django` (zum Beispiel unter c-info
      als "c-beam fragen").
- [x] View-Tests über den Django-Testclient mit gemocktem Modell.

## 5. Wissensdatenbank (Qdrant)

- [x] `knowledge.py`: Collection-Layout einmal lesen (`GET /collections/{name}`,
      Header `api-key`), Vektorgröße und bei benannten Vektoren den Namen für `using`
      merken (Prozess-Cache).
- [x] Embedding: `POST {ai}/embeddings` mit `search_query: ` Präfix; Längenprüfung gegen
      die Collection.
- [x] Suche: `POST /collections/{name}/points/query`, `limit 5`, `score_threshold 0.40`,
      `with_payload true`.
- [x] Text und Quelle aus dem Payload in der Reihenfolge aus Abschnitt 9.1, Chunk auf
      700 Zeichen, Quelle auf 80 Zeichen.
- [x] Werkzeugergebnis-Format "Fundstellen der Ähnlichkeitssuche, …" und der
      Kein-Treffer-Text mit der Datenrettungssonde Siri.
- [x] Fehlertexte 401/403 "zugriff verweigert, api-key prüfen", 404 "collection nicht
      gefunden".
- [x] Tests mit gemocktem Qdrant und Embedding.

## 6. Terminal mit Texteingabe

- [x] Template `cbeamd/templates/cbeamd/assistant.django`: schwarzer Kasten, dünner
      türkiser Rahmen, Monospace, 12 Zeilen Scrollback, Prompt `<user>@c-beam>`, alles
      klein geschrieben. CSS an den bestehenden `.terminal`-Stil der Startseite anlehnen.
- [x] Eingabezeile direkt hinter dem Prompt, Enter sendet; während einer laufenden
      Anfrage gesperrt.
- [x] Reines JavaScript als statische Datei (`cbeamd/static/assistant.js`), kein
      React-Build. `fetch` mit CSRF-Token aus dem Cookie.
- [x] Fortschrittszeilen ("denke nach…", Werkzeugbeschreibung) werden durch die nächste
      Ausgabe ersetzt, nicht angehängt.
- [x] CONFIRM: Zeile `durchsage: „…“ [j/n]` beziehungsweise `sound: name [j/n]` mit
      Knöpfen "verwerfen" und "ausführen".
- [x] Fehler als Zeile `fehler: …`.
- [x] Pfeil hoch/runter blättert durch die gesendeten Eingaben (pro Tab in
      `sessionStorage`, 50 Einträge), Textauswahl im Kasten bleibt für Copy & Paste erhalten.
- [ ] Manuell im Browser gegen den echten KI-Server testen, auch Nachfragen
      ("und in Fuß?"). Stand 2026-10-29: der Ablauf (Bar, Crew, Events, Durchsage
      verwerfen, Sound ausführen, Rechnen mit Nachfrage) ist per curl gegen die
      JSON-Endpunkte und das echte Modell geprüft; das JavaScript ist nur
      syntaxgeprüft, der Klick-Test im Browser steht noch aus.

## 7. Vorlesen im Browser

- [x] Schalter "antworten vorlesen" auf der Seite, Zustand in `localStorage`, Standard aus.
- [x] `speechSynthesis` mit einer deutschen Stimme, die auf dem Gerät läuft
      (`localService`), wie in der App; fehlt eine, einmalig die Zeile
      "sprachausgabe: keine deutsche offline-stimme im browser".
- [x] Aussprache-Ersetzungen mit Wortgrenzen: c-base → ssiebays, c-beam → ssiebiem,
      crew → kru (Konstante `PRONUNCIATION` in `assistant.js`).
- [ ] Ersetzungen nach Gehör im Browser prüfen und anpassen.
- [x] Vorgelesen werden: Antwort, "Erledigt." nach SELF, "<Beschreibung>. Ausführen?"
      bei CONFIRM.
- [x] `speechSynthesis.cancel()` vor jeder Aufnahme und beim Verlassen der Seite.

## 8. Spracheingabe (Hold-to-talk)

- [x] `POST /assistant/transcribe`: WAV als multipart an `{ai}/audio/transcriptions` mit
      `model` und dem Schreibhilfe-`prompt` aus Abschnitt 4 durchreichen; Timeouts
      5/30 s; 429 → "KI-server ausgelastet"; leer → "nichts verstanden". Obergrenze für
      die Dateigröße (20 s bei 16 kHz mono 16 Bit sind rund 640 KB).
- [x] Browser: `getUserMedia` (16 kHz, mono), Aufnahme über `AudioWorklet` in PCM,
      WAV-Encoder mit 44-Byte-RIFF-Header in JavaScript. Die Browser-eigene
      `SpeechRecognition` wird nicht benutzt, weil sie Audio an einen Cloud-Dienst schickt.
- [x] Mikrofonknopf mit `pointerdown` / `pointerup` / `pointercancel`: unter 0,5 s
      verwerfen ("zum sprechen halten"), hartes Limit 20 s, danach automatisch senden.
- [x] Aufnahmezustand: roter Balken "● aufnahme läuft 0:07 / 0:20" mit Pegelmeter aus
      100-ms-Blöcken.
- [x] Transkript als Zeile `<user>@c-beam> <text>` ins Terminal, dann `ask` mit
      `voice: true` (Prompt-Variante mit Spracherkennungs-Sätzen).
- [x] Knopf nur zeigen, wenn `navigator.mediaDevices.getUserMedia` verfügbar ist
      (HTTPS oder localhost); sonst Hinweis.
- [ ] Auf Handy und Desktop ausprobieren (Touch, Maus, Berechtigungsdialog). Stand
      2026-10-29: der Endpunkt ist mit einer espeak-ng-Aufnahme gegen das echte Whisper
      geprüft ("Wer ist gerade in der C-base an Bord?" kam wörtlich zurück); die
      Aufnahme im Browser (`assistant-worklet.js`, WAV-Encoder) ist nur syntaxgeprüft.

## 9. Abschluss

- [x] `README.md`: Abschnitt zum Assistenten mit Konfiguration und Hinweis, dass die
      KI-Dienste nur aus dem Crew-Netz erreichbar sind.
- [x] `AI-ASSISTANT.md`: Abschnitt 15 mit der Web-Version und den Abweichungen (lokales
      Vorlesen, `announce` und `play_sound` über c_out, Sound als freier String,
      Prompt-Absatz ohne Wissensquelle).
- [x] `make test` grün, Commit (292 Tests am 2026-10-29).

## 10. Später, nicht für die erste Version

- [ ] Sandy Strands als zweite Wissensquelle (`websocket-client`-Abhängigkeit, 90 s
      Antwortzeit, nur Text, Audio serverseitig verwerfen).
- [ ] Modellwahl aus `GET {ai}/models` als Einstellung.
- [ ] Terminal als Panel auf allen Seiten statt eigener Seite.
- [ ] Wegzieh-Geste zum Verwerfen einer Aufnahme.
- [ ] Falls doch gewünscht: `say` als CONFIRM-Werkzeug über c_out (`tts` in `audio.py`
      ist zurzeit ein Stub).
