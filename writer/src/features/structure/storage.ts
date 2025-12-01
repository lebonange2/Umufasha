import { DocumentState } from './types';
import { DEFAULT_NUMBERING } from './types';

const STRUCTURE_PREFIX = 'writer_structure_';
const STRUCTURE_VERSION_PREFIX = 'writer_structure_version_';
const MAX_VERSIONS = 20;

export class StructureStorage {
  private dbName = 'writer_db';
  private dbVersion = 2; // Increment to trigger upgrade
  private db: IDBDatabase | null = null;

  async init(): Promise<void> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.dbVersion);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        this.db = request.result;
        resolve();
      };

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;
        
        // Create structured documents store
        if (!db.objectStoreNames.contains('structured_drafts')) {
          db.createObjectStore('structured_drafts', { keyPath: 'id' });
        }
        
        // Create structured versions store
        if (!db.objectStoreNames.contains('structured_versions')) {
          const versionStore = db.createObjectStore('structured_versions', { keyPath: 'id' });
          versionStore.createIndex('draftId', 'draftId', { unique: false });
          versionStore.createIndex('createdAt', 'createdAt', { unique: false });
        }
      };
    });
  }

  async saveStructuredDraft(id: string, state: DocumentState): Promise<void> {
    // Always save to localStorage as backup, even if IndexedDB is available
    try {
      localStorage.setItem(
        `${STRUCTURE_PREFIX}${id}`, 
        JSON.stringify({ id, state, updatedAt: Date.now() })
      );
    } catch (e) {
      console.error('Failed to save to localStorage:', e);
    }

    if (this.db) {
      try {
        const transaction = this.db.transaction(['structured_drafts'], 'readwrite');
        const store = transaction.objectStore('structured_drafts');
        await new Promise<void>((resolve, reject) => {
          const request = store.put({ 
            id, 
            state, 
            updatedAt: Date.now() 
          });
          request.onsuccess = () => resolve();
          request.onerror = () => reject(request.error);
        });
      } catch (error) {
        console.error('Failed to save to IndexedDB, using localStorage only:', error);
      }
    }
  }

  async getStructuredDraft(id: string): Promise<DocumentState | null> {
    if (this.db) {
      const transaction = this.db.transaction(['structured_drafts'], 'readonly');
      const store = transaction.objectStore('structured_drafts');
      const request = store.get(id);
      return new Promise((resolve, reject) => {
        request.onsuccess = () => {
          const result = request.result;
          resolve(result ? result.state : null);
        };
        request.onerror = () => reject(request.error);
      });
    } else {
      const data = localStorage.getItem(`${STRUCTURE_PREFIX}${id}`);
      if (data) {
        const parsed = JSON.parse(data);
        return parsed.state;
      }
      return null;
    }
  }

  async saveStructuredVersion(draftId: string, state: DocumentState): Promise<string> {
    const versionId = `${draftId}_${Date.now()}`;
    const version = {
      id: versionId,
      createdAt: Date.now(),
      state,
    };

    if (this.db) {
      const transaction = this.db.transaction(['structured_versions'], 'readwrite');
      const store = transaction.objectStore('structured_versions');
      await store.put({ ...version, draftId });

      // Clean up old versions
      const index = store.index('draftId');
      const request = index.getAll(draftId);
      request.onsuccess = () => {
        const versions = request.result.sort((a: any, b: any) => b.createdAt - a.createdAt);
        if (versions.length > MAX_VERSIONS) {
          const toDelete = versions.slice(MAX_VERSIONS);
          const deleteTransaction = this.db!.transaction(['structured_versions'], 'readwrite');
          const deleteStore = deleteTransaction.objectStore('structured_versions');
          toDelete.forEach((v: any) => deleteStore.delete(v.id));
        }
      };
    } else {
      // Fallback to localStorage
      const versions = this.getVersionsFromLocalStorage(draftId);
      versions.push(version);
      versions.sort((a, b) => b.createdAt - a.createdAt);
      if (versions.length > MAX_VERSIONS) {
        versions.splice(MAX_VERSIONS);
      }
      localStorage.setItem(`${STRUCTURE_VERSION_PREFIX}${draftId}`, JSON.stringify(versions));
    }

    return versionId;
  }

  async getStructuredVersions(draftId: string): Promise<Array<{ id: string; createdAt: number; state: DocumentState }>> {
    if (this.db) {
      const transaction = this.db.transaction(['structured_versions'], 'readonly');
      const store = transaction.objectStore('structured_versions');
      const index = store.index('draftId');
      const request = index.getAll(draftId);
      return new Promise((resolve, reject) => {
        request.onsuccess = () => {
          const versions = request.result.map((v: any) => ({
            id: v.id,
            createdAt: v.createdAt,
            state: v.state,
          }));
          resolve(versions.sort((a, b) => b.createdAt - a.createdAt));
        };
        request.onerror = () => reject(request.error);
      });
    } else {
      return this.getVersionsFromLocalStorage(draftId);
    }
  }

  private getVersionsFromLocalStorage(draftId: string): Array<{ id: string; createdAt: number; state: DocumentState }> {
    const data = localStorage.getItem(`${STRUCTURE_VERSION_PREFIX}${draftId}`);
    if (data) {
      return JSON.parse(data);
    }
    return [];
  }

  createInitialState(): DocumentState {
    const rootId = `root_${Date.now()}`;
    return {
      rootId,
      nodes: {
        [rootId]: {
          id: rootId,
          kind: 'toc',
          parentId: null,
          order: 0,
          title: 'Document Root',
        },
      },
      settings: {
        numbering: DEFAULT_NUMBERING,
        pageMode: {
          enabled: false,
          wordsPerPage: 300,
        },
      },
      labels: {},
      versions: [],
    };
  }
}

export const structureStorage = new StructureStorage();

