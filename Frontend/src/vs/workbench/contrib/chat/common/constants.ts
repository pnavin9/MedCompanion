/*---------------------------------------------------------------------------------------------
 *  Copyright (c) Microsoft Corporation. All rights reserved.
 *  Licensed under the MIT License. See License.txt in the project root for license information.
 *--------------------------------------------------------------------------------------------*/

export enum ChatConfiguration {
	UnifiedChatView = 'chat.unifiedChatView',
	UseFileStorage = 'chat.useFileStorage',
	AgentEnabled = 'chat.agent.enabled',
	Edits2Enabled = 'chat.edits2.enabled',
	ExtensionToolsEnabled = 'chat.extensionTools.enabled',
}

export enum ChatMode {
	Agent = 'agent',
	Plan = 'plan',
	Diagnose = 'diagnose',
	Consult = 'consult'
}

export function validateChatMode(mode: unknown): ChatMode | undefined {
	switch (mode) {
		case ChatMode.Agent:
		case ChatMode.Plan:
		case ChatMode.Diagnose:
		case ChatMode.Consult:
			return mode as ChatMode;
		default:
			return undefined;
	}
}

export enum ChatDomain {
	General = 'general',
	Radiology = 'radiology',
	Pathology = 'pathology',
	Dermatology = 'dermatology'
}

export function validateChatDomain(domain: unknown): ChatDomain | undefined {
	switch (domain) {
		case ChatDomain.General:
		case ChatDomain.Radiology:
		case ChatDomain.Pathology:
		case ChatDomain.Dermatology:
			return domain as ChatDomain;
		default:
			return undefined;
	}
}

export type RawChatParticipantLocation = 'panel' | 'terminal' | 'notebook' | 'editing-session';

export enum ChatAgentLocation {
	Panel = 'panel',
	Terminal = 'terminal',
	Notebook = 'notebook',
	Editor = 'editor',
	EditingSession = 'editing-session',
}

export namespace ChatAgentLocation {
	export function fromRaw(value: RawChatParticipantLocation | string): ChatAgentLocation {
		switch (value) {
			case 'panel': return ChatAgentLocation.Panel;
			case 'terminal': return ChatAgentLocation.Terminal;
			case 'notebook': return ChatAgentLocation.Notebook;
			case 'editor': return ChatAgentLocation.Editor;
			case 'editing-session': return ChatAgentLocation.EditingSession;
		}
		return ChatAgentLocation.Panel;
	}
}
