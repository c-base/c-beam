all: Debug Release
	@echo "All Done."
	@echo ""

##### Which OS are we building on? Linux? Darwin? other?
os = $(shell uname)
tar_file_name = tagEventor-$(os)-$(version_string).tar.gz

binary: Release
	@tar -cpz --exclude .svn scripts/generic bin/Release \
                 tagEventord gtagEventor.desktop icons \
                 install-sh > $(tar_file_name)
	@echo Binary install package for OS=$(os) created as $(tar_file_name)
  
Debug:
	@make -s -C tagReader -f Makefile Debug
	@make -s -C tagEventor -f tagEventor.mak Debug
	#@make -s -C tagEventor -f gtagEventor.mak Debug
	@echo "Debug Done."
	@echo ""

Release:
	@make -s -C tagReader -f Makefile Release
	@make -s -C tagEventor -f tagEventor.mak Release
	#@make -s -C tagEventor -f gtagEventor.mak Release
	@echo "Release Done."
	@echo ""

cleanDebug:
	@make -s -C tagReader -f Makefile cleanDebug
	@make -s -C tagEventor -f tagEventor.mak cleanDebug
	#@make -s -C tagEventor -f gtagEventor.mak cleanDebug
	@echo "cleanDebug Done."
	@echo ""

cleanRelease:
	@make -s -C tagReader -f Makefile cleanRelease
	@make -s -C tagEventor -f tagEventor.mak cleanRelease
	#@make -s -C tagEventor -f gtagEventor.mak cleanRelease
	@echo "cleanRelease Done."
	@echo ""

# Clean up all stray editor back-up files, any .o or .a left around in this directory
# Remove all built object files (.o and .a) and compiled and linked binaries
clean:
	@rm -rf *~
	@make -s -C tagReader -f Makefile clean
	@make -s -C tagEventor -f tagEventor.mak clean
	#@make -s -C tagEventor -f gtagEventor.mak clean
	@echo "Clean Done."
