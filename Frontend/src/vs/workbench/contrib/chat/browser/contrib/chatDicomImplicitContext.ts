/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

import { Disposable, IDisposable, toDisposable } from '../../../../../base/common/lifecycle.js';
import { Emitter } from '../../../../../base/common/event.js';
import { IWorkbenchContribution } from '../../../../common/contributions.js';
import { IChatWidget, IChatWidgetService } from '../chat.js';
import { ICommandService } from '../../../../../platform/commands/common/commands.js';
import { IFileService } from '../../../../../platform/files/common/files.js';
import { IBaseChatRequestVariableEntry } from '../../common/chatModel.js';
import { ChatAgentLocation } from '../../common/constants.js';

export interface DicomSliceInfo {
	imagePath: string;
	sliceIndex: number;
	totalSlices: number;
	outputFolder: string;
	folderPath: string;
}

export interface DicomViewerState {
	outputFolder: string;
	currentSliceIndex: number;
	totalSlices: number;
	folderPath: string;
}

export class DicomImplicitContext extends Disposable {
	get id() {
		return 'vscode.implicit.dicom';
	}

	get name(): string {
		return this._sliceInfo
			? `dicom:slice-${this._sliceInfo.sliceIndex + 1}`
			: 'dicom';
	}

	readonly kind = 'implicit';

	get modelDescription(): string {
		return this._sliceInfo
			? `Current DICOM slice ${this._sliceInfo.sliceIndex + 1}/${this._sliceInfo.totalSlices}`
			: 'DICOM viewer context';
	}

	readonly isImage = true;
	readonly isFile = false;

	private _isSelection = false;
	public get isSelection(): boolean {
		return this._isSelection;
	}

	private _onDidChangeValue = new Emitter<void>();
	readonly onDidChangeValue = this._onDidChangeValue.event;

	private _enabled = true;
	get enabled() {
		return this._enabled;
	}

	set enabled(value: boolean) {
		this._enabled = value;
		this._onDidChangeValue.fire();
	}

	private _sliceInfo: DicomSliceInfo | undefined;
	get value() {
		return this._sliceInfo;
	}

	constructor(sliceInfo?: DicomSliceInfo) {
		super();
		this._sliceInfo = sliceInfo;
	}

	setDicomContext(info: DicomSliceInfo | undefined) {
		this._sliceInfo = info;
		this._onDidChangeValue.fire();
	}

	toBaseEntry(): IBaseChatRequestVariableEntry {
		return {
			id: this.id,
			name: this.name,
			value: this.value,
			isFile: false,
			isImage: true,
			modelDescription: this.modelDescription
		};
	}
}

export class DicomImplicitContextContribution extends Disposable implements IWorkbenchContribution {
	static readonly ID = 'chat.dicomImplicitContext';

	private _lastState: string | undefined;

	constructor(
		@IChatWidgetService private readonly chatWidgetService: IChatWidgetService,
		@ICommandService private readonly commandService: ICommandService,
		@IFileService _fileService: IFileService,
	) {
		super();

		// Poll for DICOM state changes
		this._register(this.startPolling());

		// Initialize for existing widgets
		this._register(this.chatWidgetService.onDidAddWidget(async (widget) => {
			await this.updateDicomContext(widget);
		}));
	}

	private startPolling(): IDisposable {
		// Poll every 500ms for DICOM state changes
		const intervalId = setInterval(() => {
			this.updateDicomContext();
		}, 500);

		return toDisposable(() => clearInterval(intervalId));
	}

	private async updateDicomContext(updateWidget?: IChatWidget): Promise<void> {
		try {
			// Get current DICOM state via command
			const state = await this.commandService.executeCommand<DicomViewerState | undefined>('dicomViewer.getCurrentState');

			// Create a state signature for change detection
			const stateSignature = state
				? `${state.outputFolder}:${state.currentSliceIndex}:${state.totalSlices}`
				: undefined;

			// Only update if state actually changed
			if (stateSignature === this._lastState) {
				return;
			}

			this._lastState = stateSignature;

			if (!state) {
				// No DICOM viewer active - clear context
				this.setContextForAllWidgets(undefined, updateWidget);
				return;
			}

			// Build DicomSliceInfo from state
			const sliceInfo = await this.buildSliceInfo(state);

			// Update all chat widgets
			this.setContextForAllWidgets(sliceInfo, updateWidget);
		} catch (error) {
			// Silently fail if command doesn't exist (extension not loaded)
		}
	}

	private async buildSliceInfo(state: DicomViewerState): Promise<DicomSliceInfo> {
		// Build the PNG path for current slice
		const sliceFileName = `slice-${state.currentSliceIndex.toString().padStart(4, '0')}.png`;
		const imagePath = `${state.outputFolder}/${sliceFileName}`;

		return {
			imagePath,
			sliceIndex: state.currentSliceIndex,
			totalSlices: state.totalSlices,
			outputFolder: state.outputFolder,
			folderPath: state.folderPath
		};
	}

	private setContextForAllWidgets(sliceInfo: DicomSliceInfo | undefined, updateWidget?: IChatWidget) {
		const widgets = updateWidget ? [updateWidget] : [
			...this.chatWidgetService.getWidgetsByLocations(ChatAgentLocation.Panel),
			...this.chatWidgetService.getWidgetsByLocations(ChatAgentLocation.EditingSession),
			...this.chatWidgetService.getWidgetsByLocations(ChatAgentLocation.Editor),
		];

		for (const widget of widgets) {
			if (!widget.input.dicomImplicitContext) {
				continue;
			}
			widget.input.dicomImplicitContext.setDicomContext(sliceInfo);
		}
	}
}
