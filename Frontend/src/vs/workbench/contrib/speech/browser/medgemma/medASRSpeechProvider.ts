/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

import { CancellationToken } from '../../../../../base/common/cancellation.js';
import { Emitter, Event } from '../../../../../base/common/event.js';
import { Disposable } from '../../../../../base/common/lifecycle.js';
import { ExtensionIdentifier } from '../../../../../platform/extensions/common/extensions.js';
import { ISpeechProvider, ISpeechProviderMetadata, ISpeechToTextSession, ITextToSpeechSession, IKeywordRecognitionSession, ISpeechToTextEvent, ITextToSpeechEvent, IKeywordRecognitionEvent, SpeechToTextStatus } from '../../common/speechService.js';

export class MedASRSpeechProvider implements ISpeechProvider {

	readonly metadata: ISpeechProviderMetadata = {
		extension: new ExtensionIdentifier('medcompanion.medasr'),
		displayName: 'MedASR Medical Speech'
	};

	createSpeechToTextSession(token: CancellationToken): ISpeechToTextSession {
		return new MedASRSpeechToTextSession(token);
	}

	createTextToSpeechSession(token: CancellationToken): ITextToSpeechSession {
		// Not implemented - return no-op session
		return new NoOpTextToSpeechSession();
	}

	createKeywordRecognitionSession(token: CancellationToken): IKeywordRecognitionSession {
		// Not implemented - return no-op session
		return new NoOpKeywordRecognitionSession();
	}
}

class MedASRSpeechToTextSession extends Disposable implements ISpeechToTextSession {

	private readonly _onDidChange = this._register(new Emitter<ISpeechToTextEvent>());
	readonly onDidChange: Event<ISpeechToTextEvent> = this._onDidChange.event;

	private mediaRecorder: MediaRecorder | undefined;
	private stream: MediaStream | undefined;
	private completed = false; // Flag to prevent double-firing of events
	private audioChunks: Blob[] = []; // Collect audio chunks during recording

	constructor(token: CancellationToken) {
		super();

		// Start capturing audio when session is created
		this.startRecording();

		// Note: We don't listen to token cancellation here because we want
		// to fire final events via complete(), not when token is cancelled.
		// This ensures the listener in VoiceChatSessions receives the events
		// before it gets disposed.
	}

	/**
	 * Complete the session and fire final events.
	 * This should be called before disposal to ensure listeners receive final events.
	 */
	complete(): void {
		console.log('[MedASR] complete() called, completed flag:', this.completed);
		if (this.completed) {
			console.log('[MedASR] Already completed, returning early');
			return; // Already completed, don't fire events again
		}
		this.completed = true;

		// Stop recording if still active
		// This triggers async transcription in the background
		console.log('[MedASR] Stopping recording...');
		this.stopRecording();

		// Fire Stopped event synchronously so disposal can proceed
		// Transcription will complete asynchronously and fire Recognized later
		// (Recognized events are allowed even after session is stopped)
		console.log('[MedASR] Firing Stopped event synchronously');
		this._onDidChange.fire({ status: SpeechToTextStatus.Stopped });
		console.log('[MedASR] Stopped event fired, complete() returning');
	}

	private async startRecording(): Promise<void> {
		console.log('[MedASR] startRecording() called');
		try {
			// Check if mediaDevices is available
			if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
				throw new Error('getUserMedia not supported in this browser');
			}

			// Request microphone access
			this.stream = await navigator.mediaDevices.getUserMedia({
				audio: {
					echoCancellation: true,
					noiseSuppression: true,
					autoGainControl: true
				}
			});

			// Create MediaRecorder
			this.mediaRecorder = new MediaRecorder(this.stream);

			// Collect audio chunks as they become available
			this.mediaRecorder.ondataavailable = (event) => {
				if (event.data.size > 0) {
					console.log('[MedASR] Audio chunk received:', event.data.size, 'bytes');
					this.audioChunks.push(event.data);
				}
			};

			// Emit Started event
			console.log('[MedASR] Firing Started event');
			this._onDidChange.fire({ status: SpeechToTextStatus.Started });

			// Start recording
			this.mediaRecorder.start();
			console.log('[MedASR] MediaRecorder started');

			// When recording stops, send to backend for transcription
			this.mediaRecorder.addEventListener('stop', () => {
				console.log('[MedASR] MediaRecorder stop event fired, calling handleRecordingStopped()');
				this.handleRecordingStopped();
			});

		} catch (error) {
			// Log detailed error information
			const errorMessage = error instanceof Error ? error.message : 'Unknown error';
			const errorName = error instanceof Error ? error.name : 'Error';
			console.error('[MedASR] Failed to access microphone:', errorName, errorMessage, error);

			// Error accessing microphone
			this._onDidChange.fire({
				status: SpeechToTextStatus.Error,
				text: `Failed to access microphone: ${errorName} - ${errorMessage}`
			});
			this._onDidChange.fire({ status: SpeechToTextStatus.Stopped });
		}
	}

	private stopRecording(): void {
		// Stop MediaRecorder
		if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
			this.mediaRecorder.stop();
		}

		// Clean up media stream
		if (this.stream) {
			this.stream.getTracks().forEach(track => track.stop());
			this.stream = undefined;
		}
	}

	private async handleRecordingStopped(): Promise<void> {
		console.log('[MedASR] handleRecordingStopped() called, completed flag:', this.completed);

		// Check if we have audio chunks
		if (this.audioChunks.length === 0) {
			console.warn('[MedASR] No audio chunks collected');
			return;
		}

		// Combine chunks into single Blob
		const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
		const audioBlobCopy = audioBlob; // Keep reference before clearing
		this.audioChunks = []; // Clear chunks for next recording

		console.log(`[MedASR] Sending ${audioBlobCopy.size} bytes to backend for transcription...`);

		// Create FormData
		const formData = new FormData();
		formData.append('audio', audioBlobCopy, 'recording.webm');

		// Send to backend
		try {
			const response = await fetch('http://localhost:8000/api/v1/speech/transcribe', {
				method: 'POST',
				body: formData
			});

			if (!response.ok) {
				throw new Error(`HTTP ${response.status}: ${response.statusText}`);
			}

			const result = await response.json();

			if (result.success && result.text) {
				console.log('[MedASR] Transcription received:', result.text);
				console.log('[MedASR] About to fire Recognized event, completed flag:', this.completed);

				// Fire Recognized event with real transcription
				this._onDidChange.fire({
					status: SpeechToTextStatus.Recognized,
					text: result.text
				});

				console.log('[MedASR] Recognized event fired successfully');
			} else {
				throw new Error(result.error || 'Transcription failed');
			}
		} catch (error) {
			const errorMessage = error instanceof Error ? error.message : 'Unknown error';
			console.error('[MedASR] Transcription failed:', errorMessage, error);

			// Fire Error event
			this._onDidChange.fire({
				status: SpeechToTextStatus.Error,
				text: `Transcription failed: ${errorMessage}`
			});
		}
		// Note: Stopped event is fired synchronously by complete(), not here
		console.log('[MedASR] handleRecordingStopped() complete');
	}

	override dispose(): void {
		// Just clean up resources, don't fire events
		// Events should have been fired via complete() before disposal
		this.stopRecording();
		super.dispose();
	}
}

class NoOpTextToSpeechSession implements ITextToSpeechSession {
	readonly onDidChange: Event<ITextToSpeechEvent> = Event.None;

	async synthesize(text: string): Promise<void> {
		// No-op
	}
}

class NoOpKeywordRecognitionSession implements IKeywordRecognitionSession {
	readonly onDidChange: Event<IKeywordRecognitionEvent> = Event.None;
}
