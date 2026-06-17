from qtpy.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QSpinBox, QDoubleSpinBox,
    QHBoxLayout, QLabel, QMessageBox
)
from vpv.solver_eq_therm import SolverFourierTherm
from vpv.visualizer import FourierHeatVisualizer
from typing import Optional
import napari
import json
from pathlib import Path

STATE_FILE = Path(__file__).parent / 'state.json'

class ControlPanelFourierVis(QWidget):
    def __init__(self, viewer: napari.Viewer) -> None:
        super().__init__()
        self.viewer = viewer
        self.visualizer: Optional[FourierHeatVisualizer] = None
        self.setWindowTitle("Fourier Heat Control")

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.h_edit = QLineEdit("0.5")
        form.addRow("h (cooling):", self.h_edit)

        self.P_edit = QLineEdit("50")
        form.addRow("P (Watt):", self.P_edit)

        self.a_edit = QLineEdit("1e-5")
        form.addRow("a (diffusivity):", self.a_edit)

        self.T_air_edit = QLineEdit("25")
        form.addRow("T_air (°C):", self.T_air_edit)

        self.N_spin = QSpinBox()
        self.N_spin.setRange(10, 150)
        self.N_spin.setValue(40)
        form.addRow("Grid N:", self.N_spin)

        self.T0_spin = QDoubleSpinBox()
        self.T0_spin.setRange(-50, 1000)
        self.T0_spin.setValue(0.0)
        form.addRow("T0 (°C):", self.T0_spin)

        self.dt_edit = QLineEdit("1e-5")
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
        try:
            h = float(self.h_edit.text())
            P = float(self.P_edit.text())
            a = float(self.a_edit.text())
            T_air = float(self.T_air_edit.text())
            N = self.N_spin.value()
            T0 = self.T0_spin.value()
            dt = float(eval(self.dt_edit.text()))
        except Exception as e:
            QMessageBox.critical(self, "Parameter Error", f"Invalid parameter:\n{e}")
            return None

        if a <= 0 or dt <= 0 or P < 0:
            QMessageBox.critical(self, "Parameter Error", "a, dt must be > 0, P >= 0")
            return None

        return {"N": N, "T0": T0, "a": a, "h": h, "P": P, "T_air": T_air, "dt": dt}

    def on_start(self) -> None:
        params = self._read_parameters()
        if params is None:
            return
        if self.visualizer is not None:
            self.visualizer.stop()
            self.visualizer = None

        solver = SolverFourierTherm(
            N=params["N"], T0=params["T0"], a=params["a"],
            h=params["h"], P=params["P"], T_air=params["T_air"],
            dt=params["dt"]
        )
        self.visualizer = FourierHeatVisualizer(solver, self.viewer)
        self.visualizer.start(interval_ms=10)

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

    def on_stop(self) -> None:
        if self.visualizer is not None:
            self.visualizer.stop()
            self.visualizer = None
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def back_to_menu(self) -> None:
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