/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

import { IFileService } from '../../../../../platform/files/common/files.js';
import { IWorkspaceContextService } from '../../../../../platform/workspace/common/workspace.js';
import { URI } from '../../../../../base/common/uri.js';

export interface MedicalDocument {
	fileName: string;
	filePath: string;
	content: string;
	uri: URI;
}

export class WorkspaceFileScanner {
	constructor(
		@IFileService private readonly fileService: IFileService,
		@IWorkspaceContextService private readonly workspaceContextService: IWorkspaceContextService
	) { }

	/**
	 * Scans all workspace folders for markdown (.md) files
	 * @returns Array of medical documents with their content
	 */
	async scanForMarkdownFiles(): Promise<MedicalDocument[]> {
		const workspaceFolders = this.workspaceContextService.getWorkspace().folders;

		if (workspaceFolders.length === 0) {
			return [];
		}

		const allDocuments: MedicalDocument[] = [];

		// Scan each workspace folder
		for (const folder of workspaceFolders) {
			try {
				const documents = await this.scanFolder(folder.uri);
				allDocuments.push(...documents);
			} catch (error) {
				console.error(`Error scanning folder ${folder.uri.fsPath}:`, error);
				// Continue with other folders even if one fails
			}
		}

		return allDocuments;
	}

	/**
	 * Scans all workspace folders for PDF (.pdf) files
	 * @returns Array of PDF file paths
	 */
	async scanForPdfFiles(): Promise<string[]> {
		const workspaceFolders = this.workspaceContextService.getWorkspace().folders;

		if (workspaceFolders.length === 0) {
			return [];
		}

		const pdfPaths: string[] = [];

		// Scan each workspace folder
		for (const folder of workspaceFolders) {
			try {
				const paths = await this.scanFolderForPdfs(folder.uri);
				pdfPaths.push(...paths);
			} catch (error) {
				console.error(`Error scanning folder for PDFs ${folder.uri.fsPath}:`, error);
			}
		}

		return pdfPaths;
	}

	/**
	 * Recursively scans a folder for PDF files
	 */
	private async scanFolderForPdfs(folderUri: URI): Promise<string[]> {
		const pdfPaths: string[] = [];

		try {
			const stat = await this.fileService.resolve(folderUri, { resolveMetadata: true });

			if (!stat.children) {
				return pdfPaths;
			}

			// Process each child item
			for (const child of stat.children) {
				if (child.isDirectory) {
					// Skip common directories
					const dirName = child.name.toLowerCase();
					if (dirName === 'node_modules' ||
						dirName === '.git' ||
						dirName === 'dist' ||
						dirName === 'build' ||
						dirName === 'medgemma-env' ||
						dirName.startsWith('.')) {
						continue;
					}

					// Recursively scan subdirectories
					const subPaths = await this.scanFolderForPdfs(child.resource);
					pdfPaths.push(...subPaths);
				} else if (child.name.toLowerCase().endsWith('.pdf')) {
					// Add PDF file path
					pdfPaths.push(child.resource.fsPath);
				}
			}
		} catch (error) {
			console.error(`Error resolving folder ${folderUri.fsPath}:`, error);
		}

		return pdfPaths;
	}

	/**
	 * Recursively scans a folder for markdown files
	 */
	private async scanFolder(folderUri: URI): Promise<MedicalDocument[]> {
		const documents: MedicalDocument[] = [];

		try {
			const stat = await this.fileService.resolve(folderUri, { resolveMetadata: true });

			if (!stat.children) {
				return documents;
			}

			// Process each child item
			for (const child of stat.children) {
				if (child.isDirectory) {
					// Skip common directories that shouldn't be scanned
					const dirName = child.name.toLowerCase();
					if (dirName === 'node_modules' ||
						dirName === '.git' ||
						dirName === 'dist' ||
						dirName === 'build' ||
						dirName === 'medgemma-env' ||
						dirName.startsWith('.')) {
						continue;
					}

					// Recursively scan subdirectories
					const subDocs = await this.scanFolder(child.resource);
					documents.push(...subDocs);
				} else if (child.name.toLowerCase().endsWith('.md')) {
					// Process markdown file
					try {
						const doc = await this.readMarkdownFile(child.resource);
						if (doc && doc.content.trim().length > 0) {
							documents.push(doc);
						}
					} catch (error) {
						console.error(`Error reading file ${child.resource.fsPath}:`, error);
						// Continue with other files
					}
				}
			}
		} catch (error) {
			console.error(`Error resolving folder ${folderUri.fsPath}:`, error);
		}

		return documents;
	}

	/**
	 * Reads a markdown file and returns its content
	 */
	private async readMarkdownFile(uri: URI): Promise<MedicalDocument | null> {
		try {
			const content = await this.fileService.readFile(uri);
			const textContent = content.value.toString();

			// Skip empty files
			if (textContent.trim().length === 0) {
				return null;
			}

			return {
				fileName: uri.path.split('/').pop() || uri.path,
				filePath: uri.fsPath,
				content: textContent,
				uri: uri
			};
		} catch (error) {
			console.error(`Failed to read file ${uri.fsPath}:`, error);
			return null;
		}
	}

	/**
	 * Formats the collected documents into a prompt string for the AI
	 */
	formatDocumentsForPrompt(documents: MedicalDocument[]): string {
		if (documents.length === 0) {
			return '';
		}

		const parts: string[] = [];
		parts.push('Here are the medical documents from the workspace:\n');

		for (const doc of documents) {
			parts.push(`\n--- File: ${doc.fileName} ---`);
			parts.push(doc.content);
			parts.push('--- End of file ---\n');
		}

		return parts.join('\n');
	}
}
