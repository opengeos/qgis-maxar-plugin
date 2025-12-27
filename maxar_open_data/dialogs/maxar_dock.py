"""
Maxar Open Data Dock Widget

This module provides the main dockable panel for browsing and visualizing
Maxar Open Data satellite imagery.
"""

import json
import os
import tempfile
from urllib.request import urlopen
from urllib.error import URLError, HTTPError

from qgis.PyQt.QtCore import Qt, QThread, pyqtSignal, QSettings
from qgis.PyQt.QtWidgets import (
    QDockWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QSpinBox,
    QCheckBox,
    QFormLayout,
    QGroupBox,
    QProgressBar,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QSplitter,
    QMessageBox,
    QDateEdit,
)
from qgis.PyQt.QtGui import QFont
from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    QgsRasterLayer,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsFeature,
    QgsGeometry,
    QgsField,
    QgsFields,
    QgsWkbTypes,
    QgsMapLayerType,
    QgsRectangle,
    QgsFillSymbol,
    QgsSimpleFillSymbolLayer,
)
from qgis.PyQt.QtCore import QVariant, QDate
from qgis.PyQt.QtGui import QColor


# GitHub URLs for the Maxar Open Data
GITHUB_RAW_URL = "https://raw.githubusercontent.com/opengeos/maxar-open-data/master"
DATASETS_CSV_URL = f"{GITHUB_RAW_URL}/datasets.csv"
GEOJSON_URL_TEMPLATE = f"{GITHUB_RAW_URL}/datasets/{{event}}.geojson"


class DataFetchWorker(QThread):
    """Worker thread for fetching data from GitHub."""

    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, url, data_type="text"):
        super().__init__()
        self.url = url
        self.data_type = data_type

    def run(self):
        """Fetch data from the URL."""
        try:
            self.progress.emit(f"Fetching data from {self.url}...")
            with urlopen(self.url, timeout=30) as response:
                content = response.read().decode("utf-8")

            if self.data_type == "json":
                data = json.loads(content)
            else:
                data = content

            self.finished.emit(data)

        except HTTPError as e:
            self.error.emit(f"HTTP Error: {e.code} - {e.reason}")
        except URLError as e:
            self.error.emit(f"URL Error: {e.reason}")
        except json.JSONDecodeError as e:
            self.error.emit(f"JSON Parse Error: {str(e)}")
        except Exception as e:
            self.error.emit(f"Error fetching data: {str(e)}")


class MaxarDockWidget(QDockWidget):
    """Main dockable panel for browsing Maxar Open Data."""

    def __init__(self, iface, parent=None):
        """Initialize the dock widget.

        Args:
            iface: QGIS interface instance.
            parent: Parent widget.
        """
        super().__init__("Maxar Open Data", parent)
        self.iface = iface
        self.settings = QSettings()
        self.events = []
        self.current_geojson = None
        self.footprints_layer = None
        self.fetch_worker = None

        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self._setup_ui()
        self._load_events()

    def _setup_ui(self):
        """Set up the dock widget UI."""
        # Main widget
        main_widget = QWidget()
        self.setWidget(main_widget)

        # Main layout
        layout = QVBoxLayout(main_widget)
        layout.setSpacing(10)

        # Header
        header_label = QLabel("Maxar Open Data")
        header_font = QFont()
        header_font.setPointSize(12)
        header_font.setBold(True)
        header_label.setFont(header_font)
        header_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(header_label)

        # Description
        desc_label = QLabel(
            "Browse and visualize high-resolution satellite imagery from the "
            "Maxar Open Data Program for disaster events."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: gray;")
        layout.addWidget(desc_label)

        # Event Selection Group
        event_group = QGroupBox("Event Selection")
        event_layout = QFormLayout(event_group)

        # Event dropdown
        self.event_combo = QComboBox()
        self.event_combo.setMinimumWidth(200)
        self.event_combo.currentIndexChanged.connect(self._on_event_changed)
        event_layout.addRow("Event:", self.event_combo)

        # Refresh events button
        refresh_btn_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh Events")
        self.refresh_btn.clicked.connect(self._load_events)
        refresh_btn_layout.addWidget(self.refresh_btn)
        refresh_btn_layout.addStretch()
        event_layout.addRow("", refresh_btn_layout)

        layout.addWidget(event_group)

        # Filters Group
        filter_group = QGroupBox("Filters")
        filter_layout = QFormLayout(filter_group)

        # Max cloud cover
        self.cloud_spin = QSpinBox()
        self.cloud_spin.setRange(0, 100)
        self.cloud_spin.setValue(100)
        self.cloud_spin.setSuffix(" %")
        filter_layout.addRow("Max Cloud Cover:", self.cloud_spin)

        # Date filter checkbox
        self.date_check = QCheckBox("Filter by date range")
        self.date_check.setChecked(False)
        self.date_check.stateChanged.connect(self._on_date_filter_changed)
        filter_layout.addRow("", self.date_check)

        # Start date
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate(2020, 1, 1))
        self.start_date_edit.setEnabled(False)
        filter_layout.addRow("Start Date:", self.start_date_edit)

        # End date
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.setEnabled(False)
        filter_layout.addRow("End Date:", self.end_date_edit)

        layout.addWidget(filter_group)

        # Load footprints button
        load_btn_layout = QHBoxLayout()
        self.load_footprints_btn = QPushButton("Load Footprints")
        self.load_footprints_btn.clicked.connect(self._load_footprints)
        self.load_footprints_btn.setEnabled(False)
        load_btn_layout.addWidget(self.load_footprints_btn)
        layout.addLayout(load_btn_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Splitter for table and controls
        splitter = QSplitter(Qt.Vertical)

        # Footprints table
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        table_layout.setContentsMargins(0, 0, 0, 0)

        table_label = QLabel("Imagery Footprints:")
        table_label.setStyleSheet("font-weight: bold;")
        table_layout.addWidget(table_label)

        self.footprints_table = QTableWidget()
        self.footprints_table.setColumnCount(6)
        self.footprints_table.setHorizontalHeaderLabels(
            ["Date", "Platform", "GSD", "Cloud %", "Catalog ID", "Quadkey"]
        )
        self.footprints_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )
        self.footprints_table.horizontalHeader().setStretchLastSection(True)
        self.footprints_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.footprints_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.footprints_table.setAlternatingRowColors(True)
        self.footprints_table.itemSelectionChanged.connect(
            self._on_footprint_selection_changed
        )
        table_layout.addWidget(self.footprints_table)

        splitter.addWidget(table_widget)

        # Actions group
        actions_widget = QWidget()
        actions_layout = QVBoxLayout(actions_widget)
        actions_layout.setContentsMargins(0, 0, 0, 0)

        actions_group = QGroupBox("Actions")
        actions_inner = QVBoxLayout(actions_group)

        # Zoom to selection
        self.zoom_btn = QPushButton("Zoom to Selected")
        self.zoom_btn.clicked.connect(self._zoom_to_selected)
        self.zoom_btn.setEnabled(False)
        actions_inner.addWidget(self.zoom_btn)

        # Load imagery buttons
        imagery_layout = QHBoxLayout()

        self.load_visual_btn = QPushButton("Load Visual")
        self.load_visual_btn.setToolTip("Load visual (RGB) imagery as COG")
        self.load_visual_btn.clicked.connect(lambda: self._load_imagery("visual"))
        self.load_visual_btn.setEnabled(False)
        imagery_layout.addWidget(self.load_visual_btn)

        self.load_ms_btn = QPushButton("Load MS")
        self.load_ms_btn.setToolTip("Load multispectral imagery as COG")
        self.load_ms_btn.clicked.connect(lambda: self._load_imagery("ms_analytic"))
        self.load_ms_btn.setEnabled(False)
        imagery_layout.addWidget(self.load_ms_btn)

        self.load_pan_btn = QPushButton("Load Pan")
        self.load_pan_btn.setToolTip("Load panchromatic imagery as COG")
        self.load_pan_btn.clicked.connect(lambda: self._load_imagery("pan_analytic"))
        self.load_pan_btn.setEnabled(False)
        imagery_layout.addWidget(self.load_pan_btn)

        actions_inner.addLayout(imagery_layout)

        # Clear layers button
        self.clear_btn = QPushButton("Clear All Layers")
        self.clear_btn.clicked.connect(self._clear_layers)
        actions_inner.addWidget(self.clear_btn)

        actions_layout.addWidget(actions_group)

        splitter.addWidget(actions_widget)

        # Set splitter sizes
        splitter.setSizes([300, 150])

        layout.addWidget(splitter)

        # Status label
        self.status_label = QLabel("Ready - Select an event to begin")
        self.status_label.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(self.status_label)

    def _load_events(self):
        """Load available events from GitHub."""
        self.refresh_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.status_label.setText("Loading events...")
        self.status_label.setStyleSheet("color: blue; font-size: 10px;")

        self.fetch_worker = DataFetchWorker(DATASETS_CSV_URL)
        self.fetch_worker.finished.connect(self._on_events_loaded)
        self.fetch_worker.error.connect(self._on_events_error)
        self.fetch_worker.start()

    def _on_events_loaded(self, csv_content):
        """Handle successful events loading."""
        self.progress_bar.setVisible(False)
        self.refresh_btn.setEnabled(True)

        # Parse CSV
        self.events = []
        lines = csv_content.strip().split("\n")
        for line in lines[1:]:  # Skip header
            parts = line.split(",")
            if len(parts) >= 2:
                event_name = parts[0].strip()
                count = int(parts[1].strip())
                self.events.append((event_name, count))

        # Sort by name
        self.events.sort(key=lambda x: x[0].lower())

        # Populate combo box
        self.event_combo.clear()
        self.event_combo.addItem("-- Select an event --", None)
        for event_name, count in self.events:
            self.event_combo.addItem(f"{event_name} ({count} tiles)", event_name)

        self.status_label.setText(f"Loaded {len(self.events)} events")
        self.status_label.setStyleSheet("color: green; font-size: 10px;")

    def _on_events_error(self, error_msg):
        """Handle events loading error."""
        self.progress_bar.setVisible(False)
        self.refresh_btn.setEnabled(True)
        self.status_label.setText(f"Error: {error_msg}")
        self.status_label.setStyleSheet("color: red; font-size: 10px;")

        QMessageBox.warning(
            self,
            "Error Loading Events",
            f"Failed to load events from GitHub:\n\n{error_msg}\n\n"
            "Please check your internet connection and try again.",
        )

    def _on_event_changed(self, index):
        """Handle event selection change."""
        event_name = self.event_combo.currentData()
        self.load_footprints_btn.setEnabled(event_name is not None)
        if event_name:
            self.status_label.setText(f"Selected: {event_name}")
            self.status_label.setStyleSheet("color: gray; font-size: 10px;")

    def _on_date_filter_changed(self, state):
        """Handle date filter checkbox state change."""
        enabled = state == Qt.Checked
        self.start_date_edit.setEnabled(enabled)
        self.end_date_edit.setEnabled(enabled)

    def _load_footprints(self):
        """Load footprints for the selected event."""
        event_name = self.event_combo.currentData()
        if not event_name:
            return

        self.load_footprints_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.status_label.setText(f"Loading footprints for {event_name}...")
        self.status_label.setStyleSheet("color: blue; font-size: 10px;")

        url = GEOJSON_URL_TEMPLATE.format(event=event_name)
        self.fetch_worker = DataFetchWorker(url, data_type="json")
        self.fetch_worker.finished.connect(self._on_footprints_loaded)
        self.fetch_worker.error.connect(self._on_footprints_error)
        self.fetch_worker.start()

    def _on_footprints_loaded(self, geojson_data):
        """Handle successful footprints loading."""
        self.progress_bar.setVisible(False)
        self.load_footprints_btn.setEnabled(True)

        self.current_geojson = geojson_data
        features = geojson_data.get("features", [])

        # Apply cloud filter
        max_cloud = self.cloud_spin.value()
        filtered_features = [
            f
            for f in features
            if f.get("properties", {}).get("tile:clouds_percent", 0) <= max_cloud
        ]

        # Apply date filter if enabled
        if self.date_check.isChecked():
            start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
            end_date = self.end_date_edit.date().toString("yyyy-MM-dd")
            filtered_features = [
                f
                for f in filtered_features
                if self._is_date_in_range(
                    f.get("properties", {}).get("datetime", ""), start_date, end_date
                )
            ]

        # Populate table
        self._populate_footprints_table(filtered_features)

        # Add layer to QGIS (use filtered geojson)
        filtered_geojson = {"type": "FeatureCollection", "features": filtered_features}
        if geojson_data.get("crs"):
            filtered_geojson["crs"] = geojson_data["crs"]

        self._add_footprints_layer(filtered_geojson)

        self.status_label.setText(
            f"Loaded {len(filtered_features)} footprints "
            f"(filtered from {len(features)} total)"
        )
        self.status_label.setStyleSheet("color: green; font-size: 10px;")

    def _is_date_in_range(self, datetime_str, start_date, end_date):
        """Check if a datetime string is within the date range.

        Args:
            datetime_str: ISO format datetime string (e.g., "2023-10-25T04:57:18Z")
            start_date: Start date in "yyyy-MM-dd" format
            end_date: End date in "yyyy-MM-dd" format

        Returns:
            True if the date is within range, False otherwise
        """
        if not datetime_str:
            return False
        try:
            # Extract just the date part
            date_part = datetime_str[:10]
            return start_date <= date_part <= end_date
        except (IndexError, TypeError):
            return False

    def _on_footprints_error(self, error_msg):
        """Handle footprints loading error."""
        self.progress_bar.setVisible(False)
        self.load_footprints_btn.setEnabled(True)
        self.status_label.setText(f"Error: {error_msg}")
        self.status_label.setStyleSheet("color: red; font-size: 10px;")

        QMessageBox.warning(
            self,
            "Error Loading Footprints",
            f"Failed to load footprints:\n\n{error_msg}",
        )

    def _populate_footprints_table(self, features):
        """Populate the footprints table with feature data."""
        self.footprints_table.setRowCount(0)
        self.footprints_table.setRowCount(len(features))

        for row, feature in enumerate(features):
            props = feature.get("properties", {})

            # Store the full feature data
            self.footprints_table.setItem(
                row, 0, QTableWidgetItem(props.get("datetime", "")[:10])
            )
            self.footprints_table.setItem(
                row, 1, QTableWidgetItem(props.get("platform", ""))
            )
            self.footprints_table.setItem(
                row, 2, QTableWidgetItem(str(props.get("gsd", "")))
            )
            self.footprints_table.setItem(
                row, 3, QTableWidgetItem(str(props.get("tile:clouds_percent", "")))
            )
            self.footprints_table.setItem(
                row, 4, QTableWidgetItem(props.get("catalog_id", ""))
            )
            self.footprints_table.setItem(
                row, 5, QTableWidgetItem(props.get("quadkey", ""))
            )

            # Store feature index for later reference
            self.footprints_table.item(row, 0).setData(Qt.UserRole, row)
            self.footprints_table.item(row, 0).setData(Qt.UserRole + 1, feature)

    def _add_footprints_layer(self, geojson_data):
        """Add footprints as a vector layer to QGIS."""
        event_name = self.event_combo.currentData()

        # Remove existing footprints layer if any
        if self.footprints_layer:
            try:
                QgsProject.instance().removeMapLayer(self.footprints_layer.id())
            except Exception:
                pass

        # Create a temporary GeoJSON file
        temp_dir = tempfile.gettempdir()
        temp_file = os.path.join(temp_dir, f"maxar_{event_name}_footprints.geojson")

        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(geojson_data, f)

        # Load as vector layer
        layer_name = f"Maxar - {event_name} Footprints"
        self.footprints_layer = QgsVectorLayer(temp_file, layer_name, "ogr")

        if self.footprints_layer.isValid():
            # Set CRS to WGS84
            layer_crs = QgsCoordinateReferenceSystem("EPSG:4326")
            self.footprints_layer.setCrs(layer_crs)

            # Apply semi-transparent styling
            self._apply_footprints_style(self.footprints_layer)

            # Add to project
            QgsProject.instance().addMapLayer(self.footprints_layer)

            # Zoom to layer extent with CRS transformation
            self._zoom_to_layer_extent(self.footprints_layer)
        else:
            QMessageBox.warning(
                self,
                "Layer Error",
                "Failed to create footprints layer.",
            )

    def _apply_footprints_style(self, layer):
        """Apply semi-transparent styling to footprints layer.

        Args:
            layer: QgsVectorLayer to style
        """
        # Get opacity from settings (default 50%)
        opacity = self.settings.value("MaxarOpenData/opacity", 50, type=int)
        opacity_fraction = opacity / 100.0

        # Create a simple fill symbol with transparency
        symbol = QgsFillSymbol.createSimple(
            {
                "color": "31,120,180,128",  # Blue with some transparency
                "outline_color": "0,0,255,255",  # Solid blue outline
                "outline_width": "0.5",
            }
        )

        # Set the opacity on the symbol
        symbol.setOpacity(opacity_fraction)

        # Apply the symbol to the layer
        layer.renderer().setSymbol(symbol)
        layer.triggerRepaint()

    def _zoom_to_layer_extent(self, layer):
        """Zoom the map canvas to the layer extent with proper CRS transformation.

        Args:
            layer: QgsVectorLayer to zoom to
        """
        canvas = self.iface.mapCanvas()

        # Get the layer extent in layer CRS
        layer_extent = layer.extent()

        # Transform extent to map canvas CRS if different
        layer_crs = layer.crs()
        canvas_crs = canvas.mapSettings().destinationCrs()

        if layer_crs != canvas_crs:
            transform = QgsCoordinateTransform(
                layer_crs, canvas_crs, QgsProject.instance()
            )
            layer_extent = transform.transformBoundingBox(layer_extent)

        # Set extent and refresh
        canvas.setExtent(layer_extent)
        canvas.refresh()

    def _on_footprint_selection_changed(self):
        """Handle footprint selection change in table."""
        selected_rows = self.footprints_table.selectionModel().selectedRows()
        has_selection = len(selected_rows) > 0

        self.zoom_btn.setEnabled(has_selection)
        self.load_visual_btn.setEnabled(has_selection)
        self.load_ms_btn.setEnabled(has_selection)
        self.load_pan_btn.setEnabled(has_selection)

        if has_selection:
            self.status_label.setText(f"{len(selected_rows)} footprint(s) selected")
            self.status_label.setStyleSheet("color: gray; font-size: 10px;")

    def _get_selected_features(self):
        """Get the selected features from the table."""
        features = []
        selected_rows = self.footprints_table.selectionModel().selectedRows()

        for model_index in selected_rows:
            row = model_index.row()
            item = self.footprints_table.item(row, 0)
            if item:
                feature = item.data(Qt.UserRole + 1)
                if feature:
                    features.append(feature)

        return features

    def _zoom_to_selected(self):
        """Zoom to the selected footprints."""
        features = self._get_selected_features()
        if not features:
            return

        # Calculate bounding box
        min_x = min_y = float("inf")
        max_x = max_y = float("-inf")

        for feature in features:
            coords = feature.get("geometry", {}).get("coordinates", [[]])
            if coords:
                for ring in coords:
                    for coord in ring:
                        min_x = min(min_x, coord[0])
                        max_x = max(max_x, coord[0])
                        min_y = min(min_y, coord[1])
                        max_y = max(max_y, coord[1])

        if min_x != float("inf"):
            canvas = self.iface.mapCanvas()
            extent = QgsRectangle(min_x, min_y, max_x, max_y)

            # Transform from WGS84 to canvas CRS if needed
            source_crs = QgsCoordinateReferenceSystem("EPSG:4326")
            canvas_crs = canvas.mapSettings().destinationCrs()

            if source_crs != canvas_crs:
                transform = QgsCoordinateTransform(
                    source_crs, canvas_crs, QgsProject.instance()
                )
                extent = transform.transformBoundingBox(extent)

            canvas.setExtent(extent)
            canvas.refresh()

    def _load_imagery(self, imagery_type):
        """Load imagery for selected footprints.

        Args:
            imagery_type: One of 'visual', 'ms_analytic', or 'pan_analytic'
        """
        features = self._get_selected_features()
        if not features:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select one or more footprints from the table.",
            )
            return

        loaded_count = 0
        failed_count = 0

        for feature in features:
            props = feature.get("properties", {})
            url = props.get(imagery_type)

            if not url:
                failed_count += 1
                continue

            # Create layer name
            catalog_id = props.get("catalog_id", "unknown")
            quadkey = props.get("quadkey", "")
            date = props.get("datetime", "")[:10]
            layer_name = f"Maxar {imagery_type} - {catalog_id} - {quadkey} ({date})"

            # Load as COG using GDAL vsicurl
            cog_url = f"/vsicurl/{url}"
            layer = QgsRasterLayer(cog_url, layer_name, "gdal")

            if layer.isValid():
                QgsProject.instance().addMapLayer(layer)
                loaded_count += 1
            else:
                failed_count += 1

        # Report results
        if loaded_count > 0:
            self.status_label.setText(f"Loaded {loaded_count} imagery layer(s)")
            self.status_label.setStyleSheet("color: green; font-size: 10px;")
            self.iface.messageBar().pushSuccess(
                "Maxar Open Data", f"Loaded {loaded_count} imagery layer(s)"
            )
        if failed_count > 0:
            self.iface.messageBar().pushWarning(
                "Maxar Open Data", f"Failed to load {failed_count} imagery layer(s)"
            )

    def _clear_layers(self):
        """Clear all Maxar layers from the project."""
        layers_to_remove = []

        for layer_id, layer in QgsProject.instance().mapLayers().items():
            if layer.name().startswith("Maxar"):
                layers_to_remove.append(layer_id)

        for layer_id in layers_to_remove:
            QgsProject.instance().removeMapLayer(layer_id)

        self.footprints_layer = None
        self.current_geojson = None
        self.footprints_table.setRowCount(0)

        # Refresh the map canvas
        self.iface.mapCanvas().refresh()

        # Disable action buttons
        self.zoom_btn.setEnabled(False)
        self.load_visual_btn.setEnabled(False)
        self.load_ms_btn.setEnabled(False)
        self.load_pan_btn.setEnabled(False)

        self.status_label.setText("Cleared all Maxar layers")
        self.status_label.setStyleSheet("color: gray; font-size: 10px;")

    def closeEvent(self, event):
        """Handle dock widget close event."""
        # Stop any running workers
        if self.fetch_worker and self.fetch_worker.isRunning():
            self.fetch_worker.terminate()
            self.fetch_worker.wait()

        event.accept()
