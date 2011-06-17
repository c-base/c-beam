/*
  tagMifareUltra.h - definitions of logical tag structures for MiFare ULTRA tag

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


/*********************************************************************/
/**************************** MiFARE Ultra ***************************/
/*********************************************************************/

/**************************** CONSTANTS ******************************/
#define	NUM_BYTES_UID_MIFARE_ULTRA		        (7)
#define NUM_USER_BYTES_PER_PAGE_MIFARE_ULTRA	(4)
#define NUM_OTP_BYTES_MIFARE_ULTRA		        (4)
#define NUM_PAGES_MIFARE_ULTRA			        (12)

/**************************    TYPEDEFS    **************************/
typedef struct		{
			char		    data[NUM_USER_BYTES_PER_PAGE_MIFARE_ULTRA];
			unsigned char	locked;/* is it locked or can it be written to */
			unsigned char	valid; /* has this data been read from tag?    */
			unsigned char	writePending; /* data has changed but not written to the tag */
			} t_Logical_Page_MIFARE_ULTRA;

typedef	char		t_Logical_OTP_MIFARE_ULTRA[NUM_OTP_BYTES_MIFARE_ULTRA];

typedef struct		{
			    t_Logical_OTP_MIFARE_ULTRA  OTP;
			    t_Logical_Page_MIFARE_ULTRA	pages[NUM_PAGES_MIFARE_ULTRA];
			} tTagContents_MIFARE_ULTRA;
