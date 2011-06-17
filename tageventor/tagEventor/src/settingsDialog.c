/*
  settingsDialog.c - C source code for gtagEventor Gtk/GNOME dettings
                    dialog window

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

#ifdef BUILD_SETTINGS_DIALOG
#include <stdlib.h>
#include <unistd.h>
#include <gtk/gtk.h>
#include <string.h>

#include "stringConstants.h"
#include "tagEventor.h"
#include "systemTray.h"
#include "settingsDialog.h"

static GtkWidget   *settingsDialog = NULL, *statusBar = NULL, *applyButton = NULL, *closeButton = NULL;
static GtkWidget   *pollDelayScale = NULL, *verbosityScale = NULL;
static char         settingsSavePending = FALSE;

typedef struct {
                char        *label;
                int         bit;    /* corresponding bit in the reader bitmap */
                GtkWidget   *toggle;
} tReaderNumToggle;

static tReaderNumToggle readerNumToggle[MAX_NUM_READERS+1] = {
                {"AUTO",    READER_BIT_AUTO,    NULL},
                {"0",       READER_BIT_0,       NULL},
                {"1",       READER_BIT_1,       NULL},
                {"2",       READER_BIT_2,       NULL},
                {"3",       READER_BIT_3,       NULL},
                {"4",       READER_BIT_4,       NULL},
                {"5",       READER_BIT_5,       NULL}
                };

static void
hideSettingsDialog( void )
{

    /* hide if exists AND is visible */
    if ( settingsDialog )
    {
        gtk_widget_hide( settingsDialog );
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
    hideSettingsDialog();
}

/* Call back for the cancel button */
static void
cancelSignalHandler(
                   GtkDialog    *dialog,
                   gpointer     user_data
                   )
{
    hideSettingsDialog();
}

/* This get's called when the user closes the window using the Window Manager 'X' box */
static char
deleteSignalHandler(
            GtkWidget *widget,
            GdkEvent  *event,
            gpointer   data
            )
{

    if ( settingsSavePending == FALSE )
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
    hideSettingsDialog();

    /* it seems that when this get's called the widget actually get's destroyed */
    /* so, show it's not existant and on next activate it will get re-built */
    settingsDialog = NULL;

}

static void
setSettingsSavePending( unsigned char pending )
{

    settingsSavePending = pending;
    gtk_widget_set_sensitive( applyButton, pending );
    gtk_widget_set_sensitive( closeButton, !pending );

    /* put some help text in the status bar */
    if ( settingsDialog )
    {
        if ( pending )
            gtk_statusbar_push((GtkStatusbar *)statusBar, 0, (gchar *)TAGEVENTOR_STRING_SETTINGS_SAVE_PENDING );
        else
            gtk_statusbar_push((GtkStatusbar *)statusBar, 0, (gchar *)"" );
    }
}


/* This will be called by the systemTray when it wants to quit, and hence asks us here */
/* to quite too. before doing so we check our status. If we have something to do then  */
/* we pop-up the dialogs to do it, and we tell the systemTray to not quit just yet     */
char
settingsDialogQuit( void )
{

    /* request from the systemtrayIcon to exit */
    /* if we can, then close our own stuff and tell the systemtrayIcon it can also exit */
    if ( settingsSavePending == FALSE )
        return (TRUE ); /* can exit */
    else
    {
        /* TODO call settings exit routines to handle the saving etc */
        return( FALSE );
    }

}

static void
applyChanges( void )
{
    int     i;

    /* get the reader settings, form a bitmap and set it */
    for ( i = 0; i <  (MAX_NUM_READERS +1); i++ )
    {
        /* if the GUI toggle is set */
        if ( gtk_toggle_button_get_active( (GtkToggleButton *)readerNumToggle[i].toggle ) )
            readersSettingBitmapBitSet(  &readerManager, readerNumToggle[i].bit );
        else
            readersSettingBitmapBitUnset(  &readerManager, readerNumToggle[i].bit );
    }

    /* save the setting for poll delay */
    appPollDelaySet( gtk_range_get_value( (GtkRange *)pollDelayScale ) );

    /* and for verbosityLevel */
    appVerbosityLevelSet( gtk_range_get_value( (GtkRange *)verbosityScale ) );

    /* change means a save is now NOT needed */
    setSettingsSavePending( FALSE );

}

/* Callback for when each entry's toggle button to enable it is toggled */
static void
toggleChange(
             GtkWidget *widget,
             gpointer   readerNumSetting
             )
{
    int     i;

    unsigned char autoSet;

    if ( (int)readerNumSetting == READER_BIT_AUTO )
    {
        /* see if AUTO has been set or unset */
        autoSet = gtk_toggle_button_get_active( (GtkToggleButton *)widget );

        /* then , starting at the second widget, make the other toggles insensitive */
        for ( i = 1; i <  (readerManager.nbReaders +1); i++ )
            gtk_widget_set_sensitive( readerNumToggle[i].toggle, !autoSet );
    }

    /* change means a save is now needed */
    setSettingsSavePending( TRUE );

}

static void
scaleChanged(
                GtkRange    *hScale,
                gpointer    user_data
                )
{

    /* change means a save is now needed */
    setSettingsSavePending( TRUE );

}

static GtkWidget *
buildSettingsDialog ( void  )
{
    GtkWidget   *dialog;
    GtkWidget   *vbox, *buttonBox, *table, *label;
    GtkWidget   *cancelButton;
    int         i;
    char        windowTitle[strlen(PROGRAM_NAME) + strlen(SETTINGS_DIALOG_WINDOW_TITLE) + 10];

    dialog = gtk_window_new( GTK_WINDOW_TOPLEVEL );
    sprintf(windowTitle, "%s%s", PROGRAM_NAME, SETTINGS_DIALOG_WINDOW_TITLE);
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

    /******************************* Table ******************************************/
    /* create the table for tag IDs, 3 rows, 7 columns */
    table = gtk_table_new( 3, 1, FALSE);

    /* This packs the scrolled window into the vbox (a gtk container). */
    gtk_box_pack_start( GTK_BOX(vbox), table, TRUE, TRUE, 3);

    /* Reader number toggles */
    label = gtk_label_new( "Reader Numbers:" );
    gtk_label_set_justify( (GtkLabel *)label, GTK_JUSTIFY_RIGHT );
    gtk_table_attach( (GtkTable *)table, label, 0, 1, 0, 1, GTK_FILL, GTK_FILL, 0, 10 );
    gtk_widget_show( label );

    /* the 6 possible options are  AUTO plus the readers 0, 1, 2, 3, 4, 5, */
    for ( i = 0; i < (MAX_NUM_READERS +1); i++ )
    {
        readerNumToggle[i].toggle = gtk_check_button_new_with_label( readerNumToggle[i].label);
        gtk_toggle_button_set_active( (GtkToggleButton *)readerNumToggle[i].toggle, readersSettingBitmapBitTest(  &readerManager, 1 << i) );

        /* attach a new widget into the table, row 0, for the 6 columns */
        gtk_table_attach( (GtkTable *)table, readerNumToggle[i].toggle, i+1, i+2, 0, 1, GTK_FILL, GTK_FILL, 5, 0 );
        /* add a callback to the button which will be passed the setting value */
        g_signal_connect (G_OBJECT (readerNumToggle[i].toggle), "toggled", G_CALLBACK (toggleChange), (gpointer)(readerNumToggle[i].bit) );

        /* however, if AUTO is set, then set the other toggles to insensitive */
        if ( ( i > 0) && ( readerNumToggle[0].bit & READER_BIT_AUTO ) )
            gtk_widget_set_sensitive( readerNumToggle[i].toggle, FALSE );
    }

    /* polly delay setting */
    label = gtk_label_new( "Poll Delay (ms):" );
    gtk_label_set_justify( (GtkLabel *)label, GTK_JUSTIFY_RIGHT );
    gtk_table_attach( (GtkTable *)table, label, 0, 1, 1, 2, GTK_FILL, GTK_FILL, 0, 10 );
    gtk_widget_show( label );

    /* H Scale - slider for setting poll delay */
    pollDelayScale = gtk_hscale_new_with_range( POLL_DELAY_MILLI_SECONDS_MIN, POLL_DELAY_MILLI_SECONDS_MAX, 100 );

    /* set it up with the actual value */
    gtk_range_set_value( (GtkRange *)pollDelayScale, appPollDelayGet() );

    /* add a callback for when the setting value is changed */
    g_signal_connect (G_OBJECT (pollDelayScale), "value-changed", G_CALLBACK (scaleChanged), NULL );

    gtk_table_attach( (GtkTable *)table, pollDelayScale, 1, 7, 1, 2, GTK_FILL, GTK_FILL, 0, 10 );
    gtk_widget_show( pollDelayScale );

    /* verbosity setting */
    label = gtk_label_new( "Verbosity Level:" );
    gtk_label_set_justify( (GtkLabel *)label, GTK_JUSTIFY_RIGHT );
    gtk_table_attach( (GtkTable *)table, label, 0, 1, 2, 3, GTK_FILL, GTK_FILL, 0, 10 );
    gtk_widget_show( label );

    /* H Scale - slider for setting verbosity level */
    verbosityScale = gtk_hscale_new_with_range( VERBOSITY_MIN, VERBOSITY_MAX, 1 );

    /* set it up with the actual value */
    gtk_range_set_value( (GtkRange *)verbosityScale, appVerbosityLevelGet() );

    /* add a callback for when the setting value is changed */
    g_signal_connect (G_OBJECT (verbosityScale), "value-changed", G_CALLBACK (scaleChanged), NULL );

    gtk_table_attach( (GtkTable *)table, verbosityScale, 1, 7, 2, 3, GTK_FILL, GTK_FILL, 0, 10 );
    gtk_widget_show( verbosityScale );

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
    setSettingsSavePending( FALSE );

    /**************************** Status Bar ******************************************/
    /* create the status bar */
    statusBar = gtk_statusbar_new();

    /* This packs the status bar into the vbox (a gtk container)  */
    gtk_box_pack_start(GTK_BOX(vbox), statusBar, FALSE, TRUE, 0);

    return ( dialog );

}

void
settingsDialogActivate( void )
{

    /* if it exists i.e. has been built */
    if ( settingsDialog )
    {
        /* make sure it always become visible for the user as could be hidden
               on another workspace, iconized etc */
        gtk_window_present( (GtkWindow *)settingsDialog );
    }
    else
    /* build it from scratch the first time, so we're not using that memory etc if not needed */
    {
        /* build the widget tree for the entire UI */
        settingsDialog = buildSettingsDialog();

        /* Show window, and recursively all contained widgets */
        gtk_widget_show_all( settingsDialog );
    }

}

#endif
