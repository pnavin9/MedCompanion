/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

import { Disposable } from '../../../../../base/common/lifecycle.js';
import { IWorkbenchContribution } from '../../../../common/contributions.js';
import { ISpeechService } from '../../common/speechService.js';
import { MedASRSpeechProvider } from './medASRSpeechProvider.js';

export class MedASRSpeechContribution extends Disposable implements IWorkbenchContribution {

	static readonly ID = 'workbench.contrib.medASRSpeech';

	constructor(
		@ISpeechService private readonly speechService: ISpeechService
	) {
		super();
		this.registerProvider();
	}

	private registerProvider(): void {
		const provider = new MedASRSpeechProvider();
		this._register(this.speechService.registerSpeechProvider('medasr', provider));
	}
}
