/*
  rulesEditor.c - C source code for gtagEventor Gtk/GNOME rules editor

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

#ifdef BUILD_RULES_EDITOR
#include <stdlib.h>
#include <unistd.h>
#include <gtk/gtk.h>
#include <string.h>

#include "stringConstants.h"
#include "systemTray.h"
#include "rulesEditor.h"
#include "rulesEditorHelp.h"
#include "rulesEditor.h"
#include "rulesTable.h"
#include "aboutDialog.h"

#define DEFAULT_WIDTH_PIX       (620)
#define DEFAULT_HEIGHT_PIX      (270)

#define NUM_COLUMNS             (5)
static const gchar      *columnHeader[NUM_COLUMNS] = { "Rule Description", "Tag ID Match", "Folder", "Match", "Enabled" };
static char             savePending = FALSE;
static GtkWidget        *rulesEditorWindow = NULL, *statusBar = NULL, *applyButton = NULL, *closeButton = NULL;
static GtkWidget        *instructionLabel;


/* This will be called by the systemTray when it wants to quit, and hence asks us here */
/* to quite too. before doing so we check our status. If we have something to do then  */
/* we pop-up the dialogs to do it, and we tell the systemTray to not quit just yet     */
char
rulesEditorQuit( void )
{
    /* request from the systemtrayIcon to exit */
    /* if we can, then close our own stuff and tell the systemtrayIcon it can also exit */
    if (savePending == FALSE )
        return (TRUE ); /* can exit */
    else
    {
        /* TODO call cpanel exit routines to handle the saving etc */
        return( FALSE );
    }
}

void
rulesEditorSetStatus(
                        char        connected,
                        const char  *message
                        )
{

    /* put the result onto the status bar */
    if ( rulesEditorWindow )
        gtk_statusbar_push((GtkStatusbar *)statusBar, 0, (gchar *)message);

}

static void
hiderulesEditorWindow( void )
{

    /* hide the main window if it exists ADN is visible */
    if ( rulesEditorWindow )
    {
        gtk_widget_hide( rulesEditorWindow );
    }

}


/* Call back for the close button */
static void
closeSignalHandler(
                   GtkDialog    *dialog,
                   gpointer     user_data
                   )
{
    /* if the button was sensitive and could be pressed then it's OK to close window ASAP */
    hiderulesEditorWindow();
}

/* Call back for the cancel button */
static void
cancelSignalHandler(
                   GtkDialog    *dialog,
                   gpointer     user_data
                   )
{
/* TODO we should (arguable, reset the tag array back to the way it was when the rules editor was opened,
   or when the last save was made..... so that the changes aren't kept around in memory forever
*/
    /* OK to close window ASAP */
    hiderulesEditorWindow();

}

/* This get's called when the user closes the window using the Window Manager 'X' box */
static char
deleteSignalHandler(
            GtkWidget *widget,
            GdkEvent  *event,
            gpointer   data
            )
{

    if ( savePending == FALSE )
    {
        /* If you return FALSE GTK will propograte event and we'll get a "destroy" signal. */
        return( FALSE );
    }
    else
    {
      /* Returning TRUE means you don't want the event propograted further. */
/* TODO Pop-up the window here */
        return( TRUE );
    }
}

static void
destroy(
        GtkWidget *widget,
        gpointer   data
        )
{

    /* hide the main cpanel window */
    hiderulesEditorWindow();

    /* it seems that when this get's called the widget actually get's destroyed */
    /* so, show it's not existant and on next activate it will get re-built */
    rulesEditorWindow = NULL;

}

static void
setSavePending( unsigned char pending )
{

    savePending = pending;
    gtk_widget_set_sensitive( applyButton, pending );
    gtk_widget_set_sensitive( closeButton, !pending );

}

/* Callback for when each entry's file selection is changed */
static void
folderChosen(
             GtkWidget *widget,
             gpointer   entryIndex
             )
{
    gchar *folderName;

    /* get the button state and put into tagEntryArray */

    /* get the name of the folder chosen by the user via the dialog */
    folderName = gtk_file_chooser_get_current_folder ( (GtkFileChooser *) widget );

/* TODO note that this MIGHT not be in ASCII according to the manual
File Names and Encodings
When the user is finished selecting files in a GtkFileChooser, your program can get the
selected names either as filenames or as URIs. For URIs, the normal escaping rules are
applied if the URI contains non-ASCII characters. However, filenames are always returned
in the character set specified by the G_FILENAME_ENCODING environment variable.
Please see the Glib documentation for more details about this variable.

Important
This means that while you can pass the result of gtk_file_chooser_get_filename() to
open(2) or fopen(3), you may not be able to directly set it as the text of a GtkLabel
widget unless you convert it first to UTF-8, which all GTK+ widgets expect.
You should use g_filename_to_utf8() to convert filenames into strings that can be
passed to GTK+ widgets.
*/

/*
then set the tagentry using the index
*/

    setSavePending( TRUE );

}

/* callback for match drop down */
static void
matchChosen(
             GtkWidget *widget,
             gpointer   entryIndex
             )
{

/* Get the new statr and save it into the tag Array */
/* TODO figure this out how to get the entry !!!!     tagEntryArray[(int)entryIndex].script = gtk_toggle_button_get_active( (GtkToggleButton *)widget); */

    /* change means a save is now needed */
    setSavePending( TRUE );

}


/* Callback for when each entry's toggle button to enable it is toggled */
static void
enableChange(
             GtkWidget *widget,
             gpointer   entryIndex
             )
{

    /* get the button state and put into tagEntryArray */
/* TODO check that casting this is correct, and it's not the destination of the pointer */
    rulesTableEntryEnable( (int)entryIndex, gtk_toggle_button_get_active( (GtkToggleButton *)widget) );

    /* change means a save is now needed */
    setSavePending( TRUE );

}

static void
applyChanges( void )
{

    /* if all is OK, then modify the table we use to process events */
    /* save the changes */
    rulesTableSave();

    /* now the table used to process events matches what's in the UI so we are in sync */
    /* change means a save is now needed */
    setSavePending( FALSE );

}

static void
tableAddRow( GtkTable *pTable, int i )
{
    GtkWidget           *label, *chooser, *enable, *description;
    GtkWidget           *matchMenu, *matchMenuItem;
    GError              *pError;

    const tRulesTableEntry   *pTagEntry;

    /* get a pointer to this entry in the table */
    pTagEntry = rulesTableEntryGet( i );

    /* description entry of upto 80 characters which can benefit from expanding horizontally*/
    description = gtk_entry_new();
    gtk_entry_set_max_length( (GtkEntry *)description, MAX_DESCRIPTION_LENGTH);
    gtk_entry_set_text((GtkEntry *)description, pTagEntry->description);
    /* attach a new widget into the table */
    gtk_table_attach(pTable, (GtkWidget *)description, 0, 1, i+1, i+2, GTK_EXPAND | GTK_FILL, GTK_FILL, 4, 0 );

    /* Tag ID match regexp of upto 20 char which does not need to expand with window size */
    label = gtk_label_new(pTagEntry->IDRegex);
    gtk_label_set_width_chars( (GtkLabel *)label, 20 );
    gtk_label_set_max_width_chars( (GtkLabel *)label, 20 );
    /* attach a new widget into the table */
    gtk_table_attach(pTable, label, 1, 2, i+1, i+2, GTK_FILL, GTK_FILL, 5, 0 );

    /* file chooser for folder to look for script in, which may have long name and so expand*/
    chooser = gtk_file_chooser_button_new( "Navigate to the folder to search in for scripts, then press Open", GTK_FILE_CHOOSER_ACTION_OPEN );
/* TODO I think this should be GTK_FILE_CHOOSER_ACTION_SELECT_FOLDER but it doesn't work as I expected
   opening only a list of bookmarks not a full dialog, so we may have to create a custom dialog and then
   use gtk_file_chooser_button_new_with_dialog() to attach the dialog to this button */

    /* if the folder is defined, configure the widget with that folder as if selected by user */
    if (pTagEntry->folder)
    {
/* TODO NOTE: Manuel says we should really convert to UTF for use in a widget
g_filename_to_utf8 ()
gchar*              g_filename_to_utf8                  (const gchar *opsysstring,
                                                         gssize len,
                                                         gsize *bytes_read,
                                                         gsize *bytes_written,
                                                         GError **error);
*/
        gtk_file_chooser_set_filename( GTK_FILE_CHOOSER (chooser), pTagEntry->folder );
    }
/* TODO add a file filter to only allow selection of folders ? */

    /* attach a new widget into the table */
    gtk_table_attach(pTable, chooser, 2, 3, i+1, i+2, GTK_FILL, GTK_FILL, 0, 2 );
    /* add a callback to the button which will be passed the index of this entry in the tagEntryArray */
    g_signal_connect (G_OBJECT (chooser), "file-set", G_CALLBACK (folderChosen), (gpointer)i);


    /* for executing events better to restrict folders to those on the local file syste */
    gtk_file_chooser_set_local_only( GTK_FILE_CHOOSER (chooser), TRUE );
    /* otherwise it's a new blank name, so default to width of 10 characters */
    gtk_file_chooser_button_set_width_chars((GtkFileChooserButton *)chooser, 10 );
    /* add short-cut to the dialog to help the user find folders related to gtagEventor */
    gtk_file_chooser_add_shortcut_folder( GTK_FILE_CHOOSER (chooser),
                                          DEFAULT_COMMAND_DIR, &pError );


    /*  add the match option menu */
    matchMenu = gtk_menu_new();

    matchMenuItem = gtk_radio_menu_item_new_with_label( NULL, "Tag ID" );
    gtk_menu_shell_append( GTK_MENU_SHELL( matchMenu ), matchMenuItem );
    g_signal_connect (G_OBJECT (matchMenuItem), "toggled", G_CALLBACK (matchChosen), (gpointer)TAG_ID_MATCH );
    gtk_widget_show( matchMenuItem );

    matchMenuItem = gtk_radio_menu_item_new_with_label( NULL, "'generic'" );
    gtk_menu_shell_append( GTK_MENU_SHELL( matchMenu ), matchMenuItem );
    g_signal_connect (G_OBJECT (matchMenuItem), "toggled", G_CALLBACK (matchChosen), (gpointer)GENERIC_MATCH );
    gtk_widget_show( matchMenuItem );

    gtk_widget_show( matchMenu );

    gtk_table_attach(pTable, matchMenu, 3, 4, i+1, i+2, GTK_FILL, GTK_FILL, 0, 0 );

    enable = gtk_check_button_new(); /* check button to enable the script for this tag */
    gtk_toggle_button_set_active( (GtkToggleButton *)enable, pTagEntry->enabled);
    /* attach a new widget into the table */
    gtk_table_attach(pTable, enable, 4, 5, i+1, i+2, GTK_FILL, GTK_FILL, 0, 0 );
    /* add a callback to the button which will be passed the index of this entry in the tagEntryArray */
    g_signal_connect (G_OBJECT (enable), "toggled", G_CALLBACK (enableChange), (gpointer)i);

    /* make the new widgets visible */
    gtk_widget_show( label );
    gtk_widget_show( chooser );
    gtk_widget_show( description );
    gtk_widget_show( matchMenu );
    gtk_widget_show( enable );

}


static void
addColumnHeaders(
                GtkTable *pTable
                )
{
    int i;
    GtkWidget           *label;

    /* add the four column labels in the table*/
    for (i = 0; i < NUM_COLUMNS; i++)
    {
        label = gtk_label_new( columnHeader[i] );

        /* attach a new widget into the table in column 'i', row 0 */
        gtk_table_attach(pTable, label, i, i+1, 0, 1, GTK_FILL, GTK_FILL, 5, 3 );

        gtk_widget_show( label );
    }
}


static void
addTagEntry(
            GtkWidget *widget,
            gpointer *pTable
            )
{
    int i, numEntries;

    numEntries = rulesTableAddEntry();

    /* resize the table widget - with an extra row for the header */
    gtk_table_resize( (GtkTable *)pTable, (numEntries + 1), NUM_COLUMNS );

    /* if this is the first tag / row we add then put in the column headers */
    if ( numEntries == 1 )
    {
        /* delete the label that was put in earlier with instruction */
        gtk_widget_destroy( instructionLabel );

        addColumnHeaders( (GtkTable *)pTable );
    }

    /* this entry's index */
    i = (numEntries -1);
    tableAddRow((GtkTable *)pTable, i);

/* TODO try and force scroll or focus on the new row so that it becomes visible */
}

static void
fillTable(
            GtkTable    *pTable,
            int         numTags
            )
{
    int         i;

    if ( numTags == 0 )
    {
        instructionLabel = gtk_label_new( "No Tags configured. Use the 'Add' button below to configure a tag" );
        gtk_table_attach(pTable, instructionLabel, 0, 1, 0, 1, GTK_FILL | GTK_EXPAND, GTK_FILL | GTK_EXPAND, 10, 10 );
    }
    else
    {
        /* resize the table to be big enough to hold all entries */
        /* Row 0  =  Column headers */
        /* So we need numConfigTags + 1 rows, and 4 columns */
        gtk_table_resize( (GtkTable *)pTable, (numTags + 1), NUM_COLUMNS );

        addColumnHeaders( (GtkTable *)pTable );

        /* add a new row of widgets for each tag script configuration found */
        for (i = 0; i < numTags; i++)
            tableAddRow(pTable, i );
    }
}


static GtkWidget *
buildrulesEditor ( void  )
{
    GtkWidget   *mainWindow;
    GtkWidget   *vbox, *scroll, *buttonBox, *table, *helpText;
    GtkWidget   *helpButton, *aboutButton, *addButton, *cancelButton;
    int         numEntries;
    char        windowTitle[strlen(PROGRAM_NAME) + strlen(RULES_EDITOR_WINDOW_TITLE) + 10];

    /******************************* Main Application Window ************************/
    mainWindow = gtk_window_new( GTK_WINDOW_TOPLEVEL );
    sprintf(windowTitle, "%s%s", PROGRAM_NAME, RULES_EDITOR_WINDOW_TITLE);
    gtk_window_set_title( (GtkWindow *)mainWindow, windowTitle );
    /* Smallest height possible then should expand to hold what's needed */
    gtk_window_set_default_size( (GtkWindow *)mainWindow, DEFAULT_WIDTH_PIX, DEFAULT_HEIGHT_PIX );

    /* set the icon for the window */
    gtk_window_set_icon_name( (GtkWindow *)mainWindow, ICON_NAME_CONNECTED );

    /* When the window is given the "delete" signal (this is given
     * by the window manager, usually by the "close" option, or on the
     * titlebar) */
    g_signal_connect (G_OBJECT (mainWindow), "delete_event",
		      G_CALLBACK (deleteSignalHandler), NULL);

    /* Here we connect the "destroy" event to a signal handler.
     * This event occurs when we call gtk_widget_destroy() on the window,
     * or if we return FALSE in the "delete_event" callback. */
    g_signal_connect (G_OBJECT (mainWindow), "destroy",
		      G_CALLBACK (destroy), NULL);


    /******************************* Vertical Box ***********************************/
    /* vertical box to hold things, Not homogeneous sizes and spaceing 0 */
    vbox = gtk_vbox_new(FALSE, 0);

    /* This packs the vbox into the window (a gtk container). */
    gtk_container_add (GTK_CONTAINER (mainWindow), vbox);

    numEntries = rulesTableNumber( );

    /******************************* Help Box ***************************************/
    helpText = gtk_label_new( "When a tag is detected, rules will be tested in the order shown (from top to bottom) until one fits and can be executed." );

    /* This packs the labelinto the vbox (a gtk container). */
    gtk_box_pack_start( GTK_BOX(vbox), helpText, FALSE, FALSE, 6);

    /******************************* Table ******************************************/
    /* create the scolled window that will hold the viewport and table */
    scroll = gtk_scrolled_window_new( NULL, NULL);

    /* This packs the scrolled window into the vbox (a gtk container). */
    gtk_box_pack_start( GTK_BOX(vbox), scroll, TRUE, TRUE, 3);

    /* create the table for tag IDs */
    table = gtk_table_new( 1, 1, FALSE);

    /* fill the table with rows and columns of widgets for scripts */
    fillTable( (GtkTable *)table, numEntries );

    /* add the non-scrollable Table to the scrolled window via a viewport */
    gtk_scrolled_window_add_with_viewport( (GtkScrolledWindow *)scroll, table );
    /******************************* End of Table *************************************/

    /******************************** Add Button  *************************************/
    addButton = gtk_button_new_from_stock( "gtk-add" );

    /* This packs the button into the hbutton box  (a gtk container). */
    gtk_box_pack_start( GTK_BOX(vbox), addButton, FALSE, FALSE, 3);

    /* When the button receives the "clicked" signal, it will call the
     * function applyChanges() passing it NULL as its argument. */
    g_signal_connect (G_OBJECT (addButton), "released", G_CALLBACK (addTagEntry), table);

    /******************************* Button Box ***************************************/
    /* create the box for the buttons */
    buttonBox = gtk_hbox_new( FALSE, 0);

#ifdef BUILD_RULES_EDITOR_HELP
    /********************************************* Help Button ***********************/
    helpButton = gtk_button_new_from_stock( "gtk-help" );

    /* This packs the button into the hbutton box */
    gtk_box_pack_start( GTK_BOX(buttonBox), helpButton, FALSE, TRUE, 3);

    /* When the button receives the "clicked" signal, it will call the
     * function applyChanges() passing it NULL as its argument. */
    g_signal_connect (G_OBJECT (helpButton), "released", G_CALLBACK (rulesEditorHelpShow), NULL);
#endif

#ifdef BUILD_ABOUT_DIALOG
    /********************************************* About Button ***********************/
    aboutButton = gtk_button_new_from_stock( "About" );

    /* This packs the button into the hbutton box  */
    gtk_box_pack_start( GTK_BOX(buttonBox), aboutButton, FALSE, TRUE, 3);

    /* When the button receives the "clicked" signal, it will call the
     * function applyChanges() passing it NULL as its argument. */
    g_signal_connect (G_OBJECT (aboutButton), "released", G_CALLBACK (aboutDialogShow), NULL);
#endif

    /********************************************* Close Button ***********************/
    closeButton = gtk_button_new_from_stock( "gtk-close" );

    /* This packs the button into the hbutton box  (a gtk container). */
    gtk_box_pack_end( GTK_BOX(buttonBox), closeButton, FALSE, TRUE, 3);

    /* When the button receives the "clicked" signal, it will call the
     * function applyChanges() passing it NULL as its argument. */
     /* TODO can't get this signal to work and close things! */
    g_signal_connect (G_OBJECT (closeButton), "released", G_CALLBACK (closeSignalHandler), NULL);

    /********************************************* Apply Button ***********************/
    applyButton = gtk_button_new_from_stock( "gtk-apply" );

    /* This packs the button into the hbutton box  (a gtk container). */
    gtk_box_pack_end( GTK_BOX(buttonBox), applyButton, FALSE, TRUE, 3);

    /* When the button receives the "clicked" signal, it will call the
     * function applyChanges() passing it NULL as its argument. */
    g_signal_connect (G_OBJECT (applyButton), "released", G_CALLBACK (applyChanges), NULL);

    /* This packs the hbutton box into the vbox (a gtk container). */
    gtk_box_pack_start(GTK_BOX(vbox), buttonBox, FALSE, TRUE, 3);

    /********************************************* Cancel Button ***********************/
    cancelButton = gtk_button_new_from_stock( "gtk-cancel" );

    /* This packs the button into the hbutton box  (a gtk container). */
    gtk_box_pack_end( GTK_BOX(buttonBox), cancelButton, FALSE, TRUE, 3);

    /* When the button receives the "clicked" signal, it will call the
     * function applyChanges() passing it NULL as its argument. */
    g_signal_connect (G_OBJECT (cancelButton), "released", G_CALLBACK (cancelSignalHandler), NULL);

    /**************************** End of buttons **************************************/
    /* This packs the hbutton box into the vbox (a gtk container). */
    gtk_box_pack_start(GTK_BOX(vbox), buttonBox, FALSE, TRUE, 3);

    /* at start-up there cannot be any pending changes made to be saved */
    setSavePending( FALSE );

    /**************************** Status Bar ******************************************/
    /* create the status bar */
    statusBar = gtk_statusbar_new();

    /* This packs the status bar into the vbox (a gtk container)  */
    gtk_box_pack_start(GTK_BOX(vbox), statusBar, FALSE, TRUE, 0);

    return ( mainWindow );

}

void
rulesEditorActivate( void )
{

    /* if it exists i.e. has been built */
    if ( rulesEditorWindow )
    {
        /* check to see if it's on top level for user, if so, then hide it */
        /* thus clicking on the status icon toggles it, like skype */
        if (gtk_window_is_active( (GtkWindow *)rulesEditorWindow ) )
            closeSignalHandler( NULL, NULL );
        else
        /* it's built, but not visible, so pop it up to the top! */
        {
            /* make sure it always become visible for the user as could be hidden
               on another workspace, iconized etc */
            gtk_window_present( (GtkWindow *)rulesEditorWindow );
        }
    }
    else
    /* build it from scratch the first time, so we're not using that memory etc if not needed */
    {
        /* build the widget tree for the entire UI */
        rulesEditorWindow = buildrulesEditor();

        /* Show window, and recursively all contained widgets */
        gtk_widget_show_all( rulesEditorWindow );
    }

}

#endif
