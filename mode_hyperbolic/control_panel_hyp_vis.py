from qtpy.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QSpinBox, QDoubleSpinBox,
    QHBoxLayout, QLabel, QMessageBox
)
from sympy import false

from mode_hyperbolic.solver_hyp_eq_therm import SolverHypEqTherm
from mode_hyperbolic.hyperbolic_visualizer import HyperbolicHeatVisualizer
from typing import Optional
import napari
import json
from pathlib import Path

STATE_FILE = Path(__file__).parent / 'state.json'


class ControlPanelHypVis(QWidget):
    """Interactive control panel for the hyperbolic heat conduction simulation.

    Attributes:
        viewer (napari.Viewer): The Napari viewer instance this panel belongs to.
        visualizer (HyperbolicHeatVisualizer or None): Currently running visualizer.
        S_edit (QLineEdit): Input field for the heat source expression.
        N_spin (QSpinBox): Spin box for grid size N.
        x0_edit, y0_edit, z0_edit (QLineEdit): Source coordinate fields.
        T0_spin (QDoubleSpinBox): Initial temperature input.
        tau_edit (QLineEdit): Relaxation time input.
        a_edit (QLineEdit): Thermal diffusivity input.
        dt_edit (QLineEdit): Time step input (may contain arithmetic expressions).
        start_btn, stop_btn (QPushButton): Control buttons.
    """

    def __init__(self, viewer: napari.Viewer) -> None:
        """Initialize the panel and attach it to a Napari viewer.

        Args:
            viewer (napari.Viewer): The Napari viewer instance where the
                simulation will be displayed.
        """

        super().__init__()
        self.viewer = viewer
        self.visualizer: Optional[HyperbolicHeatVisualizer] = None

        self.setWindowTitle("Hyperbolic Heat Control")

        layout = QVBoxLayout(self)

        form = QFormLayout()

        self.S_edit = QLineEdit(
            "1e5 * exp(-((x-x0)**2 + (y-y0)**2 + (z-z0)**2)/(2*0.2**2)) * exp(-(t-0.003)**2/(2*0.0008**2))"
        )
        form.addRow("S(t,x,y,z):", self.S_edit)

        self.N_spin = QSpinBox()
        self.N_spin.setRange(10, 200)
        self.N_spin.setValue(40)
        form.addRow("Grid N:", self.N_spin)

        coord_layout = QHBoxLayout()
        self.x0_edit = QLineEdit("0.2")
        self.y0_edit = QLineEdit("0.5")
        self.z0_edit = QLineEdit("0.5")
        coord_layout.addWidget(QLabel("x0:"))
        coord_layout.addWidget(self.x0_edit)
        coord_layout.addWidget(QLabel("y0:"))
        coord_layout.addWidget(self.y0_edit)
        coord_layout.addWidget(QLabel("z0:"))
        coord_layout.addWidget(self.z0_edit)
        form.addRow("Source pos:", coord_layout)

        self.T0_spin = QDoubleSpinBox()
        self.T0_spin.setRange(0, 1e6)
        self.T0_spin.setValue(200.0)
        form.addRow("T0:", self.T0_spin)

        self.tau_edit = QLineEdit("1e-4")
        form.addRow("τ:", self.tau_edit)

        self.a_edit = QLineEdit("1000e-4")
        form.addRow("α:", self.a_edit)

        self.dt_edit = QLineEdit("1e-4 / 2")
        form.addRow("dt:", self.dt_edit)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start")
        self.stop_btn = QPushButton("Stop")
        self.back_btn = QPushButton("Back")

        self.stop_btn.setEnabled(False)

        self.start_btn.clicked.connect(self.on_start)
        self.stop_btn.clicked.connect(self.on_stop)
        self.back_btn.clicked.connect(self.back_to_menu)

        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        btn_layout.addWidget(self.back_btn)
        layout.addLayout(btn_layout)

    def _read_parameters(self) -> dict | None:
        """Parse and validate all parameter inputs.

        Returns:
            dict or None: A dictionary with keys 'N', 'T0', 'tau', 'a',
                'crds_S' (tuple), 'S' (str), 'dt' if all inputs are valid.
                Returns None and shows an error message if any parameter
                is unparseable or out of bounds.
        """
        try:
            N = self.N_spin.value()
            T0 = self.T0_spin.value()
            tau = float(self.tau_edit.text())
            a = float(self.a_edit.text())
            x0 = float(self.x0_edit.text())
            y0 = float(self.y0_edit.text())
            z0 = float(self.z0_edit.text())
            dt = float(eval(self.dt_edit.text()))
            S = self.S_edit.text()

        except Exception as e:
            QMessageBox.critical(self, "Parameter Error", f"Invalid parameter:\n{e}")
            return None

        if tau <= 0 or a <= 0 or dt <= 0:
            QMessageBox.critical(self, "Parameter Error", "τ, α, dt must be > 0")
            return None

        return {
            "N": N, "T0": T0, "tau": tau, "a": a,
            "crds_S": (x0, y0, z0), "S": S, "dt": dt
        }

    def on_start(self) -> None:
        """Slot for the Start button.

        Reads parameters, creates a new SolverHypEqTherm instance,
        instantiates a HyperbolicHeatVisualizer attached to the existing
        viewer, and begins the simulation timer.

        If a previous simulation is running, it is stopped first.
        """
        params = self._read_parameters()
        if params is None:
            return

        if self.visualizer is not None:
            self.visualizer.stop()
            self.visualizer = None

        solver = SolverHypEqTherm(
            N=params["N"],
            T0=params["T0"],
            tau=params["tau"],
            a=params["a"],
            crds_S=params["crds_S"],
            S=params["S"],
            dt=params["dt"]
        )

        self.visualizer = HyperbolicHeatVisualizer(solver, self.viewer)
        self.visualizer.start(interval_ms=10)

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

    def on_stop(self) -> None:
        """Slot for the Stop button.

        Stops the simulation timer and discards the current visualizer.
        Re-enables the Start button for a new run.
        """
        if self.visualizer is not None:
            self.visualizer.stop()
            self.visualizer = None

        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def back_to_menu(self) -> None:
        """Stop any running simulation, write the state file to request the
        launcher to return to the main menu, and then terminate the current
        process.
        """

        if self.visualizer is not None:
            self.visualizer.stop()
            self.visualizer = None

        state = {'mode': 0, 'should_continue': True}
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f)

        self.viewer.window.close()
        app = QApplication.instance()
        if app is not None:
            app.quit()