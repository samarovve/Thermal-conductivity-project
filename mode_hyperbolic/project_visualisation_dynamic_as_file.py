import napari
from mode_hyperbolic.control_panel_hyp_vis import ControlPanelHypVis

def start() -> None:
    """Launch the hyperbolic heat conduction simulation in a dedicated Napari viewer."""

    viewer = napari.Viewer(title="Hyperbolic Heat Conduction", ndisplay=3)
    panel = ControlPanelHypVis(viewer)
    viewer.window.add_dock_widget(panel, area='right')
    napari.run()

start()