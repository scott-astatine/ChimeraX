# === UCSF ChimeraX Copyright ===
# Copyright 2016 Regents of the University of California.
# All rights reserved.  This software provided pursuant to a
# license agreement containing restrictions on its disclosure,
# duplication and use.  For details see:
# http://www.rbvi.ucsf.edu/chimerax/docs/licensing.html
# This notice must be embedded in or attached to all copies,
# including partial copies, of the software or any revisions
# or derivations thereof.
# === UCSF ChimeraX Copyright ===

TOP = ../..
include $(TOP)/mk/config.make

SUBDIRS = $(APP_NAME) structcomp
ifneq (,$(wildcard /usr/bin/valgrind))
SUBDIRS += valgrind
endif

NO_SUBDIR_TEST=1
include $(TOP)/mk/subdir.make

all:

install:

clean:
