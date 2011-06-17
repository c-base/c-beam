/*
  tagReader.c - C source code for tagReader library

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
#include <string.h>
#include <unistd.h>
#include <stdarg.h>

#include <PCSC/wintypes.h>
#include <PCSC/winscard.h>

#include "tagReader.h"
#include "readerDriver.h"

/********************** HACKS   !!!! *****************************/
/* It seems this error code is returned on versions of pcsclite.h*/
/* that ship with Linux, but not the (older?) versions on Mac OS */
/* but if it depends on versions then it could also happen on    */
/* on other OS, not just Mac OS X, so I don't use a Mac flag     */
#ifndef SCARD_E_NO_READERS_AVAILABLE
#define SCARD_E_NO_READERS_AVAILABLE 0x8010002E
#endif

/*******************   MACROS ************************************/
#ifdef DEBUG
#define PCSC_ERROR( pMgr, rv, text) \
if (rv != SCARD_S_SUCCESS) \
{ \
   sprintf(messageString, "%s: %s (0x%lX)", text, pcsc_stringify_error(rv), rv); \
   readersLogMessage( pMgr, LOG_ERR, 0, messageString);\
}
#else
#define PCSC_ERROR(pMgr, rv, text)
#endif


#define RESET_READER( read )    { \
                                (read).hCard = NULL; \
                                (read).name = NULL; \
                                (read).pDriver = NULL; \
                                (read).driverDescriptor = NULL; \
                                (read).SAM = FALSE; \
                                (read).SAM_serial[0] = '\0'; \
                                (read).SAM_id[0] = '\0'; \
                                (read).scanning = FALSE; \
                                (read).tagList.numTags = 0; \
                                (read).tagList.pTags = NULL; \
}

/**********    STATIC VARIABLES TO THIS FILE     ***************/
static char		messageString[MAX_LOG_MESSAGE];

extern tReaderDriver    acr122UDriver;
/* This is a NULL terminated list of pointers to driver structures */
/* one for each driver we know about                               */
static tReaderDriver   *readerDriverTable[] = { &acr122UDriver, NULL };

static inline void
sPrintBufferHex(
                char *asciiDest,
                int num,
                unsigned char *byteSource
                )
{
    LONG j;

	for ( j = 0; j < num; j++ )
	{
        sprintf( asciiDest, "%02X", (int)(*byteSource));
        asciiDest+=2;
        byteSource++;
	}

    /* don't forget to null terminate the string */
    *asciiDest = '\0';
}


/* utility function for other modules that returns the current setting for the reader number bitmap */
unsigned int
readersSettingBitmapGet(
                        tReaderManager *pManager
                        )
{
    return ( pManager->readerSetting );
}

/* utility function for settings modules that sets the state of current setting for the reader number bitmap */
unsigned int
readersSettingBitmapSet(
                        tReaderManager *pManager ,
                        unsigned int   readerSettingBitmap
                )
{

    pManager->readerSetting = readerSettingBitmap;

    return ( pManager->readerSetting );

}

/* Utility function to set one specific reader number in the bitmap */
void
readersSettingBitmapBitSet(
                            tReaderManager *pManager,
                            unsigned int bitmap
                            )
{
    /* bit 0 of the bitmap is reserved for AUTO */
    /* so OR in the bit shifted an extra 1   number 0 = bit 1 etc */
    pManager->readerSetting |= bitmap;

}

/* Utility function to unset one specific reader number in the bitmap */
void
readersSettingBitmapBitUnset(
                            tReaderManager *pManager,
                            unsigned int bitmap
                            )
{
    /* bit 0 of the bitmap is reserved for AUTO */
    /* so OR in the bit shifted an extra 1   number 0 = bit 1 etc */
    pManager->readerSetting &= (~bitmap);

}

unsigned int
readersSettingBitmapNumberSet(
                            tReaderManager *pManager,
                            unsigned int     numberOfTheBitToSet
                            )
{
    /* bit 0 of the bitmap is reserved for AUTO */
    /* so test  number 0 = bit 1 etc */
    pManager->readerSetting |= (1 << ( numberOfTheBitToSet +1 ) );

    return ( pManager->readerSetting );
}

/* Utility function to add one specific reader number to the bitmap */
unsigned int
readersSettingBitmapBitTest(
                            tReaderManager *pManager,
                            unsigned int bitmap
                            )
{
    /* bit 0 of the bitmap is reserved for AUTO */
    /* so test  number 0 = bit 0 etc */
    return( pManager->readerSetting & bitmap );

}

/* Utility function to add one specific reader number to the bitmap */
unsigned int
readersSettingBitmapNumberTest(
                                tReaderManager *pManager,
                                unsigned int bitNumber
                                )
{
    /* bit 0 of the bitmap is reserved for AUTO */
    /* so test  number 0 = bit 1 etc */
    return( pManager->readerSetting & ( 1 << ( bitNumber +1 )) );

}

void
readersInit(
            tReaderManager *pManager
            )
{
    int i;

    pManager->nbReaders = 0;
    pManager->mszReaders = NULL;
    pManager->hContext = NULL;
    pManager->tagList.numTags = 0;
    pManager->tagList.pTags = NULL;
    pManager->readerSetting = 0; /* no readers, not even AUTO to start with */
    pManager->libVerbosityLevel = 0; /* silent */
    pManager->runningInBackground = FALSE;

    /* some help to make sure we close whatś needed, not more */
    for ( i = 0; i < MAX_NUM_READERS; i++ )
        RESET_READER( pManager->readers[i] );

}

/**************************** LOG MESSAGE************************/
/* type = LOG_WARNING (something unexpected, not a big problem) */
/* type = LOG_ERR (something went wrong that was´t expected     */
/* type = LOG_INFO (just info */
void
readersLogMessage(
                 const tReaderManager   *pManager,
                 int		            type,
                 int		            messageLevel,
                 const char 	        *message
                    )
{

   switch (type)
   {
      case LOG_WARNING:
         if ( pManager->runningInBackground )
            syslog( type , "WARNING: %s", message );
         else
            fprintf(stderr, "WARNING: %s\n", message);
      break;

      case LOG_ERR:
         if (pManager->runningInBackground )
            syslog( type , "ERROR: %s", message );
         else
            fprintf(stderr, "ERROR: %s\n", message);
      break;

      case LOG_INFO:
         if ( pManager->libVerbosityLevel >= messageLevel )
         {
            if ( pManager->runningInBackground )
               syslog( type, "INFO [%d]: %s", messageLevel, message);
            else
               fprintf( stdout,  "INFO [%d]: %s\n", messageLevel, message);
         }
         break;
   }

}
/**************************** LOG ************************/


/**************************** READER SET OPTIONS *********/
int readersSetOptions (
                        tReaderManager  *pManager,
                        int		        verbosity,
                        unsigned char   background
                        )

{

   /* set the verbosity level for all our output, if requested to */
   if ( verbosity != IGNORE_OPTION )
      pManager->libVerbosityLevel = verbosity;

   /* set flag for running in foreground, or background as daemon */
   pManager->runningInBackground = background;

   return ( SCARD_S_SUCCESS );

}
/**************************** READER SET OPTIONS *********/

/*************************** READERS ENUMERATE *****************/
static int
readersEnumerate(
                tReaderManager  *pManager
                )
{

    LONG    rv;
    DWORD   dwReaders;
    char 	*ptr;
    int     i, previousNumReaders;

    /* remember how many readers there used to be */
    previousNumReaders = pManager->nbReaders;

    /* Call with a null buffer to get the number of bytes to allocate */
    rv = SCardListReaders( (SCARDCONTEXT)(pManager->hContext), NULL, NULL, &dwReaders);
    if ( rv != SCARD_S_SUCCESS )
    {
        /* if there are no readers, then zero everything out but don't report an error */
        if ( rv == SCARD_E_NO_READERS_AVAILABLE )
        {
            pManager->nbReaders = 0;

            if ( pManager->mszReaders )
                free( pManager->mszReaders );
            pManager->mszReaders = NULL;

            readersLogMessage( pManager, LOG_INFO, 2, "Found 0 Readers" );
        }
        else
            PCSC_ERROR( pManager, rv, "SCardListReaders");

        return ( rv );
    }

    /* if array already exists, then liberate it and alloc a new one for the */
    /* number of readers reported from SCardListReader */
    if ( pManager->mszReaders )
        free( pManager->mszReaders );
    /* malloc enough memory for dwReader string */
    pManager->mszReaders = malloc(sizeof(char)*dwReaders);

    /* now get the list into the mszReaders array */
    rv = SCardListReaders( (SCARDCONTEXT)(pManager->hContext), NULL, pManager->mszReaders, &dwReaders);
    if (rv != SCARD_S_SUCCESS)
    {
        /* Avoid reporting an error just because no reader is connected */
        if ( rv != SCARD_E_NO_READERS_AVAILABLE )
            PCSC_ERROR( pManager, rv, "SCardListReaders");
        return (rv);
    }

    /* Extract readers from the null separated string and get the total
        * number of readers */
    pManager->nbReaders = 0;
    ptr = pManager->mszReaders;
    while (*ptr != '\0')
    {
        ptr += strlen(ptr)+1;
        (pManager->nbReaders)++;
    }

    sprintf(messageString, "Found %d Readers", pManager->nbReaders);
    readersLogMessage( pManager, LOG_INFO, 2, messageString);

    /* fill the array of readers with pointers to the appropriate point */
    /* in the long mszReaders multi-string */
    pManager->nbReaders = 0;
    ptr = pManager->mszReaders;
    while (*ptr != '\0')
    {
        sprintf(messageString, "Reader [%d]: %s", pManager->nbReaders, ptr);
        readersLogMessage( pManager, LOG_INFO, 3, messageString);
        pManager->readers[pManager->nbReaders].name = ptr;
        ptr += strlen(ptr)+1;
        (pManager->nbReaders)++;
    }

    /* if we have fewer readers than we used to then zero out the "lost ones" */
    if ( pManager->nbReaders < previousNumReaders )
       for ( i = pManager->nbReaders; i < previousNumReaders; i++ )
          RESET_READER( pManager->readers[i] );

    return( SCARD_S_SUCCESS );

}
/*************************** READERS ENUMERATE *****************/


/************************* READER MANAGER CONNECT **************/
/* This is added to make things a bit more efficient when you  */
/* are using multiple readers connected to one reader manager  */
/* I have left the readerConnect() function as is for back-    */
/* -wards compatibility. If you use this function then set the */
/* hCOntext element of each tReader structure to this value and*/
/* then they will all use the same context and avoid overhead  */
int
readersManagerConnect(
                    tReaderManager *pManager
                    )
{
    LONG 		    rv;

    if ( pManager == NULL )
        return( SCARD_E_INVALID_PARAMETER );

    rv = SCardEstablishContext(SCARD_SCOPE_SYSTEM, NULL, NULL, (LPSCARDCONTEXT)&(pManager->hContext) );
    if (rv != SCARD_S_SUCCESS)
    {
        PCSC_ERROR( pManager, rv, "SCardEstablishContext");
        pManager->hContext = NULL;

        eventDispatch( PCSCD_FAIL, NULL, 0, pManager );

        return( rv );
    }

    eventDispatch( PCSCD_CONNECT, NULL, 0, pManager );

    /* Find all the readers and fill the readerManager data structure */
    rv = readersEnumerate( pManager );

    return (rv);

}
/************************* READER MANAGER CONNECT **************/

/************************* READER MANAGER DISCONNECT ***********/
int
readersManagerDisconnect(
                        tReaderManager *pManager
                        )
{
    LONG 		    rv;

    if ( pManager == NULL )
        return( SCARD_E_INVALID_PARAMETER );

    if ( pManager->hContext )
    {
        readersLogMessage( pManager, LOG_INFO, 2, "Disconnecting from pcscd server");

        rv = SCardReleaseContext( (SCARDCONTEXT) (pManager->hContext) );
        if ( rv != SCARD_S_SUCCESS )
            PCSC_ERROR( pManager, rv, "SCardReleaseContext");

        /* libreate memory that was allocated when we connected to manager */
        if (pManager->mszReaders)
        {
            free(pManager->mszReaders);
            pManager->mszReaders = NULL;
        }
    }
    else
        rv = SCARD_E_INVALID_PARAMETER;

    /* now it should be NULL either way */
    pManager->hContext = NULL;

    eventDispatch( PCSCD_DISCONNECT, NULL, 0, pManager );

    return( rv );
}
/************************* READER MANAGER DISCONNECT ***********/


/************************* READER CONNECT **********************/
int readersConnect (
                    tReaderManager  *pManager
                 )
{
    LONG 		    rv;
    BOOL			    readerSupported;
    DWORD 		    dwActiveProtocol;
    int              i, num;
    BOOL             automatic;

    /* Duh. If you pass me a NULL pointer then I'm out of here */
    if ( pManager == NULL )
        return( SCARD_E_INVALID_PARAMETER );

    automatic = ( readersSettingBitmapBitTest( pManager, READER_BIT_AUTO ) != 0 );

    if ( automatic )
    {
        /* re-enumerate the readers in the system as it may have changed */
        rv = readersEnumerate( pManager );
        if ( rv != SCARD_S_SUCCESS )
            return( rv );
    }

    if ( pManager->nbReaders == 0 )
        return( SCARD_E_NO_READERS_AVAILABLE );

    /* try and connect to all readers that are present according to readerSetting */
    for ( num = 0; num < pManager->nbReaders; num++ )
    {
        /* if we are not already connected and should be trying then do so */
        if ( ( pManager->readers[num].hCard == NULL) &&
             ( automatic || readersSettingBitmapNumberTest( pManager, num ) ) )
        {
            dwActiveProtocol = -1;
            rv = SCardConnect( (SCARDCONTEXT)(pManager->hContext),
                                pManager->readers[num].name,
                                SCARD_SHARE_SHARED, SCARD_PROTOCOL_T0 ,
                                (LPSCARDHANDLE) &(pManager->readers[num].hCard),
                                &dwActiveProtocol);
            if (rv == SCARD_S_SUCCESS)
            {
                eventDispatch( READER_DETECTED, NULL, num, pManager );

                /* Query the drivers in the list until one of them can handle the reader */
                i = 0;
                readerSupported = FALSE;
                /* call the function to check if this driver works with this reader */
                while ( (readerDriverTable[i] != NULL) && (readerSupported == FALSE) )
                    rv = readerDriverTable[i++]->readerCheck( &(pManager->readers[num]), &readerSupported );

                if ( rv != SCARD_S_SUCCESS )
                {
                    RESET_READER( pManager->readers[num] );
                    PCSC_ERROR( pManager, rv, "readerCheck:" );
                    return( rv );
                }

                /* we couldn't find a driver that knows how to handle this reader... */
                if ( ( readerSupported == FALSE) )
                {
                    pManager->readers[num].pDriver = NULL;
                    sprintf(messageString, "Reader (%s) not supported by any known driver", pManager->readers[num].name );
                    readersLogMessage( pManager, LOG_ERR, 0, messageString);
                    return (SCARD_E_UNKNOWN_READER);
                }
                else
                {
                    /* if we got this far then a driver was successfully found, remember it! */
                    pManager->readers[num].pDriver = readerDriverTable[i -1];
                    pManager->readers[num].driverDescriptor = readerDriverTable[i -1]->driverDescriptor;
                    eventDispatch( READER_DETECTED, NULL, num, pManager );

                }
            }
            else
                RESET_READER( pManager->readers[num] );
        }
    }

    return ( SCARD_S_SUCCESS );

}
/************************* READER CONNECT **********************/

/************************ READER DISCONNECT ********************/
void
readersDisconnect(
                tReaderManager  *pManager
                   )
{
    LONG    rv;
    int     i;

    /* Duh. If you pass me a NULL pointer then I'm out of here */
    if ( ( pManager == NULL ) || ( pManager->hContext == NULL ) )
       return;

    if ( readersSettingBitmapBitTest( pManager, READER_BIT_AUTO ) )
    {
        /* re-enumerate the readers in the system as it may have changed */
        rv = readersEnumerate( pManager );
        if ( rv != SCARD_S_SUCCESS )
            return;
    }

    /* then check all readers we were ABLE to connect to */
    for ( i = 0; i < pManager->nbReaders; i++ )
    {
        if ( pManager->readers[i].hCard != NULL )
        {
            sprintf(messageString, "Disconnecting from reader %d", i );
            readersLogMessage( pManager, LOG_INFO, 2, messageString);

            rv = SCardDisconnect( (SCARDHANDLE) (pManager->readers[i].hCard), SCARD_UNPOWER_CARD);
            RESET_READER( pManager->readers[i] );

            eventDispatch( READER_DISCONNECT, NULL, i, pManager );

            if ( rv != SCARD_S_SUCCESS )
                PCSC_ERROR( pManager, rv, "SCardDisconnect");
        }
    }
}
/************************** READER DISCONNECT ********************/

/************************ GET CONTACTLESS STATUS *****************/
/* TODO : this function hasn't really been tested                */
int
readerGetContactlessStatus(
                            tReaderManager  *pManager,
                            tReader	        *pReader
                          )
{
    DWORD		dwRecvLength;
    BYTE		pbRecvBuffer[20];
    LONG		rv;
    int         i;
    BOOL        automatic;

    /* Duh. If you pass me a NULL pointer then I'm out of here */
    if ( ( pManager == NULL ) || ( pManager->hContext == NULL ) )
       return( SCARD_E_INVALID_PARAMETER );

    automatic = readersSettingBitmapBitTest( pManager, READER_BIT_AUTO );

    if ( automatic )
    {
        /* re-enumerate the readers in the system as it may have changed */
        rv = readersConnect( pManager );
        if ( rv != SCARD_S_SUCCESS )
            return( rv );
    }

    sprintf(messageString, "Requesting contactles status");
    readersLogMessage( pManager, LOG_INFO, 2, messageString);

    /* then check all readers we were ABLE to connect to */
    for ( i = 0; i < pManager->nbReaders; i++ )
    {
        /* check we have connected and have a driver for this reader */
        if ( ( pReader[i].hCard != NULL ) && ( pReader[i].pDriver != NULL ) &&
             ( automatic || readersSettingBitmapNumberTest( pManager, i ) ) )
        {
            dwRecvLength = sizeof(pbRecvBuffer);
            rv = ((tReaderDriver *)(pReader[i].pDriver))->getContactlessStatus(pReader, pbRecvBuffer, &dwRecvLength);

            if ( rv == SCARD_S_SUCCESS )
            {
                if (pManager->libVerbosityLevel)
                {
                    sprintf(messageString, "Reader %d Status: ", i);
                    sPrintBufferHex( (messageString + strlen("Reader %d Status: ") ), dwRecvLength, pbRecvBuffer);
                    readersLogMessage( pManager, LOG_INFO, 2, messageString);

                    sprintf(messageString, "Number of Tags = %d", pbRecvBuffer[4]);
                    readersLogMessage( pManager, LOG_INFO, 2, messageString);
                }
            }
            else
                PCSC_ERROR( pManager, rv, "driver->getConnectlessStatus:");
        }
    }

   return (rv);
}
/************************ GET CONTACTLESS STATUS *****************/



/************************ GET TAG LIST ***************************/
/*** as the list of tags is of unknown and varying length this   */
/* function allocates the memory for the list you must handle it!*/
int
readersGetTagList(
                tReaderManager  *pManager
                )
{
    LONG		rv = SCARD_S_SUCCESS;
    tTag        *pTags[MAX_NUM_READERS]; /* an array of pointers to tags (that act like arrays) ! */
    int         i, j;
    int         uniqueListIndex;
    BOOL        automatic;
    char        *namePointer;

    /* Duh. If you pass me a NULL pointer then I'm out of here */
    if ( ( pManager == NULL ) || ( pManager->hContext == NULL ) )
       return( SCARD_E_INVALID_PARAMETER );

    automatic = readersSettingBitmapBitTest( pManager, READER_BIT_AUTO );

    if ( automatic )
    {
        /* re-connect the readers in the system as it may have changed */
        rv = readersConnect( pManager );
        if ( rv != SCARD_S_SUCCESS )
            return( rv );
    }

    /* before we start, reset the total count to 0 */
    pManager->tagList.numTags = 0;

    /* for all readers we were connected to PREVIOUSLY or are now after AUTMATIC reconnect */
    for ( i = 0; i < pManager->nbReaders; i++ )
    {
        /* make sure it's initialized, as depending on reader settings we may skip over */
        /* one of these pointers in the array and later try to free an invalid pointer */
        pTags[i] = NULL;
        pManager->readers[i].tagList.numTags = 0;

        /* check we are connected, have a driver and should be reading it */
        if ( ( pManager->readers[i].hCard != NULL ) && ( pManager->readers[i].pDriver != NULL ) &&
             ( automatic || readersSettingBitmapNumberTest( pManager, i ) ) )
        {
            /* I'd normally check if a tag is present using readerGetContactlessStatus() before    */
            /* querying the tag list, but all my testing to date has failed to get the contactless */
            /* status APDU to work, it always returns D5 05 00 00 00 80 90 00 to indicate no tag   */
            /* is present. I have reported this issue to ACS by e-mail - Andrew                    */

            /* allocate the structure for this reader to read tag list into upto max size */
            pTags[i] = (tTag *)malloc( ( ((tReaderDriver *)(pManager->readers[i].pDriver))->maxTags ) * sizeof(tTag) );

            /* call the reader's associated driver's function to read the tag list */
            rv = ((tReaderDriver *)(pManager->readers[i].pDriver))->getTagList( &(pManager->readers[i]), pTags[i] );
            if ( rv != SCARD_S_SUCCESS )
            {
                PCSC_ERROR( pManager, rv, "driver->getTagList():");
                RESET_READER( pManager->readers[i] );
                if ( pTags[i] != NULL )
                    free( pTags[i] );
                pTags[i] = NULL;
            }
            /* accumulate the total number of tags found */
            pManager->tagList.numTags += pManager->readers[i].tagList.numTags;
        }
    }

    /* now mash them all up into one big list */
    pManager->tagList.pTags = NULL; /* for the zero tag case */
    uniqueListIndex = 0;

    if ( pManager->tagList.numTags > 0 )
    {
        pManager->tagList.pTags = (tTag *)malloc( (pManager->tagList.numTags) * sizeof( tTag ) );

        /* copy all the individual lists across into the unique list */
        for( i = 0; i < pManager->nbReaders; i++)
        {
            /* make the pointer in the per-reader structure point to it's parts of the overall list */
            pManager->readers[i].tagList.pTags = &(pManager->tagList.pTags[uniqueListIndex]);

            /* for each of the tags detected in this reader */
            for ( j = 0; j < pManager->readers[i].tagList.numTags; j++ )
            {
                /* copy the tag from the tempory list to the unique one */
                pManager->tagList.pTags[uniqueListIndex] = (pTags[i])[j];

                TAG_TYPE_NAME_FROM_ENUM( pManager->tagList.pTags[uniqueListIndex].tagType, namePointer );

                sprintf(messageString, "Tag ID:   %s\tType: %s", pManager->tagList.pTags[uniqueListIndex].uid, namePointer);

                readersLogMessage( pManager, LOG_INFO, 2, messageString);
                uniqueListIndex++;
            }

            /* free the space allocated for that list, even if it was never filled with anything */
            if ( pTags[i] )
                free( pTags[i] );
        }
    }

    sprintf( messageString, "Total Number of tags: %d", (int)(pManager->tagList.numTags) );
    readersLogMessage( pManager, LOG_INFO, 2, messageString );

   return (rv);
}
/************************ GET TAG LIST ***************************/
