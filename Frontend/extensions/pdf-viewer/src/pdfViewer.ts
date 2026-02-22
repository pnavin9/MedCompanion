/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

import * as vscode from 'vscode';

interface PdfDocument extends vscode.CustomDocument {
	fileName: string;
}

export class PdfViewerProvider implements vscode.CustomReadonlyEditorProvider<PdfDocument> {
	constructor(private readonly context: vscode.ExtensionContext) { }

	async openCustomDocument(uri: vscode.Uri): Promise<PdfDocument> {
		return {
			uri,
			fileName: uri.fsPath,
			dispose: () => { }
		};
	}

	async resolveCustomEditor(
		document: PdfDocument,
		webviewPanel: vscode.WebviewPanel
	): Promise<void> {
		webviewPanel.webview.options = {
			enableScripts: true,
			localResourceRoots: [
				vscode.Uri.joinPath(this.context.extensionUri, 'pdfjs-viewer', 'build'),
				vscode.Uri.joinPath(this.context.extensionUri, 'pdfjs-viewer', 'web')
			]
		};

		// Read PDF file as Uint8Array
		const pdfData = await vscode.workspace.fs.readFile(document.uri);

		webviewPanel.webview.html = this.getWebviewContent(webviewPanel.webview, document, pdfData);
	}

	private getWebviewContent(webview: vscode.Webview, document: PdfDocument, pdfData: Uint8Array): string {
		// Get URIs for PDF.js resources
		const pdfJsUri = webview.asWebviewUri(
			vscode.Uri.joinPath(this.context.extensionUri, 'pdfjs-viewer', 'build', 'pdf.mjs')
		);
		const pdfWorkerUri = webview.asWebviewUri(
			vscode.Uri.joinPath(this.context.extensionUri, 'pdfjs-viewer', 'build', 'pdf.worker.mjs')
		);

		// Convert PDF data to base64 for embedding
		const pdfBase64 = Buffer.from(pdfData).toString('base64');

		return `<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<meta http-equiv="Content-Security-Policy" content="
		default-src 'none';
		connect-src ${webview.cspSource};
		img-src ${webview.cspSource} data: blob:;
		style-src ${webview.cspSource} 'unsafe-inline';
		script-src ${webview.cspSource} 'unsafe-inline' 'unsafe-eval';
		worker-src ${webview.cspSource} blob:;
		font-src ${webview.cspSource} data:;
	">
	<title>PDF Viewer - ${document.uri.fsPath.split('/').pop()}</title>
	<style>
		body, html {
			margin: 0;
			padding: 0;
			width: 100%;
			height: 100vh;
			overflow: hidden;
			background: #525659;
		}
		#viewerContainer {
			width: 100%;
			height: 100%;
			overflow: auto;
			display: flex;
			flex-direction: column;
			align-items: center;
			padding: 20px 0;
			padding-top: 60px;
		}
		.pageContainer {
			position: relative;
			margin: 10px 0;
			box-shadow: 0 2px 8px rgba(0,0,0,0.3);
			background: white;
		}
		.pageContainer canvas {
			display: block;
		}
		.textLayer {
			position: absolute;
			left: 0;
			top: 0;
			right: 0;
			bottom: 0;
			overflow: hidden;
			opacity: 1;
			line-height: 1.0;
			user-select: text;
			-webkit-user-select: text;
		}
		.textLayer > span {
			color: transparent;
			position: absolute;
			white-space: pre;
			cursor: text;
			transform-origin: 0% 0%;
		}
		.textLayer ::selection {
			background: rgba(0, 100, 255, 0.4);
		}
		.textLayer ::-moz-selection {
			background: rgba(0, 100, 255, 0.4);
		}
		#toolbar {
			position: fixed;
			top: 0;
			left: 0;
			right: 0;
			height: 40px;
			background: #323639;
			display: flex;
			align-items: center;
			padding: 0 10px;
			gap: 10px;
			z-index: 1000;
			color: white;
		}
		#toolbar button {
			background: #4a4d50;
			border: none;
			color: white;
			padding: 6px 12px;
			cursor: pointer;
			border-radius: 3px;
		}
		#toolbar button:hover {
			background: #5a5d60;
		}
		#pageInfo {
			color: #d1d1d1;
		}
	</style>
</head>
<body>
	<div id="toolbar">
		<button id="zoomOut">−</button>
		<button id="zoomIn">+</button>
		<button id="fitWidth">Fit Width</button>
		<button id="actualSize">100%</button>
		<span id="pageInfo"></span>
	</div>
	<div id="viewerContainer"></div>

	<script type="module">
		import * as pdfjsLib from '${pdfJsUri}';

		pdfjsLib.GlobalWorkerOptions.workerSrc = '${pdfWorkerUri}';

		const container = document.getElementById('viewerContainer');
		const pageInfo = document.getElementById('pageInfo');
		let pdfDoc = null;
		let scale = 1.5;

		async function renderPage(num) {
			const page = await pdfDoc.getPage(num);
			const viewport = page.getViewport({ scale });

			// Create page container
			const pageContainer = document.createElement('div');
			pageContainer.className = 'pageContainer';
			pageContainer.style.width = viewport.width + 'px';
			pageContainer.style.height = viewport.height + 'px';

			// Render canvas with high-DPI support
			const canvas = document.createElement('canvas');
			const context = canvas.getContext('2d');
			const outputScale = window.devicePixelRatio || 1;

			canvas.width = Math.floor(viewport.width * outputScale);
			canvas.height = Math.floor(viewport.height * outputScale);
			canvas.style.width = viewport.width + 'px';
			canvas.style.height = viewport.height + 'px';

			const transform = outputScale !== 1
				? [outputScale, 0, 0, outputScale, 0, 0]
				: null;

			await page.render({
				canvasContext: context,
				viewport: viewport,
				transform: transform
			}).promise;

			pageContainer.appendChild(canvas);

			// Render text layer for selection
			const textLayer = document.createElement('div');
			textLayer.className = 'textLayer';
			textLayer.style.width = viewport.width + 'px';
			textLayer.style.height = viewport.height + 'px';

			const textContent = await page.getTextContent();
			const textItems = textContent.items;

			textItems.forEach((item, idx) => {
				if (!item.str) return;

				const tx = pdfjsLib.Util.transform(
					pdfjsLib.Util.transform(viewport.transform, item.transform),
					[1, 0, 0, -1, 0, 0]
				);

				const style = textContent.styles[item.fontName];
				const fontHeight = Math.sqrt((tx[2] * tx[2]) + (tx[3] * tx[3]));
				const fontAscent = style && style.ascent ? style.ascent : 0.75;

				const span = document.createElement('span');
				span.textContent = item.str;
				span.style.left = tx[4] + 'px';
				span.style.top = (tx[5] - (fontHeight * fontAscent)) + 'px';
				span.style.fontSize = fontHeight + 'px';
				span.style.fontFamily = item.fontName || 'sans-serif';

				// Handle width for proper text alignment
				if (item.width) {
					const scaleX = Math.sqrt((tx[0] * tx[0]) + (tx[1] * tx[1]));
					span.style.width = (item.width * scaleX) + 'px';
				}

				textLayer.appendChild(span);
			});

			pageContainer.appendChild(textLayer);

			return pageContainer;
		}

		let isRendering = false;
		let renderTimeout = null;
		let currentRenderScale = scale;
		let targetScale = scale;

		async function renderAllPages(immediate = false) {
			if (isRendering && !immediate) return;
			isRendering = true;

			currentRenderScale = targetScale;

			// Create temporary container to render off-screen
			const tempDiv = document.createElement('div');

			// Render all pages into temporary container
			for (let i = 1; i <= pdfDoc.numPages; i++) {
				const pageContainer = await renderPage(i);
				tempDiv.appendChild(pageContainer);
			}

			// Swap content
			const scrollPos = container.scrollTop;
			const scrollLeft = container.scrollLeft;
			container.innerHTML = '';
			while (tempDiv.firstChild) {
				container.appendChild(tempDiv.firstChild);
			}
			container.scrollTop = scrollPos;
			container.scrollLeft = scrollLeft;

			// Reset transform since we rendered at the target scale
			container.style.transform = 'scale(1)';
			container.style.transformOrigin = 'top left';

			pageInfo.textContent = \`\${pdfDoc.numPages} page(s) - Zoom: \${Math.round(targetScale * 100)}%\`;
			isRendering = false;
		}

		function updateZoomImmediate(newScale) {
			targetScale = newScale;

			// Apply CSS transform immediately for smooth zoom
			const scaleRatio = targetScale / currentRenderScale;
			container.style.transform = \`scale(\${scaleRatio})\`;
			container.style.transformOrigin = 'top left';

			pageInfo.textContent = \`\${pdfDoc.numPages} page(s) - Zoom: \${Math.round(targetScale * 100)}%\`;

			// Debounce the actual re-render
			clearTimeout(renderTimeout);
			renderTimeout = setTimeout(() => {
				renderAllPages(true);
			}, 300); // Re-render 300ms after zoom stops
		}

		function setZoom(newScale) {
			scale = Math.max(0.25, Math.min(5, newScale));
			updateZoomImmediate(scale);
		}

		document.getElementById('zoomIn').addEventListener('click', () => {
			setZoom(scale + 0.25);
		});

		document.getElementById('zoomOut').addEventListener('click', () => {
			setZoom(scale - 0.25);
		});

		document.getElementById('actualSize').addEventListener('click', () => {
			setZoom(1);
		});

		document.getElementById('fitWidth').addEventListener('click', async () => {
			if (pdfDoc) {
				const page = await pdfDoc.getPage(1);
				const viewport = page.getViewport({ scale: 1 });
				const containerWidth = container.clientWidth - 40; // subtract padding
				const fitScale = containerWidth / viewport.width;
				setZoom(fitScale);
			}
		});

		// Zoom with Ctrl/Cmd + scroll wheel
		container.addEventListener('wheel', (e) => {
			if (e.ctrlKey || e.metaKey) {
				e.preventDefault();
				const delta = e.deltaY > 0 ? -0.1 : 0.1;
				setZoom(scale + delta);
			}
		}, { passive: false });

		// Load PDF from base64 data
		const pdfData = atob('${pdfBase64}');
		const pdfArray = new Uint8Array(pdfData.length);
		for (let i = 0; i < pdfData.length; i++) {
			pdfArray[i] = pdfData.charCodeAt(i);
		}

		pdfjsLib.getDocument({ data: pdfArray }).promise.then(pdf => {
			pdfDoc = pdf;
			renderAllPages();
		}).catch(err => {
			container.innerHTML = '<div style="color: white; padding: 20px;">Error loading PDF: ' + err.message + '</div>';
		});
	</script>
</body>
</html>`;
	}
}
