all: Debug Release
	@echo ""

debug_binaries = Debug/gtagEventor
release_binaries = Release/gtagEventor
binaries = $(debug_binaries) $(release_binaries)

debug_archive = ../tagReader/Debug/libtagReader.a

release_archive = ../tagReader/Release/libtagReader.a

debug_objects = Debug/gtagEventor.o \
                Debug/rulesTable.o  \
                Debug/daemonControl.o  \
                Debug/aboutDialog.o \
                Debug/rulesEditor.o \
                Debug/rulesEditorHelp.o \
                Debug/settingsDialog.o \
                Debug/explorer.o \
                Debug/systemTray.o

release_objects = Release/gtagEventor.o \
                  Release/rulesTable.o \
                  Release/daemonControl.o \
                  Release/aboutDialog.o \
                  Release/rulesEditor.o \
                  Release/rulesEditorHelp.o \
                  Release/settingsDialog.o \
                  Release/explorer.o \
                  Release/systemTray.o

debug_dependencies = $(debug_objects:.o=.d)
release_dependencies = $(release_objects:.o=.d)

#dependancy generation and use
include $(debug_dependencies)
include $(release_dependencies)

###### Build Flags
build_flags = -DBUILD_SYSTEM_TRAY \
              -DBUILD_CONTROL_PANEL \
              -DBUILD_ABOUT_DIALOG \
              -DBUILD_CONTROL_PANEL_HELP \
              -DBUILD_SETTINGS_DIALOG \
              -DBUILD_RULES_EDITOR \
              -DBUILD_RULES_EDITOR_HELP \
              -DBUILD_EXPLORER \
              -DDEFAULT_LOCK_FILE_DIR='"/var/run/tagEventor"' \
              -DDAEMON_NAME='"tagEventord"'

icon_flags = -DICON_INSTALL_DIR='"/usr/share/gtagEventor/icons/"' \
             -DICON_NAME_CONNECTED='"gtagEventor"' \
             -DICON_NAME_NOT_CONNECTED='"gtagEventorNoReader"'

# NOTE: do not put spaces inside the '(' and ')' on this next line or Mac build fails
os = $(shell uname)
ifeq ($(os),Darwin)
	architecture = $(shell arch)
	linker = /usr/bin/gcc
	link_flags = -framework PCSC \
                     -L/Library/Frameworks/GLib.framework/Libraries -lglib-2.0.0 -lgobject-2.0.0 \
                     -L/Library/Frameworks/Cairo.framework/Libraries -lcairo.2 \
                     -L/Library/Frameworks/Gtk.framework/Libraries -lgtk-quartz-2.0.0 \
                     -arch $(architecture) -lc -ltagReader
	os_cc_flags = -I /Library/Frameworks/GLib.framework/Headers/ \
                      -I /Library/Frameworks/Cairo.framework/Headers/ \
                      -I /Library/Frameworks/Gtk.framework/Headers/ \
                      -DDEFAULT_COMMAND_DIR='"/Library/Application Support/gtagEventor"'
else
	linker = gcc
	link_flags =  `pkg-config --cflags --libs gtk+-2.0 gmodule-2.0` \
                      -l tagReader -l pcsclite -l notify
	os_cc_flags = `pkg-config --cflags --libs gtk+-2.0 gmodule-2.0` \
                      -I /usr/include/PCSC \
                      -DDEFAULT_COMMAND_DIR='"/etc/gtagEventor"'
endif

##### Get rev_string and version_string
include version.mak

##### Compile flags
cc_flags = $(build_flags) $(icon_flags) -I src -I ../tagReader/source -Wall \
          -DPROGRAM_NAME='"gtagEventor"' $(os_cc_flags)

debug_cc_flags = $(cc_flags) -DDEBUG -g \
                 -DVERSION_STRING='$(version_string) $(rev_string) " Debug"'

release_cc_flags = $(cc_flags) \
                 -DVERSION_STRING='$(version_string) $(rev_string) " Release"'

################################## Targets #################################
# Clean up all stray editor back-up files, any .o or .a left around in this directory
# Remove all built object files (.o and .a) and compiled and linked binaries
clean: cleanDebug cleanRelease
	@echo ""

########################## Debug TARGETS ###############################
cleanDebug:
	@rm -f $(debug_binaries) $(debug_objects) $(debug_dependencies)
	@echo "gtagEventor Debug files cleaned"

Debug: $(debug_binaries)

###### Debug version LINK
bin/Debug/gtagEventor: $(debug_archive) $(debug_objects)
	@$(linker)  $(debug_objects) -Llib/Debug $(link_flags) -o $@
	@echo gtagEventor Debug version BUILT $@
	@echo ""

$(debug_archive):

########## Debug version DEPENDENCIES
Debug/%.d: src/%.c
	@set -e; rm -f $@; \
	gcc -M $(debug_cc_flags) $< > $@.$$$$; \
	sed 's,\($*\)\.o[ :]*,$(@D)/$*.o $@ : ,g' < $@.$$$$ > $@; \
	rm -f $@.$$$$

###### Debug version COMPILE
Debug/gtagEventor.o: src/tagEventor.c
	@gcc -c $< $(debug_cc_flags) -o $@
	@echo "Compiling " $< "---->" $@

Debug/gtagEventor.d: src/tagEventor.c
	@set -e; rm -f $@; \
	gcc -M $(debug_cc_flags) $< > $@.$$$$; \
	sed 's,tagEventor.o[ :]*,$(@D)/gtagEventor.o $@ : ,g' < $@.$$$$ > $@; \
	rm -f $@.$$$$

Debug/%.o : src/%.c
	@gcc -c $< $(debug_cc_flags) -o $@
	@echo "Compiling " $<

########################## Release TARGETS ###############################
cleanRelease:
	@rm -f $(release_binaries) $(release_objects) $(release_dependencies)
	@echo "gtagEventor Release files cleaned"

Release: $(release_binaries)

########## Release version LINK
Release/gtagEventor: $(release_archive) $(release_objects)
	@$(linker)  $(release_objects) -L../tagReader/Release $(link_flags) -o $@
	@echo gtagEventor Release version BUILT $@
	@echo ""

$(release_archive):

########## Release version COMPILE
Release/gtagEventor.o : src/tagEventor.c
	@gcc -c $< $(release_cc_flags) -o $@
	@echo "Compiling " $< "---->" $@

Release/gtagEventor.d: src/tagEventor.c
	@set -e; rm -f $@; \
	gcc -M $(release_cc_flags) $< > $@.$$$$; \
	sed 's,tagEventor.o[ :]*,$(@D)/gtagEventor.o $@ : ,g' < $@.$$$$ > $@; \
	rm -f $@.$$$$

########## Release version DEPENDENCIES
Release/%.d: src/%.c
	@set -e; rm -f $@; \
	gcc -M $(release_cc_flags) $< > $@.$$$$; \
	sed 's,\($*\)\.o[ :]*,$(@D)/$*.o $@ : ,g' < $@.$$$$ > $@; \
	rm -f $@.$$$$

Release/%.o : src/%.c
	@gcc -c $< $(release_cc_flags) -o $@
	@echo "Compiling " $<
