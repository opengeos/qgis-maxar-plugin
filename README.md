# Maxar Open Data QGIS Plugin

[![QGIS Plugin](https://img.shields.io/badge/QGIS-Plugin-green.svg)](https://plugins.qgis.org/plugins/maxar_open_data)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

A QGIS plugin for browsing, visualizing, and downloading [Maxar Open Data](https://www.maxar.com/open-data) satellite imagery for disaster events.

![](https://github.com/user-attachments/assets/a7fe192f-abb7-4ddc-b347-d01f57892a80)

## Features

- **Event Browser**: Browse 50+ disaster events with available satellite imagery
- **Footprint Viewer**: View and filter imagery footprints on the map
- **COG Visualization**: Load and visualize Cloud Optimized GeoTIFFs (COG) directly
- **Download Imagery**: Download imagery for selected footprints
- **Filtering**: Filter imagery by cloud cover percentage
- **Multiple Imagery Types**: Support for visual (RGB), multispectral, and panchromatic imagery
- **Automatic Updates**: Check for and install updates from GitHub

## Data Source

This plugin provides access to the [Maxar Open Data Program](https://www.maxar.com/open-data), which offers pre- and post-event high-resolution satellite imagery for:

- Emergency planning
- Risk assessment
- Monitoring of staging areas
- Emergency response
- Damage assessment
- Recovery efforts

The data catalog is maintained at [opengeos/maxar-open-data](https://github.com/opengeos/maxar-open-data). It is also available on [AWS Open Data Registry](https://registry.opendata.aws/maxar-open-data/).

## Installation

### From QGIS Plugin Manager (Recommended)

1. Open QGIS
2. Go to **Plugins** → **Manage and Install Plugins...**
3. Search for "Maxar Open Data"
4. Click **Install Plugin**

### Manual Installation

#### Using Python Script

```bash
# Clone the repository
git clone https://github.com/opengeos/qgis-maxar-plugin.git
cd qgis-maxar-plugin

# Install the plugin
python install.py
```

#### Using Shell Script (Linux/macOS)

```bash
# Clone the repository
git clone https://github.com/opengeos/qgis-maxar-plugin.git
cd qgis-maxar-plugin

# Make the script executable and run
chmod +x install.sh
./install.sh
```

#### Manual Copy

Copy the `maxar_open_data` folder to your QGIS plugins directory:

- **Linux**: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
- **macOS**: `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/`
- **Windows**: `%APPDATA%/QGIS/QGIS3/profiles/default/python/plugins/`

After copying, restart QGIS and enable the plugin in **Plugins** → **Manage and Install Plugins...**.

## Usage

### Opening the Plugin

1. After installation, you'll find a new menu item: **Maxar Open Data**
2. Click on **Maxar Open Data Panel** to open the main dock widget
3. The plugin also adds a toolbar with quick access buttons

### Browsing Events

1. In the Maxar Open Data panel, select an event from the dropdown
2. Optionally adjust the maximum cloud cover filter
3. Click **Load Footprints** to load the imagery footprints for that event

### Viewing Imagery

1. Select one or more footprints from the table
2. Click **Zoom to Selected** to zoom the map to those footprints
3. Click one of the imagery buttons to load the actual satellite imagery:
   - **Load Visual**: RGB visual imagery
   - **Load MS**: Multispectral imagery
   - **Load Pan**: Panchromatic (high-resolution grayscale) imagery

### Downloading Imagery

1. Select one or more footprints from the table
2. Click one of the download buttons to download the imagery to your local machine:
   - **Download Visual**: RGB visual imagery
   - **Download MS**: Multispectral imagery
   - **Download Pan**: Panchromatic (high-resolution grayscale) imagery

### Settings

Access plugin settings by clicking the **Settings** button in the toolbar or menu. You can configure:

- Data source (GitHub or local copy)
- Default cloud cover filter
- Display options
- Network timeout settings

## Screenshots

![](https://github.com/user-attachments/assets/d795d960-478f-40b3-9fb0-7b06963cbdd8)

## Requirements

- QGIS 3.28 or later
- Internet connection (for fetching event data and imagery)

## Packaging for Distribution

To create a zip file for uploading to the QGIS plugin repository:

```bash
# Using Python
python package_plugin.py

# Or using shell script
./package_plugin.sh
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Maxar Technologies](https://www.maxar.com/) for providing open data imagery
- [opengeos/maxar-open-data](https://github.com/opengeos/maxar-open-data) for maintaining the data catalog
- QGIS Development Team for the excellent GIS platform

## Links

- [Maxar Open Data Program](https://www.maxar.com/open-data)
- [Maxar Open Data on AWS](https://registry.opendata.aws/maxar-open-data/)
- [Maxar Open Data Catalog (GitHub)](https://github.com/opengeos/maxar-open-data)
- [Report Issues](https://github.com/opengeos/qgis-maxar-plugin/issues)
