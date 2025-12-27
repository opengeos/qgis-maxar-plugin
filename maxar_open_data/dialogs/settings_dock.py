"""
Settings Dock Widget for Maxar Open Data Plugin

This module provides a settings panel for configuring plugin options.
"""

from qgis.PyQt.QtCore import Qt, QSettings
from qgis.PyQt.QtWidgets import (
    QDockWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QGroupBox,
    QComboBox,
    QSpinBox,
    QCheckBox,
    QFormLayout,
    QMessageBox,
    QFileDialog,
    QTabWidget,
)
from qgis.PyQt.QtGui import QFont


class SettingsDockWidget(QDockWidget):
    """A settings panel for configuring Maxar Open Data plugin options."""

    # Settings keys
    SETTINGS_PREFIX = "MaxarOpenData/"

    def __init__(self, iface, parent=None):
        """Initialize the settings dock widget.

        Args:
            iface: QGIS interface instance.
            parent: Parent widget.
        """
        super().__init__("Maxar Settings", parent)
        self.iface = iface
        self.settings = QSettings()

        self.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)

        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        """Set up the settings UI."""
        # Main widget
        main_widget = QWidget()
        self.setWidget(main_widget)

        # Main layout
        layout = QVBoxLayout(main_widget)
        layout.setSpacing(10)

        # Header
        header_label = QLabel("Plugin Settings")
        header_font = QFont()
        header_font.setPointSize(12)
        header_font.setBold(True)
        header_label.setFont(header_font)
        header_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(header_label)

        # Tab widget for organized settings
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)

        # Data settings tab
        data_tab = self._create_data_tab()
        tab_widget.addTab(data_tab, "Data")

        # Display settings tab
        display_tab = self._create_display_tab()
        tab_widget.addTab(display_tab, "Display")

        # Advanced settings tab
        advanced_tab = self._create_advanced_tab()
        tab_widget.addTab(advanced_tab, "Advanced")

        # Buttons
        button_layout = QHBoxLayout()

        self.save_btn = QPushButton("Save Settings")
        self.save_btn.clicked.connect(self._save_settings)
        button_layout.addWidget(self.save_btn)

        self.reset_btn = QPushButton("Reset Defaults")
        self.reset_btn.clicked.connect(self._reset_defaults)
        button_layout.addWidget(self.reset_btn)

        layout.addLayout(button_layout)

        # Stretch at the end
        layout.addStretch()

        # Status label
        self.status_label = QLabel("Settings loaded")
        self.status_label.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(self.status_label)

    def _create_data_tab(self):
        """Create the data settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Data source group
        source_group = QGroupBox("Data Source")
        source_layout = QFormLayout(source_group)

        # Use local data option
        self.use_local_check = QCheckBox()
        self.use_local_check.setChecked(False)
        self.use_local_check.stateChanged.connect(self._on_local_data_changed)
        source_layout.addRow("Use local data:", self.use_local_check)

        # Local data path
        path_layout = QHBoxLayout()
        self.local_path_input = QLineEdit()
        self.local_path_input.setPlaceholderText(
            "Path to local maxar-open-data folder..."
        )
        self.local_path_input.setEnabled(False)
        path_layout.addWidget(self.local_path_input)
        self.browse_btn = QPushButton("...")
        self.browse_btn.setMaximumWidth(30)
        self.browse_btn.setEnabled(False)
        self.browse_btn.clicked.connect(self._browse_local_path)
        path_layout.addWidget(self.browse_btn)
        source_layout.addRow("Local path:", path_layout)

        # Cache settings
        self.cache_check = QCheckBox()
        self.cache_check.setChecked(True)
        source_layout.addRow("Cache downloaded data:", self.cache_check)

        layout.addWidget(source_group)

        # Filter defaults group
        filter_group = QGroupBox("Default Filters")
        filter_layout = QFormLayout(filter_group)

        # Default max cloud cover
        self.default_cloud_spin = QSpinBox()
        self.default_cloud_spin.setRange(0, 100)
        self.default_cloud_spin.setValue(100)
        self.default_cloud_spin.setSuffix(" %")
        filter_layout.addRow("Default max cloud cover:", self.default_cloud_spin)

        layout.addWidget(filter_group)

        layout.addStretch()
        return widget

    def _create_display_tab(self):
        """Create the display settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Layer settings group
        layer_group = QGroupBox("Layer Settings")
        layer_layout = QFormLayout(layer_group)

        # Auto-zoom to footprints
        self.auto_zoom_check = QCheckBox()
        self.auto_zoom_check.setChecked(True)
        layer_layout.addRow("Auto-zoom to footprints:", self.auto_zoom_check)

        # Add layers to group
        self.group_layers_check = QCheckBox()
        self.group_layers_check.setChecked(True)
        layer_layout.addRow("Group layers by event:", self.group_layers_check)

        # Default imagery type
        self.default_imagery_combo = QComboBox()
        self.default_imagery_combo.addItems(
            ["Visual (RGB)", "Multispectral", "Panchromatic"]
        )
        layer_layout.addRow("Default imagery type:", self.default_imagery_combo)

        layout.addWidget(layer_group)

        # Footprint styling group
        style_group = QGroupBox("Footprint Styling")
        style_layout = QFormLayout(style_group)

        # Footprint opacity
        self.opacity_spin = QSpinBox()
        self.opacity_spin.setRange(0, 100)
        self.opacity_spin.setValue(50)
        self.opacity_spin.setSuffix(" %")
        style_layout.addRow("Fill opacity:", self.opacity_spin)

        # Show labels
        self.show_labels_check = QCheckBox()
        self.show_labels_check.setChecked(False)
        style_layout.addRow("Show footprint labels:", self.show_labels_check)

        layout.addWidget(style_group)

        layout.addStretch()
        return widget

    def _create_advanced_tab(self):
        """Create the advanced settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Network group
        network_group = QGroupBox("Network")
        network_layout = QFormLayout(network_group)

        # Request timeout
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(5, 120)
        self.timeout_spin.setValue(30)
        self.timeout_spin.setSuffix(" seconds")
        network_layout.addRow("Request timeout:", self.timeout_spin)

        # Max concurrent downloads
        self.max_downloads_spin = QSpinBox()
        self.max_downloads_spin.setRange(1, 10)
        self.max_downloads_spin.setValue(3)
        network_layout.addRow("Max concurrent downloads:", self.max_downloads_spin)

        layout.addWidget(network_group)

        # Debug group
        debug_group = QGroupBox("Debug")
        debug_layout = QFormLayout(debug_group)

        # Debug mode
        self.debug_check = QCheckBox()
        self.debug_check.setChecked(False)
        debug_layout.addRow("Debug mode:", self.debug_check)

        # Show COG URLs
        self.show_urls_check = QCheckBox()
        self.show_urls_check.setChecked(False)
        debug_layout.addRow("Show COG URLs in messages:", self.show_urls_check)

        layout.addWidget(debug_group)

        layout.addStretch()
        return widget

    def _on_local_data_changed(self, state):
        """Handle local data checkbox change."""
        enabled = state == Qt.Checked
        self.local_path_input.setEnabled(enabled)
        self.browse_btn.setEnabled(enabled)

    def _browse_local_path(self):
        """Open directory browser for local data path."""
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Maxar Open Data Directory", self.local_path_input.text() or ""
        )
        if dir_path:
            self.local_path_input.setText(dir_path)

    def _load_settings(self):
        """Load settings from QSettings."""
        # Data
        self.use_local_check.setChecked(
            self.settings.value(f"{self.SETTINGS_PREFIX}use_local", False, type=bool)
        )
        self.local_path_input.setText(
            self.settings.value(f"{self.SETTINGS_PREFIX}local_path", "", type=str)
        )
        self.cache_check.setChecked(
            self.settings.value(f"{self.SETTINGS_PREFIX}cache_data", True, type=bool)
        )
        self.default_cloud_spin.setValue(
            self.settings.value(f"{self.SETTINGS_PREFIX}default_cloud", 100, type=int)
        )

        # Display
        self.auto_zoom_check.setChecked(
            self.settings.value(f"{self.SETTINGS_PREFIX}auto_zoom", True, type=bool)
        )
        self.group_layers_check.setChecked(
            self.settings.value(f"{self.SETTINGS_PREFIX}group_layers", True, type=bool)
        )
        self.default_imagery_combo.setCurrentIndex(
            self.settings.value(f"{self.SETTINGS_PREFIX}default_imagery", 0, type=int)
        )
        self.opacity_spin.setValue(
            self.settings.value(f"{self.SETTINGS_PREFIX}opacity", 50, type=int)
        )
        self.show_labels_check.setChecked(
            self.settings.value(f"{self.SETTINGS_PREFIX}show_labels", False, type=bool)
        )

        # Advanced
        self.timeout_spin.setValue(
            self.settings.value(f"{self.SETTINGS_PREFIX}timeout", 30, type=int)
        )
        self.max_downloads_spin.setValue(
            self.settings.value(f"{self.SETTINGS_PREFIX}max_downloads", 3, type=int)
        )
        self.debug_check.setChecked(
            self.settings.value(f"{self.SETTINGS_PREFIX}debug", False, type=bool)
        )
        self.show_urls_check.setChecked(
            self.settings.value(f"{self.SETTINGS_PREFIX}show_urls", False, type=bool)
        )

        # Update enabled states
        self._on_local_data_changed(
            Qt.Checked if self.use_local_check.isChecked() else Qt.Unchecked
        )

        self.status_label.setText("Settings loaded")
        self.status_label.setStyleSheet("color: gray; font-size: 10px;")

    def _save_settings(self):
        """Save settings to QSettings."""
        # Data
        self.settings.setValue(
            f"{self.SETTINGS_PREFIX}use_local", self.use_local_check.isChecked()
        )
        self.settings.setValue(
            f"{self.SETTINGS_PREFIX}local_path", self.local_path_input.text()
        )
        self.settings.setValue(
            f"{self.SETTINGS_PREFIX}cache_data", self.cache_check.isChecked()
        )
        self.settings.setValue(
            f"{self.SETTINGS_PREFIX}default_cloud", self.default_cloud_spin.value()
        )

        # Display
        self.settings.setValue(
            f"{self.SETTINGS_PREFIX}auto_zoom", self.auto_zoom_check.isChecked()
        )
        self.settings.setValue(
            f"{self.SETTINGS_PREFIX}group_layers", self.group_layers_check.isChecked()
        )
        self.settings.setValue(
            f"{self.SETTINGS_PREFIX}default_imagery",
            self.default_imagery_combo.currentIndex(),
        )
        self.settings.setValue(
            f"{self.SETTINGS_PREFIX}opacity", self.opacity_spin.value()
        )
        self.settings.setValue(
            f"{self.SETTINGS_PREFIX}show_labels", self.show_labels_check.isChecked()
        )

        # Advanced
        self.settings.setValue(
            f"{self.SETTINGS_PREFIX}timeout", self.timeout_spin.value()
        )
        self.settings.setValue(
            f"{self.SETTINGS_PREFIX}max_downloads", self.max_downloads_spin.value()
        )
        self.settings.setValue(
            f"{self.SETTINGS_PREFIX}debug", self.debug_check.isChecked()
        )
        self.settings.setValue(
            f"{self.SETTINGS_PREFIX}show_urls", self.show_urls_check.isChecked()
        )

        self.settings.sync()

        self.status_label.setText("Settings saved")
        self.status_label.setStyleSheet("color: green; font-size: 10px;")

        self.iface.messageBar().pushSuccess(
            "Maxar Open Data", "Settings saved successfully!"
        )

    def _reset_defaults(self):
        """Reset all settings to defaults."""
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset all settings to defaults?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply != QMessageBox.Yes:
            return

        # Data
        self.use_local_check.setChecked(False)
        self.local_path_input.clear()
        self.cache_check.setChecked(True)
        self.default_cloud_spin.setValue(100)

        # Display
        self.auto_zoom_check.setChecked(True)
        self.group_layers_check.setChecked(True)
        self.default_imagery_combo.setCurrentIndex(0)
        self.opacity_spin.setValue(50)
        self.show_labels_check.setChecked(False)

        # Advanced
        self.timeout_spin.setValue(30)
        self.max_downloads_spin.setValue(3)
        self.debug_check.setChecked(False)
        self.show_urls_check.setChecked(False)

        # Update enabled states
        self._on_local_data_changed(Qt.Unchecked)

        self.status_label.setText("Defaults restored (not saved)")
        self.status_label.setStyleSheet("color: orange; font-size: 10px;")
