/*
  rulesEditorHelp.c - C source code for gtagEventor Gtk/GNOME help
                    dialog for rules editor

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

#ifdef BUILD_RULES_EDITOR_HELP

#include "rulesEditorHelp.h"
#include "systemTray.h"
#include <gtk/gtk.h>

static void
rulesEditorHelpClose(
                    GtkDialog   *dialog,
                    gpointer   user_data
                    )
{

    gtk_widget_destroy( (GtkWidget *)dialog );

}


static void
rulesEditorHelpResponse(
                        GtkDialog *dialog,
                        gint       response_id,
                        gpointer   user_data
                        )
{
    /* will this be called when the CLOSE button is hit on the about dialog...? */
    gtk_widget_destroy( GTK_WIDGET( dialog ) );

}

void
rulesEditorHelpShow( void )
{

    GtkWidget   *rulesEditorHelpDialog;

    rulesEditorHelpDialog = gtk_dialog_new();

    /* set the icon for the window */
    gtk_window_set_icon_name( (GtkWindow *)rulesEditorHelpDialog, ICON_NAME_CONNECTED );

    /* add a close button Response ID for it is 0, although we won't use it */
    gtk_dialog_add_button( (GtkDialog *)rulesEditorHelpDialog, "Close", 0 );

    /* this will be triggered when escape key is used */
    g_signal_connect ( G_OBJECT (rulesEditorHelpDialog), "close", G_CALLBACK (rulesEditorHelpClose), NULL );
/* TODO set the default button that is pressed with Enter */

    g_signal_connect ( G_OBJECT (rulesEditorHelpDialog), "response", G_CALLBACK (rulesEditorHelpResponse), NULL );

    gtk_widget_show( rulesEditorHelpDialog );

}

#endif
