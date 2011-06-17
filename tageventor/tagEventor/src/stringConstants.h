/*
  stringConstants.h - Header file that defines strings used in UI/output

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

#define TAGEVENTOR_STRING_PCSCD_OK_READER_NOT   "Connected to pcscd, %d readers found.\nCould not connect to reader(s)"
#define TAGEVENTOR_STRING_PCSCD_PROBLEM         "Problems connecting to pcscd daemon, check it is running using 'ps -ef' command"
#define TAGEVENTOR_STRING_CONNECTED_READER      "Connected to pcscd, %d readers, %d tags"
#define TAGEVENTOR_STRING_TAG_LINE              "Tag UID: %s  "

#define TAGEVENTOR_STRING_COMMAND_LINE_READER_NUM_ERROR_1 "Reader number must be AUTO or a valid number between 0 and %d\n"
#define TAGEVENTOR_STRING_COMMAND_LINE_READER_NUM_ERROR_2 "Reader number argument '%s' ignored\n"

#define TAGEVENTOR_STRING_USAGE "Usage: %s <options>\n\t-n <reader number> : default = AUTO, min = 0, max = 4\n\t-v <verbosity level> : default = 0 (silent), max = 3 \n\t-d start | stop (daemon options)\n\t-p <msecs> : tag polling delay, min = %d, default = %d, max = %d\n\t-h : print this message\nVersion Number: %s\n"

#define TAGEVENTOR_STRING_SETTINGS_SAVE_PENDING "Press 'Apply' to save settings then 'Close'. Press 'Cancel' to exit without saving changes"

#define TOOL_TIP_TEXT               "Left-click for Rules Editor.\nRight-click for menu."

#define RULES_EDITOR_WINDOW_TITLE   " - Rules Editor"
#define SETTINGS_DIALOG_WINDOW_TITLE " - Settings"
#define TAG_EVENTOR_EXPLORER_WINDOW_TITLE " - Explorer"

