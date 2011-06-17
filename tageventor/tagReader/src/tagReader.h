/*
  tagReader.h - public header files for tagReader library

  Copyright 2008-2009 Autelic Association (http://www.autelic.org)

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

#ifndef TAG_READER_INCLUDED
#define TAG_READER_INCLUDED

/* this is needed for definitions of different types of log messages etc */
#include <syslog.h>

#include "tagReaderTypes.h"

/**************************** CONSTANTS ******************************/
#define	MAX_LOG_MESSAGE	(200)

/* use this to have readerSetOptions() not touch a given option value */
#define	IGNORE_OPTION	(-1)

#define READER_BIT_NONE     (0)
#define READER_BIT_AUTO     (1<<0)
#define READER_BIT_0        (1<<1)
#define READER_BIT_1        (1<<2)
#define READER_BIT_2        (1<<3)
#define READER_BIT_3        (1<<4)
#define READER_BIT_4        (1<<5)
#define READER_BIT_5        (1<<6)
#define READER_BIT_DEFAULT  READER_BIT_AUTO

/**********************    STRINGS ****************************/
#define LIBTAGREADER_STRING_PCSCD_OK              "libTagReader: Successfully connected to pcscd server"
#define LIBTAGREADER_STRING_PCSCD_NO              "libTagReader: Failed to connect to pcscd server"

typedef enum { TAG_IN = 0, TAG_OUT = 1,
            READER_DETECTED = 2, READER_CONNECTED_TO = 3, READER_LOST = 4, READER_DISCONNECT =5,
            PCSCD_CONNECT = 6, PCSCD_FAIL = 7, PCSCD_DISCONNECT = 8
             } tEventType;

/************************ EXTERNAL FUNCTIONS **********************/
extern void             readersInit( tReaderManager *pManager );
extern unsigned int     readersSettingBitmapGet( tReaderManager *pManager  );
extern unsigned int     readersSettingBitmapSet( tReaderManager *pManager, unsigned int bitmap );
extern void             readersSettingBitmapBitSet( tReaderManager *pManager, unsigned int bitmap );
extern void             readersSettingBitmapBitUnset( tReaderManager *pManager, unsigned int bitmap );
extern unsigned int     readersSettingBitmapBitTest( tReaderManager *pManager, unsigned int bitmap );
extern unsigned int     readersSettingBitmapNumberSet( tReaderManager *pManager, unsigned int number );
extern unsigned int     readersSettingBitmapNumberTest( tReaderManager *pManager, unsigned int bitNumber );

extern int              readersSetOptions ( tReaderManager *pManager,
                                            int	            verbosity,
                                            unsigned char	background );

extern int              readersManagerConnect( tReaderManager *pManager );
extern int              readersManagerDisconnect( tReaderManager *pManager );

extern int              readersConnect(  tReaderManager  *pManager );
extern void             readersDisconnect( tReaderManager *pManager );
extern int              readersGetTagList( tReaderManager *pManager );
extern int              readersGetContactlessStatus( tReaderManager *pManager );
extern void             readersLogMessage(  const tReaderManager    *pManager,
                                            int		                messageType,
                                            int	    	            messageLevel,
                                            const char 	            *message);

extern void eventDispatch(tEventType         eventType,
                            tTag              *pTag,
                            int                readerNumber,
                            tReaderManager    *pManager );

#endif
