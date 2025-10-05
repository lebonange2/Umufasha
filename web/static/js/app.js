// Brainstorming Assistant - Frontend JavaScript

let isRecording = false;
let mediaRecorder = null;
let audioChunks = [];
let sessionId = null;
let microphoneGranted = false;
let audioContext = null;
let mediaStreamSource = null;
let recordingProcessor = null;

// Document mode variables
let currentMode = 'brainstorm';
let currentDocument = null;
let documents = [];
let isDocumentRecording = false;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeSession();
    loadSessionData();
    checkMicrophonePermission();
    setInterval(loadSessionData, 5000); // Refresh every 5 seconds
});

// Initialize session
async function initializeSession() {
    try {
        const response = await fetch('/api/session/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ project_name: 'web-session' })
        });
        
        const data = await response.json();
        if (data.success) {
            sessionId = data.session_id;
            document.getElementById('projectName').textContent = data.project_name;
            showToast('Session started', 'success');
        }
    } catch (error) {
        console.error('Failed to initialize session:', error);
        showToast('Failed to start session', 'error');
    }
}

// Check microphone permission
async function checkMicrophonePermission() {
    const statusEl = document.getElementById('micPermissionStatus');
    const textEl = document.getElementById('micPermissionText');
    const enableBtn = document.getElementById('enableMicBtn');
    const recordBtn = document.getElementById('recordBtn');
    
    // Show status element
    statusEl.style.display = 'block';
    
    // Check if getUserMedia is supported
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        setMicPermissionStatus('getUserMedia not supported in this browser.', 'error', false);
        recordBtn.disabled = true;
        return;
    }
    
    try {
        // Try to check permission using Permissions API (not supported everywhere)
        if (navigator.permissions && navigator.permissions.query) {
            try {
                const permissionStatus = await navigator.permissions.query({ name: 'microphone' });
                
                if (permissionStatus.state === 'granted') {
                    setMicPermissionStatus('Microphone access granted ✅', 'success', true);
                    enableBtn.style.display = 'none';
                    recordBtn.disabled = false;
                    microphoneGranted = true;
                    // Hide status after 3 seconds
                    setTimeout(() => { statusEl.style.display = 'none'; }, 3000);
                } else if (permissionStatus.state === 'denied') {
                    setMicPermissionStatus('Microphone is blocked. Check site/OS settings.', 'error', false);
                    enableBtn.style.display = 'none';
                    recordBtn.disabled = true;
                } else {
                    // "prompt" state - request permission automatically
                    setMicPermissionStatus('Requesting microphone permission...', 'warning', false);
                    await requestMicrophoneAccess();
                }
                
                // Listen for permission changes
                permissionStatus.onchange = () => checkMicrophonePermission();
            } catch (e) {
                // Permissions API query failed, try direct request
                console.log('Permissions API not fully supported, trying direct request');
                await requestMicrophoneAccess();
            }
        } else {
            // Fallback: try direct request
            setMicPermissionStatus('Requesting microphone permission...', 'warning', false);
            await requestMicrophoneAccess();
        }
    } catch (error) {
        console.error('Error checking microphone permission:', error);
        setMicPermissionStatus('Could not check permission: ' + error.message, 'error', false);
        enableBtn.style.display = 'block';
        recordBtn.disabled = true;
    }
}

// Request microphone access
async function requestMicrophoneAccess() {
    const statusEl = document.getElementById('micPermissionStatus');
    const enableBtn = document.getElementById('enableMicBtn');
    const recordBtn = document.getElementById('recordBtn');
    
    try {
        setMicPermissionStatus('Requesting microphone permission...', 'warning', false);
        
        // Request microphone access
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        
        // Stop the stream immediately (we just needed the permission)
        stream.getTracks().forEach(track => track.stop());
        
        // Success
        setMicPermissionStatus('Microphone access granted ✅', 'success', true);
        enableBtn.style.display = 'none';
        recordBtn.disabled = false;
        microphoneGranted = true;
        showToast('Microphone access granted', 'success');
        
        // Hide status after 3 seconds
        setTimeout(() => { statusEl.style.display = 'none'; }, 3000);
    } catch (error) {
        console.error('Microphone access denied:', error);
        setMicPermissionStatus('Access denied: ' + (error.message || error), 'error', false);
        enableBtn.style.display = 'block';
        recordBtn.disabled = true;
        microphoneGranted = false;
        showToast('Microphone access denied', 'error');
    }
}

// Set microphone permission status UI
function setMicPermissionStatus(text, type, granted) {
    const statusEl = document.getElementById('micPermissionStatus');
    const textEl = document.getElementById('micPermissionText');
    const iconEl = statusEl.querySelector('i');
    
    textEl.textContent = text;
    
    // Update styling based on type
    statusEl.style.backgroundColor = 
        type === 'success' ? '#e8f5e9' : 
        type === 'error' ? '#ffebee' : 
        '#fff8e1';
    
    statusEl.style.color = 
        type === 'success' ? '#1b5e20' : 
        type === 'error' ? '#b71c1c' : 
        '#8d6e63';
    
    // Update icon
    iconEl.className = 
        type === 'success' ? 'fas fa-check-circle' : 
        type === 'error' ? 'fas fa-exclamation-circle' : 
        'fas fa-info-circle';
}

// Toggle recording
async function toggleRecording() {
    if (!isRecording) {
        await startRecording();
    } else {
        await stopRecording();
    }
}

// Start recording
async function startRecording() {
    // Check if microphone permission is granted
    if (!microphoneGranted) {
        showToast('Please grant microphone access first', 'warning');
        await checkMicrophonePermission();
        return;
    }
    
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ 
            audio: {
                channelCount: 1,
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true
            } 
        });
        
        // Create MediaRecorder
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];
        
        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };
        
        mediaRecorder.onstop = async () => {
            // Create blob from chunks
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            
            // Convert to PCM and process
            await convertAndProcessAudio(audioBlob, stream);
        };
        
        mediaRecorder.start();
        isRecording = true;
        
        // Update UI
        const btn = document.getElementById('recordBtn');
        btn.classList.add('recording');
        btn.innerHTML = '<i class="fas fa-stop"></i><span>Stop Recording</span>';
        
        document.getElementById('recordingStatus').innerHTML = 
            '<i class="fas fa-circle" style="color: var(--error);"></i> Recording... Speak now!';
        
        showToast('Recording started', 'info');
        
    } catch (error) {
        console.error('Failed to start recording:', error);
        showToast('Microphone access denied', 'error');
        microphoneGranted = false;
        await checkMicrophonePermission();
    }
}

// Stop recording
async function stopRecording() {
    if (mediaRecorder && isRecording) {
        isRecording = false;
        mediaRecorder.stop();
        
        // Update UI
        const btn = document.getElementById('recordBtn');
        btn.classList.remove('recording');
        btn.innerHTML = '<i class="fas fa-microphone"></i><span>Start Recording</span>';
        
        document.getElementById('recordingStatus').innerHTML = 
            '<i class="fas fa-info-circle"></i> Processing audio...';
    }
}

// Convert WebM audio to PCM and process
async function convertAndProcessAudio(audioBlob, stream) {
    try {
        // Stop all tracks
        stream.getTracks().forEach(track => track.stop());
        
        // Create audio context for decoding
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        
        // Read blob as array buffer
        const arrayBuffer = await audioBlob.arrayBuffer();
        
        // Decode audio data
        const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
        
        // Get audio data (mono)
        const channelData = audioBuffer.getChannelData(0);
        
        // Resample to 16kHz if needed
        const targetSampleRate = 16000;
        const currentSampleRate = audioBuffer.sampleRate;
        
        let resampledData;
        if (currentSampleRate !== targetSampleRate) {
            const sampleRateRatio = currentSampleRate / targetSampleRate;
            const newLength = Math.round(channelData.length / sampleRateRatio);
            resampledData = new Float32Array(newLength);
            
            for (let i = 0; i < newLength; i++) {
                const srcIndex = Math.round(i * sampleRateRatio);
                resampledData[i] = channelData[srcIndex];
            }
        } else {
            resampledData = channelData;
        }
        
        // Convert float32 to int16
        const int16Data = new Int16Array(resampledData.length);
        for (let i = 0; i < resampledData.length; i++) {
            const s = Math.max(-1, Math.min(1, resampledData[i]));
            int16Data[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        
        console.log(`Audio converted: ${int16Data.length} samples, ${(int16Data.length/16000).toFixed(2)}s at 16kHz`);
        
        // Process the audio
        await processAudio(int16Data);
        
        // Close audio context
        audioContext.close();
        
    } catch (error) {
        console.error('Failed to convert audio:', error);
        showToast('Failed to convert audio: ' + error.message, 'error');
        document.getElementById('recordingStatus').innerHTML = 
            '<i class="fas fa-info-circle"></i> Click the button to start recording';
        showLoading(false);
    }
}

// Process audio
async function processAudio(audioData) {
    showLoading(true);
    
    try {
        // Convert Int16Array to base64
        const audioBytes = new Uint8Array(audioData.buffer);
        let binary = '';
        for (let i = 0; i < audioBytes.length; i++) {
            binary += String.fromCharCode(audioBytes[i]);
        }
        const base64Audio = btoa(binary);
        
        // Send to server
        const response = await fetch('/api/transcribe', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ audio: base64Audio })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Transcribed successfully', 'success');
            
            // Add to transcript
            addTranscriptEntry('user', data.text);
            
            // Add assistant response if available
            if (data.assistant_response) {
                setTimeout(() => {
                    addTranscriptEntry('assistant', data.assistant_response);
                    updateAssistantResponse(data.assistant_response);
                }, 500);
            }
            
            // Reload session data
            await loadSessionData();
        } else {
            showToast(data.error || 'Transcription failed', 'error');
        }
        
        // Reset status
        document.getElementById('recordingStatus').innerHTML = 
            '<i class="fas fa-info-circle"></i> Click the button to start recording';
        
        showLoading(false);
        
    } catch (error) {
        console.error('Failed to process audio:', error);
        showToast('Failed to process audio', 'error');
        document.getElementById('recordingStatus').innerHTML = 
            '<i class="fas fa-info-circle"></i> Click the button to start recording';
        showLoading(false);
    }
}

// Load session data
async function loadSessionData() {
    try {
        const response = await fetch('/api/session/data');
        const data = await response.json();
        
        if (data.success) {
            updateIdeas(data.ideas);
            updateClusters(data.clusters);
            updateActions(data.actions);
            updateStats(data.stats);
        }
    } catch (error) {
        console.error('Failed to load session data:', error);
    }
}

// Update ideas list
function updateIdeas(ideas) {
    const list = document.getElementById('ideasList');
    
    if (ideas.length === 0) {
        list.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-lightbulb"></i>
                <p>Start recording to capture ideas</p>
            </div>
        `;
        return;
    }
    
    list.innerHTML = ideas.map(idea => `
        <div class="idea-item ${idea.promoted ? 'promoted' : ''}">
            <div class="idea-header">
                <div class="idea-text">${escapeHtml(idea.text)}</div>
                <div class="idea-actions">
                    <button class="idea-action-btn" onclick="promoteIdea('${idea.id}')" title="Promote">
                        <i class="fas fa-star"></i>
                    </button>
                    <button class="idea-action-btn" onclick="deleteIdea('${idea.id}')" title="Delete">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
            ${idea.tags && idea.tags.length > 0 ? `
                <div class="idea-tags">
                    ${idea.tags.map(tag => `<span class="tag">${escapeHtml(tag)}</span>`).join('')}
                </div>
            ` : ''}
        </div>
    `).join('');
    
    document.getElementById('ideasCount').textContent = ideas.length;
}

// Update clusters list
function updateClusters(clusters) {
    const list = document.getElementById('clustersList');
    
    if (clusters.length === 0) {
        list.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-folder-tree"></i>
                <p>Clusters will be generated automatically</p>
            </div>
        `;
        return;
    }
    
    list.innerHTML = clusters.map(cluster => `
        <div class="cluster-item">
            <div class="cluster-name">
                <i class="fas fa-folder"></i>
                ${escapeHtml(cluster.name)}
            </div>
            <div class="cluster-count">${cluster.idea_ids.length} ideas</div>
        </div>
    `).join('');
    
    document.getElementById('clustersCount').textContent = clusters.length;
}

// Update actions list
function updateActions(actions) {
    const list = document.getElementById('actionsList');
    
    const activeActions = actions.filter(a => !a.completed);
    
    if (activeActions.length === 0) {
        list.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-tasks"></i>
                <p>Action items will appear here</p>
            </div>
        `;
        return;
    }
    
    list.innerHTML = activeActions.map(action => `
        <div class="action-item ${action.completed ? 'completed' : ''}">
            <input type="checkbox" class="action-checkbox" ${action.completed ? 'checked' : ''}>
            <div class="action-text">${escapeHtml(action.text)}</div>
        </div>
    `).join('');
    
    document.getElementById('actionsCount').textContent = activeActions.length;
}

// Update stats
function updateStats(stats) {
    document.getElementById('statIdeas').textContent = stats.total_ideas || 0;
    document.getElementById('statClusters').textContent = stats.total_clusters || 0;
    document.getElementById('statActions').textContent = stats.total_actions || 0;
    document.getElementById('statKeyIdeas').textContent = stats.key_ideas || 0;
}

// Add transcript entry
function addTranscriptEntry(speaker, text) {
    const list = document.getElementById('transcriptList');
    
    // Remove empty state if present
    const emptyState = list.querySelector('.empty-state');
    if (emptyState) {
        list.innerHTML = '';
    }
    
    const entry = document.createElement('div');
    entry.className = `transcript-entry ${speaker}`;
    entry.innerHTML = `
        <div class="transcript-speaker">
            <i class="fas fa-${speaker === 'user' ? 'user' : 'robot'}"></i>
            ${speaker === 'user' ? 'You' : 'AI Assistant'}
        </div>
        <div class="transcript-text">${escapeHtml(text)}</div>
        <div class="transcript-time">${new Date().toLocaleTimeString()}</div>
    `;
    
    list.appendChild(entry);
    list.scrollTop = list.scrollHeight;
}

// Update assistant response
function updateAssistantResponse(text) {
    const container = document.getElementById('assistantResponse');
    container.innerHTML = `<div class="assistant-message">${escapeHtml(text)}</div>`;
}

// Promote idea
async function promoteIdea(ideaId) {
    try {
        const response = await fetch('/api/idea/promote', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ idea_id: ideaId })
        });
        
        const data = await response.json();
        if (data.success) {
            showToast('Idea promoted', 'success');
            await loadSessionData();
        }
    } catch (error) {
        console.error('Failed to promote idea:', error);
        showToast('Failed to promote idea', 'error');
    }
}

// Delete idea
async function deleteIdea(ideaId) {
    if (!confirm('Are you sure you want to delete this idea?')) return;
    
    try {
        const response = await fetch('/api/idea/delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ idea_id: ideaId })
        });
        
        const data = await response.json();
        if (data.success) {
            showToast('Idea deleted', 'success');
            await loadSessionData();
        }
    } catch (error) {
        console.error('Failed to delete idea:', error);
        showToast('Failed to delete idea', 'error');
    }
}

// Export session
async function exportSession(format) {
    showLoading(true);
    
    try {
        const response = await fetch(`/api/export/${format}`);
        const data = await response.json();
        
        if (data.success) {
            showToast(`Exported to ${format.toUpperCase()}`, 'success');
            closeModal('exportModal');
        } else {
            showToast('Export failed', 'error');
        }
    } catch (error) {
        console.error('Failed to export:', error);
        showToast('Export failed', 'error');
    } finally {
        showLoading(false);
    }
}

// Show/hide modals
function showExportModal() {
    document.getElementById('exportModal').classList.add('active');
}

function showSettingsModal() {
    showToast('Settings coming soon', 'info');
}

function showAddActionModal() {
    const text = prompt('Enter action item:');
    if (text) {
        addAction(text);
    }
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

// Add action
async function addAction(text) {
    try {
        const response = await fetch('/api/action/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });
        
        const data = await response.json();
        if (data.success) {
            showToast('Action added', 'success');
            await loadSessionData();
        }
    } catch (error) {
        console.error('Failed to add action:', error);
        showToast('Failed to add action', 'error');
    }
}

// Filter ideas
function filterIdeas(filter) {
    // TODO: Implement filtering
    showToast(`Filter: ${filter}`, 'info');
}

// Show loading overlay
function showLoading(show) {
    const overlay = document.getElementById('loadingOverlay');
    if (show) {
        overlay.classList.add('active');
    } else {
        overlay.classList.remove('active');
    }
}

// Show toast notification
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Utility: Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Close modals on outside click
window.onclick = function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.classList.remove('active');
    }
}

// ============================================
// DOCUMENT MODE FUNCTIONS
// ============================================

// Switch between brainstorm and document mode
function switchMode(mode) {
    currentMode = mode;
    
    // Update UI
    document.getElementById('brainstormView').classList.toggle('active', mode === 'brainstorm');
    document.getElementById('documentView').classList.toggle('active', mode === 'document');
    document.getElementById('brainstormView').style.display = mode === 'brainstorm' ? 'block' : 'none';
    document.getElementById('documentView').style.display = mode === 'document' ? 'block' : 'none';
    
    document.getElementById('brainstormModeBtn').classList.toggle('active', mode === 'brainstorm');
    document.getElementById('documentModeBtn').classList.toggle('active', mode === 'document');
    
    if (mode === 'document') {
        loadDocuments();
    }
}

// Load all documents
async function loadDocuments() {
    try {
        const response = await fetch('/api/documents/list');
        const data = await response.json();
        
        if (data.success) {
            documents = data.documents;
            renderDocumentList();
        }
    } catch (error) {
        console.error('Failed to load documents:', error);
        showToast('Failed to load documents', 'error');
    }
}

// Render document list
function renderDocumentList() {
    const list = document.getElementById('documentList');
    
    if (documents.length === 0) {
        list.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-file-alt"></i>
                <p>No documents yet</p>
            </div>
        `;
        return;
    }
    
    list.innerHTML = documents.map(doc => `
        <div class="document-item ${currentDocument && currentDocument.id === doc.id ? 'active' : ''}" 
             onclick="loadDocument('${doc.id}')">
            <div class="document-item-title">${escapeHtml(doc.title)}</div>
            <div class="document-item-meta">
                ${doc.word_count} words • ${new Date(doc.updated_at).toLocaleDateString()}
            </div>
        </div>
    `).join('');
}

// Create new document
async function createNewDocument() {
    try {
        console.log('Creating new document...');
        const response = await fetch('/api/documents/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title: 'Untitled Document', content: '' })
        });
        
        const data = await response.json();
        console.log('Create document response:', data);
        
        if (data.success) {
            currentDocument = data.document;
            console.log('Document created:', currentDocument);
            await loadDocuments();
            displayDocument(currentDocument);
            showToast('New document created', 'success');
        } else {
            console.error('Document creation failed:', data.error);
            showToast('Failed to create document: ' + (data.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        console.error('Failed to create document:', error);
        showToast('Failed to create document: ' + error.message, 'error');
    }
}

// Load a specific document
async function loadDocument(docId) {
    try {
        const response = await fetch(`/api/documents/get/${docId}`);
        const data = await response.json();
        
        if (data.success) {
            currentDocument = data.document;
            displayDocument(currentDocument);
            renderDocumentList();
        }
    } catch (error) {
        console.error('Failed to load document:', error);
        showToast('Failed to load document', 'error');
    }
}

// Display document in editor
function displayDocument(doc) {
    document.getElementById('documentTitle').value = doc.title;
    document.getElementById('documentEditor').value = doc.content;
    updateWordCount();
    document.getElementById('lastSaved').textContent = new Date(doc.updated_at).toLocaleString();
}

// Save current document
async function saveDocument() {
    if (!currentDocument) {
        showToast('No document to save', 'warning');
        return;
    }
    
    const title = document.getElementById('documentTitle').value;
    const content = document.getElementById('documentEditor').value;
    
    try {
        console.log('Saving document:', currentDocument.id, 'Title:', title, 'Content length:', content.length);
        const response = await fetch(`/api/documents/save/${currentDocument.id}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, content })
        });
        
        const data = await response.json();
        console.log('Save response:', data);
        
        if (data.success) {
            currentDocument = data.document;
            document.getElementById('lastSaved').textContent = new Date().toLocaleString();
            await loadDocuments();
            showToast('Document saved', 'success');
        } else {
            console.error('Save failed:', data.error);
            showToast('Failed to save: ' + (data.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        console.error('Failed to save document:', error);
        showToast('Failed to save document: ' + error.message, 'error');
    }
}

// Delete current document
async function deleteDocument() {
    if (!currentDocument) {
        showToast('No document to delete', 'warning');
        return;
    }
    
    if (!confirm(`Delete "${currentDocument.title}"?`)) return;
    
    try {
        const response = await fetch(`/api/documents/delete/${currentDocument.id}`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentDocument = null;
            document.getElementById('documentTitle').value = '';
            document.getElementById('documentEditor').value = '';
            await loadDocuments();
            showToast('Document deleted', 'success');
        }
    } catch (error) {
        console.error('Failed to delete document:', error);
        showToast('Failed to delete document', 'error');
    }
}

// Toggle document recording
async function toggleDocumentRecording() {
    if (!microphoneGranted) {
        showToast('Please grant microphone access first', 'warning');
        await checkMicrophonePermission();
        return;
    }
    
    // Check if a document is open
    if (!currentDocument && !isDocumentRecording) {
        showToast('Please create or open a document first', 'warning');
        return;
    }
    
    if (!isDocumentRecording) {
        await startDocumentRecording();
    } else {
        await stopDocumentRecording();
    }
}

// Start document recording
async function startDocumentRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ 
            audio: {
                channelCount: 1,
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true
            } 
        });
        
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];
        
        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };
        
        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            await convertAndProcessDocumentAudio(audioBlob, stream);
        };
        
        mediaRecorder.start();
        isDocumentRecording = true;
        
        // Update UI
        const btn = document.getElementById('recordBtnDoc');
        btn.classList.add('recording');
        btn.innerHTML = '<i class="fas fa-stop"></i><span>Stop Recording</span>';
        
        document.getElementById('recordingStatusDoc').innerHTML = 
            '<i class="fas fa-circle" style="color: var(--error);"></i> Recording... Speak your research notes';
        
        showToast('Recording started', 'info');
        
    } catch (error) {
        console.error('Failed to start recording:', error);
        showToast('Microphone access denied', 'error');
    }
}

// Stop document recording
async function stopDocumentRecording() {
    if (mediaRecorder && isDocumentRecording) {
        isDocumentRecording = false;
        mediaRecorder.stop();
        
        // Update UI
        const btn = document.getElementById('recordBtnDoc');
        btn.classList.remove('recording');
        btn.innerHTML = '<i class="fas fa-microphone"></i><span>Start Recording</span>';
        
        document.getElementById('recordingStatusDoc').innerHTML = 
            '<i class="fas fa-info-circle"></i> Processing audio...';
    }
}

// Convert and process document audio
async function convertAndProcessDocumentAudio(audioBlob, stream) {
    try {
        stream.getTracks().forEach(track => track.stop());
        
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const arrayBuffer = await audioBlob.arrayBuffer();
        const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
        const channelData = audioBuffer.getChannelData(0);
        
        // Resample to 16kHz
        const targetSampleRate = 16000;
        const currentSampleRate = audioBuffer.sampleRate;
        
        let resampledData;
        if (currentSampleRate !== targetSampleRate) {
            const sampleRateRatio = currentSampleRate / targetSampleRate;
            const newLength = Math.round(channelData.length / sampleRateRatio);
            resampledData = new Float32Array(newLength);
            
            for (let i = 0; i < newLength; i++) {
                const srcIndex = Math.round(i * sampleRateRatio);
                resampledData[i] = channelData[srcIndex];
            }
        } else {
            resampledData = channelData;
        }
        
        // Convert float32 to int16
        const int16Data = new Int16Array(resampledData.length);
        for (let i = 0; i < resampledData.length; i++) {
            const s = Math.max(-1, Math.min(1, resampledData[i]));
            int16Data[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        
        console.log(`Document audio: ${int16Data.length} samples, ${(int16Data.length/16000).toFixed(2)}s`);
        
        // Transcribe and append to document
        await transcribeAndAppendToDocument(int16Data);
        
        audioContext.close();
        
    } catch (error) {
        console.error('Failed to convert audio:', error);
        showToast('Failed to convert audio: ' + error.message, 'error');
        document.getElementById('recordingStatusDoc').innerHTML = 
            '<i class="fas fa-info-circle"></i> Click to record research notes';
    }
}

// Transcribe and append to document
async function transcribeAndAppendToDocument(audioData) {
    showLoading(true);
    
    try {
        // Convert Int16Array to base64
        const audioBytes = new Uint8Array(audioData.buffer);
        let binary = '';
        for (let i = 0; i < audioBytes.length; i++) {
            binary += String.fromCharCode(audioBytes[i]);
        }
        const base64Audio = btoa(binary);
        
        console.log('Sending audio to document transcription endpoint...');
        
        // Send to document-specific transcription endpoint (doesn't save to brainstorm)
        const response = await fetch('/api/documents/transcribe', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ audio: base64Audio })
        });
        
        const data = await response.json();
        console.log('Document transcription response:', data);
        
        if (data.success) {
            // Append transcribed text to document
            const editor = document.getElementById('documentEditor');
            const currentContent = editor.value;
            const newContent = currentContent + (currentContent ? '\n\n' : '') + data.text;
            editor.value = newContent;
            
            updateWordCount();
            showToast('Text added to document', 'success');
            
            // Auto-save
            if (currentDocument) {
                console.log('Auto-saving document after transcription...');
                await saveDocument();
            } else {
                console.warn('No current document to save to');
                showToast('Please create a document first', 'warning');
            }
        } else {
            showToast(data.error || 'Transcription failed', 'error');
        }
        
        document.getElementById('recordingStatusDoc').innerHTML = 
            '<i class="fas fa-info-circle"></i> Click to record research notes';
        
        showLoading(false);
        
    } catch (error) {
        console.error('Failed to transcribe:', error);
        showToast('Failed to transcribe audio', 'error');
        document.getElementById('recordingStatusDoc').innerHTML = 
            '<i class="fas fa-info-circle"></i> Click to record research notes';
        showLoading(false);
    }
}

// Update word count
function updateWordCount() {
    const content = document.getElementById('documentEditor').value;
    const words = content.trim().split(/\s+/).filter(w => w.length > 0).length;
    document.getElementById('wordCount').textContent = words;
}

// Show document export modal
function showDocumentExportModal() {
    if (!currentDocument) {
        showToast('No document to export', 'warning');
        return;
    }
    document.getElementById('documentExportModal').classList.add('active');
}

// Export document
async function exportDocument(format) {
    if (!currentDocument) {
        showToast('No document to export', 'warning');
        return;
    }
    
    showLoading(true);
    
    try {
        console.log(`Exporting document ${currentDocument.id} as ${format}...`);
        const response = await fetch(`/api/documents/export/${currentDocument.id}/${format}`);
        const data = await response.json();
        
        console.log('Export response:', data);
        
        if (data.success) {
            showToast(`Exported to ${data.filename}`, 'success');
            closeModal('documentExportModal');
        } else {
            showToast('Export failed: ' + (data.error || 'Unknown error'), 'error');
        }
    } catch (error) {
        console.error('Failed to export document:', error);
        showToast('Export failed: ' + error.message, 'error');
    } finally {
        showLoading(false);
    }
}

// Auto-update word count on typing
document.addEventListener('DOMContentLoaded', () => {
    const editor = document.getElementById('documentEditor');
    if (editor) {
        editor.addEventListener('input', updateWordCount);
    }
});
