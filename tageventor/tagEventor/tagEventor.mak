all: Debug Release

release_binary = Release/tagEventor
debug_binary = Debug/tagEventor

debug_library = Debug/libtagReader.a
release_library = Release/libtagReader.a

debug_objects = Debug/tagEventor.o \
                Debug/rulesTable.o \
                Debug/daemonControl.o
release_objects = Release/tagEventor.o \
                  Release/rulesTable.o \
                  Release/daemonControl.o

debug_dependencies = $(debug_objects:.o=.d)
release_dependencies = $(release_objects:.o=.d)

# Clean up all stray editor back-up files, any .o or .a left around in this directory
# Remove all built object files (.o and .a) and compiled and linked binaries
clean: cleanDebug cleanRelease

cleanRelease:
	@rm -f $(release_objects) $(release_binary) $(release_dependencies)
	@echo "tagEventor Release files cleaned"

cleanDebug:
	@rm -f $(debug_objects) $(debug_binary) $(debug_dependencies)
	@echo "tagEventor Debug files cleaned"

#dependancy generation and use
include $(debug_dependencies)
include $(release_dependencies)

##### Get rev_string and version_string
include version.mak

##### Compile Flags
cc_flags = -Wall -I . -I ../tagReader/src \
           -DPROGRAM_NAME="tagEventor" \
           -DDEFAULT_LOCK_FILE_DIR='"/var/run/tagEventor"' \
           -DDAEMON_NAME='"tagEventord"'

os = $(shell uname)
ifeq ($(os),Darwin)
	debug_link_flags =   -L../tagReader/Debug   -l tagReader -framework PCSC
	release_link_flags = -L../tagReader/Release -l tagReader -framework PCSC
	debug_cc_flags = $(cc_flags) -DDEBUG -g \
                 -DDEFAULT_COMMAND_DIR='"/Library/Application Support/tagEventor"' \
                 -DVERSION_STRING='$(version_string) $(rev_string) " Debug"'
	release_cc_flags = $(cc_flags) \
                 -DDEFAULT_COMMAND_DIR='"/Library/Application Support/tagEventor"' \
                 -DVERSION_STRING='$(version_string) $(rev_string) " Release"'
else
	debug_link_flags =   -L../tagReader/Debug   -l tagReader -l pcsclite
	release_link_flags = -L../tagReader/Release -l tagReader -l pcsclite
	debug_cc_flags = $(cc_flags) -I /usr/include/PCSC  -DDEBUG -g -DDEFAULT_COMMAND_DIR='"/etc/tagEventor"' \
                 -DVERSION_STRING='$(version_string) $(rev_string) " Debug"'

	release_cc_flags = $(cc_flags) -I /usr/include/PCSC  -DDEFAULT_COMMAND_DIR='"/etc/tagEventor"' \
                 -DVERSION_STRING='$(version_string) $(rev_string) " Release"'
endif

########## Debug version DEPENDENCIES
Debug/%.d: src/%.c
	@set -e; rm -f $@; \
	gcc -M $(debug_cc_flags) $< > $@.$$$$; \
	sed 's,\($*\)\.o[ :]*,$(@D)/$*.o $@ : ,g' < $@.$$$$ > $@; \
	rm -f $@.$$$$

Debug: $(debug_binary)

###### Debug version LINK
$(debug_binary): $(debug_objects) $(debug_library)
	@gcc $(debug_objects) $(debug_link_flags) -o $@
	@echo tagEventor Debug version $(rev_string) BUILT $@
	@echo ""

$(debug_library):

###### Debug version COMPILE
Debug/%.o : src/%.c
	@gcc -c $< $(debug_cc_flags) -o $@
	@echo "Compiling " $<

########## Release version DEPENDENCIES
Release/%.d: src/%.c
	@set -e; rm -f $@; \
	gcc -M $(release_cc_flags) $< > $@.$$$$; \
	sed 's,\($*\)\.o[ :]*,$(@D)/$*.o $@ : ,g' < $@.$$$$ > $@; \
	rm -f $@.$$$$

########## Release version LINK
Release: $(release_binary)

$(release_binary): $(release_library) $(release_objects)
	@gcc $(release_objects) $(release_link_flags) -o $@
	@echo tagEventor Release version $(rev_string) BUILT $@
	@echo ""

$(release_library):

########## Release version COMPILE
Release/%.o : src/%.c
	@gcc -c $< $(release_cc_flags) -o $@
	@echo "Compiling " $<
