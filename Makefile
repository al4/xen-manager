# Debian Makefile for PHP web apps

# App name is derived from debian/control and version from debian/changelog
APPNAME=`awk '/^Package:/ { print $$2 }' debian/control`
VERSION=`head -1 debian/changelog | sed -e 's/^.*(//' -e 's/).*$$//'`
PACKAGE=$(APPNAME)_$(VERSION)_all.deb

all:

install:
	@mkdir -p $(DESTDIR)/etc/opta/
	@rsync -a --delete config/ $(DESTDIR)/etc/opta/
	@mkdir -p $(DESTDIR)/usr/share/$(APPNAME)/
	@rsync -a xenm $(DESTDIR)/usr/share/$(APPNAME)/
	@rsync -a --delete xen_manager/ $(DESTDIR)/usr/share/$(APPNAME)/

version:
	@echo $(APPNAME)
	@echo $(VERSION)
	@echo $(PACKAGE)

package:
	@echo Building $(PACKAGE)
	@dpkg-buildpackage -A -tc -us -uc

	@echo ""
	@echo Now try lintian ../$(PACKAGE)
