TOPDIR          = ../..

include ${TOPDIR}/Config


# include path for header files.
INCLDEFS += -I${JAVA_HOME}/include -I${JAVA_HOME}/include/${MACH_JNI_INCLDIR}

ifeq (${ENABLE_TRACING},yes)
CPPFLAGS += -DDEBUG
CCFLAGS += -DDEBUG 
endif

CPP = cpp

# platform specific defines
ifeq (${ARCH}, win32)

# name of final native library
DSTLIB = jpcsc.dll
# suffix of object files
OBJSUFFIX = .obj
# cc
CC = cl.exe
# compile command
COMPILE = ${CC} -nologo ${CDEFS} -c -WX $< -Fo$@
# link command
LINK = 	link /dll ${COBJS} winscard.lib /out:${ARCHDIR}/${DSTLIB} ${LDFLAGS} 

else
# a unix target

# include pcsc in include-path

os = $(shell uname)
ifeq ($(os),Darwin)
	INCLDEFS += -I/Developer/SDKs/MacOSX10.6.sdk/System/Library/Frameworks/PCSC.framework/Versions/A/Headers
	LDFLAGS += -lpthread -framework PCSC
else
	INCLDEFS += -I${PCSCDIR}/include -I${PCSCDIR}/include/PCSC
	LDFLAGS += -L${PCSCDIR}/lib -lpcsclite -lpthread
endif


# name of native lib.
ifeq ($(os),Darwin)
	DSTLIB = libjpcsc.jnilib
else
	DSTLIB = libjpcsc.so
endif

# suffix of object files
OBJSUFFIX=.o
# cc flags
CCFLAGS += -Wall
# cc
CC = gcc
# ciompile command
COMPILE = ${CC} -c ${CDEFS} $< -o $@
# link command
LINK = 	${CC} -shared -o ${ARCHDIR}/${DSTLIB} ${COBJS} ${LDFLAGS}

endif

JCPPSRCS = $(wildcard *.java)
JCPPDEFS = ${CPPFLAGS} -P -C -DPCSC_PACKAGE_NAME=${PCSC_PACKAGE_NAME} 

C_PCSC_PACKAGE_NAME = $(subst .,_,${PCSC_PACKAGE_NAME})
DIR_PCSC_PACKAGE_NAME = $(subst .,/,${PCSC_PACKAGE_NAME})

JAVACDIR = ${CLASSDIR}/$(DIR_PCSC_PACKAGE_NAME)
ABSJAVACSRCS = $(addprefix ${JAVACDIR}/,${JCPPSRCS})
RELJAVACSRCS = $(addprefix ${DIR_PCSC_PACKAGE_NAME}/,${JCPPSRCS})
CLASSFILES = $(subst .java,.class, ${RELJAVACSRCS})

CSRCS = $(wildcard *.c)
COBJS = $(addprefix ${ARCHDIR}/,$(subst .c,${OBJSUFFIX}, ${CSRCS}))

INCLDEFS += -I${ARCHDIR}
CDEFS = ${INCLDEFS} ${CCFLAGS}


all: builddirs jar native docs

# build classes
builddirs:
	mkdir -p ${BUILDDIR} ${BUILDDIR}/docs ${ARCHDIR} ${CLASSDIR} ${JAVACDIR} 

${JAVACDIR}/%.java: %.java
	${CPP} ${JCPPDEFS} $< $@

${CLASSDIR}/${JARNAME}: ${ABSJAVACSRCS}
	cd ${CLASSDIR} && ${JAVAC} ${RELJAVACSRCS}
	cd ${CLASSDIR} && ${JAR} cv0f ${JARNAME} ${DIR_PCSC_PACKAGE_NAME}/*.class

jar: ${CLASSDIR}/${JARNAME}


# build native code
${ARCHDIR}/gen1.h:
	echo "#define GEN_FUNCNAME(FUNCNAME) Java_${C_PCSC_PACKAGE_NAME}_##FUNCNAME" > ${ARCHDIR}/gen1.h

${ARCHDIR}/gen2.h:
	echo "#define PCSC_EX_CLASSNAME \"${DIR_PCSC_PACKAGE_NAME}/PCSCException\"" > ${ARCHDIR}/gen2.h

${ARCHDIR}/.built-jni: ${CLASSDIR}/${JARNAME}
	${JAVAH} -classpath ${CLASSDIR} -d ${ARCHDIR} -jni \
		  ${PCSC_PACKAGE_NAME}.Context ${PCSC_PACKAGE_NAME}.Card ${PCSC_PACKAGE_NAME}.PCSC
	touch ${ARCHDIR}/.built-jni

${ARCHDIR}/%${OBJSUFFIX}: %.c ${CLASSDIR}/${JARNAME}
	${COMPILE}

${ARCHDIR}/${DSTLIB}: ${ARCHDIR}/.built-jni ${ARCHDIR}/gen1.h ${ARCHDIR}/gen2.h ${COBJS} 
	${LINK}

native: ${ARCHDIR}/${DSTLIB}


# javadoc: document public symcols, add -private for also documenting private symbols
${BUILDDIR}/docs/.built: ${CLASSDIR}/${JARNAME}
	mkdir -p ${BUILDDIR}/docs
	${JAVADOC} -use -classpath ${CLASSDIR} -d ${BUILDDIR}/docs ${PCSC_PACKAGE_NAME}
	touch ${BUILDDIR}/docs/.built

docs: ${BUILDDIR}/docs/.built

# copy binaries to bin
bins: all
	mkdir -p ${BINDIR} ${BINDIR}/${ARCH} ${TOPDIR}/apidoc
	cp ${CLASSDIR}/${JARNAME} ${BINDIR}
	cp ${ARCHDIR}/${DSTLIB} ${BINDIR}/${ARCH}
	cp -R ${BUILDDIR}/docs/* ${TOPDIR}/apidoc

# installation rule
install: all
	mkdir -p ${JNILIB_INSTALL_DIR} ${JPCSCJAR_INSTALL_DIR} ${DOC_INSTALL_DIR} ${DOC_INSTALL_DIR}/api
	cp ${JPCSCJAR} ${JPCSCJAR_INSTALL_DIR}
	chmod 644  ${JPCSCJAR_INSTALL_DIR}/${JARNAME}
	cp ${ARCHDIR}/${DSTLIB} ${JNILIB_INSTALL_DIR}
	chmod 755  ${JNILIB_INSTALL_DIR}/${DSTLIB}
	cp -R ${BUILDDIR}/docs/* ${DOC_INSTALL_DIR}/api

# clean-up
clean:
	rm -rf ${ARCHDIR}/* ${BUILDDIR}/docs ${CLASSDIR}/*



