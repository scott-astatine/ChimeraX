// vi: set expandtab shiftwidth=4 softtabstop=4:

/*
 * === UCSF ChimeraX Copyright ===
 * Copyright 2016 Regents of the University of California.
 * All rights reserved.  This software provided pursuant to a
 * license agreement containing restrictions on its disclosure,
 * duplication and use.  For details see:
 * http://www.rbvi.ucsf.edu/chimerax/docs/licensing.html
 * This notice must be embedded in or attached to all copies,
 * including partial copies, of the software or any revisions
 * or derivations thereof.
 * === UCSF ChimeraX Copyright ===
 */

// ----------------------------------------------------------------------------
//
#ifndef STL_HEADER_INCLUDED
#define STL_HEADER_INCLUDED

#include <Python.h>			// use PyObject

extern "C" {

PyObject *stl_pack(PyObject *s, PyObject *args, PyObject *keywds);
PyObject *stl_unpack(PyObject *s, PyObject *args, PyObject *keywds);

}

#endif
