import napari
from control_panel import ControlPanelHypVis

def main():
    viewer = napari.Viewer(title="Hyperbolic Heat Conduction", ndisplay=3)
    panel = ControlPanelHypVis(viewer)
    viewer.window.add_dock_widget(panel, area="right")
    napari.run()

if __name__ == "__main__":
    main()