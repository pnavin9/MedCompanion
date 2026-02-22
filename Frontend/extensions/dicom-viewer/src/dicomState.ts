/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

/**
 * Global state manager for DICOM viewer
 * Stores current viewer state to be accessible by other parts of VSCode (e.g., chat)
 */

export interface DicomViewerState {
	outputFolder: string;
	currentSliceIndex: number;
	totalSlices: number;
	folderPath: string;
}

class DicomStateManager {
	private currentState: DicomViewerState | undefined;

	setViewerState(state: DicomViewerState): void {
		this.currentState = state;
	}

	getViewerState(): DicomViewerState | undefined {
		return this.currentState;
	}

	clearViewerState(): void {
		this.currentState = undefined;
	}

	isViewerActive(): boolean {
		return this.currentState !== undefined;
	}
}

// Global singleton instance
export const dicomStateManager = new DicomStateManager();
