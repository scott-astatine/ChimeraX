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

from chimerax.core.tools import ToolInstance
from chimerax.core.errors import UserError
from chimerax.core.settings import Settings
from Qt.QtCore import Qt
from Qt.QtWidgets import QDialog

class DouseSettings(Settings):
    AUTO_SAVE = {
        "show_hbonds": True,
    }

from chimerax.check_waters.tool import CheckWaterViewer, check_overlap
class DouseResultsViewer(CheckWaterViewer):

    help = "help:user/tools/waterplacement.html#waterlist"

    def __init__(self, session, tool_name, orig_model=None, douse_model=None, compared_waters=None,
            map=None):
        # if 'model' is None, we are being restored from a session and _finalize_init() will be called later
        super().__init__(session, tool_name, douse_model, compare_info=(orig_model, compared_waters),
            model_labels=("input", "douse"), compare_map=map, category_tips=(
            "Waters placed by douse that are not in input model",
            "Waters in input model and also found by douse",
            "Waters in input model only"
            ))

from chimerax.core.settings import Settings
from .douse import command_defaults as douse_defaults
class LaunchDouseSettings(Settings):
    AUTO_SAVE = {
        'first_shell': not douse_defaults['far_water'],
        'keep_waters': douse_defaults['keep_input_water'],
        'hide_map': douse_defaults['map_range'] > 0,
        'hide_map_dist': douse_defaults['map_range'],
        'res_range': douse_defaults['residue_range'],
        'verbose': douse_defaults['verbose'],
    }

class LaunchDouseTool(ToolInstance):
    help = "help:user/tools/waterplacement.html"

    def __init__(self, session, tool_name):
        super().__init__(session, tool_name)
        from chimerax.ui import MainToolWindow
        self.tool_window = tw = MainToolWindow(self)
        parent = tw.ui_area

        from Qt.QtWidgets import QVBoxLayout, QGridLayout, QLabel
        from Qt.QtCore import Qt
        layout = QVBoxLayout()
        parent.setLayout(layout)
        #layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(1)

        input_layout = QGridLayout()
        #input_layout.setContentsMargins(0,0,0,0)
        input_layout.setSpacing(1)
        layout.addLayout(input_layout)
        input_layout.addWidget(QLabel("Place waters for structure..."), 0, 0,
            alignment=Qt.AlignHCenter|Qt.AlignBottom)
        input_layout.addWidget(QLabel("Guided by map..."), 0, 1, alignment=Qt.AlignHCenter|Qt.AlignBottom)
        from chimerax.atomic.widgets import AtomicStructureMenuButton
        self.structure_menu = AtomicStructureMenuButton(session)
        input_layout.addWidget(self.structure_menu, 1, 0, alignment=Qt.AlignHCenter|Qt.AlignTop)
        from chimerax.ui.widgets import ModelMenuButton
        from chimerax.map import Volume
        self.map_menu = ModelMenuButton(session, class_filter=Volume)
        input_layout.addWidget(self.map_menu, 1, 1, alignment=Qt.AlignHCenter|Qt.AlignTop)

        if not hasattr(self.__class__, 'settings'):
            self.__class__.settings = LaunchDouseSettings(session, "launch douse")
        from chimerax.ui.options import OptionsPanel, BooleanOption, FloatOption
        options = OptionsPanel(sorting=False, scrolled=False)
        layout.addWidget(options)
        self.keep_waters_option = BooleanOption("Keep waters from input structure",
            None, None, attr_name="keep_waters", settings=self.settings)
        options.add_option(self.keep_waters_option)
        self.first_shell_option = BooleanOption("First shell only", None, None,
            attr_name="first_shell", settings=self.settings,
            balloon="Only place waters that interact directly with structure, rather than other waters")
        options.add_option(self.first_shell_option)
        from .douse import douse_needs_resolution
        if douse_needs_resolution(session):
            self.resolution_option = FloatOption("Map resolution", 3.0, None, decimal_places=1,
                min=0.0, max=99.9, right_text="\N{ANGSTROM SIGN}")
            options.add_option(self.resolution_option)
        self.hide_map_option = BooleanOption("Hide map far from waters", None, None,
            attr_name="hide_map", settings=self.settings)
        options.add_option(self.hide_map_option)
        self.hide_map_dist_option = FloatOption("Map-hiding distance", None, None,
            attr_name="hide_map_dist", settings=self.settings, decimal_places=1, step=1, min=0, max=99,
            right_text="\N{ANGSTROM SIGN}")
        options.add_option(self.hide_map_dist_option)
        self.res_range_option = FloatOption("Show residues with atoms within this distance of waters", None,
            None, attr_name="res_range", settings=self.settings, decimal_places=1, step=1, min=0, max=99,
            right_text="\N{ANGSTROM SIGN}")
        options.add_option(self.res_range_option)
        self.verbose_option = BooleanOption("Show full douse output in log", None, None,
            attr_name="verbose", settings=self.settings)
        options.add_option(self.verbose_option)

        from Qt.QtWidgets import QDialogButtonBox as qbbox
        self.bbox = bbox = qbbox(qbbox.Ok | qbbox.Close | qbbox.Help)
        bbox.accepted.connect(self.launch_douse)
        bbox.rejected.connect(self.delete)
        from chimerax.core.commands import run
        bbox.helpRequested.connect(lambda *, run=run, ses=session: run(ses, "help " + self.help))
        layout.addWidget(bbox)

        tw.manage(placement=None)

    def launch_douse(self):
        structure = self.structure_menu.value
        if not structure:
            raise UserError("Must specify a structure for water placement")
        map = self.map_menu.value
        if not map:
            raise UserError("Must specify a map for water placement")
        check_overlap(structure, map)
        cmd = "phenix douse %s near %s" % (map.atomspec, structure.atomspec)
        from chimerax.core.commands import BoolArg
        first_shell = self.first_shell_option.value
        if first_shell != (not douse_defaults['far_water']):
            cmd +=  " farWater %s" % BoolArg.unparse(not first_shell)
        keep_waters = self.keep_waters_option.value
        if keep_waters != douse_defaults['keep_input_water']:
            cmd += " keepInputWater %s" % BoolArg.unparse(keep_waters)
        hide_map = self.hide_map_option.value
        if hide_map:
            hide_map_dist = self.hide_map_dist_option.value
            if hide_map_dist != douse_defaults['map_range']:
                cmd += " mapRange %g" % hide_map_dist
        elif douse_defaults['map_range'] > 0:
            cmd += " mapRange 0"
        res_range = self.res_range_option.value
        if res_range != douse_defaults['residue_range']:
            cmd += " residueRange %g" % res_range
        verbose = self.verbose_option.value
        if verbose != douse_defaults['verbose']:
            cmd += " verbose %s" % BoolArg.unparse(verbose)
        if hasattr(self, 'resolution_option'):
            cmd += " resolution %g" % self.resolution_option.value
        from chimerax.core.commands import run
        run(self.session, cmd)
        self.delete()

class LaunchEmplaceLocalTool(ToolInstance):
    help = "help:user/tools/localemfitting.html"

    CENTER_MODEL = "center of model..."
    CENTER_SELECTION = "center of selection"
    CENTER_VIEW = "center of view"
    CENTER_XYZ = "specified xyz position..."
    CENTERING_METHODS = [CENTER_MODEL, CENTER_SELECTION, CENTER_VIEW, CENTER_XYZ]

    def __init__(self, session, tool_name):
        super().__init__(session, tool_name)
        from chimerax.ui import MainToolWindow
        self.tool_window = tw = MainToolWindow(self, close_destroys=False)
        parent = tw.ui_area

        if not hasattr(self.__class__, 'settings'):
            self.__class__.settings = LaunchEmplaceLocalSettings(session, "launch emplace local")

        from Qt.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QWidget, QPushButton, QMenu, QLineEdit
        from Qt.QtWidgets import QCheckBox, QGridLayout
        from Qt.QtGui import QDoubleValidator
        from Qt.QtCore import Qt
        layout = QVBoxLayout()
        parent.setLayout(layout)
        #layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(1)

        centering_widget = QWidget()
        layout.addWidget(centering_widget, alignment=Qt.AlignCenter, stretch=1)
        structure_layout = QGridLayout()
        structure_layout.setSpacing(1)
        centering_widget.setLayout(structure_layout)
        structure_layout.addWidget(QLabel("Fit "), 0, 0, alignment=Qt.AlignRight)
        from chimerax.atomic.widgets import AtomicStructureMenuButton
        self.structure_menu = AtomicStructureMenuButton(session)
        structure_layout.addWidget(self.structure_menu, 0, 1)
        structure_layout.addWidget(QLabel(" using "), 0, 2)
        self.HALF_MAPS, self.FULL_MAP = self.menu_items = ["half maps", "full map"]
        self.mt_explanations = {
            self.HALF_MAPS: "Using half maps is recommended if available.  If local resolution is not specified (i.e. is zero) then it will be estimated from the half maps.",
            self.FULL_MAP: "Using only the full map is less reliable than using half maps, so use half maps if available.  If using a full map, then specifying a (non-zero) resolution is mandatory."
        }
        assert len(self.menu_items) == len(self.mt_explanations)
        self.map_type_mb = QPushButton(self.HALF_MAPS)
        structure_layout.addWidget(self.map_type_mb, 0, 3)
        mt_menu = QMenu(self.map_type_mb)
        mt_menu.triggered.connect(self._map_type_changed)
        for item in self.menu_items:
            mt_menu.addAction(item)
        self.map_type_mb.setMenu(mt_menu)
        from chimerax.ui.widgets import ModelListWidget, ModelMenuButton
        ex_lab = self.mt_explanation_label = QLabel(self.mt_explanations[self.HALF_MAPS])
        ex_lab.setWordWrap(True)
        ex_lab.setAlignment(Qt.AlignCenter)
        from chimerax.ui import shrink_font
        shrink_font(ex_lab, fraction=0.85)
        structure_layout.addWidget(ex_lab, 1, 0, 1, 4)
        class ShortMLWidget(ModelListWidget):
            def sizeHint(self):
                hint = super().sizeHint()
                hint.setHeight(hint.height()//2)
                return hint
        from chimerax.map import Volume
        self.half_map_list = ShortMLWidget(session, class_filter=Volume)
        structure_layout.addWidget(self.half_map_list, 0, 4, 2, 1, alignment=Qt.AlignLeft)
        structure_layout.setRowStretch(1, 1)
        structure_layout.setColumnStretch(4, 1)

        from chimerax.ui.options import OptionsPanel, FloatOption
        res_options = OptionsPanel(scrolled=False, contents_margins=(0,0,0,0))
        layout.addWidget(res_options, alignment=Qt.AlignCenter)
        self.res_option = FloatOption("Local map resolution:", None, None, min=0.0, decimal_places=2,
            step=0.1, max=99.99, balloon="Map resolution in the search region.\n"
            "If unknown, and using half maps, providing a value of zero will cause an estimated\n"
            "resolution to be used.  For full maps, providing the resolution is mandatory.")
        res_options.add_option(self.res_option)

        centering_widget = QWidget()
        layout.addWidget(centering_widget, alignment=Qt.AlignCenter, stretch=1)
        centering_layout = QHBoxLayout()
        centering_layout.setSpacing(1)
        centering_widget.setLayout(centering_layout)
        centering_tip = '''How to specify the center of the fitting search.  Choices are:

%s — If the center of rotation is being displayed ("cofr showPivot true") use that.  Otherwise,
    if the center of rotation is a fixed point ("cofr fixed") use that.  If neither of those is
    true, use the midpoint of where the center of the window intersects the front and back of
    the bounding box of the map.

%s — The center of a particular model, frequently the map, or the structure to be fitted once
    it has been approximately positioned.

%s - The center of the bounding box enclosing currently selected objects.

%s — A specific X/Y/Z position, given in angstroms relative to the origin of the map.
        ''' % (self.CENTER_VIEW.rstrip('.'), self.CENTER_MODEL.rstrip('.'),
            self.CENTER_SELECTION.rstrip('.'), self.CENTER_XYZ.rstrip('.'))
        centering_label = QLabel("Center search at")
        centering_label.setToolTip(centering_tip)
        centering_layout.addWidget(centering_label, alignment=Qt.AlignRight)
        self.centering_button = QPushButton()
        self.centering_button.setToolTip(centering_tip)
        centering_layout.addWidget(self.centering_button)
        centering_menu = QMenu(self.centering_button)
        for method in self.CENTERING_METHODS:
            centering_menu.addAction(method)
        centering_menu.triggered.connect(lambda act: self._set_centering_method(act.text()))
        self.centering_button.setMenu(centering_menu)
        self.xyz_area = QWidget()
        xyz_layout = QHBoxLayout()
        xyz_layout.setSpacing(1)
        self.xyz_area.setLayout(xyz_layout)
        self.xyz_widgets = []
        for lab in ["X", " Y", " Z"]:
            xyz_layout.addWidget(QLabel(lab), alignment=Qt.AlignRight)
            entry = QLineEdit()
            entry.setValidator(QDoubleValidator())
            entry.setAlignment(Qt.AlignCenter)
            entry.setMaximumWidth(50)
            entry.setText("0")
            xyz_layout.addWidget(entry, alignment=Qt.AlignLeft)
            self.xyz_widgets.append(entry)
        self.model_menu = ModelMenuButton(session)
        centering_layout.addWidget(self.model_menu)
        centering_layout.addWidget(self.xyz_area)
        self._set_centering_method()

        self.verify_center_checkbox = QCheckBox("Interactively verify/adjust center before searching")
        self.verify_center_checkbox.setChecked(True)
        layout.addWidget(self.verify_center_checkbox, alignment=Qt.AlignCenter)
        self.opaque_maps_checkbox = QCheckBox("Make maps opaque while verifying center")
        self.opaque_maps_checkbox.setToolTip(
            "ChimeraX cannot show multiple transparent objects correctly, so make maps opaque\n"
            "while transparent interactive search-center sphere is being displayed"
        )
        self.opaque_maps_checkbox.setChecked(self.settings.opaque_maps)
        self.verify_center_checkbox.clicked.connect(lambda checked, b=self.opaque_maps_checkbox:
            b.setHidden(not checked))
        layout.addWidget(self.opaque_maps_checkbox, alignment=Qt.AlignCenter)
        self.show_sharpened_map_checkbox = QCheckBox("Show locally sharpened map computed by Phenix")
        self.show_sharpened_map_checkbox.setChecked(self.settings.show_sharpened_map)
        self.show_sharpened_map_checkbox.setToolTip(
            "Phenix.emplace_local computes a sharpened map for the region being searched.\n"
            "This sharpened map is what is actually used for the fitting.  This checkbox\n"
            "controls whether the sharpened map is initially shown in ChimeraX once the\n"
            "calculation completes.  Even if not checked, the map will be opened (but hidden)."
        )
        layout.addWidget(self.show_sharpened_map_checkbox, alignment=Qt.AlignCenter)
        layout.addStretch(1)

        from Qt.QtWidgets import QDialogButtonBox as qbbox
        self.bbox = bbox = qbbox(qbbox.Ok | qbbox.Apply | qbbox.Close | qbbox.Help)
        bbox.accepted.connect(self.launch_emplace_local)
        bbox.button(qbbox.Apply).clicked.connect(lambda *args: self.launch_emplace_local(apply=True))
        bbox.rejected.connect(self.delete)
        if self.help:
            from chimerax.core.commands import run
            bbox.helpRequested.connect(lambda *, run=run, ses=session: run(ses, "help " + self.help))
        else:
            bbox.button(qbbox.Help).setEnabled(False)
        layout.addWidget(bbox)

        tw.manage(placement=None)

    def launch_emplace_local(self, apply=False):
        structure = self.structure_menu.value
        if not structure:
            raise UserError("Must specify a structure to fit")
        map_type = self.map_type_mb.text()
        maps = self.half_map_list.value
        res = self.res_option.value
        if map_type == self.HALF_MAPS:
            if len(maps) != 2:
                raise UserError("Must specify exactly two half maps for fitting")
        else:
            if len(maps) != 1:
                raise UserError("Must specify exactly one full map for fitting")
            if res == 0.0:
                raise UserError("Must specify a resolution value for the full map")
        method = self.centering_button.text()
        if method == self.CENTER_XYZ:
            center = [float(widget.text()) for widget in self.xyz_widgets]
        elif method == self.CENTER_MODEL:
            centering_model = self.model_menu.value
            if centering_model is None:
                raise UserError("No model chosen for specifying search center")
            bnds = centering_model.bounds()
            if bnds is None:
                raise UserError("No part of model for specifying search center is displayed")
            center = bnds.center()
        elif method == self.CENTER_VIEW:
            # If pivot point shown or using fixed center of rotation, use that.
            # Otherwise, midpoint where center of window intersects front and back of halfmap bounding box.
            view_center = None
            mv = self.session.main_view
            for d in mv.drawing.child_drawings():
                if d.__class__.__name__ == "PivotIndicator":
                    view_center = d.position.origin()
                    break
            else:
                if mv.center_of_rotation_method == "fixed":
                    view_center = mv.center_of_rotation
            if view_center is None:
                from chimerax.map import Volume
                shown_vols = [v for v in self.session.models if isinstance(v, Volume) and v.display]
                if len(shown_vols) == 1:
                    view_map = shown_vols[0]
                else:
                    view_map = maps[0]
                from .emplace_local import view_box, ViewBoxError
                try:
                    view_center = view_box(self.session, view_map)
                except ViewBoxError as e:
                    raise UserError(str(e))
            center = view_center
        elif method == self.CENTER_SELECTION:
            if self.session.selection.empty():
                raise UserError("Nothing selected")
            from chimerax.atomic import selected_atoms
            sel_atoms = selected_atoms(self.session)
            from chimerax.geometry import point_bounds, union_bounds
            atom_bbox = point_bounds(sel_atoms.scene_coords)
            atom_models = set(sel_atoms.unique_structures)
            bbox = union_bounds([atom_bbox]
                + [m.bounds() for m in self.session.selection.models() if m not in atom_models])
            if bbox is None:
                raise UserError("No bounding box for selected items")
            center = bbox.center()
        else:
            raise AssertionError("Unknown centering method")
        self.settings.search_center = method
        self.settings.show_sharpened_map = ssm = self.show_sharpened_map_checkbox.isChecked()
        if self.verify_center_checkbox.isChecked():
            self.settings.opaque_maps = self.opaque_maps_checkbox.isChecked()
            VerifyCenterDialog(self.session, structure, maps, res, center, self.settings.opaque_maps, ssm)
        else:
            _run_emplace_local_command(self.session, structure, maps, res, center, ssm)
        if not apply:
            self.display(False)

    def _map_type_changed(self, action):
        self.map_type_mb.setText(action.text())
        self.mt_explanation_label.setText(self.mt_explanations[action.text()])

    def _set_centering_method(self, method=None):
        if method is None:
            method = self.settings.search_center
            if method not in self.CENTERING_METHODS:
                method = self.CENTER_MODEL
        self.centering_button.setText(method)
        self.xyz_area.setHidden(True)
        self.model_menu.setHidden(True)
        if method == self.CENTER_XYZ:
            self.xyz_area.setHidden(False)
        elif method == self.CENTER_MODEL:
            self.model_menu.setHidden(False)

class VerifyCenterDialog(QDialog):
    def __init__(self, session, structure, maps, resolution, initial_center, opaque_maps,
            show_sharpened_map):
        super().__init__()
        self.session = session
        self.structure = structure
        self.maps = maps
        self.resolution = resolution
        self.opaque_maps = opaque_maps
        self.show_sharpened_map = show_sharpened_map

        # adjusted_center used to compensate for map origin, but improvements to emplace_local
        # have made that adjustment unnecessary
        adjusted_center = initial_center
        marker_set_id = session.models.next_id()[0]
        from chimerax.core.commands import run
        self.marker = run(session, "marker #%d position %g,%g,%g radius %g color 100,65,0,50"
            % (marker_set_id, *adjusted_center, self.find_search_radius()))

        from chimerax.core.models import REMOVE_MODELS
        self.handler = session.triggers.add_handler(REMOVE_MODELS, self._check_still_valid)
        from Qt.QtWidgets import QVBoxLayout, QLabel
        layout = QVBoxLayout()
        self.setLayout(layout)
        search_button_label = "Start search"
        instructions = QLabel(
            "A transparent orange marker (model #%d) has been drawn to show the search volume and location. "
            "  Fits that place any part of the atomic structure within the marker sphere will be evaluated."
            "  The size of the search volume is based on the size of the structure and cannot be adjusted, "
            "but the search center can be moved by moving the marker, "
            "using any ChimeraX method for moving markers or models "
            '(e.g. the "move markers" right mouse mode in the Markers section of the toolbar).'
            '  When the position is satisfactory, click "%s."'
             % (marker_set_id, search_button_label)
        )
        instructions.setWordWrap(True)
        instructions.setAlignment(Qt.AlignCenter)
        layout.addWidget(instructions)

        from Qt.QtWidgets import QDialogButtonBox as qbbox
        bbox = qbbox(qbbox.Cancel)
        bbox.addButton(search_button_label, bbox.AcceptRole)
        bbox.accepted.connect(self.launch_emplace_local)
        bbox.accepted.connect(self.close)
        bbox.rejected.connect(self.close)
        layout.addWidget(bbox)

        if opaque_maps:
            from chimerax.map import VolumeSurface
            self.opaque_data = {}
            for m in session.models:
                if isinstance(m, VolumeSurface) and m.rgba[-1] < 1.0:
                    self.opaque_data[m] = m.rgba[-1]
                    rgba = list(m.rgba)
                    rgba[-1] = 1.0
                    m.rgba = tuple(rgba)

        self.show()

    def closeEvent(self, event):
        if not self.marker.structure.deleted:
            self.session.models.close([self.marker.structure])
        self.handler.remove()
        super().closeEvent(event)

    def find_search_radius(self):
        import numpy
        crds = self.structure.atoms.coords
        crd_min = numpy.amin(crds, axis=0)
        crd_max = numpy.amax(crds, axis=0)
        mid = (crd_min + crd_max) / 2
        return max(numpy.linalg.norm(crds-mid, axis=1))

    def launch_emplace_local(self):
        if self.opaque_maps:
            for m, alpha in self.opaque_data.items():
                if not m.deleted:
                    rgba = list(m.rgba)
                    rgba[-1] = alpha
                    m.rgba = tuple(rgba)
        center = self.marker.scene_coord
        _run_emplace_local_command(self.session, self.structure, self.maps, self.resolution, center,
            self.show_sharpened_map)

    def _check_still_valid(self, trig_name, removed_models):
        for rm in removed_models:
            if rm in self.maps + [self.structure, self.marker.structure]:
                self.close()
                break

class LaunchEmplaceLocalSettings(Settings):
    AUTO_SAVE = {
        'search_center': LaunchEmplaceLocalTool.CENTER_MODEL,
        'opaque_maps': True,
        'show_sharpened_map': False
    }

def _run_emplace_local_command(session, structure, maps, resolution, center, show_sharpened_map):
    from chimerax.core.commands import run, concise_model_spec, BoolArg
    from chimerax.map import Volume
    cmd = "phenix emplaceLocal %s mapData %s resolution %g center %g,%g,%g showSharpenedMap %s" % (
        structure.atomspec, concise_model_spec(session, maps, relevant_types=Volume, allow_empty_spec=False),
        resolution, *center, BoolArg.unparse(show_sharpened_map))
    run(session, cmd)
