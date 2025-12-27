"""
Maxar Open Data Plugin for QGIS

A plugin for browsing, filtering, and visualizing Maxar Open Data satellite imagery.
This plugin provides access to pre- and post-event high-resolution satellite imagery
for emergency planning, damage assessment, and recovery.
"""

from .maxar_open_data import MaxarOpenData


def classFactory(iface):
    """Load MaxarOpenData class from file maxar_open_data.

    Args:
        iface: A QGIS interface instance.

    Returns:
        MaxarOpenData: The plugin instance.
    """
    return MaxarOpenData(iface)
