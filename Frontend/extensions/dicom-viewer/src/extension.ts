/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

import * as vscode from 'vscode';
import { DicomViewerProvider } from './dicomViewer';
import { dicomStateManager } from './dicomState';

export function activate(context: vscode.ExtensionContext) {
	const provider = new DicomViewerProvider(context);

	context.subscriptions.push(
		vscode.window.registerCustomEditorProvider(
			'dicomViewer.viewer',
			provider,
			{
				supportsMultipleEditorsPerDocument: false,
				webviewOptions: {
					retainContextWhenHidden: true
				}
			}
		)
	);

	// Register command to get current DICOM viewer state
	// This is called by the chat system to get the current slice context
	context.subscriptions.push(
		vscode.commands.registerCommand('dicomViewer.getCurrentState', () => {
			return dicomStateManager.getViewerState();
		})
	);
}

export function deactivate() { }
