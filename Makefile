# Debian Makefile for PHP web apps

# App name is derived from debian/control and version from debian/changelog
APPNAME=`awk '/^Package:/ { print $$2 }' debian/control`
VERSION=`head -1 debian/changelog | sed -e 's/^.*(//' -e 's/).*$$//'`
PACKAGE=$(APPNAME)_$(VERSION)_all.deb

all:

install:
	@mkdir -p $(DESTDIR)/etc/opta/
	@rsync -a --delete --exclude '/.svn' --exclude '*/.svn' config/ $(DESTDIR)/etc/opta/
	@mkdir -p $(DESTDIR)/usr/share/$(APPNAME)/htdocs/
	@rsync -a --delete --exclude '/.svn' --exclude '*/.svn' htdocs/ $(DESTDIR)/usr/share/$(APPNAME)/htdocs/

version:
	@echo $(APPNAME)
	@echo $(VERSION)
	@echo $(PACKAGE)

package:
	@echo Building $(PACKAGE)
	@dpkg-buildpackage -A -tc -us -uc

	@echo ""
	@echo Now try lintian ../$(PACKAGE)
