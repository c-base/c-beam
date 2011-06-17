/*
  explorer.c - C source code for gtagEventor Gtk/GNOME explorer

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

#ifdef BUILD_EXPLORER
#include <stdlib.h>
#include <unistd.h>
#include <gtk/gtk.h>
#include <string.h>

#include <tagReader.h>

#include "stringConstants.h"
#include "tagEventor.h"
#include "systemTray.h"
#include "explorer.h"

static GtkWidget        *explorerWindow = NULL;
static GtkTreeStore     *store = NULL;
static GtkWidget        *treeView;

static GtkTreeIter      rootIter;  /* Parent iter */

enum {
    OBJECT_COLUMN,
    DESCRIPTION_COLUMN,
    N_COLUMNS };


static void
explorerWindowDestroy( void )
{

    gtk_widget_destroy( explorerWindow );
    explorerWindow = NULL;

}


/* Call back for the close button */
static void
closeSignalHandler(
                   GtkDialog    *dialog,
                   gpointer     user_data
                   )
{
    explorerWindowDestroy();
}

/* This get's called when the user closes the window using the Window Manager 'X' box */
static char
deleteSignalHandler(
            GtkWidget *widget,
            GdkEvent  *event,
            gpointer   data
            )
{
    /* If you return FALSE GTK will propograte event and we'll get a "destroy" signal. */
    return( FALSE );
}

static void
destroy(
        GtkWidget *widget,
        gpointer   data
        )
{

    /* destroy the explorer window */
    explorerWindowDestroy();

}

static void
tagAdd(
        const tReaderManager    *pManager,
        GtkTreeIter             *pTagListIter,
        int                     readerNumber,
        int                     tagNumber
    )
{
    char                numberString[20];
    const char          *tagTypeName;
    GtkTreeIter         tagIter, tagTypeIter, tagDataIter, dataCharIter, dataHexIter;

    sprintf( numberString, "Tag %d", tagNumber );

    gtk_tree_store_insert_before( store, &tagIter, pTagListIter, NULL );
    gtk_tree_store_set( store, &tagIter,
                        OBJECT_COLUMN, numberString,
                        DESCRIPTION_COLUMN, pManager->readers[readerNumber].tagList.pTags[tagNumber].uid, -1);

    TAG_TYPE_NAME_FROM_ENUM( pManager->readers[readerNumber].tagList.pTags[tagNumber].tagType, tagTypeName );
    gtk_tree_store_append( store, &tagTypeIter, &tagIter );
    gtk_tree_store_set( store, &tagTypeIter,
                        OBJECT_COLUMN, "TagType",
                        DESCRIPTION_COLUMN, tagTypeName, -1);

    /* if we have tag contents then show them */
    if ( pManager->readers[readerNumber].tagList.pTags[tagNumber].contents.dataSize > 0 )
    {
        sprintf( numberString, "%d Bytes", pManager->readers[readerNumber].tagList.pTags[tagNumber].contents.dataSize );
        gtk_tree_store_append( store, &tagDataIter, &tagIter );
        gtk_tree_store_set( store, &tagDataIter,
                            OBJECT_COLUMN, "Contents",
                            DESCRIPTION_COLUMN, numberString, -1);

        gtk_tree_store_append( store, &dataCharIter, &tagDataIter );
        gtk_tree_store_set( store, &dataCharIter,
                            OBJECT_COLUMN, "ASCII",
                            DESCRIPTION_COLUMN, pManager->readers[readerNumber].tagList.pTags[tagNumber].contents.pData, -1);

        gtk_tree_store_append( store, &dataHexIter, &tagDataIter );
        gtk_tree_store_set( store, &dataHexIter,
                            OBJECT_COLUMN, "Hex",
                            DESCRIPTION_COLUMN, pManager->readers[readerNumber].tagList.pTags[tagNumber].contents.extensionHook, -1);

    }

}

void
explorerRemoveReader(
                int                     readerNumber
                )
{
    GtkTreeIter  iter;

    if ( gtk_tree_model_iter_nth_child( GTK_TREE_MODEL( store ), &iter, &rootIter, readerNumber ) )
        gtk_tree_store_remove( store, &iter );

}

void
explorerAddReader(
                int                     readerNumber
                )
{
    char                numberString[20];
    int                 tagNum;
    GtkTreeIter         readerIter, nameIter, driverIter, SAMIter, SAMIDIter, SAMSerialIter, tagListIter;

    sprintf( numberString, "Reader %d", readerNumber );

    gtk_tree_store_insert( store, &readerIter, &rootIter, readerNumber );  /* Acquire a child iterator */

    /* if we are currently connected to this reader then we can show info */
    if ( readerManager.readers[readerNumber].hCard != NULL )
    {
        gtk_tree_store_set( store, &readerIter,
                            OBJECT_COLUMN, numberString,
                            DESCRIPTION_COLUMN, "Connected", -1);

        /***************** NAME **********************/
        gtk_tree_store_append( store, &nameIter, &readerIter );
        gtk_tree_store_set( store, &nameIter,
                        OBJECT_COLUMN, "Name/Firmware",
                        DESCRIPTION_COLUMN, readerManager.readers[readerNumber].name, -1);

        /***************** DRIVER **********************/
        gtk_tree_store_append( store, &driverIter, &readerIter );
        gtk_tree_store_set( store, &driverIter,
                            OBJECT_COLUMN, "Driver",
                            DESCRIPTION_COLUMN, readerManager.readers[readerNumber].driverDescriptor, -1);

        /******************** SAM **********************/
        gtk_tree_store_append( store, &SAMIter, &readerIter );
        /* if there is a SAM present then show it's details */
        if ( readerManager.readers[readerNumber].SAM )
        {
            gtk_tree_store_set( store, &SAMIter,
                                OBJECT_COLUMN, "SAM",
                                DESCRIPTION_COLUMN, "Present", -1);

            gtk_tree_store_append( store, &SAMIDIter, &SAMIter );
            gtk_tree_store_set( store, &SAMIDIter,
                                OBJECT_COLUMN, "ID",
                                DESCRIPTION_COLUMN, readerManager.readers[readerNumber].SAM_id, -1);

            gtk_tree_store_append( store, &SAMSerialIter, &SAMIter );
            gtk_tree_store_set( store, &SAMSerialIter,
                                OBJECT_COLUMN, "Serial",
                                DESCRIPTION_COLUMN, readerManager.readers[readerNumber].SAM_serial, -1);
        }
        else
            gtk_tree_store_set( store, &SAMIter,
                                OBJECT_COLUMN, "SAM",
                                DESCRIPTION_COLUMN, "No SAM present", -1);

        /******************** TAGS **********************/
        sprintf( numberString, "%d tags", readerManager.readers[readerNumber].tagList.numTags);
        gtk_tree_store_append( store, &tagListIter, &readerIter );
        gtk_tree_store_set( store, &tagListIter,
                            OBJECT_COLUMN, "Tags",
                            DESCRIPTION_COLUMN, numberString, -1);

        for ( tagNum = 0; tagNum < readerManager.readers[readerNumber].tagList.numTags; tagNum++ )
             tagAdd( &readerManager, &tagListIter, readerNumber, tagNum );
    }
    else
    {
        /* we have not connected to this reader, see if it exists */
        if ( readerNumber >= readerManager.nbReaders )
        {
            gtk_tree_store_set( store, &readerIter,
                            OBJECT_COLUMN, numberString,
                            DESCRIPTION_COLUMN, "Not detected", -1);
        }
        else
        {   /* there is such a reader in the system, although we're not connected to it */
            gtk_tree_store_set( store, &readerIter,
                                OBJECT_COLUMN, numberString,
                                DESCRIPTION_COLUMN, "Not connected", -1);

            if ( readerManager.readers[readerNumber].name != NULL )
            {
                /***************** NAME **********************/
                gtk_tree_store_append( store, &nameIter, &readerIter );
                gtk_tree_store_set( store, &nameIter,
                                OBJECT_COLUMN, "Name/Firmware",
                                DESCRIPTION_COLUMN, readerManager.readers[readerNumber].name, -1);

                /***************** DRIVER **********************/
                gtk_tree_store_append( store, &driverIter, &readerIter );
                gtk_tree_store_set( store, &driverIter,
                                    OBJECT_COLUMN, "Driver",
                                    DESCRIPTION_COLUMN, "Information not available", -1);
            }
        }
    }
}

static void
explorerFillTreeModel( void )
{

    int         i;
    char        descriptionText[40];

    gtk_tree_store_append( store, &rootIter, NULL);  /* Acquire a top-level iterator */

    /* check if we were able to connect to PCSD */
    if ( readerManager.hContext == NULL )
        sprintf( descriptionText, "Not Connected to 'pcscd', check syslog and that 'pcscd' is running" );
    else
        sprintf( descriptionText, "Connected to 'pcscd', %d readers detected", readerManager.nbReaders );

    gtk_tree_store_set( store, &rootIter,
                        OBJECT_COLUMN, PROGRAM_NAME,
                        DESCRIPTION_COLUMN, descriptionText, -1);

    /* add branch for each reader that exists in the system */
    for ( i = 0; i < readerManager.nbReaders; i++ )
        explorerAddReader( i );

}

static GtkWidget *
buildExplorer ( void *pData )
{
    GtkWidget   *dialog;
    GtkWidget   *vbox, *buttonBox, *closeButton, *statusBar;
    char        windowTitle[strlen(PROGRAM_NAME) + strlen(TAG_EVENTOR_EXPLORER_WINDOW_TITLE) + 10];
    GtkTreeViewColumn *column;
    GtkCellRenderer *renderer;


    dialog = gtk_window_new( GTK_WINDOW_TOPLEVEL );
    sprintf(windowTitle, "%s%s", PROGRAM_NAME, TAG_EVENTOR_EXPLORER_WINDOW_TITLE );
    gtk_window_set_title( (GtkWindow *)dialog, windowTitle );

    /* set the icon for the window */
    gtk_window_set_icon_name( (GtkWindow *)dialog, ICON_NAME_CONNECTED );

    /* When the window is given the "delete" signal (this is given
     * by the window manager, usually by the "close" option, or on the
     * titlebar) */
    g_signal_connect (G_OBJECT (dialog), "delete_event",
		      G_CALLBACK (deleteSignalHandler), NULL);

    /* Here we connect the "destroy" event to a signal handler.
     * This event occurs when we call gtk_widget_destroy() on the window,
     * or if we return FALSE in the "delete_event" callback. */
    g_signal_connect (G_OBJECT (dialog), "destroy",
		      G_CALLBACK (destroy), NULL);

    /******************************* Vertical Box ***********************************/
    /* vertical box to hold things, Not homogeneous sizes and spaceing 0 */
    vbox = gtk_vbox_new(FALSE, 0);

    /* This packs the vbox into the window (a gtk container). */
    gtk_container_add (GTK_CONTAINER (dialog), vbox);

    /****************************** Tree View ***************************************/
    /* Create a model for the tree view. with two text columns */
    store = gtk_tree_store_new ( N_COLUMNS, G_TYPE_STRING, G_TYPE_STRING);

    /* custom function to fill the model with data */
    explorerFillTreeModel();

    /* Create a view */
    treeView = gtk_tree_view_new_with_model ( GTK_TREE_MODEL ( store ) );

    /* The view now holds a reference.  We can get rid of our own reference */
    g_object_unref (G_OBJECT (store));

    /* Create a columnfor the object name */
    renderer = gtk_cell_renderer_text_new ();
    column = gtk_tree_view_column_new_with_attributes ("Object", renderer,
                                                   "text", OBJECT_COLUMN,
                                                   NULL);
    gtk_tree_view_append_column (GTK_TREE_VIEW (treeView), column);

    /* Second column.. description of object */
    renderer = gtk_cell_renderer_text_new ();
    column = gtk_tree_view_column_new_with_attributes ("Description", renderer,
                                                      "text", DESCRIPTION_COLUMN,
                                                      NULL);
    gtk_tree_view_append_column( GTK_TREE_VIEW (treeView), column);

    gtk_tree_view_set_enable_tree_lines( GTK_TREE_VIEW(treeView), TRUE );

    gtk_tree_view_expand_all( GTK_TREE_VIEW( treeView ) );

    /************** Pack in Tree View *********************************/
    /* This packs the scrolled window into the vbox (a gtk container). */
    gtk_box_pack_start( GTK_BOX(vbox), treeView, TRUE, TRUE, 3);


    /******************************* Button Box ***************************************/
    /* create the box for the buttons */
    buttonBox = gtk_hbox_new( FALSE, 0);

    /********************************************* Close Button ***********************/
    closeButton = gtk_button_new_from_stock( "gtk-close" );

    /* This packs the button into the hbutton box  (a gtk container). */
    gtk_box_pack_end( GTK_BOX(buttonBox), closeButton, FALSE, TRUE, 3);

    /* When the button receives the "clicked" signal, it will call the
     * function applyChanges() passing it NULL as its argument. */
     /* TODO can't get this signal to work and close things! */
    g_signal_connect (G_OBJECT (closeButton), "released", G_CALLBACK (closeSignalHandler), NULL);

    /**************************** End of buttons **************************************/
    /* This packs the hbutton box into the vbox (a gtk container). */
    gtk_box_pack_start(GTK_BOX(vbox), buttonBox, FALSE, TRUE, 3);

   /**************************** Status Bar ******************************************/
    /* create the status bar */
    statusBar = gtk_statusbar_new();

    /* This packs the status bar into the vbox (a gtk container)  */
    gtk_box_pack_start(GTK_BOX(vbox), statusBar, FALSE, TRUE, 0);

    return ( dialog );

}

void
explorerActivate( void *readersArray )
{

    /* if it exists delete it as the situation might have changed */
    if ( explorerWindow )
    {
        /* make sure it's visible */
        gtk_window_present( (GtkWindow *)explorerWindow );
    }
    else
    {
        /* build the widget tree for the entire UI */
        explorerWindow = buildExplorer( readersArray );

        /* Show window, and recursively all contained widgets */
        gtk_widget_show_all( explorerWindow );
    }

}


void
explorerViewUpdate( void )
{

/* TODO doesn't seem to work yet! */
#if 0
    if ( explorerWindow )
        gtk_tree_view_set_model( GTK_TREE_VIEW( treeView ), GTK_TREE_MODEL( store ) );

this gives an assertion error and above too
    gtk_widget_queue_draw(GTK_WIDGET( treeView ));
#endif

/* IN theory not needed at all !!!*/

}

#endif
