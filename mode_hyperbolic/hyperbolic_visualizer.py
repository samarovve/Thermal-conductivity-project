from typing import Any, Optional
import napari
from qtpy import QtCore

class HyperbolicHeatVisualizer:
    """
    Real-time 3D visualization of a hyperbolic heat conduction simulation
    using Napari as the rendering backend.

    This class couples a numerical solver with a visualization loop
    driven by a Qt timer.
    """

    def __init__(self, solver: Any, viewer: Optional[napari.Viewer] = None) -> None:
        """
        Initialize the visualizer.

        Args:
            solver : Any
                A heat equation solver instance that must provide:
                - arr_T : 3D numpy array (temperature field)
                - state : tuple/list where state[2] is time
                - next_step_integration() method
            viewer : napari.Viewer or None
                Existing viewer to attach to (if None, a new one is created).
        """
        self.solver: Any = solver
        self._own_viewer = viewer is None

        if self._own_viewer:
            self.viewer = napari.Viewer(
                title="Hyperbolic Heat Conduction",
                ndisplay=3
            )
        else:
            self.viewer = viewer

        # Удаляем старый слой с таким же именем, если он уже есть
        for layer in list(self.viewer.layers):
            if layer.name == "Temperature":
                self.viewer.layers.remove(layer)

        self.layer = self.viewer.add_image(
            solver.arr_T,
            name="Temperature",
            colormap="hot",
            rendering="translucent",
            opacity=0.6
        )

        self.step: int = 0
        self.timer: Optional[QtCore.QTimer] = None

    def update(self) -> None:
        """
        Perform one simulation step and update visualization.
        """
        self.solver.next_step_integration()

        T = self.solver.arr_T
        t = self.solver.state[2]

        self.layer.data = T
        self.layer.contrast_limits = [200, float(T.max())]

        self.viewer.title = (
            f"Time: {t * 1000:.3f} ms | Max T: {T.max():.2f}"
        )

        self.step += 1

    def start(self, interval_ms: int = 10) -> None:
        """
        Start the simulation loop using a Qt timer.
        If the viewer was created internally, also launches napari.run().
        """
        if self.timer is not None:
            self.stop()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(interval_ms)

        if self._own_viewer:
            napari.run()

    def stop(self) -> None:
        """Stop the simulation timer without closing the viewer."""
        if self.timer is not None:
            self.timer.stop()
            self.timer.deleteLater()
            self.timer = None