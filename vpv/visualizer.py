from typing import Any, Optional
import napari
from qtpy import QtCore

class FourierHeatVisualizer:
    """
    Визуализация уравнения теплопроводности Фурье в реальном времени.
    """
    def __init__(self, solver: Any, viewer: Optional[napari.Viewer] = None) -> None:
        self.solver: Any = solver
        self._own_viewer = viewer is None

        if self._own_viewer:
            self.viewer = napari.Viewer(title="Fourier Heat Conduction", ndisplay=3)
        else:
            self.viewer = viewer

        for layer in list(self.viewer.layers):
            if layer.name == "Temperature":
                self.viewer.layers.remove(layer)

        self.layer = self.viewer.add_image(
            solver.arr_T, name="Temperature",
            colormap="hot", rendering="translucent", opacity=0.6
        )
        self.step: int = 0
        self.timer: Optional[QtCore.QTimer] = None

    def update(self) -> None:
        self.solver.next_step_integration()
        T = self.solver.arr_T
        t = self.solver.state[1]

        self.layer.data = T
        self.layer.contrast_limits = [float(T.min()), float(T.max())]
        self.viewer.title = f"Time: {t*1000:.3f} ms | Max T: {T.max():.2f} "
        self.step += 1

    def start(self, interval_ms: int = 10) -> None:
        if self.timer is not None:
            self.stop()
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(interval_ms)
        if self._own_viewer:
            napari.run()

    def stop(self) -> None:
        if self.timer is not None:
            self.timer.stop()
            self.timer.deleteLater()
            self.timer = None