# vim: set expandtab ts=4 sw=4:

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

from chimerax.core.toolshed import BundleAPI

class _ModelSeriesAPI(BundleAPI):

    @staticmethod
    def register_command(command_name, logger):
        from . import mseries
        mseries.register_mseries_command(logger)

    @staticmethod
    def get_class(class_name):
        if class_name in ['ModelSequenceSlider']:
            from . import mseries
            return getattr(mseries, class_name)

bundle_api = _ModelSeriesAPI()
