from typing import Any
import napari
from qtpy import QtCore


class HyperbolicHeatVisualizer:
    """
    Real-time 3D visualization of a hyperbolic heat conduction simulation
    using Napari as the rendering backend.

    This class couples a numerical solver with a visualization loop
    driven by a Qt timer.
    """

    def __init__(self, solver: Any) -> None:
        """
        Initialize the visualizer.

        Args:
            solver : Any
                A heat equation solver instance that must provide:
                - arr_T : 3D numpy array (temperature field)
                - state : tuple/list where state[2] is time
                - next_step_integration() method
        """
        self.solver: Any = solver

        self.viewer: napari.Viewer = napari.Viewer(
            title="Hyperbolic Heat Conduction",
            ndisplay=3
        )

        self.layer = self.viewer.add_image(
            solver.arr_T,
            name="Temperature",
            colormap="hot",
            rendering="translucent",
            opacity=0.2
        )

        self.step: int = 0
        self.timer: QtCore.QTimer | None = None

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

    def start(self) -> None:
        """
        Start the simulation loop using a Qt timer and launch Napari.
        """
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(10)

        napari.run()