# development

this file contains development guidelines and preferences for the c-beam project.

## writing preferences

### c-base naming

always write "c-base" in all lowercase letters exactly like that: c-base

this applies to all text output, documentation, comments, and code strings.

### capitalization

prefer lowercase letters in text output and documentation.

use proper capitalization only when required by language syntax or established conventions.

## c-base culture and language

### c-lang

c-base has its own language variation of german and english, many letters are replaced with c. for detailed information refer to online source about c-lang: https://wiki.c-base.org/dokuwiki/c-lang

## django backend design principles

### ease of use for c-base developers

the django backend should be easily usable by people from c-base that want to create their own connected application. therefore debug was set to true, in order to allow easy discovery of available urls and endpoints.

### api versatility

versatility is also important, that is why the backend provides json rpc and rest, please keep both available