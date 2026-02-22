/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

import * as vscode from 'vscode';
import { PdfViewerProvider } from './pdfViewer';

export function activate(context: vscode.ExtensionContext) {
	const provider = new PdfViewerProvider(context);

	context.subscriptions.push(
		vscode.window.registerCustomEditorProvider(
			'pdfViewer.viewer',
			provider,
			{
				supportsMultipleEditorsPerDocument: false,
				webviewOptions: {
					retainContextWhenHidden: true
				}
			}
		)
	);
}

export function deactivate() { }
