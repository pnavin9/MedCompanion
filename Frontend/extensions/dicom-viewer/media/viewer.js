/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

// @ts-check
"use strict";

(function () {
	// @ts-ignore
	const vscode = acquireVsCodeApi();

	let slices = [];
	let currentIndex = 0;
	let seriesMetadata = {};

	// Notify extension we're ready
	window.addEventListener('load', () => {
		vscode.postMessage({ type: 'ready' });
	});

	// Handle messages from extension
	window.addEventListener('message', (event) => {
		const message = event.data;

		switch (message.type) {
			case 'loading':
				showLoading(message.message);
				break;
			case 'seriesLoaded':
				hideLoading();
				loadSeries(message.data);
				break;
			case 'error':
				showError(message.message);
				break;
		}
	});

	function showLoading(msg) {
		const loading = document.getElementById('loading');
		const viewer = document.getElementById('viewer');
		if (loading && viewer) {
			loading.textContent = msg || 'Loading...';
			loading.style.display = 'block';
			viewer.style.display = 'none';
		}
	}

	function hideLoading() {
		const loading = document.getElementById('loading');
		const viewer = document.getElementById('viewer');
		if (loading && viewer) {
			loading.style.display = 'none';
			viewer.style.display = 'flex';
		}
	}

	function showError(msg) {
		const error = document.getElementById('error');
		const loading = document.getElementById('loading');
		if (error && loading) {
			error.textContent = msg;
			error.style.display = 'block';
			loading.style.display = 'none';
		}
	}

	function loadSeries(data) {
		slices = data.slices;
		seriesMetadata = data.metadata;

		// Setup slider
		/** @type {HTMLInputElement | null} */
		const slider = /** @type {HTMLInputElement | null} */ (document.getElementById('slider'));
		const total = document.getElementById('total');
		if (slider && total) {
			slider.max = String(slices.length - 1);
			total.textContent = String(slices.length);
		}

		// Display series metadata
		displaySeriesMetadata(seriesMetadata);

		// Render first slice
		renderSlice(0);

		// Setup event listeners
		setupControls();
	}

	function renderSlice(index) {
		if (index < 0 || index >= slices.length) {
			return;
		}

		currentIndex = index;
		const slice = slices[index];

		// Update image
		/** @type {HTMLImageElement | null} */
		const img = /** @type {HTMLImageElement | null} */ (document.getElementById('image'));
		if (img) {
			img.src = slice.imageUri;
		}

		// Update UI
		const current = document.getElementById('current');
		/** @type {HTMLInputElement | null} */
		const slider = /** @type {HTMLInputElement | null} */ (document.getElementById('slider'));
		if (current) {
			current.textContent = String(index + 1);
		}
		if (slider) {
			slider.value = String(index);
		}

		// Display slice info
		displaySliceInfo(index);

		// Notify extension about slice change
		vscode.postMessage({
			type: 'sliceChanged',
			index: index,
			totalSlices: slices.length
		});
	}

	function displaySeriesMetadata(metadata) {
		const seriesInfo = document.getElementById('series-info');
		if (!seriesInfo) {
			return;
		}

		const html = `
			<p><strong>Patient:</strong> ${metadata.patient_name || 'Unknown'}</p>
			<p><strong>Study Date:</strong> ${metadata.study_date || 'Unknown'}</p>
			<p><strong>Modality:</strong> ${metadata.modality || 'Unknown'}</p>
			<p><strong>Body Part:</strong> ${metadata.body_part_examined || 'N/A'}</p>
			<p><strong>Series:</strong> ${metadata.series_description || 'N/A'}</p>
		`;
		seriesInfo.innerHTML = html;
	}

	function displaySliceInfo(index) {
		const sliceInfo = document.getElementById('slice-info');
		if (!sliceInfo) {
			return;
		}

		const html = `<p>Slice ${index + 1} of ${slices.length}</p>`;
		sliceInfo.innerHTML = html;
	}

	function setupControls() {
		// Slider
		/** @type {HTMLInputElement | null} */
		const slider = /** @type {HTMLInputElement | null} */ (document.getElementById('slider'));
		if (slider) {
			slider.addEventListener('input', (e) => {
				const target = /** @type {HTMLInputElement} */ (e.target);
				if (target) {
					renderSlice(parseInt(target.value));
				}
			});
		}

		// Keyboard navigation
		document.addEventListener('keydown', (e) => {
			if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') {
				e.preventDefault();
				if (currentIndex > 0) {
					renderSlice(currentIndex - 1);
				}
			} else if (e.key === 'ArrowDown' || e.key === 'ArrowRight') {
				e.preventDefault();
				if (currentIndex < slices.length - 1) {
					renderSlice(currentIndex + 1);
				}
			} else if (e.key === 'Home') {
				e.preventDefault();
				renderSlice(0);
			} else if (e.key === 'End') {
				e.preventDefault();
				renderSlice(slices.length - 1);
			}
		});

		// Mouse wheel navigation
		const image = document.getElementById('image');
		if (image) {
			image.addEventListener('wheel', (e) => {
				e.preventDefault();
				if (e.deltaY < 0 && currentIndex > 0) {
					renderSlice(currentIndex - 1);
				} else if (e.deltaY > 0 && currentIndex < slices.length - 1) {
					renderSlice(currentIndex + 1);
				}
			});
		}
	}
}());
