TOPDIR=.

include ./Config

SUBDIRS = src/jpcsc src/samples

ZIPDIR=${BUILDDIR}/zip

all bins clean ::
	@for dir in $(SUBDIRS); do \
		$(MAKE) -C $$dir $@; \
	done

test tool testbin toolbin:
	$(MAKE) -C src/samples $@

install: 
	@for dir in $(SUBDIRS); do \
		$(MAKE) -C $$dir $@; \
	done
	cp README License.html ${DOC_INSTALL_DIR}


# build jpcsc-${VERSION}.zip inclusing sources and binaries 
zippkg: bins 
	rm -rf ${ZIPDIR}/jpcsc jpcsc-${JPCSC_VERSION}.zip 
	mkdir -p ${ZIPDIR}/jpcsc
	cp -r bin apidoc misc debian src jpcsc.spec Config  License.html  Makefile  README ${ZIPDIR}/jpcsc
	find ${ZIPDIR} -name "*~" -exec rm -rf \{} \; || true
	find ${ZIPDIR} -name "CVS" -exec rm -rf \{} \; || true
	find ${ZIPDIR} -name ".#*" -exec rm -rf \{} \; || true
	cd ${ZIPDIR} && zip -rq jpcsc-${JPCSC_VERSION}.zip jpcsc

# build jpcsc-${VERSION}-src.zip inclusing sources
srcpkg: bins
	rm -rf ${ZIPDIR}/jpcsc jpcsc-${JPCSC_VERSION}-src.zip 
	mkdir -p ${ZIPDIR}/jpcsc
	cp -r apidoc misc debian src jpcsc.spec Config  License.html  Makefile  README ${ZIPDIR}/jpcsc
	find ${ZIPDIR} -name "*~" -exec rm -rf \{} \; || true
	find ${ZIPDIR} -name "CVS" -exec rm -rf \{} \; || true
	find ${ZIPDIR} -name ".#*" -exec rm -rf \{} \; || true
	cd ${ZIPDIR} && zip -rq jpcsc-${JPCSC_VERSION}-src.zip jpcsc


rpmpkgs: zippkg
	cp ${ZIPDIR}/jpcsc-${JPCSC_VERSION}.zip ${RPM_BUILD_DIR}/SOURCES
	cp jpcsc.spec ${RPM_BUILD_DIR}/SPECS
	rpmbuild -ba ${RPM_BUILD_DIR}/SPECS/jpcsc.spec


FILES=$(filter-out build,$(wildcard *))
DEBDIR=${BUILDDIR}/debian/jpcsc-${JPCSC_VERSION}

debpkg:
	mkdir -p ${DEBDIR}
	rm -rf ${DEBDIR}/*
	cp -r ${FILES} ${DEBDIR}
	cd ${DEBDIR} && dpkg-buildpackage -rfakeroot


