/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

/**
 * Detects if a user's chat message is requesting a medical summary
 */
export class MedicalSummaryDetector {

	private readonly summaryKeywords = [
		'summary',
		'summarize',
		'summarise',  // British spelling
		'patient summary',
		'medical summary',
		'overview',
		'overview of',
		'overview of files',
		'overview of documents',
		'medical history',
		'patient history',
		'patient overview',
		'medical overview',
		'summarize medical',
		'summarize patient',
		'summarize files',
		'summarize documents',
		'give me a summary',
		'generate summary',
		'create summary',
		'provide summary',
		'show summary'
	];

	/**
	 * Checks if the user message is requesting a medical summary
	 * @param message The user's chat message
	 * @returns true if this appears to be a summary request
	 */
	isSummaryRequest(message: string): boolean {
		if (!message || message.trim().length === 0) {
			return false;
		}

		const lowerMessage = message.toLowerCase().trim();

		// Check for keyword matches
		for (const keyword of this.summaryKeywords) {
			if (lowerMessage.includes(keyword)) {
				return true;
			}
		}

		// Check for common summary-related patterns
		const summaryPatterns = [
			/what('s| is) (in )?the medical (files|documents)/i,
			/show me (the )?(patient|medical) (files|documents|records)/i,
			/give me (an? )?(overview|summary)/i,
			/can you summarize/i,
			/please summarize/i,
			/provide (an? )?(overview|summary)/i
		];

		for (const pattern of summaryPatterns) {
			if (pattern.test(message)) {
				return true;
			}
		}

		return false;
	}

	/**
	 * Extracts any specific focus areas from the summary request
	 * For example: "summarize the patient's lab results" -> "lab results"
	 * @param message The user's chat message
	 * @returns The focus area if found, or undefined
	 */
	extractFocusArea(message: string): string | undefined {
		// Common medical focus areas
		const focusPatterns = [
			{ pattern: /(lab|laboratory) (results?|tests?|work)/i, area: 'laboratory results' },
			{ pattern: /imaging|radiology|x-?ray|ct|mri|ultrasound/i, area: 'imaging studies' },
			{ pattern: /medications?|drugs?|prescriptions?/i, area: 'medications' },
			{ pattern: /diagnos(is|es)/i, area: 'diagnoses' },
			{ pattern: /symptoms?/i, area: 'symptoms' },
			{ pattern: /vital signs?|vitals/i, area: 'vital signs' },
			{ pattern: /treatment|therapy/i, area: 'treatment' },
			{ pattern: /consultation|consult|visit/i, area: 'consultations' }
		];

		for (const { pattern, area } of focusPatterns) {
			if (pattern.test(message)) {
				return area;
			}
		}

		return undefined;
	}
}
