import { useState, useCallback, useEffect, useRef } from 'react';
import { DocumentState, NodeKind } from './types';
import { createNode, deleteNode, moveNode, promoteNode, demoteNode, splitAtCaret, mergeWithPrev } from './tree';
import { setLabel, insertReference } from './references';
import { structureStorage } from './storage';

export function useStructure(draftId: string, initialState?: DocumentState) {
  const [state, setState] = useState<DocumentState>(() => initialState || structureStorage.createInitialState());
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const autosaveTimeoutRef = useRef<number | null>(null);
  const hasLoadedRef = useRef(false);
  const lastDraftIdRef = useRef<string | null>(null);

  // Load initial state
  useEffect(() => {
    // Reset hasLoadedRef if draftId changed
    if (lastDraftIdRef.current !== draftId) {
      hasLoadedRef.current = false;
      lastDraftIdRef.current = draftId;
    }

    // If initial state was provided, use it immediately
    if (initialState && !hasLoadedRef.current) {
      console.log('Using provided initial state:', {
        nodes: Object.keys(initialState.nodes).length,
        rootId: initialState.rootId,
        chapters: Object.values(initialState.nodes).filter(n => n.kind === 'chapter').length,
      });
      setState(initialState);
      hasLoadedRef.current = true;
      return;
    }

    // Only load from storage if no initial state was provided
    if (!initialState && draftId && !hasLoadedRef.current) {
      console.log('Loading from storage, draftId:', draftId);
      structureStorage.init().then(async () => {
        // Try IndexedDB first
        let saved = await structureStorage.getStructuredDraft(draftId);
        
        // If not found, try localStorage fallback
        if (!saved) {
          const localStorageKey = `writer_structure_${draftId}`;
          const localStorageData = localStorage.getItem(localStorageKey);
          if (localStorageData) {
            try {
              const parsed = JSON.parse(localStorageData);
              saved = parsed.state;
              console.log('Loaded from localStorage fallback');
            } catch (e) {
              console.error('Failed to parse localStorage data:', e);
            }
          }
        }
        
        // If still not found, try loading from the current structure draft
        if (!saved) {
          const currentStructureDraft = localStorage.getItem('writer_current_structure_draft');
          if (currentStructureDraft) {
            // Try IndexedDB first
            const savedDraft = await structureStorage.getStructuredDraft(currentStructureDraft);
            if (savedDraft) {
              saved = savedDraft;
              console.log('Loaded from current structure draft (IndexedDB):', currentStructureDraft);
            } else {
              // Try localStorage
              const localStorageKey = `writer_structure_${currentStructureDraft}`;
              const localStorageData = localStorage.getItem(localStorageKey);
              if (localStorageData) {
                try {
                  const parsed = JSON.parse(localStorageData);
                  saved = parsed.state;
                  console.log('Loaded from current structure draft (localStorage):', currentStructureDraft);
                } catch (e) {
                  console.error('Failed to parse localStorage data:', e);
                }
              }
            }
          }
        }
        
        if (saved) {
          console.log('Loaded state from storage:', {
            nodes: Object.keys(saved.nodes).length,
            rootId: saved.rootId,
            chapters: Object.values(saved.nodes).filter(n => n.kind === 'chapter').length,
            sections: Object.values(saved.nodes).filter(n => n.kind === 'section').length,
          });
          setState(saved);
        } else {
          console.log('No saved state found, using initial state');
          const initial = structureStorage.createInitialState();
          setState(initial);
        }
        hasLoadedRef.current = true;
      }).catch(err => {
        console.error('Failed to load from storage:', err);
        // Try localStorage as last resort
        const localStorageKey = `writer_structure_${draftId}`;
        const localStorageData = localStorage.getItem(localStorageKey);
        if (localStorageData) {
          try {
            const parsed = JSON.parse(localStorageData);
            console.log('Loaded from localStorage after storage error:', {
              nodes: Object.keys(parsed.state.nodes).length,
              draftId,
            });
            setState(parsed.state);
          } catch (e) {
            console.error('Failed to parse localStorage data:', e);
            // Try current structure draft as last resort
            const currentStructureDraft = localStorage.getItem('writer_current_structure_draft');
            if (currentStructureDraft) {
              const currentData = localStorage.getItem(`writer_structure_${currentStructureDraft}`);
              if (currentData) {
                try {
                  const parsed = JSON.parse(currentData);
                  console.log('Loaded from current structure draft as fallback');
                  setState(parsed.state);
                  hasLoadedRef.current = true;
                  return;
                } catch (e2) {
                  console.error('Failed to parse current structure draft:', e2);
                }
              }
            }
            setState(structureStorage.createInitialState());
          }
        } else {
          // Try current structure draft as absolute last resort
          const currentStructureDraft = localStorage.getItem('writer_current_structure_draft');
          if (currentStructureDraft) {
            const currentData = localStorage.getItem(`writer_structure_${currentStructureDraft}`);
            if (currentData) {
              try {
                const parsed = JSON.parse(currentData);
                console.log('Loaded from current structure draft as absolute fallback');
                setState(parsed.state);
                hasLoadedRef.current = true;
                return;
              } catch (e) {
                console.error('Failed to parse current structure draft:', e);
              }
            }
          }
          setState(structureStorage.createInitialState());
        }
        hasLoadedRef.current = true;
      });
    }
  }, [draftId, initialState]);

  // Autosave with immediate save on navigation
  useEffect(() => {
    if (draftId && state) {
      if (autosaveTimeoutRef.current !== null) {
        window.clearTimeout(autosaveTimeoutRef.current);
      }

      // Save immediately for critical changes, debounce for minor changes
      const saveState = async () => {
        try {
          await structureStorage.init();
          await structureStorage.saveStructuredDraft(draftId, state);
          console.log('Structure state saved:', draftId);
        } catch (error) {
          console.error('Failed to save structure state:', error);
          // Fallback to localStorage
          try {
            localStorage.setItem(`writer_structure_${draftId}`, JSON.stringify({ 
              id: draftId, 
              state, 
              updatedAt: Date.now() 
            }));
          } catch (e) {
            console.error('Failed to save to localStorage:', e);
          }
        }
      };

      // Debounced save for frequent changes (1 second for faster persistence)
      autosaveTimeoutRef.current = window.setTimeout(() => {
        saveState();
        autosaveTimeoutRef.current = null;
      }, 1000);

      return () => {
        if (autosaveTimeoutRef.current !== null) {
          window.clearTimeout(autosaveTimeoutRef.current);
        }
      };
    }
  }, [state, draftId]);

  // Save immediately before page unload
  useEffect(() => {
    const handleBeforeUnload = async () => {
      if (draftId && state) {
        try {
          await structureStorage.init();
          await structureStorage.saveStructuredDraft(draftId, state);
          // Also save to localStorage as backup
          localStorage.setItem(`writer_structure_${draftId}`, JSON.stringify({ 
            id: draftId, 
            state, 
            updatedAt: Date.now() 
          }));
        } catch (error) {
          console.error('Failed to save on unload:', error);
        }
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [draftId, state]);

  const handleStateChange = useCallback((newState: DocumentState) => {
    setState(newState);
  }, []);

  const handleCreateNode = useCallback((parentId: string | null, kind: NodeKind, position?: number) => {
    try {
      const { state: newState, nodeId } = createNode(state, parentId, kind, position);
      setState(newState);
      setSelectedNodeId(nodeId);
      return nodeId;
    } catch (error: any) {
      alert(error.message);
      return null;
    }
  }, [state]);

  const handleDeleteNode = useCallback((nodeId: string, moveChildrenUp: boolean = false) => {
    if (!confirm('Delete this node? This action cannot be undone.')) {
      return;
    }
    try {
      const newState = deleteNode(state, nodeId, moveChildrenUp);
      setState(newState);
      if (selectedNodeId === nodeId) {
        setSelectedNodeId(null);
      }
    } catch (error: any) {
      alert(error.message);
    }
  }, [state, selectedNodeId]);

  const handleMoveNode = useCallback((nodeId: string, newParentId: string | null, newOrder: number) => {
    try {
      const newState = moveNode(state, nodeId, newParentId, newOrder);
      setState(newState);
    } catch (error: any) {
      alert(error.message);
    }
  }, [state]);

  const handlePromoteNode = useCallback((nodeId: string) => {
    try {
      const newState = promoteNode(state, nodeId);
      setState(newState);
    } catch (error: any) {
      alert(error.message);
    }
  }, [state]);

  const handleDemoteNode = useCallback((nodeId: string) => {
    try {
      const newState = demoteNode(state, nodeId);
      setState(newState);
    } catch (error: any) {
      alert(error.message);
    }
  }, [state]);

  const handleSplitAtCaret = useCallback((nodeId: string, caretPosition: number) => {
    try {
      const { state: newState, newNodeId } = splitAtCaret(state, nodeId, caretPosition);
      setState(newState);
      setSelectedNodeId(newNodeId);
    } catch (error: any) {
      alert(error.message);
    }
  }, [state]);

  const handleMergeWithPrev = useCallback((nodeId: string) => {
    try {
      const newState = mergeWithPrev(state, nodeId);
      setState(newState);
      // Select the merged node (previous sibling)
      const node = state.nodes[nodeId];
      if (node) {
        const siblings = Object.values(state.nodes)
          .filter((n) => n.parentId === node.parentId)
          .sort((a, b) => a.order - b.order);
        const prevSibling = siblings.find((s) => s.order === node.order - 1);
        if (prevSibling) {
          setSelectedNodeId(prevSibling.id);
        }
      }
    } catch (error: any) {
      alert(error.message);
    }
  }, [state]);

  const handleSetLabel = useCallback((nodeId: string, label: string | null) => {
    try {
      const newState = setLabel(state, nodeId, label);
      setState(newState);
    } catch (error: any) {
      alert(error.message);
    }
  }, [state]);

  const handleInsertReference = useCallback((targetNodeId: string) => {
    try {
      const ref = insertReference(state, targetNodeId);
      return ref;
    } catch (error: any) {
      alert(error.message);
      return null;
    }
  }, [state]);

  const handleUpdateNodeContent = useCallback((nodeId: string, content: string) => {
    const newNodes = { ...state.nodes };
    newNodes[nodeId] = {
      ...state.nodes[nodeId],
      content,
    };
    setState({ ...state, nodes: newNodes });
  }, [state]);

  const handleUpdateNodeTitle = useCallback((nodeId: string, title: string) => {
    const newNodes = { ...state.nodes };
    newNodes[nodeId] = {
      ...state.nodes[nodeId],
      title,
    };
    setState({ ...state, nodes: newNodes });
  }, [state]);

  return {
    state,
    selectedNodeId,
    searchQuery,
    setState: handleStateChange,
    setSelectedNodeId,
    setSearchQuery,
    createNode: handleCreateNode,
    deleteNode: handleDeleteNode,
    moveNode: handleMoveNode,
    promoteNode: handlePromoteNode,
    demoteNode: handleDemoteNode,
    splitAtCaret: handleSplitAtCaret,
    mergeWithPrev: handleMergeWithPrev,
    setLabel: handleSetLabel,
    insertReference: handleInsertReference,
    updateNodeContent: handleUpdateNodeContent,
    updateNodeTitle: handleUpdateNodeTitle,
  };
}

