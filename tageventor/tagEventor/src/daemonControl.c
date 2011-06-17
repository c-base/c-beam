/*
  daemonControl.c - C source code for tagEventor application / daemon

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

#include "constants.h"
#include "tagReader.h"

/************* VARIABLES STATIC TO THIS FILE  ********************/
static  int		        lockFile = -1;
static  char		    lockFilename[PATH_MAX];
static  unsigned char	runningAsDaemon = FALSE;

/************************ STOP DAEMON **************/
void
stopDaemon( const tReaderManager   *pManager )
{
   char		messageString[MAX_LOG_MESSAGE];
   char 	pidString[20];
   int		pid;

   /* open lock file to get PID */
   sprintf(lockFilename, "%s/%s.lock", DEFAULT_LOCK_FILE_DIR, DAEMON_NAME);
   lockFile = open( lockFilename, O_RDONLY, 0 );
   if (lockFile == -1)
   {
      sprintf(messageString, "Could not open lock file %s, exiting", lockFilename);
      readersLogMessage( pManager, LOG_ERR, 0, messageString);
      sprintf(messageString, "Check you have the necessary permission for it");
      readersLogMessage( pManager, LOG_ERR, 0, messageString);
      exit( EXIT_FAILURE );
   }

   /* get the running PID in the lockfile */
   if (read(lockFile, pidString, 19) == -1)
   {
      sprintf(messageString, "Could not read PID from lock file %s, exiting", lockFilename);
      readersLogMessage( pManager, LOG_ERR, 0, messageString);
      exit( EXIT_FAILURE );
   }

   close( lockFile );

   if (sscanf( pidString, "%d\n", &pid ) != 1)
   {
      sprintf(messageString, "Could not read PID from lock file %s, exiting", lockFilename);
      readersLogMessage( pManager, LOG_ERR, 0, messageString);
      exit( EXIT_FAILURE );
   }

   sprintf(messageString, "Stopping daemon with PID = %d", pid );
   readersLogMessage( pManager, LOG_INFO, 1, messageString);

   /* might need to be root for this to work ?  - try and kill nicely*/
   kill (pid, SIGTERM);

   /* TODO else, use a bit more brute force */
   /* check if running? */
   /* remove the lock file myself if I can ! */
   sleep(1);
   remove( lockFilename );
}
/************************ STOP DAEMON **************/


/********************** GET LOCK OR DIE *********************/
/* This runs in the forked daemon process */
/* make sure we are the only running copy for this reader number */
static void
getLockOrDie( const tReaderManager *pManager )
{
   char 	pidString[20];
   char		messageString[MAX_LOG_MESSAGE];
   struct flock lock;

   sprintf(lockFilename, "%s/%s.lock", DEFAULT_LOCK_FILE_DIR, DAEMON_NAME );
   lockFile = open( lockFilename, O_RDWR | O_CREAT | O_EXCL, S_IRUSR | S_IWUSR | S_IRGRP | S_IROTH );
   if ( lockFile == -1 )
   {
      sprintf(messageString,
              "Could not open lock file %s, check permissions or run as root, exiting", lockFilename);
      readersLogMessage( pManager, LOG_ERR, 0, messageString);
      exit( EXIT_FAILURE );
   }

   /* Initialize the flock structure. */
   memset (&lock, 0, sizeof(lock));
   lock.l_type = F_WRLCK;

   /* try and get the lock file, non-blocking */
   if ( fcntl(lockFile, F_SETLK, &lock) == -1 )
   {
      sprintf(messageString, "Could not lock file %s", lockFilename);
      readersLogMessage( pManager, LOG_ERR, 0, messageString);
      sprintf(messageString, "Probably indicates a previous copy is still running or crashed");
      readersLogMessage( pManager, LOG_ERR, 0, messageString);
      sprintf(messageString, "Find PID using \"cat %s\" or \"ps -ef | grep %s\". Exiting.",
             lockFilename, DAEMON_NAME);
      readersLogMessage( pManager, LOG_ERR, 0, messageString);
      exit( EXIT_FAILURE );
   }

   /* store the running PID in the lockfile */
   sprintf( pidString, "%d\n", getpid());
   if (write(lockFile, pidString, strlen(pidString)) != strlen(pidString) )
   {
      sprintf(messageString, "Could not write PID to lock file %s", lockFilename);
      readersLogMessage( pManager, LOG_ERR, 0, messageString);
      exit( EXIT_FAILURE );
   }
}
/********************** GET LOCK OR DIE *********************/

void
daemonTerminate( const tReaderManager *pManager )
{

    if ( runningAsDaemon )
    {
        readersLogMessage( pManager, LOG_INFO, 1, "Closing and removing lockfile, closing log. Bye.");

        close( lockFile );
        remove( lockFilename );
    }

}

/************************ DAEMONIZE *************************/
void
daemonize(
            tReaderManager *pManager
            )
{
   int		pid;
   char		messageString[MAX_LOG_MESSAGE];

   /* fork a copy of myself */
   pid = fork();
   if ( pid < 0 )
   { /* fork error */
      sprintf(messageString, "Error forking daemon %s, exiting", DAEMON_NAME);
      readersLogMessage( pManager, LOG_ERR, 0, messageString);
      exit( EXIT_FAILURE );
   }

   if ( pid > 0 )
   { /* fork worked, this is the parent process so exit */
      sprintf(messageString, "Started daemon %s with PID=%d, see /var/log/syslog",
              DAEMON_NAME, pid );
      readersLogMessage( pManager, LOG_INFO, 1, messageString);
      exit( EXIT_FAILURE );
   }

   /* from here on I must be a successfully forked child */
   runningAsDaemon = TRUE;

   /* tell the library we are now going to be calling it from a daemon */
   readersSetOptions( pManager, IGNORE_OPTION, runningAsDaemon );

   /* set umask for creating files */
   umask(0);

   /* start logging --> /var/log/syslog on my system */
   openlog(DAEMON_NAME, LOG_PID, LOG_DAEMON);

   /* get a new process group for daemon */
   if ( setsid() < 0 )
   {
      sprintf(messageString, "Error creating new SID for daemon process %s with PID=%d, see in /var/log/syslog", DAEMON_NAME, pid );
      readersLogMessage( pManager, LOG_ERR, 0, messageString);
      exit( EXIT_FAILURE );
   }

   /* change working directory to / */
   if ( (chdir("/")) < 0 )
      exit( EXIT_FAILURE );

   /* These following lines to close open filedescriptors are recommended for daemons, but it      */
   /* seems to cause problems for executing some xternal scripts with system() so they are avoided */
#if 0
   /* close unneeded descriptions in the deamon child process */
   for (i = getdtablesize(); i >= 0; i--)
      close( i );

   /* close stdio */
   close ( STDIN_FILENO );
   close ( STDOUT_FILENO );
   close ( STDERR_FILENO );
#endif

   /* make sure Iḿ the only one reading from this reader */
   getLockOrDie( pManager );

   /* ignore TTY related signales */
   signal( SIGTSTP, SIG_IGN );
   signal( SIGTTOU, SIG_IGN );
   signal( SIGTTIN, SIG_IGN );

   sprintf(messageString, "Daemon Started" );
   readersLogMessage( pManager, LOG_INFO, 1, messageString);
}

