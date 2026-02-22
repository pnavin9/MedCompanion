/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

import { URI } from '../../../../base/common/uri.js';
import { IFileService } from '../../../../platform/files/common/files.js';
import { ICommandService } from '../../../../platform/commands/common/commands.js';

export interface DicomViewerState {
	outputFolder: string;
	currentSliceIndex: number;
	totalSlices: number;
	folderPath: string;
}

export interface DicomContextInfo {
	imagePath: string;
	sliceIndex: number;
	totalSlices: number;
	metadata: {
		series: any;
		slice: any;
	};
}

export class DicomContextService {
	constructor(
		@IFileService private readonly fileService: IFileService,
		@ICommandService private readonly commandService: ICommandService
	) { }

	/**
	 * Gets the current DICOM viewer context if a DICOM viewer is active
	 */
	async getCurrentDicomContext(): Promise<DicomContextInfo | undefined> {
		try {
			// Get state from DICOM extension via command
			const state = await this.commandService.executeCommand<DicomViewerState | undefined>('dicomViewer.getCurrentState');

			if (!state) {
				return undefined;
			}

			// Build the PNG path for current slice
			const sliceFileName = `slice-${state.currentSliceIndex.toString().padStart(4, '0')}.png`;
			const imagePath = URI.file(state.outputFolder).with({ path: `${state.outputFolder}/${sliceFileName}` }).fsPath;

			// Read metadata files
			const seriesInfoPath = URI.file(`${state.outputFolder}/series-info.json`);
			const sliceInfoPath = URI.file(`${state.outputFolder}/slice-${state.currentSliceIndex.toString().padStart(4, '0')}.json`);

			let seriesMetadata: any = {};
			let sliceMetadata: any = {};

			try {
				const seriesData = await this.fileService.readFile(seriesInfoPath);
				seriesMetadata = JSON.parse(seriesData.value.toString());
			} catch (e) {
				console.warn('Could not read series metadata', e);
			}

			try {
				const sliceData = await this.fileService.readFile(sliceInfoPath);
				sliceMetadata = JSON.parse(sliceData.value.toString());
			} catch (e) {
				console.warn('Could not read slice metadata', e);
			}

			return {
				imagePath,
				sliceIndex: state.currentSliceIndex,
				totalSlices: state.totalSlices,
				metadata: {
					series: seriesMetadata,
					slice: sliceMetadata
				}
			};
		} catch (error) {
			console.error('Error getting DICOM context:', error);
			return undefined;
		}
	}

	/**
	 * Formats metadata as a text prefix for the chat message
	 */
	formatMetadataContext(context: DicomContextInfo): string {
		const { metadata, sliceIndex, totalSlices } = context;
		const series = metadata.series;
		const slice = metadata.slice;

		const lines: string[] = ['[DICOM Context]'];

		// Series information
		if (series.series_description) {
			lines.push(`Series: ${series.series_description}`);
		}
		if (series.modality) {
			lines.push(`Modality: ${series.modality}`);
		}
		if (series.body_part_examined) {
			lines.push(`Body Part: ${series.body_part_examined}`);
		}
		if (series.patient_name && series.patient_name !== 'Unknown') {
			lines.push(`Patient: ${series.patient_name}${series.patient_id ? ` (ID: ${series.patient_id})` : ''}`);
		}
		if (series.study_date && series.study_date !== 'Unknown') {
			lines.push(`Study Date: ${series.study_date}`);
		}

		// Slice information
		lines.push(`Slice: ${sliceIndex + 1}/${totalSlices}`);
		if (slice.slice_location) {
			lines.push(`Slice Location: ${slice.slice_location}mm`);
		}

		lines.push('---');
		lines.push(''); // Empty line before user message

		return lines.join('\n');
	}
}
