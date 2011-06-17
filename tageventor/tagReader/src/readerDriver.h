/*
  readerDriver.h - public header files for tagReader library that
  defines structures and functions for specific reader drivers

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

#include "tagReaderTypes.h"

/* wintypes.h is NOT included by winscard.h on Mac and so needed    */
/* explicitly for the Mac build to work                             */
#include <PCSC/wintypes.h>
#include <PCSC/winscard.h>

/**************************    TYPEDEFS    **************************/
typedef LONG   (*tReaderCheckFunction)(
                                      tReader   *pReader,
                                      BOOL      *pReaderSupported
                                      );

typedef LONG   (*tGetContactlessStatusFunction)(
                                       const tReader	*pReader,
                                        BYTE			*pRecvBuffer,
                                        DWORD		    *pRecvLength
                                        );

typedef LONG   (*tGetTagListFunction)(
                                    tReader	        *pReader,
                                    tTag	        pTags[]
                                    );

typedef const char    * tDriverDescriptor;

typedef struct  {
                 tReaderCheckFunction           readerCheck;
                 tGetContactlessStatusFunction  getContactlessStatus;
                 tGetTagListFunction            getTagList;
                 tDriverDescriptor              driverDescriptor;
                 int                            maxTags;
                } tReaderDriver;
