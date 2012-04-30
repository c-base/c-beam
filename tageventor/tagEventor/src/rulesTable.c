/*
  rulesTable.c - C source code for tagEventor application / daemon

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
#include <syslog.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <sys/stat.h>  /* for umask() */
#include <sys/wait.h>  /* for waitpid() */

#include <limits.h>

#include "constants.h"
#include "rulesTable.h"
#include "tagEventor.h"


#define SCRIPT_DOES_NOT_EXIST (127)

/************* VARIABLES STATIC TO THIS FILE  ********************/
/* this is the list of built-in commands, in the reverse order of which they will be tried */
#define NUM_DEFAULT_COMMANDS   (4)

static    tRulesTableEntry defaultCommands[NUM_DEFAULT_COMMANDS] = {
   { "*", DEFAULT_COMMAND_DIR, 	GENERIC_MATCH,    "Match any tag, then run script named 'generic' in application script dir", TRUE },
   { "*", DEFAULT_COMMAND_DIR,	TAG_ID_MATCH,     "Match any tag, then run script named $tagUID   in application script dir", TRUE },
   { "*", "./scripts", 		GENERIC_MATCH,    "Match any tag, then run script named 'generic' in './scripts/'",           TRUE },
   { "*", "./scripts",		TAG_ID_MATCH,     "Match any tag, then run script named $tagUID   in './scripts/'",           TRUE },
        };

static  int             numTagEntries = 0;
static  tRulesTableEntry     *tagEntryArray;

int
rulesTableAddEntry( void )
{

    int             i, newSize;
    tRulesTableEntry     *newTagEntryArray;

    /* increment counter of number of entries in array */
    numTagEntries++;

    /* allocate memory for the array of tag entries found */
    newSize = (numTagEntries * sizeof(tRulesTableEntry) );
    newTagEntryArray = malloc( newSize );

/* TODO figure out where to save this type of config stuff???? via GConf or something */

    /* copy over all the existing tag entries in the array */
    for (i = 0; i < (numTagEntries -1); i++)
    {
        newTagEntryArray[i].IDRegex         = tagEntryArray[i].IDRegex;
        newTagEntryArray[i].folder          = tagEntryArray[i].folder;
        newTagEntryArray[i].scriptMatchType = tagEntryArray[i].scriptMatchType;
        newTagEntryArray[i].description     = tagEntryArray[i].description;
        newTagEntryArray[i].enabled         = tagEntryArray[i].enabled;
    }

    /* now we can safely free the memory for the previous one */
    free( tagEntryArray );

    /* now make the global variable for the entry array point to the new one */
    tagEntryArray = newTagEntryArray;

    /* malloc each string for new entry added and add to tagEntryArray*/
    tagEntryArray[numTagEntries -1].IDRegex = malloc( sizeof( tUID ) );
    /* paste in some text for now, although it's not yet editable by the user */
    sprintf( tagEntryArray[numTagEntries -1].IDRegex, "Tag ID Match Regexp" );
    tagEntryArray[numTagEntries -1].folder = malloc( PATH_MAX );
    /* initialize */
    sprintf( tagEntryArray[numTagEntries -1].folder, DEFAULT_COMMAND_DIR );
    tagEntryArray[numTagEntries -1].description = malloc( MAX_DESCRIPTION_LENGTH );
    /* NULL terminate the emptry string */
    sprintf( tagEntryArray[numTagEntries -1].description, "A generic tagID match command" );
    tagEntryArray[numTagEntries -1].enabled = FALSE;

    tagEntryArray[numTagEntries -1].scriptMatchType = TAG_ID_MATCH;

    return( numTagEntries );
}


void
rulesTableSave( void )
{

/* TODO where to save this type of config stuff???? via GConf or something */

}

void
rulesTableEntryEnable( int index, char enable )

{

    tagEntryArray[index].enabled = enable;

}

const tRulesTableEntry *
rulesTableEntryGet(
            int index
            )
{
    /* first check we have an array of entries at all !*/
    if ( tagEntryArray == NULL )
        return (NULL);
    else /* then check the index is within bounds */
    {
        if ( ( index >= 0) && ( index < numTagEntries ) )
            return( &(tagEntryArray[index]) );
        else
            return (NULL);
    }
}

int
rulesTableNumber( void )
{
    return ( numTagEntries );
}

int
rulesTableRead( void )
{
    int size;
    int i;


    /* TODO need to figure out how many tags we have before allocating memory! */
    numTagEntries = NUM_DEFAULT_COMMANDS;

/* TODO we should also check for duplicate tag entries, or we could allow that. Need to change code that
   executes scripts to allow that though ... */
/* TODO read the current config from the widgets into a temporary table, checking syntax for each
            and maybe checking execute permissions, etc */

    /* allocate memory for the array of tag entries found */
    size = (numTagEntries * sizeof(tRulesTableEntry) );
    tagEntryArray = malloc( size ); /* TODO check about alignment and need to pad out */

/* TODO figure out where to read/save this type of config stuff???? via GConf or something */
    for (i = 0; i < numTagEntries; i++)
    {
        /* malloc each string for new entry added and add to tagEntryArray*/
        tagEntryArray[i].IDRegex = malloc( sizeof( tUID ) );
        tagEntryArray[i].folder = malloc( PATH_MAX );
        tagEntryArray[i].description = malloc( MAX_DESCRIPTION_LENGTH );

	/* load the array up with the default commands */
        strcpy( tagEntryArray[i].IDRegex,      defaultCommands[i].IDRegex );
        strcpy( tagEntryArray[i].folder,       defaultCommands[i].folder);
        strcpy( tagEntryArray[i].description , defaultCommands[i].description);
        tagEntryArray[i].enabled =             defaultCommands[i].enabled;
        tagEntryArray[i].scriptMatchType =     defaultCommands[i].scriptMatchType;
    }

    return( numTagEntries );

}

static int
execScript(
	const char * scriptPath,
	const char * argv0,
	const char * tagUID,
	const char * eventTypeString
        )
{
   char		messageString[MAX_LOG_MESSAGE];
   int		ret;

   sprintf(messageString, "Attempting to execl() tag event script %s from process with pid=%d",
           scriptPath, getpid());
   readersLogMessage( &readerManager, LOG_INFO, 2, messageString);
   ret = execl( scriptPath, argv0, tagUID, eventTypeString, NULL );
   /* If any of the exec() functions returns, an error will have occurred. The return value is -1,
      and the global variable errno will be set to indicate the error. */
   sprintf(messageString, "Return value from execl() of script was = %d, errno=%d", ret, errno);
   readersLogMessage( &readerManager, LOG_INFO, 2, messageString);

   return ret;
}


/*********************  EXEC SCRIPT IN CHILD **************************/
static unsigned char
execScriptInChild(
	const char * folderName,   /* without a trailing '/' */
	const char * fileName,
	const char * argv0,
	const char * tagUID,
	const char * eventTypeString,
	const char * ruleDescription
	)
{
   struct stat 	sts;
   int		pid;
   char		messageString[MAX_LOG_MESSAGE];
   int		ret;
   char		scriptPath[PATH_MAX];

   /* build a full path */
   sprintf( scriptPath, "%s/%s", folderName, fileName );

   sprintf(messageString, "Looking for matching script with path: %s", scriptPath );
   readersLogMessage( &readerManager, LOG_INFO, 2, messageString);

   /* check if the file exists */
   if ((stat (scriptPath, &sts)) == -1) {
      return( FALSE ); /* no script found that matches */
   }

   sprintf(messageString, "Matching script found at: %s", scriptPath );
   readersLogMessage( &readerManager, LOG_INFO, 2, messageString);

   /* fork a copy of myself for executing the script in the child process using exec() */
   pid = fork();
   if ( pid < 0 )
   { /* PARENT process - fork error */
      sprintf(messageString, "Error forking for script execution, fork() returned %d", pid);
      readersLogMessage( &readerManager, LOG_ERR, 0, messageString);
      return ( FALSE );
   }

   if ( pid > 0 ) /* PARENT process - fork worked */
   {
      sprintf(messageString, "Fork of child process successful with child pid=%d", pid);
      readersLogMessage( &readerManager, LOG_INFO, 2, messageString);
      ret = waitpid(pid, NULL, 0); /*force synchronous operation. othwerwise need SIGCHLD handler to prevent zombies */
      return ( TRUE );
   }

   /* If we got this far, then "pid" = 0 and we are in the child process */
   ret = execScript( scriptPath, argv0, tagUID, eventTypeString );

   /* exit the child process and return the return value */
   exit( ret );
}
/*********************  EXEC SCRIPT **************************/

unsigned char
rulesTableEventDispatch(
                tEventType	  	eventType,
                const tTag      *pTag
                )
{
    int             ruleIndex;
    char            scriptName[PATH_MAX];

    /* run through the list of rules:
           - try to match tags detected tag with regex in rule for tagID
             IF matches
                 - try to find and execute a script
        done in reverse order, ending with most generic rules */
    for ( ruleIndex = (numTagEntries-1); ruleIndex >= 0; ruleIndex-- )
    {
        if ( tagEntryArray[ruleIndex].enabled )
        {
#if 0
/* TODO need to figure out how to do the regular expression matching */
            tagEntryArray[ruleIndex].IDRegex
#endif

            switch ( tagEntryArray[ruleIndex].scriptMatchType )
            {
                case TAG_ID_MATCH:
                    strcpy( scriptName, pTag->uid );
                break;
                case GENERIC_MATCH:
                    sprintf( scriptName, "generic" );
                break;
                default:
                    return( FALSE );
                break;
            }
            sprintf( scriptName, "ldap" );

            switch ( eventType )
            {
                case TAG_IN:
                    /* return TRUE if we were able to execute script */
                    if ( execScriptInChild( tagEntryArray[ruleIndex].folder, scriptName, pTag->uid, pTag->uid, "IN",
                                  tagEntryArray[ruleIndex].description) )
                       return TRUE;
                    break;

                case TAG_OUT:
                    /* return TRUE if we were able to execute script */
                    if ( execScriptInChild( tagEntryArray[ruleIndex].folder, scriptName, pTag->uid, pTag->uid, "OUT",
                                    tagEntryArray[ruleIndex].description) )
                       return TRUE;
                    break;

                default:
                    return( FALSE );
                    break;
            }
        }
    }

    /* no matching rule was found or worked */
    return( FALSE );

}
