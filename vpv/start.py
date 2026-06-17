import napari
from vpv.control_panel_vis import ControlPanelFourierVis

def start() -> None:
    """Launch the hyperbolic heat conduction simulation in a dedicated Napari viewer."""

    viewer = napari.Viewer(title="Hyperbolic Heat Conduction", ndisplay=3)
    panel = ControlPanelFourierVis(viewer)
    viewer.window.add_dock_widget(panel, area='right')
    napari.run()

start()