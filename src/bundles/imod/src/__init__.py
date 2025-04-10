# vim: set expandtab shiftwidth=4 softtabstop=4:

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


class _IMODBundleAPI(BundleAPI):

    @staticmethod
    def run_provider(session, name, mgr):
        from chimerax.open_command import OpenerInfo
        class Info(OpenerInfo):
            def open(self, session, path, file_name, meshes = True, contours = False):
                from . import imod
                return imod.read_imod_model(session, path,
                                            meshes = meshes, contours = contours)
            @property
            def open_args(self):
                from chimerax.core.commands import IntArg, BoolArg
                return { 'meshes': BoolArg,
                         'contours': BoolArg }
        return Info()

bundle_api = _IMODBundleAPI()
