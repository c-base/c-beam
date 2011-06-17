all: Debug Release
     
debug_archive = Debug/libtagReader.a
release_archive = Release/libtagReader.a

sources = $(src/*.c)

debug_objects = Debug/tagReader.o Debug/acr122UDriver.o
release_objects = Release/tagReader.o Release/acr122UDriver.o

Release/%.d: src/%.c
	@set -e; rm -f $@; \
	gcc -MM $(release_flags) $< > $@.$$$$; \
	sed 's,\($*\)\.o[ :]*,$(@D)/$*.o $@ : ,g' < $@.$$$$ > $@; \
	rm -f $@.$$$$

Debug/%.d: src/%.c
	@set -e; rm -f $@; \
	gcc -MM $(debug_flags) $< > $@.$$$$; \
	sed 's,\($*\)\.o[ :]*,$(@D)/$*.o $@ : ,g' < $@.$$$$ > $@; \
	rm -f $@.$$$$

#dependancy generation and use
include $(debug_objects:.o=.d)
include $(release_objects:.o=.d)


# NOTE: do not put spaces inside the '(' and ')' on this next line or Mac build fails
os = $(shell uname)
ifeq ($(os),Darwin)
	architecture = $(shell arch)
	archiver = /usr/bin/libtool
	archiver_flags = -arch_only $(architecture) -o
	os_cc_flags = -F/System/Library/Frameworks/
#	os_cc_flags = -arch $(architecture)
else
	archiver = ar
	archiver_flags = rcsv
	os_cc_flags =
endif

cc_flags = $(os_cc_flags) -Wall -I . -I /usr/include/PCSC
debug_flags = $(os_cc_flags) $(cc_flags) -DDEBUG -g
release_flags = $(os_cc_flags) $(cc_flags)

###### Debug version of library
cleanDebug:
	@rm -f $(debug_objects) $(debug_archive)
	@rm -f Debug/*.d
	@echo "libtagReader Debug files cleaned"

Debug: $(debug_archive)

$(debug_archive): $(debug_objects)
	@echo "Creating library..."
	@$(archiver) $(archiver_flags) $@ $^
	@echo Library BUILT $@
	@echo ""

Debug/%.o: src/%.c
	@gcc -c $< $(debug_flags) -o $@
	@echo "Compiling " $<

###### Release version of library
cleanRelease:
	@rm -f $(release_objects) $(release_archive)
	@rm -f Release/*.d
	@echo "libtagReader Release files cleaned"

Release: $(release_archive)

$(release_archive): $(release_objects)
	@echo "Creating library..."
	@$(archiver) $(archiver_flags) $@ $^
	@echo Library BUILT $@
	@echo ""

Release/%.o: src/%.c
	@gcc -c $< $(release_flags) -o $@
	@echo "Compiling " $<

# Clean up all stray editor back-up files, any .o or .a left around in this directory
# Remove all built object files (.o and .a) and compiled and linked binaries
clean: cleanDebug cleanRelease
	@rm -f *~
	@echo ""
