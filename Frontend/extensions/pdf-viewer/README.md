# PDF Viewer Extension

Built-in PDF viewer for VS Code using Mozilla's complete PDF.js viewer application.

## Features

### Professional PDF Viewing
- **Full Mozilla PDF.js Viewer** - The same viewer used in Firefox browser
- **Text Selection Layer** - Native-quality text selection and copying
- **Thumbnail Sidebar** - Quick navigation with page thumbnails
- **Search Functionality** - Find text within PDF documents
- **Advanced Zoom Controls** - Fit-to-page, fit-to-width, custom zoom levels
- **Page Navigation** - Arrows, page input, thumbnail clicks
- **Document Outline** - Navigate via PDF bookmarks (if available)
- **Page Rotation** - Rotate pages 90° increments
- **Print Support** - Print PDF documents
- **Download Option** - Save PDF files

### Keyboard Shortcuts

The full Mozilla viewer includes extensive keyboard shortcuts:
- **Arrow Keys**: Navigate pages
- **Ctrl/Cmd + F**: Search in document
- **Ctrl/Cmd + +/-**: Zoom in/out
- **Home/End**: First/last page
- **R**: Rotate page

## Usage

Simply open any `.pdf` file in VS Code and it will automatically open in the PDF viewer.

## Integration with Chat

This viewer works seamlessly with the MedCompanion chat feature:

1. Open a PDF in the viewer
2. Select and copy text (native text selection via PDF.js text layer)
3. Press `Ctrl+Shift+V` (or `Cmd+Shift+V` on Mac)
4. Or run "Add PDF Clipboard to Chat" from Command Palette

The copied text will be added to your chat context.

## Architecture

### Current Implementation (v2.0)

Uses Mozilla's complete PDF.js viewer via iframe:

```
Extension → Iframe → Mozilla viewer.html → PDF.js Components → Text Layer + Canvas
```

**Key Components:**
- `pdfjs-viewer/web/viewer.html` - Complete Mozilla viewer application
- `pdfjs-viewer/web/viewer.mjs` - Viewer logic and UI controls
- `pdfjs-viewer/build/` - PDF.js core library and worker
- `src/pdfViewer.ts` - VS Code extension provider (iframe wrapper)

### Previous Implementation (v1.0)

Previously used custom HTML with basic PDF.js library:
- Custom toolbar with limited features
- Canvas-only rendering (no text layer)
- Basic zoom and navigation

## Technical Details

- **PDF.js Version**: v4.0.379
- **Rendering**: Canvas with text layer overlay
- **Offline**: Fully functional without internet connection
- **No External Dependencies**: All assets bundled in extension
- **Security**: Sandboxed iframe with proper CSP
- **Performance**: Web Worker for background rendering

## Medical Use Cases

Perfect for medical documentation:
- **Research Papers**: View medical journals and studies
- **Lab Reports**: Review PDF lab results with text selection
- **Clinical Guidelines**: Quick reference without leaving editor
- **Patient Records**: Secure PDF viewing in medical context
- **Medical Textbooks**: Study materials with search functionality

## Advantages Over Basic PDF Viewers

| Feature | Basic Viewer | Mozilla Full Viewer |
|---------|--------------|---------------------|
| Text Selection | Limited (canvas) | Excellent (text layer) |
| Search | No | Yes |
| Thumbnails | No | Yes |
| Bookmarks/Outline | No | Yes |
| Print | No | Yes |
| UI Quality | Basic | Professional |
| Zoom Options | Limited | Extensive |

## License

MIT - Same as VS Code

## Credits

- Mozilla PDF.js Team for the excellent PDF viewer
- VS Code Extension API for webview capabilities
