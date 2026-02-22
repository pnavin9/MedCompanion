# PDF Viewer Testing Guide

## Quick Start

### 1. Compile the Extension

```bash
cd /Users/navin1/vscode/extensions/pdf-viewer
nvm use 20
npx tsc -p tsconfig.json
```

### 2. Launch VS Code

From the vscode root directory:
```bash
cd /Users/navin1/vscode
./scripts/code.sh
```

### 3. Open a PDF File

- Use File → Open to select any PDF
- Or drag and drop a PDF into VS Code
- The PDF should open automatically in the new Mozilla viewer

## What to Test

### ✅ Text Selection (Primary Feature)

1. **Basic Selection**
   - Click and drag to select text
   - Text should highlight smoothly
   - Copy with Ctrl/Cmd + C
   - Paste into another app to verify

2. **Cross-Page Selection**
   - Select text that spans multiple pages
   - Verify selection works across page boundaries

3. **Complex Layouts**
   - Test with multi-column documents
   - Test with tables
   - Test with mixed text and images

### ✅ Navigation Features

1. **Thumbnail Sidebar**
   - Click the sidebar toggle button
   - Thumbnails should appear on the left
   - Click a thumbnail to jump to that page
   - Verify current page is highlighted

2. **Page Controls**
   - Use next/previous buttons
   - Use arrow keys
   - Type page number directly
   - Verify page counter updates

3. **Document Outline**
   - Open a PDF with bookmarks
   - Click outline/bookmark button
   - Navigate via bookmarks
   - Verify jumps to correct sections

### ✅ Search Functionality

1. **Basic Search**
   - Press Ctrl/Cmd + F
   - Search bar should appear
   - Type a search term
   - Verify results are highlighted

2. **Search Navigation**
   - Use next/previous match buttons
   - Verify it cycles through all matches
   - Check match counter (e.g., "3 of 15")

3. **Case Sensitivity**
   - Toggle case-sensitive search
   - Verify it filters results correctly

### ✅ Zoom Controls

1. **Zoom Buttons**
   - Click zoom in (+)
   - Click zoom out (-)
   - Verify zoom level indicator updates

2. **Zoom Presets**
   - Click zoom dropdown
   - Try "Fit to Page"
   - Try "Fit to Width"
   - Try "Automatic"
   - Try specific percentages (50%, 100%, 200%)

3. **Keyboard Zoom**
   - Ctrl/Cmd + Plus to zoom in
   - Ctrl/Cmd + Minus to zoom out
   - Verify smooth zooming

### ✅ Rotation

1. **Rotate Page**
   - Click rotate button (or press R)
   - Page should rotate 90° clockwise
   - Verify rotation persists while navigating
   - Rotate back to original orientation

### ✅ Print & Download

1. **Print**
   - Click print button
   - Print dialog should appear
   - Verify page range options
   - Test print preview

2. **Download**
   - Click download button
   - File save dialog should appear
   - Save to a location
   - Verify file is identical to original

### ✅ Chat Integration

1. **Copy Text to Chat**
   - Open a PDF
   - Select some text
   - Copy it (Ctrl/Cmd + C)
   - Run "Add PDF Clipboard to Chat" command
   - Verify text appears in chat context

2. **Medical Document Workflow**
   - Open a medical PDF (lab report, research paper)
   - Select relevant findings
   - Add to chat
   - Ask MedGemma to analyze the text

## Test Documents

### Recommended Test PDFs

1. **Simple PDF** - Basic text document
   - Test: Text selection, navigation
   - Example: README converted to PDF

2. **Multi-page Document** - 10+ pages
   - Test: Thumbnails, page jumping, search
   - Example: Research paper

3. **Complex Layout** - Tables, columns, images
   - Test: Text selection accuracy
   - Example: Lab report, medical form

4. **Large PDF** - 50+ pages
   - Test: Performance, memory usage
   - Example: Medical textbook chapter

5. **PDF with Bookmarks** - Outline/TOC
   - Test: Bookmark navigation
   - Example: Technical manual

### Medical Document Types

- Lab results (multi-page)
- Radiology reports
- Clinical guidelines
- Research papers
- Patient records (test with sample data)
- Medical textbooks

## Performance Testing

### Memory Usage

1. Open Task Manager/Activity Monitor
2. Note baseline memory usage
3. Open a large PDF (50+ pages)
4. Navigate through pages
5. Monitor memory consumption
6. Should stay under 500MB for typical documents

### Rendering Speed

1. Open a PDF
2. Time how long it takes to display first page
3. Navigate to different pages
4. Verify pages render within 1-2 seconds

### Responsiveness

1. While PDF is loading, try to interact
2. UI should remain responsive
3. No freezing or blocking

## Error Handling

### Test Error Cases

1. **Corrupted PDF**
   - Try opening a damaged PDF file
   - Should show error message
   - Should not crash VS Code

2. **Very Large File**
   - Open a 100+ MB PDF
   - Should load (may be slow)
   - Should show progress indicator

3. **Password-Protected PDF**
   - Open an encrypted PDF
   - Should prompt for password
   - Or show appropriate error

4. **Non-PDF File**
   - Try opening .txt file as PDF
   - Should show error message

## Regression Testing

### Verify Old Features Still Work

1. **Custom Editor Registration**
   - PDFs should open automatically
   - No need to choose "Open With"

2. **Multiple PDFs**
   - Open several PDFs at once
   - Each should have its own tab
   - Switching between tabs should work

3. **File Watching**
   - Open a PDF
   - Modify it externally
   - VS Code should detect changes
   - Offer to reload

## Browser Compatibility

The Mozilla viewer should work in VS Code's webview on:
- ✅ macOS (tested)
- ✅ Windows (should work)
- ✅ Linux (should work)

## Known Limitations

1. **Annotations** - Viewing only, no editing
2. **Forms** - Can view but not fill
3. **Digital Signatures** - Display only, no verification
4. **3D Content** - Not supported
5. **Multimedia** - Videos/audio in PDFs may not play

## Troubleshooting

### PDF Won't Open

1. Check console for errors (Help → Toggle Developer Tools)
2. Verify pdfjs-viewer folder exists
3. Check file permissions
4. Try recompiling extension

### Text Selection Not Working

1. Verify text layer is enabled (should be by default)
2. Check if PDF has actual text (not scanned image)
3. Try zooming in/out
4. Check browser console for errors

### Thumbnails Not Showing

1. Wait a few seconds (they load progressively)
2. Check network tab for failed requests
3. Verify images folder exists in pdfjs-viewer/web/

### Search Not Finding Text

1. Verify PDF has searchable text (not scanned)
2. Check spelling of search term
3. Try case-insensitive search
4. Wait for document to fully load

## Success Criteria

The implementation is successful if:

✅ PDFs open automatically in the new viewer
✅ Text selection works smoothly (primary goal)
✅ Thumbnails appear and are clickable
✅ Search finds text and highlights it
✅ Zoom controls work properly
✅ Navigation is smooth and responsive
✅ Chat integration still works
✅ No console errors during normal use
✅ Performance is acceptable for typical medical documents
✅ UI looks professional and polished

## Reporting Issues

If you find any issues:

1. Note the exact steps to reproduce
2. Check browser console for errors
3. Note PDF file characteristics (size, pages, type)
4. Check if issue occurs with other PDFs
5. Document expected vs actual behavior

## Next Steps After Testing

Once testing is complete:

1. Document any issues found
2. Prioritize fixes if needed
3. Consider optional enhancements
4. Update user documentation
5. Deploy to production VS Code build
