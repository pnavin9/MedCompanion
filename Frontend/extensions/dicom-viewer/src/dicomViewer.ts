/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

import * as vscode from 'vscode';
import * as path from 'path';
import { dicomStateManager } from './dicomState';

interface DicomDocument extends vscode.CustomDocument {
	folderPath: string;
	fileName: string;
}

interface SliceInfo {
	index: number;
	imageUri: string;
}

interface ProcessSeriesResult {
	success: boolean;
	output_folder: string;
	total_slices: number;
	series_info_file: string;
}
export class DicomViewerProvider implements vscode.CustomReadonlyEditorProvider<DicomDocument> {
	private currentOutputFolder: string | undefined;
	private currentDocument: DicomDocument | undefined;

	constructor(private readonly context: vscode.ExtensionContext) { }

	async openCustomDocument(uri: vscode.Uri): Promise<DicomDocument> {
		const folderPath = path.dirname(uri.fsPath);
		const fileName = path.basename(uri.fsPath);

		return {
			uri,
			folderPath,
			fileName,
			dispose: () => { }
		};
	}

	async resolveCustomEditor(
		document: DicomDocument,
		webviewPanel: vscode.WebviewPanel
	): Promise<void> {

		webviewPanel.webview.options = {
			enableScripts: true,
			localResourceRoots: [
				vscode.Uri.joinPath(this.context.extensionUri, 'media'),
				vscode.Uri.file(document.folderPath)
			]
		};

		webviewPanel.webview.html = this.getWebviewContent(webviewPanel.webview);

		// Handle messages from webview
		webviewPanel.webview.onDidReceiveMessage(async (message) => {
			if (message.type === 'ready') {
				await this.loadDicomSeries(document, webviewPanel);
			} else if (message.type === 'sliceChanged') {
				// Update global state when slice changes
				this.updateViewerState(message.index, message.totalSlices);
			}
		});

		// Clear state when panel is disposed
		webviewPanel.onDidDispose(() => {
			dicomStateManager.clearViewerState();
		});
	}

	private async loadDicomSeries(document: DicomDocument, webviewPanel: vscode.WebviewPanel) {
		const config = vscode.workspace.getConfiguration('dicomViewer');
		const serverUrl = config.get<string>('serverUrl', 'http://localhost:8000');

		try {
			webviewPanel.webview.postMessage({ type: 'loading', message: 'Processing DICOM files...' });

			// Call backend to process series
			const response = await fetch(`${serverUrl}/api/v1/dicom/process-series`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ folder: document.folderPath })
			});

			if (!response.ok) {
				throw new Error(`Server error: ${response.statusText}`);
			}

			const result = await response.json() as ProcessSeriesResult;
			const outputFolder = result.output_folder;

			// Store output folder and document for state management
			this.currentOutputFolder = outputFolder;
			this.currentDocument = document;

			// Read series info
			const seriesInfoPath = vscode.Uri.file(path.join(outputFolder, 'series-info.json'));
			const seriesInfoData = await vscode.workspace.fs.readFile(seriesInfoPath);
			const seriesMetadata = JSON.parse(seriesInfoData.toString());

			// Prepare slice data
			const slices: SliceInfo[] = [];
			for (let i = 0; i < result.total_slices; i++) {
				const pngPath = path.join(outputFolder, `slice-${i.toString().padStart(4, '0')}.png`);

				slices.push({
					index: i,
					imageUri: webviewPanel.webview.asWebviewUri(vscode.Uri.file(pngPath)).toString()
				});
			}

			// Send to webview
			webviewPanel.webview.postMessage({
				type: 'seriesLoaded',
				data: {
					totalSlices: result.total_slices,
					slices: slices,
					metadata: seriesMetadata
				}
			});

			// Initialize global state with first slice
			this.updateViewerState(0, result.total_slices);

		} catch (error) {
			vscode.window.showErrorMessage(`Failed to load DICOM series: ${error}`);
			webviewPanel.webview.postMessage({
				type: 'error',
				message: String(error)
			});
		}
	}

	private updateViewerState(sliceIndex: number, totalSlices: number): void {
		if (this.currentOutputFolder && this.currentDocument) {
			dicomStateManager.setViewerState({
				outputFolder: this.currentOutputFolder,
				currentSliceIndex: sliceIndex,
				totalSlices: totalSlices,
				folderPath: this.currentDocument.folderPath
			});
		}
	}

	private getWebviewContent(webview: vscode.Webview): string {
		const scriptUri = webview.asWebviewUri(
			vscode.Uri.joinPath(this.context.extensionUri, 'media', 'viewer.js')
		);
		const styleUri = webview.asWebviewUri(
			vscode.Uri.joinPath(this.context.extensionUri, 'media', 'viewer.css')
		);

		return `<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<meta http-equiv="Content-Security-Policy" content="default-src 'none'; img-src ${webview.cspSource} data:; style-src ${webview.cspSource} 'unsafe-inline'; script-src ${webview.cspSource};">
	<link rel="stylesheet" href="${styleUri}">
	<title>DICOM Viewer</title>
</head>
<body>
	<div id="loading" class="loading">Loading DICOM series...</div>
	<div id="error" class="error" style="display:none;"></div>

	<div id="viewer" style="display:none;">
		<div class="main-view">
			<img id="image" alt="DICOM slice">
		</div>

		<div class="controls">
			<input type="range" id="slider" min="0" max="0" value="0">
			<div class="info">
				Slice <span id="current">1</span> / <span id="total">1</span>
			</div>
		</div>

		<div class="metadata-panel">
			<h3>Series Information</h3>
			<div id="series-info"></div>

			<h3>Current Slice</h3>
			<div id="slice-info"></div>
		</div>
	</div>

	<script src="${scriptUri}"></script>
</body>
</html>`;
	}
}
