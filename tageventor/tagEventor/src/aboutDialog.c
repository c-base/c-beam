/*
  aboutDialog.c - C source code for gtagEventor Gtk/GNOME about dialog

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

#ifdef BUILD_ABOUT_DIALOG

#include <stdlib.h>
#include <gtk/gtk.h>
#include "tagEventor.h"
#include "systemTray.h"

static const gchar  *authors[] = {"Andrew Mackenzie (andrew@autelic.org)", NULL };


static void
closeAbout(
        GtkDialog   *dialog,
        gpointer   user_data
        )
{

    gtk_widget_destroy( (GtkWidget *)dialog );

}


static void
aboutResponse(
            GtkDialog *dialog,
            gint       response_id,
            gpointer   user_data
            )
{
    /* will this be called when the CLOSE button is hit on the about dialog...? */
    gtk_widget_destroy( GTK_WIDGET( dialog ) );

}

void
aboutDialogShow( void )
{

    GtkWidget   *aboutDialog;

    aboutDialog = gtk_about_dialog_new();

    /* set the icon for the window */
    gtk_window_set_icon_name( (GtkWindow *)aboutDialog, ICON_NAME_CONNECTED );

    gtk_about_dialog_set_program_name( (GtkAboutDialog *)aboutDialog, PROGRAM_NAME );

    gtk_about_dialog_set_version( (GtkAboutDialog *)aboutDialog, VERSION_STRING );

    gtk_about_dialog_set_copyright( (GtkAboutDialog *)aboutDialog, "Copyright Autelic Association" );

    gtk_about_dialog_set_license( (GtkAboutDialog *)aboutDialog, "Licensed under Apache 2.0 License" );
/* TODO show the full license text via including a file under version control into a string, at compile time
or maybe reading from a file at run time */

    gtk_about_dialog_set_website( (GtkAboutDialog *)aboutDialog, "http://tageventor.googlecode.com" );
    gtk_about_dialog_set_website_label( (GtkAboutDialog *)aboutDialog, "Development Site (Google Code)" );

    gtk_about_dialog_set_comments( (GtkAboutDialog *)aboutDialog, "An application that detects RFID/NFC tags, via an appropriate reader hardware connected to your computer, and performs actions when they are placed or removed from the reader. \nIt includes a Rules Editor to define Tag events and then what actions are to be performed for that event." );

/* find a way to read this at compile or run time from the COMMITTERS file */
    gtk_about_dialog_set_authors( (GtkAboutDialog *)aboutDialog, authors );

    /* hook-up the signal handler for the about box's close button */

/* TODO set the default button that is pressed with Enter */

/* TODO show the proper logo for this window also
gtk_about_dialog_set_logo_icon_name (GtkAboutDialog *about,
                                                         const gchar *icon_name);
*/
    /* this will be triggered when escape key is used */
    g_signal_connect ( G_OBJECT (aboutDialog), "close", G_CALLBACK (closeAbout), NULL );

    g_signal_connect ( G_OBJECT (aboutDialog), "response", G_CALLBACK (aboutResponse), NULL );

    gtk_widget_show( aboutDialog );

}

#endif
