/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

import * as dom from '../../../../../base/browser/dom.js';
import { Button } from '../../../../../base/browser/ui/button/button.js';
import { getDefaultHoverDelegate } from '../../../../../base/browser/ui/hover/hoverDelegateFactory.js';
import { Codicon } from '../../../../../base/common/codicons.js';
import { Disposable, DisposableStore } from '../../../../../base/common/lifecycle.js';
import { IHoverService } from '../../../../../platform/hover/browser/hover.js';
import { localize } from '../../../../../nls.js';
import { DicomImplicitContext } from '../contrib/chatDicomImplicitContext.js';

export class DicomImplicitContextAttachmentWidget extends Disposable {
	public readonly domNode: HTMLElement;

	private readonly renderDisposables = this._register(new DisposableStore());

	constructor(
		private readonly attachment: DicomImplicitContext,
		@IHoverService private readonly hoverService: IHoverService,
	) {
		super();

		this.domNode = dom.$('.chat-attached-context-attachment.show-file-icons.implicit.dicom');
		this.render();

		this._register(this.attachment.onDidChangeValue(() => {
			this.render();
		}));
	}

	private render() {
		dom.clearNode(this.domNode);
		this.renderDisposables.clear();

		const sliceInfo = this.attachment.value;
		if (!sliceInfo) {
			return;
		}

		this.domNode.classList.toggle('disabled', !this.attachment.enabled);

		// Create container for icon and text
		const contentContainer = dom.append(this.domNode, dom.$('.dicom-context-content'));

		// Add medical image icon
		dom.append(contentContainer, dom.$('.dicom-icon.codicon.codicon-file-media'));

		// Add slice information
		const textContainer = dom.append(contentContainer, dom.$('.dicom-text'));
		const sliceLabel = dom.append(textContainer, dom.$('.dicom-slice-label'));
		sliceLabel.textContent = `Slice ${sliceInfo.sliceIndex + 1}/${sliceInfo.totalSlices}`;

		// Hint badge
		const hintElement = dom.append(this.domNode, dom.$('span.chat-implicit-hint', undefined, 'Current DICOM'));

		// Hover tooltip
		const currentDicom = localize('currentDicom', "Current DICOM slice");
		const inactive = localize('enableHint', "disabled");
		const currentDicomHint = currentDicom + (this.attachment.enabled ? '' : ` (${inactive})`);
		const sliceDetails = `${sliceInfo.imagePath}`;
		const title = `${currentDicomHint}\n${sliceDetails}`;

		this.domNode.ariaLabel = `${currentDicom}, ${sliceLabel.textContent}`;
		this.domNode.tabIndex = 0;
		this._register(this.hoverService.setupManagedHover(getDefaultHoverDelegate('element'), hintElement, title));

		// Toggle button (eye icon)
		const buttonMsg = this.attachment.enabled
			? localize('disableDicom', "Disable current DICOM context")
			: localize('enableDicom', "Enable current DICOM context");
		const toggleButton = this.renderDisposables.add(new Button(this.domNode, { supportIcons: true, title: buttonMsg }));
		toggleButton.icon = this.attachment.enabled ? Codicon.eye : Codicon.eyeClosed;
		this.renderDisposables.add(toggleButton.onDidClick((e) => {
			e.stopPropagation();
			this.attachment.enabled = !this.attachment.enabled;
		}));
	}
}
