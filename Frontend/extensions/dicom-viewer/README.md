# DICOM Viewer Extension

A custom editor extension for viewing DICOM medical images in MedCompanion IDE.

## Features

- Opens `.dcm` files automatically
- Processes entire DICOM series via backend
- Displays medical images with slice navigation
- Supports keyboard, mouse wheel, and slider navigation
- Shows series and slice metadata

## Architecture

1. User opens a `.dcm` file
2. Extension detects the parent folder
3. Calls backend API: `POST /api/v1/dicom/process-series`
4. Backend processes all DICOM files and generates PNGs
5. Extension reads PNGs from temp folder
6. Displays in webview with navigation controls

## Build Instructions

The extension is built as part of the VSCode build process:

```bash
cd /Users/navin1/vscode
yarn install
yarn compile-extensions
```

Or build the entire IDE:

```bash
./scripts/code.sh
```

## Testing

### Prerequisites

1. **Start the MedCompanion server**:
```bash
cd /Users/navin1/MedCompanion
source medgemma-env/bin/activate
./start_server.sh
```

2. **Build and run MedCompanion IDE**:
```bash
cd /Users/navin1/vscode
./scripts/code.sh
```

### Test Steps

1. Open MedCompanion IDE
2. Navigate to a folder containing `.dcm` files (e.g., `/Users/navin1/Downloads/series_copy`)
3. Click on any `.dcm` file
4. The DICOM viewer should open automatically
5. Test navigation:
   - **Arrow keys**: Navigate through slices
   - **Mouse wheel**: Scroll through slices
   - **Slider**: Drag to jump to specific slice
   - **Home/End**: Jump to first/last slice

### Expected Behavior

- Loading message appears while processing
- First slice displays after processing completes
- Metadata panel shows:
  - Patient information
  - Study details
  - Series information
  - Current slice number
- Navigation is instant (no server calls)
- All slices load from cached PNGs

### Configuration

The server URL can be configured in VSCode settings:

```json
{
  "dicomViewer.serverUrl": "http://localhost:8000"
}
```

## File Structure

```
extensions/dicom-viewer/
├── package.json           # Extension manifest
├── tsconfig.json          # TypeScript configuration
├── src/
│   ├── extension.ts      # Extension entry point
│   └── dicomViewer.ts    # Custom editor provider
└── media/
    ├── viewer.js         # Webview JavaScript
    └── viewer.css        # Webview styles
```

## Integration with Backend

The extension communicates with the MedCompanion Python server:

**Endpoint**: `POST /api/v1/dicom/process-series`

**Request**:
```json
{
  "folder": "/path/to/dicom/folder"
}
```

**Response**:
```json
{
  "success": true,
  "output_folder": "/var/folders/.../medcompanion-dicom/series-abc123",
  "total_slices": 127,
  "series_info_file": "series-info.json"
}
```

The extension then reads the generated PNG files from the output folder and displays them in the webview.

## Troubleshooting

### Extension not loading
- Ensure the extension is built: `yarn compile-extensions`
- Check the developer console for errors: `Help > Toggle Developer Tools`

### Server connection error
- Verify server is running: `curl http://localhost:8000/api/v1/health`
- Check server URL in settings

### DICOM files not opening
- Verify file has `.dcm` or `.DCM` extension
- Check if backend can access the folder
- Look at server logs for processing errors

### No images displayed
- Check if PNGs were generated in temp folder
- Verify webview can read from temp directory
- Check browser console in webview for errors

## Known Limitations

- Only supports single-file-per-slice DICOM format
- Requires backend server to be running
- No built-in windowing/leveling controls (uses backend defaults)
- Metadata display is read-only

## Next Steps

- Add "Analyze with MedGemma" button
- Integrate with chat for AI-powered analysis
- Add brightness/contrast controls in viewer
- Support for multi-frame DICOM files
- Caching to avoid reprocessing same series
