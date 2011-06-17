#ifndef _jpcsc_h
#define _jpcsc_h

#include <stdio.h>
#include <assert.h>
#include <jni.h>

#ifdef WIN32
#include <winscard.h>
#else
#include <PCSC/winscard.h>
#endif


#include "gen1.h"
#include "gen2.h"

/*
 * Length of ATR.
 */
#define JPCSC_ATR_SIZE SCARD_ATR_LENGTH 

/*
 * Name of NullPointerException
 */
#define NP_EX_CLASSNAME "java/lang/NullPointerException"

#ifndef WIN32
#include <wintypes.h>
#endif

#ifndef WIN32
#if defined(SCARD_ATTR_VALUE)
#define HAVE_SCARD_ATTRIBUTES
#endif /* SCARD_ATTR_VALUE */
#endif /* WIN32 */

#endif /* _jpcsc_h */
