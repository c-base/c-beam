/*
  tagEventor.c - C source code for tagEventor application / daemon

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

#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <string.h>
#include <unistd.h>
#include <getopt.h>
#include <syslog.h>

#include <signal.h>
#include <sys/stat.h>  /* for umask() */
#include <limits.h>

#include <PCSC/winscard.h>

#include <tagReader.h>

#include "constants.h"
#include "tagEventor.h"
#include "rulesTable.h"
#include "systemTray.h"
#include "stringConstants.h"
#include "explorer.h"

/*************************** MACROS ************************/

/*************    TYPEDEFS TO THIS FILE     **********************/
typedef enum { FOREGROUND, START_DAEMON, STOP_DAEMON, SYSTEM_TRAY } tRunOptions;


/* strings used for tag events, for text output and name of scipts */
static int		    appPollDelayms;
static int			appVerbosityLevel;
static tTagList	    previousTagList = { NULL, 0 };


/************** GLOBALS *******************************************/
tReaderManager  readerManager;


static inline void
sPrintBufferHex(
                char *asciiDest,
                int num,
                char *byteSource
                )
{
    long j;

	for ( j = 0; j < num; j++ )
	{
        sprintf( asciiDest, "0x%02X ", (int)(*byteSource));
        asciiDest+=5;
        byteSource++;
	}

    /* don't forget to null terminate the string */
    *asciiDest = '\0';
}


int
appPollDelaySet(
                int     newPollDelay
                )
{
    /* make sure not exceed limit */
    if ( newPollDelay > POLL_DELAY_MILLI_SECONDS_MAX )
        newPollDelay = POLL_DELAY_MILLI_SECONDS_MAX;

    if ( newPollDelay < POLL_DELAY_MILLI_SECONDS_MIN )
        newPollDelay = POLL_DELAY_MILLI_SECONDS_MIN;

    /* set the new delay to the capped value */
    appPollDelayms = newPollDelay;

#ifdef BUILD_SYSTEM_TRAY
    systemTraySetPollDelay( appPollDelayms );
#endif

    /* return the value that was actually set */
    return ( appPollDelayms );

}

int
appPollDelayGet( void )
{
    return( appPollDelayms );
}

int appVerbosityLevelSet(
                    int     newLevel
                    )
{

    /* make sure not exceed limit */
    if ( newLevel > VERBOSITY_MAX )
        newLevel = VERBOSITY_MAX;

    if ( newLevel < VERBOSITY_MIN )
        newLevel = VERBOSITY_MIN;

    appVerbosityLevel = newLevel;

    /* return the value that was actually set */
    return ( appVerbosityLevel );

}

int
appVerbosityLevelGet( void )
{
    return( appVerbosityLevel );
}

/************************ PARSE COMMAND LINE OPTIONS ********/
static void
parseCommandLine(
                int 		    argc,
                char 		    *argv[],
                tRunOptions     *pRunOptions
                )
{

   unsigned char parseError = FALSE;
   int		option, newDelay, newVerbosity;
   int      number;

   /* Set default values */
   appVerbosityLevel = VERBOSITY_DEFAULT;

#ifdef BUILD_SYSTEM_TRAY
   /* this is the gtagEventor GUI version built to install in system tray */
   *pRunOptions = SYSTEM_TRAY;
#else
   /* default mode is to run in foreground at the terminal */
   *pRunOptions = FOREGROUND;
#endif

   appPollDelayms = POLL_DELAY_MILLI_SECONDS_DEFAULT;

   while ( ((option = getopt(argc, argv, "n:v:d:p:h")) != EOF) && (!parseError) )
      switch (option)
      {
         /* 'n' option is for reader number(s) to connect to */
         /* this switch could be supplied repeatedly, once for each reader. */
         /* check for the AUTO term before converting to a number! */
        /* For each case add that reader to the list enabled, even if AUTO is also specified */
        /* the program logic will take notice of Auto, but GUI will also reflect the others */
         case 'n':
            if ( strcmp( optarg, "AUTO" ) == strlen( "AUTO" ) )
                readersSettingBitmapBitSet( &readerManager, READER_BIT_AUTO );
            else
            {
                number = atoi(optarg);
                if ( ( number  < 0) || ( number >= MAX_NUM_READERS ) )
                {
                    fprintf(stderr, TAGEVENTOR_STRING_COMMAND_LINE_READER_NUM_ERROR_1, MAX_NUM_READERS );
                    fprintf(stderr, TAGEVENTOR_STRING_COMMAND_LINE_READER_NUM_ERROR_2, optarg);
                }
                else
                    readersSettingBitmapNumberSet( &readerManager, number );
            }
            break;

         /* 'v' option is for verbosity level */
         case 'v':
            newVerbosity = atoi(optarg);
            /* check if the new verbosity was within range when set */
            if ( appVerbosityLevelSet( newVerbosity ) != newVerbosity )
            {
               fprintf(stderr, "Verbosity level must be greater or equal to 0\n");
               fprintf(stderr, "Verbosity level has been forced to %d\n", appVerbosityLevelGet() );
            }
            break;

         case 'd':
            if (strcmp(optarg, "start") == 0)
               *pRunOptions = START_DAEMON;
            else if (strcmp(optarg, "stop") == 0)
                  *pRunOptions = STOP_DAEMON;
                      else
                      {
                          parseError = TRUE;
                          fprintf(stderr, "Invalid parameter for '-d' daemon option\n");
                      }
            break;

         /* 'p' option is for the delay in polling in useconds */
         case 'p':
            newDelay = atoi(optarg);
            /* check if the new delay was within range when set */
            if ( appPollDelaySet ( newDelay ) != newDelay )
            {
               fprintf(stderr, "Poll delay must be greater or equal to 0\n");
               fprintf(stderr, "Poll delay has been forced to %d\n", appPollDelayGet() );
            }
            break;

         /* 'h' option is to request print out help */
         case 'h':
                fprintf(stderr, TAGEVENTOR_STRING_USAGE, argv[0],
                        POLL_DELAY_MILLI_SECONDS_MIN, POLL_DELAY_MILLI_SECONDS_DEFAULT,
                        POLL_DELAY_MILLI_SECONDS_MAX, VERSION_STRING );
            exit ( 0 );
            break;

         default:
	    parseError = TRUE;
            break;
      }

   if (parseError)
   {
      fprintf(stderr, TAGEVENTOR_STRING_USAGE, argv[0], POLL_DELAY_MILLI_SECONDS_MIN,
              POLL_DELAY_MILLI_SECONDS_DEFAULT, POLL_DELAY_MILLI_SECONDS_MAX,
              VERSION_STRING );
      exit( EXIT_FAILURE );
   }

    /* if no reader numbers were specified and AUTO neither, then set default */
    if ( readersSettingBitmapGet( &readerManager ) == READER_BIT_NONE )
        readersSettingBitmapSet( &readerManager, READER_BIT_DEFAULT );

}
/************************ PARSE COMMAND LINE OPTIONS ********/



/***************** HANDLE SIGNALS ***************************/
static void
handleSignal(
	         int	sig
	        )
{

   switch( sig )
   {
      case SIGCHLD:
      break;

      case SIGHUP: /* restart the server using  "kill -1" at the command shell */
         readersDisconnect( &readerManager );
         readersConnect( &readerManager );
         readersLogMessage( &readerManager, LOG_INFO, 1, "Hangup signal received - disconnected and reconnected");
      break;

      case SIGINT: /* kill -2 or Control-C */
      case SIGTERM:/* "kill -15" or "kill" */
         readersDisconnect( &readerManager );
         readersLogMessage( &readerManager, LOG_INFO, 1, "SIGTERM or SIGINT received, exiting gracefully");
         daemonTerminate( &readerManager );
         closelog();
         exit(0);
      break;
   }
}

static void
tagDetachData(
            tTag            *pTag
            )
{

    //if ( pTag->contents.pData )
    //   free( pTag->contents.pData );

    pTag->contents.pData = NULL;
    pTag->contents.dataSize = 0;
    pTag->contents.extensionHook = NULL;

}

const tTagContents testTag = { "Test Data", 9, NULL };

static void
tagAttachData(
           tTag              *pTag,
           tReaderManager    *pManager
          )
{

    pTag->contents = testTag;

    /* Add interpreted data into the extensionHook */
    /* need 5 characters to show each byte in HEX '0x00 ' */
    pTag->contents.extensionHook = malloc( 5 * pTag->contents.dataSize );
    sPrintBufferHex( pTag->contents.extensionHook, pTag->contents.dataSize, pTag->contents.pData );

}


void
eventDispatch(
                tEventType         eventType,
                tTag              *pTag,
                int                readerNumber,
                tReaderManager    *pManager
                )
{
    char	        messageString[MAX_LOG_MESSAGE];

    switch( eventType )
    {
        case TAG_IN:
#ifdef BUILD_SYSTEM_TRAY
            systemTrayNotify( "Tag IN", pTag->uid, NULL );
#endif
            sprintf( messageString, "Event: Tag %s - UID: %s", "IN", pTag->uid);
            readersLogMessage( pManager, LOG_INFO, 1, messageString);

            /* find out what's inside the tag, as we might process based on that */
            tagAttachData( pTag, pManager );

            /* try to process event and notify if fails */
            if ( ! rulesTableEventDispatch( eventType, pTag ) )
            {
                sprintf( messageString, "Failed to find an executable script for the tag event" );
                readersLogMessage( pManager, LOG_INFO, 1, messageString );
#ifdef BUILD_SYSTEM_TRAY
                systemTrayNotify( messageString, pTag->uid, NULL );
#endif
            }
#ifdef BUILD_EXPLORER
            explorerViewUpdate();
#endif
            break;

        case TAG_OUT:
            sprintf(messageString, "Event: Tag %s - UID: %s", "OUT", pTag->uid);
            readersLogMessage( pManager, LOG_INFO, 1, messageString);

            /* try to process event and notify if fails */
            if ( ! rulesTableEventDispatch( eventType, pTag ) )
            {
                sprintf( messageString, "Failed to execute a script for tag event" );
                readersLogMessage( pManager, LOG_ERR, 0, messageString );
#ifdef BUILD_SYSTEM_TRAY
                systemTrayNotify( messageString, pTag->uid, NULL );
#endif
            }
#ifdef BUILD_EXPLORER
            explorerViewUpdate();
#endif
            /* we can now free the data that was allocated and attached to this tag */
            tagDetachData( pTag );
            break;

        case READER_DETECTED:
            sprintf(messageString, "Reader detected: %d, %s", readerNumber, pManager->readers[readerNumber].name );
            readersLogMessage( pManager, LOG_INFO, 2, messageString);
#ifdef BUILD_SYSTEM_TRAY
            systemTrayNotify( "Reader detected", pManager->readers[readerNumber].name, NULL );
#endif
#ifdef BUILD_EXPLORER
            explorerAddReader( readerNumber );

            explorerViewUpdate();
#endif
            break;

        case READER_CONNECTED_TO:
            sprintf(messageString, "Reader: %s, assigned driver='%s'", pManager->readers[readerNumber].name,
                    pManager->readers[readerNumber].driverDescriptor );
            readersLogMessage( pManager, LOG_INFO, 3, messageString);
#ifdef BUILD_SYSTEM_TRAY
            systemTrayNotify( "Reader connected to", pManager->readers[readerNumber].name, NULL );
#endif
#ifdef BUILD_EXPLORER
            explorerAddReader( readerNumber );

            explorerViewUpdate();
#endif
            break;

        case READER_LOST:
#ifdef BUILD_EXPLORER
            explorerRemoveReader( readerNumber );

            explorerViewUpdate();
#endif
            break;

        case READER_DISCONNECT:
#ifdef BUILD_EXPLORER
            explorerViewUpdate();
#endif
            break;

        case PCSCD_CONNECT:
            readersLogMessage( pManager, LOG_INFO, 2, LIBTAGREADER_STRING_PCSCD_OK );
#ifdef BUILD_SYSTEM_TRAY
            systemTrayNotify( "Connected to 'pcscd' daemon", NULL, NULL );
#endif
#ifdef BUILD_EXPLORER
            explorerViewUpdate();
#endif
            break;

        case PCSCD_FAIL:
            readersLogMessage( pManager, LOG_ERR, 1, LIBTAGREADER_STRING_PCSCD_NO );
#ifdef BUILD_EXPLORER
            explorerViewUpdate();
#endif
            break;

        case PCSCD_DISCONNECT:
#ifdef BUILD_EXPLORER
            explorerViewUpdate();
#endif
            break;

        default:
            break;
    }
}

static void
processTagLists(
                 void            (*callBack)( char, const char  *, const char * )
                )

{
    int			    i, j;
    unsigned char	found;
    unsigned char   listChanged = FALSE;
    char			messageString[MAX_LOG_MESSAGE],
                    tagLine[MAX_TAG_UID_SIZE + strlen(TAGEVENTOR_STRING_TAG_LINE) + 10],
                    tagMessage[MAX_LOG_MESSAGE];

    /* for each tags that was here before see if it is now missing */
    for (i = 0; i < previousTagList.numTags; i++)
    {
        found = FALSE;
        /* Look for it in the current list */
        for ( j = 0; (j < readerManager.tagList.numTags); j++ )
             if ( strcmp(previousTagList.pTags[i].uid,
                         readerManager.tagList.pTags[j].uid) == 0 )
             {
                found = TRUE;

                /* copy over the attached data (via pointers to the malloc-ed data */
                readerManager.tagList.pTags[j].contents = previousTagList.pTags[i].contents;
             }

        if ( !found )
        {
            listChanged = TRUE;
            eventDispatch( TAG_OUT, &(previousTagList.pTags[i]), 0, &readerManager );
        }
    }

    /* check for tags that are here now in the current list */
    for ( i = 0; i < readerManager.tagList.numTags; i++ )
    {
        found = FALSE;
        /* Look for it in the previous list from last time around */
        for (j = 0; ((j < previousTagList.numTags) && (!found)); j++)
            if ( strcmp(previousTagList.pTags[j].uid,
                        readerManager.tagList.pTags[i].uid) == 0 )
                found = TRUE;

        if ( !found )
        {
            listChanged = TRUE;
            eventDispatch( TAG_IN, &(readerManager.tagList.pTags[i]), 0, &readerManager );
        }
    }

    /* create a composite message that will contain all changes */
    if ( listChanged )
    {
        /* create a string with some status text and a list of the UIDs of the tags found */
        sprintf( messageString, TAGEVENTOR_STRING_CONNECTED_READER, readerManager.nbReaders, (int)(readerManager.tagList.numTags));
        tagMessage[0] = '\0'; /* NULL terminate before using strcat() */
        for ( i = 0; i < readerManager.tagList.numTags; i++ )
        {
            sprintf( tagLine, TAGEVENTOR_STRING_TAG_LINE, readerManager.tagList.pTags[i].uid );
            strcat( tagMessage, tagLine );
        }

        if ( callBack )
            (*callBack)( TRUE, messageString, tagMessage );
    }
}

static int
tagListCheck(
            void *data /* pointer to a callback function */
            )
{
    int  		    rv;
    char			messageString[MAX_LOG_MESSAGE];
    void            (*callBack)( char, const char  *, const char * ) = data;

    /*** All this work about connecting to readers is done inside the poll */
    /* function to enable disconnect and reconnect of readers in operation */
    /* so that a "best effort" is always done, and hotplugging works       */
    /* Even late starting of the pcscd daemon, or killing it and restarting */
    /* should be recovered from by tagEventor, connecting to it when avail.*/

    /* make sure messages are always valid */
    messageString[0] = '\0';

    /* If not connected to PCSCD, try and connect */
    if ( readerManager.hContext == NULL )
    {
        if ( readersManagerConnect( &readerManager ) != SCARD_S_SUCCESS )
        {
            sprintf( messageString, TAGEVENTOR_STRING_PCSCD_PROBLEM );
            if ( callBack )
                (*callBack)( FALSE, messageString, "" );

            /* nothing else to do for now, return TRUE so I get called again */
            return( TRUE );
        }
        else
        {
            /* try and connect to the specified readers on first connect */
            if ( readersConnect( &readerManager ) != SCARD_S_SUCCESS )
            {
/* TODO an event here? */
                sprintf( messageString, TAGEVENTOR_STRING_PCSCD_OK_READER_NOT ,
                        readerManager.nbReaders );
            }
        }
    }

    /**** If we get this far we are connected to PCSCD at least, readers maybe not ***/

    /*      - free the memory of the 'previous' tag array, This is equivalent to
              the currentTagList from 2 iterations ago
            - make 'previous' be 'current' from the previous iteration */
    if ( previousTagList.pTags != NULL )
        free ( previousTagList.pTags );

    /* make the previousTagList equal to the one we saved from last time around */
    /* this will be freed next time around */
    previousTagList = readerManager.tagList;

    /* reset pointers to avoid confusion, as the memory is now "owned" by previousTagList */
    readerManager.tagList.numTags = 0;
    readerManager.tagList.pTags = NULL;

    /* get the new list of tags into readerManager.tagList, allocated by readerGetTagList */
    rv = readersGetTagList( &readerManager );
    if (rv != SCARD_S_SUCCESS)
    {
        /* couldn't connect to a reader, but maybe not a problem.... */
        sprintf( messageString, TAGEVENTOR_STRING_PCSCD_OK_READER_NOT,
                 readerManager.nbReaders );
        if ( callBack )
            (*callBack)( FALSE, messageString, "" );

        /* exit, but indicate to keep calling me */
        return( TRUE );
    }

    processTagLists( callBack );

    /* keep calling me */
    return( TRUE );

}

static void
pollCallback(
             char        connected,
             const char  *generalMessage,
             const char  *tagsMessage
             )
{
    readersLogMessage(  &readerManager, LOG_INFO, 2, generalMessage );
    readersLogMessage(  &readerManager, LOG_INFO, 2, tagsMessage );
}

/************************ MAIN ******************************/
int main(
        int 		argc,
        char 		*argv[]
        )
{
    tRunOptions	runOptions;

    readersInit( &readerManager );

    parseCommandLine(argc, argv, &runOptions );

    /* set-up signal handlers */
    signal(SIGTERM,  handleSignal); /* software termination signal from kill */
    signal(SIGHUP,   handleSignal); /* hangup signal - ´restart´ as best as we can */
    signal(SIGINT,   handleSignal); /* Interrupt or Control-C signal from terminal*/
    signal(SIGCHLD,  handleSignal); /* death of a child process */

    /* set reader library verbosity to the same as that we use at the application level */
    /* here we are always foreground, not a daemon, it maybe recalled from the daemon */
    readersSetOptions(  &readerManager, appVerbosityLevel, FALSE );

	/* load the table of rules */
    rulesTableRead();

    /* if requested to start as daemon, daemonize ourselves here */
    switch (runOptions)
    {
        case START_DAEMON:
            /* will fork a daemon and return if successful */
            daemonize( &readerManager );
            break;
        case STOP_DAEMON:
            /* find the running daemon, kill it and exit */
            stopDaemon( &readerManager );
            exit( 0 );
            break;
        case FOREGROUND:
            /* enter the loop to poll for tag and execute events, FALSE to not update system tray */
            /* Loop forever - doing our best - only way out is via a signal */
            while ( tagListCheck( pollCallback ) )
                usleep(appPollDelayms * 1000);
            break;
#ifdef BUILD_SYSTEM_TRAY
        case SYSTEM_TRAY:
            /* build the status icon in the system tray area */
            startSystemTray( &argc, &argv, &tagListCheck, appPollDelayms, readerManager.readers );
            break;
#endif
        default:
            break;
    }

    readersDisconnect( &readerManager );

    readersManagerDisconnect( &readerManager );

   return ( 0 );

} /* main */
