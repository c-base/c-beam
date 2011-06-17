/*
  tagEventor.h - C source code for tagEventor

  Copyright 2009 Autelic Association (http://www.autelic.org)

  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.
*/

#ifndef TAG_EVENTOR_INCLUDED
#define TAG_EVENTOR_INCLUDED

#include <tagReader.h>

#ifndef TRUE
#define TRUE 1
#define FALSE 0
#endif

#define POLL_DELAY_MILLI_SECONDS_MIN        (500)
#define POLL_DELAY_MILLI_SECONDS_DEFAULT    (1000)
#define POLL_DELAY_MILLI_SECONDS_MAX        (5000)

#define VERBOSITY_MIN       (0)
#define VERBOSITY_DEFAULT   (0)
#define VERBOSITY_MAX       (3)

/************** TYPES *******************************************/

/************** GLOBALS *******************************************/
/* these are only needed globally as a horrible workaround for
   readersTable */
extern tReaderManager  readerManager;
extern tReader         readers[];

/*************** GLOBAL FUNCTIONS *********************************/
extern int  appPollDelaySet( int     newPollDelay );
extern int  appPollDelayGet( void );

extern int  appVerbosityLevelSet( int     newLevel );
extern int  appVerbosityLevelGet( void );

extern void daemonize( tReaderManager    *pManager );
extern void stopDaemon( const tReaderManager    *pManager );
extern void daemonTerminate( const tReaderManager    *pManager );

#endif
