TOPDIR          = ../..
TOPDIR          = /Users/andrew/Documents/DevProjects/WebApps/tageventor/jpcsc

include ${TOPDIR}/Config

JAVASRCS = $(wildcard *.java)

all: ${BUILDDIR}/samples.jar

${BUILDDIR}/samples.jar: ${JAVASRCS} ${JPCSCJAR}
	${JAVAC} -classpath "${JPCSCJAR}${CPSEP}." -d ${BUILDDIR} ${JAVASRCS}
	cd ${BUILDDIR} && ${JAR} cv0f samples.jar samples

bins: ${BUILDDIR}/samples.jar
	cp ${BUILDDIR}/samples.jar ${BINDIR}

clean:
	rm -rf ${BUILDDIR}/samples

install: all
	cp ${BUILDDIR}/samples.jar ${DOC_INSTALL_DIR}


# start samples from the build directory
test:
ifeq (${ARCH}, win32)
	${JAVA} -Djava.library.path="${ARCHDIR}" -cp "${JPCSCJAR}${CPSEP}${BUILDDIR}" samples.Test
else
	export LD_LIBRARY_PATH=${PCSCDIR}/lib:${LD_LIBRARY_PATH}; ${JAVA} -Djava.library.path="${ARCHDIR}" -cp ${JPCSCJAR}:${BUILDDIR} samples.Test
endif

tool:
ifeq (${ARCH}, win32)
	${JAVA} -Djava.library.path="${ARCHDIR}" -cp "${JPCSCJAR}${CPSEP}${BUILDDIR}" samples.APDUTool
else
	export LD_LIBRARY_PATH=${PCSCDIR}/lib:${LD_LIBRARY_PATH}; ${JAVA} -Djava.library.path="${ARCHDIR}" -cp ${JPCSCJAR}:${BUILDDIR} samples.APDUTool
endif


# start samples from the bin directory
testbin:
ifeq (${ARCH}, win32)
	${JAVA} -Djava.library.path="${BINDIR}/${ARCH}" -cp "${BINDIR}/jpcsc.jar${CPSEP}${BINDIR}/samples.jar" samples.Test
else
	export LD_LIBRARY_PATH=${PCSCDIR}/lib:${LD_LIBRARY_PATH}; ${JAVA} -Djava.library.path="${BINDIR}/${ARCH}" -cp ${BINDIR}/jpcsc.jar:${BINDIR}/samples.jar samples.Test
endif

toolbin:
ifeq (${ARCH}, win32)
	${JAVA} -Djava.library.path="${BINDIR}/${ARCH}" -cp "${BINDIR}/jpcsc.jar${CPSEP}${BINDIR}/samples.jar" samples.APDUTool
else
	export LD_LIBRARY_PATH=${PCSCDIR}/lib:${LD_LIBRARY_PATH}; ${JAVA} -Djava.library.path="${BINDIR}/${ARCH}" -cp ${BINDIR}/jpcsc.jar:${BINDIR}/samples.jar samples.APDUTool
endif
