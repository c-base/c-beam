# Makefile

include ../../Config

# directory where pcsc drivers are installed
PCSC_DRIVERS_DIR=/usr/lib/pcsc/drivers/
# directiry where reader.conf is stored
PCSC_ETC_DIR=/etc

# name of reader directory to be created 
JCOP_SIMUL_SUBDIR = jcop_simul
# name of target reader lib
LIBNAME  = libjcop_remote.so

# enable debugging info
ifeq (${ENABLE_TRACING},yes)
CDEFS     = -DDEBUG=1 
endif


CC       = gcc
CINCLUDE  = -I.
CFLAGS   = -g -fpic -w

CSRCS = $(wildcard *.c)
COBJS = $(patsubst %.c,%.o,${CSRCS})

ifeq ($(findstring darwin,${ARCH})$(findstring darwin,${ARCH}),)
all: ${LIBNAME}
else
all:
endif

clean:
	rm -f *.o $(LIBNAME) core

${LIBNAME}: $(COBJS)
	$(CC) $(CFLAGS) -shared $(COBJS) -o $(LIBNAME)

%.o: %.c
	$(CC) $(CFLAGS) $(CDEFS) -c $< $(CINCLUDE) 

install:
	mkdir -p ${PCSC_DRIVERS_DIR}/${JCOP_SIMUL_SUBDIR}
	cp ${LIBNAME} ${PCSC_DRIVERS_DIR}/${JCOP_SIMUL_SUBDIR}
	./rdrinst.pm "JCOPSimulReader" JCOP_SIMUL_RDR  ${PCSC_DRIVERS_DIR}/${JCOP_SIMUL_SUBDIR}/${LIBNAME} 0x0103F8 < ${PCSC_ETC_DIR}/reader.conf > ${PCSC_ETC_DIR}/reader.conf.new && mv ${PCSC_ETC_DIR}/reader.conf.new ${PCSC_ETC_DIR}/reader.conf

#
# FRIENDLYNAME     "JCOPSimulReader"
# DEVICENAME       JCOP_SIMUL_RDR
# LIBPATH          /local/pcsc/drivers/simulation/libjcop_remote.so
# CHANNELID        0x0103F8
#
