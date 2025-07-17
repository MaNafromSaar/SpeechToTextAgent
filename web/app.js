// API Configuration
const API_BASE_URL = 'http://localhost:8000';
const KNOWLEDGE_BASE_URL = 'http://localhost:8001';

class STTAudioRecorder {
    constructor() {
        this.mediaRecorder = null;
        this.audioContext = null;
        this.analyser = null;
        this.audioStream = null;
        this.recordedChunks = [];
        this.isRecording = false;
        this.recordingDuration = 30;
        this.recordingTimer = null;
        this.waveformCanvas = null;
        this.waveformCtx = null;
        
        this.init();
    }
    
    async init() {
        await this.setupAudioDevices();
        this.setupEventListeners();
        this.setupWaveform();
        await this.loadConfig();
    }
    
    async loadConfig() {
        try {
            const response = await fetch(`${API_BASE_URL}/health`);
            const config = await response.json();
            console.log('Loaded config:', config);
            
            // Load available models for text processing
            await this.loadAvailableModels();
            
            // Setup model status check
            await this.checkModelStatus();
            
        } catch (error) {
            console.error('Failed to load config:', error);
        }
    }
    
    async loadAvailableModels() {
        try {
            const response = await fetch(`${API_BASE_URL}/health`);
            const models = await response.json();
            console.log('Available models:', models);
            
            // Update text model dropdown
            const textModelSelect = document.getElementById('textModel');
            if (textModelSelect && models.text_models && models.text_models.length > 0) {
                textModelSelect.innerHTML = '';
                models.text_models.forEach(model => {
                    const option = document.createElement('option');
                    option.value = model;
                    option.textContent = this.getModelDisplayName(model);
                    textModelSelect.appendChild(option);
                });
                // Set 'mistral:7b' as default if available
                if (models.text_models.includes('mistral:7b')) {
                    textModelSelect.value = 'mistral:7b';
                } else {
                    textModelSelect.selectedIndex = 0;
                }
            }
            
            // Update task types if available
            if (models.task_types && models.task_types.length > 0) {
                const taskTypeSelect = document.getElementById('taskType');
                if (taskTypeSelect) {
                    taskTypeSelect.innerHTML = '';
                    models.task_types.forEach(task => {
                        const option = document.createElement('option');
                        option.value = task.id;
                        option.textContent = task.name;
                        option.title = task.description;
                        taskTypeSelect.appendChild(option);
                    });
                }
            }
            
            // Update languages if available
            if (models.languages && models.languages.length > 0) {
                const languageSelect = document.getElementById('targetLanguage');
                if (languageSelect) {
                    // Keep the auto detect option
                    const autoOption = languageSelect.querySelector('option[value=""]');
                    languageSelect.innerHTML = '';
                    if (autoOption) languageSelect.appendChild(autoOption);
                    
                    models.languages.forEach(lang => {
                        const option = document.createElement('option');
                        option.value = lang;
                        option.textContent = lang;
                        languageSelect.appendChild(option);
                    });
                }
            }
            
            this.availableModels = models;
            
        } catch (error) {
            console.error('Failed to load models:', error);
        }
    }
    
    async checkModelStatus() {
        try {
            const response = await fetch(`${API_BASE_URL}/health`);
            const status = await response.json();
            
            const statusElement = document.getElementById('modelStatus');
            if (statusElement) {
                if (status.whisper === 'available') {
                    if (status.ollama === 'available' || status.text_processing_available) {
                        statusElement.innerHTML = '<i class="fas fa-check-circle text-green-400 mr-1"></i>Local AI Ready';
                        statusElement.className = 'text-sm text-green-400';
                    } else {
                        statusElement.innerHTML = '<i class="fas fa-exclamation-triangle text-yellow-400 mr-1"></i>Transcription only (Install Ollama for text processing)';
                        statusElement.className = 'text-sm text-yellow-400';
                    }
                } else {
                    statusElement.innerHTML = '<i class="fas fa-times-circle text-red-400 mr-1"></i>AI services unavailable';
                    statusElement.className = 'text-sm text-red-400';
                }
            }
            
        } catch (error) {
            console.error('Failed to check model status:', error);
            const statusElement = document.getElementById('modelStatus');
            if (statusElement) {
                statusElement.innerHTML = '<i class="fas fa-times-circle text-red-400 mr-1"></i>Connection error';
                statusElement.className = 'text-sm text-red-400';
            }
        }
    }
    
    getModelDisplayName(model) {
        const modelNames = {
            'llama3': 'Llama 3 (General Purpose)',
            'mistral': 'Mistral (Fast & Efficient)',
            'command-r': 'Command-R (Structured Tasks)',
            'aya': 'Aya (Multilingual)',
            'codellama': 'CodeLlama (Data & Code)',
            'phi3': 'Phi-3 (Lightweight)',
            'gemma': 'Gemma (Google)',
            'qwen': 'Qwen (Alibaba)'
        };
        
        // Extract base model name (e.g., "llama3:8b" -> "llama3")
        const baseName = model.split(':')[0];
        return modelNames[baseName] || model;
    }
    
    async setupAudioDevices() {
        try {
            // Request audio permissions
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            stream.getTracks().forEach(track => track.stop()); // Stop initial stream
            
            // Get available audio input devices
            const devices = await navigator.mediaDevices.enumerateDevices();
            const audioInputs = devices.filter(device => device.kind === 'audioinput');
            
            const audioInputSelect = document.getElementById('audioInput');
            audioInputSelect.innerHTML = '<option value="">Select Input Device...</option>';
            
            audioInputs.forEach(device => {
                const option = document.createElement('option');
                option.value = device.deviceId;
                option.textContent = device.label || `Audio Input ${audioInputs.indexOf(device) + 1}`;
                
                // Highlight SSL2 devices
                if (device.label.toLowerCase().includes('ssl') || 
                    device.label.toLowerCase().includes('solid state logic')) {
                    option.textContent += ' 🎛️';
                    option.style.fontWeight = 'bold';
                    option.style.color = '#8b5cf6';
                }
                
                audioInputSelect.appendChild(option);
            });
            
            // Auto-select SSL2 if available
            const ssl2Device = audioInputs.find(device => 
                device.label.toLowerCase().includes('ssl') ||
                device.label.toLowerCase().includes('solid state logic')
            );
            
            if (ssl2Device) {
                audioInputSelect.value = ssl2Device.deviceId;
                this.showSSL2Status(true);
            }
            
        } catch (error) {
            console.error('Error setting up audio devices:', error);
            this.showError('Failed to access audio devices. Please check permissions.');
        }
    }
    
    showSSL2Status(detected) {
        if (detected) {
            const ssl2Panel = document.querySelector('.ssl2-panel');
            ssl2Panel.style.borderColor = '#10b981';
            ssl2Panel.style.boxShadow = '0 0 20px rgba(16, 185, 129, 0.3)';
            
            // Add SSL2 detected indicator
            const indicator = document.createElement('div');
            indicator.className = 'bg-green-600 text-white px-3 py-1 rounded-full text-sm font-semibold inline-flex items-center';
            indicator.innerHTML = '<i class="fas fa-check-circle mr-2"></i>SSL2 Detected';
            
            const header = ssl2Panel.querySelector('h2');
            if (!header.querySelector('.ssl2-indicator')) {
                indicator.className += ' ssl2-indicator ml-4';
                header.appendChild(indicator);
            }
        }
    }
    
    setupWaveform() {
        this.waveformCanvas = document.getElementById('waveform');
        this.waveformCtx = this.waveformCanvas.getContext('2d');
        
        // Set canvas size
        const rect = this.waveformCanvas.getBoundingClientRect();
        this.waveformCanvas.width = rect.width * window.devicePixelRatio;
        this.waveformCanvas.height = rect.height * window.devicePixelRatio;
        this.waveformCtx.scale(window.devicePixelRatio, window.devicePixelRatio);
    }
    
    setupEventListeners() {
        // Recording controls
        document.getElementById('recordBtn').addEventListener('click', () => this.startRecording());
        document.getElementById('stopBtn').addEventListener('click', () => this.stopRecording());
        document.getElementById('playBtn').addEventListener('click', () => this.playRecording());
        
        // Duration slider
        const durationSlider = document.getElementById('durationSlider');
        const durationDisplay = document.getElementById('durationDisplay');
        
        durationSlider.addEventListener('input', (e) => {
            this.recordingDuration = parseInt(e.target.value);
            durationDisplay.textContent = `${this.recordingDuration}s`;
        });
        
        // File upload
        document.getElementById('uploadBtn').addEventListener('click', () => {
            document.getElementById('fileInput').click();
        });
        
        document.getElementById('fileInput').addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleFileUpload(e.target.files[0]);
            }
        });
        
        // Copy buttons
        document.getElementById('copyTranscription').addEventListener('click', () => {
            this.copyToClipboard('transcriptionResult');
        });
        
        document.getElementById('copyProcessed').addEventListener('click', () => {
            this.copyToClipboard('processedResult');
        });
        
        // Download results
        document.getElementById('downloadResults').addEventListener('click', () => {
            this.downloadResults();
        });
        
        // Editing functionality for processed text
        document.getElementById('editProcessedBtn').addEventListener('click', () => {
            this.startEditingProcessed();
        });
        
        document.getElementById('saveProcessedBtn').addEventListener('click', () => {
            this.saveEditedProcessed();
        });
        
        document.getElementById('cancelEditBtn').addEventListener('click', () => {
            this.cancelEditingProcessed();
        });
        
        // Text processing controls
        const taskTypeSelect = document.getElementById('taskType');
        if (taskTypeSelect) {
            taskTypeSelect.addEventListener('change', (e) => {
                this.toggleTranslationOptions(e.target.value === 'translate');
            });
        }
        
        const processCustomBtn = document.getElementById('processCustomBtn');
        if (processCustomBtn) {
            processCustomBtn.addEventListener('click', () => {
                this.processCustomText();
            });
        }
        
        const clearCustomBtn = document.getElementById('clearCustomBtn');
        if (clearCustomBtn) {
            clearCustomBtn.addEventListener('click', () => {
                document.getElementById('customText').value = '';
            });
        }
        
        const refreshModelsBtn = document.getElementById('refreshModels');
        if (refreshModelsBtn) {
            refreshModelsBtn.addEventListener('click', () => {
                this.loadAvailableModels();
                this.checkModelStatus();
            });
        }
        
        const installModelBtn = document.getElementById('installModel');
        if (installModelBtn) {
            installModelBtn.addEventListener('click', () => {
                this.showInstallModelsDialog();
            });
        }
    }
    
    toggleTranslationOptions(show) {
        const translationOptions = document.getElementById('translationOptions');
        if (show) {
            translationOptions.classList.remove('hidden');
        } else {
            translationOptions.classList.add('hidden');
        }
    }
    
    async startRecording() {
        try {
            const audioInputSelect = document.getElementById('audioInput');
            const sampleRate = parseInt(document.getElementById('sampleRate').value);
            const channels = parseInt(document.getElementById('channels').value);
            
            const constraints = {
                audio: {
                    deviceId: audioInputSelect.value ? { exact: audioInputSelect.value } : undefined,
                    sampleRate: { ideal: sampleRate },
                    channelCount: { ideal: channels },
                    echoCancellation: false,
                    autoGainControl: false,
                    noiseSuppression: false,
                    // Professional audio settings
                    latency: { ideal: 0.01 }, // 10ms latency
                    sampleSize: { ideal: 24 }  // 24-bit depth
                }
            };
            
            this.audioStream = await navigator.mediaDevices.getUserMedia(constraints);
            
            // Setup audio context for level monitoring
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
                sampleRate: sampleRate
            });
            
            const source = this.audioContext.createMediaStreamSource(this.audioStream);
            this.analyser = this.audioContext.createAnalyser();
            this.analyser.fftSize = 256;
            this.analyser.smoothingTimeConstant = 0.8;
            
            source.connect(this.analyser);
            
            // Setup MediaRecorder with high-quality settings
            // Try formats that Whisper supports natively first
            const options = {
                mimeType: 'audio/mp4', // MP4 container with AAC codec
                bitsPerSecond: 256000 // High-quality bitrate
            };
            
            // Fallback chain for different browsers
            if (!MediaRecorder.isTypeSupported(options.mimeType)) {
                options.mimeType = 'audio/wav';
                if (!MediaRecorder.isTypeSupported(options.mimeType)) {
                    options.mimeType = 'audio/ogg;codecs=opus';
                    if (!MediaRecorder.isTypeSupported(options.mimeType)) {
                        options.mimeType = 'audio/webm;codecs=opus';
                        if (!MediaRecorder.isTypeSupported(options.mimeType)) {
                            options.mimeType = 'audio/webm';
                        }
                    }
                }
            }
            
            this.mediaRecorder = new MediaRecorder(this.audioStream, options);
            this.recordedChunks = [];
            this.recordingMimeType = options.mimeType; // Store the actual MIME type used
            
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.recordedChunks.push(event.data);
                }
            };
            
            this.mediaRecorder.onstop = () => {
                this.processRecording();
            };
            
            this.mediaRecorder.start(100); // Record in 100ms chunks for better quality
            this.isRecording = true;
            
            // Update UI
            this.updateRecordingUI(true);
            this.startLevelMonitoring();
            this.startRecordingTimer();
            
        } catch (error) {
            console.error('Error starting recording:', error);
            this.showError('Failed to start recording. Please check your audio device.');
        }
    }
    
    stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;
            
            // Stop all tracks
            if (this.audioStream) {
                this.audioStream.getTracks().forEach(track => track.stop());
            }
            
            // Close audio context
            if (this.audioContext) {
                this.audioContext.close();
            }
            
            // Update UI
            this.updateRecordingUI(false);
            this.stopLevelMonitoring();
            this.stopRecordingTimer();
        }
    }
    
    async processRecording() {
        const blob = new Blob(this.recordedChunks, { type: this.recordingMimeType || 'audio/webm' });
        
        // Convert to WAV for better compatibility
        const audioBuffer = await this.convertToWav(blob);
        
        // Enable play button
        document.getElementById('playBtn').disabled = false;
        
        // Create audio URL for playback
        const audioUrl = URL.createObjectURL(audioBuffer);
        document.getElementById('audioPlayer').src = audioUrl;
        
        // Auto-process if enabled
        await this.sendToAPI(audioBuffer);
    }
    
    async convertToWav(blob) {
        // For now, return the blob as-is
        // In a production environment, you might want to convert to WAV
        return blob;
    }
    
    async sendToAPI(audioBlob) {
        this.showProcessingStatus(true, 'Uploading audio...');
        
        try {
            // Determine file extension based on MIME type
            let filename = 'recording.webm'; // default fallback
            if (this.recordingMimeType) {
                if (this.recordingMimeType.includes('mp4')) filename = 'recording.m4a';
                else if (this.recordingMimeType.includes('wav')) filename = 'recording.wav';
                else if (this.recordingMimeType.includes('ogg')) filename = 'recording.ogg';
                else if (this.recordingMimeType.includes('webm')) filename = 'recording.webm';
            }
            
            const formData = new FormData();
            formData.append('file', audioBlob, filename);
            
            const languageValue = document.getElementById('language').value || 'de';
            console.log('DEBUG: Sending language value:', languageValue);
            formData.append('language', languageValue);
            formData.append('model', document.getElementById('whisperModel').value || 'base');
            
            // Text processing options using local models
            const autoProcess = document.getElementById('autoProcess');
            const enableProcessing = autoProcess ? autoProcess.checked : false;
            
            if (enableProcessing) {
                formData.append('process_text', 'true');
                formData.append('format_type', document.getElementById('taskType').value || 'improve');
                formData.append('text_model', document.getElementById('textModel').value || 'mistral:7b');
                
                const taskType = document.getElementById('taskType').value;
                if (taskType === 'translate') {
                    const targetLang = document.getElementById('targetLanguage').value;
                    if (targetLang) {
                        formData.append('target_language', targetLang);
                    }
                }
            } else {
                formData.append('process_text', 'false');
            }
            
            this.showProcessingStatus(true, 'Processing with local AI...');
            
            // Always use /api/transcribe endpoint
            const response = await fetch(`${API_BASE_URL}/transcribe`, {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
            }
            
            const result = await response.json();
            this.displayResults(result);
            
        } catch (error) {
            console.error('Error sending to API:', error);
            this.showError(`Failed to process audio: ${error.message}`);
        } finally {
            this.showProcessingStatus(false);
        }
    }
    
    async handleFileUpload(file) {
        this.showProcessingStatus(true, 'Uploading file...');
        await this.sendToAPI(file);
    }
    
    startEditingProcessed() {
        const processedResult = document.getElementById('processedResult');
        const processedEditor = document.getElementById('processedEditor');
        const editBtn = document.getElementById('editProcessedBtn');
        const saveBtn = document.getElementById('saveProcessedBtn');
        const cancelBtn = document.getElementById('cancelEditBtn');
        
        // Store original text
        this.originalProcessedText = processedResult.textContent;
        
        // Setup editor
        processedEditor.value = this.originalProcessedText;
        
        // Toggle visibility
        processedResult.classList.add('hidden');
        processedEditor.classList.remove('hidden');
        editBtn.classList.add('hidden');
        saveBtn.classList.remove('hidden');
        cancelBtn.classList.remove('hidden');
        
        // Focus editor
        processedEditor.focus();
    }
    
    cancelEditingProcessed() {
        const processedResult = document.getElementById('processedResult');
        const processedEditor = document.getElementById('processedEditor');
        const editBtn = document.getElementById('editProcessedBtn');
        const saveBtn = document.getElementById('saveProcessedBtn');
        const cancelBtn = document.getElementById('cancelEditBtn');
        
        // Toggle visibility back
        processedResult.classList.remove('hidden');
        processedEditor.classList.add('hidden');
        editBtn.classList.remove('hidden');
        saveBtn.classList.add('hidden');
        cancelBtn.classList.add('hidden');
    }
    
    async saveEditedProcessed() {
        const processedResult = document.getElementById('processedResult');
        const processedEditor = document.getElementById('processedEditor');
        const editBtn = document.getElementById('editProcessedBtn');
        const saveBtn = document.getElementById('saveProcessedBtn');
        const cancelBtn = document.getElementById('cancelEditBtn');
        const learningFeedback = document.getElementById('learningFeedback');
        
        const editedText = processedEditor.value.trim();
        
        if (editedText === this.originalProcessedText) {
            // No changes made, just cancel
            this.cancelEditingProcessed();
            return;
        }
        
        try {
            // Save changes to knowledge base
            await this.saveToKnowledgeBase(editedText);
            
            // Update display
            processedResult.textContent = editedText;
            
            // Update stored results
            if (this.lastResults) {
                this.lastResults.processed_text = editedText;
            }
            
            // Toggle visibility
            processedResult.classList.remove('hidden');
            processedEditor.classList.add('hidden');
            editBtn.classList.remove('hidden');
            saveBtn.classList.add('hidden');
            cancelBtn.classList.add('hidden');
            
            // Show learning feedback
            learningFeedback.classList.remove('hidden');
            setTimeout(() => {
                learningFeedback.classList.add('hidden');
            }, 3000);
            
        } catch (error) {
            console.error('Error saving to knowledge base:', error);
            alert('Failed to save changes to knowledge base. Please try again.');
        }
    }
    
    async saveToKnowledgeBase(editedText) {
        const payload = {
            original_transcription: this.lastResults?.transcription || '',
            original_processed: this.originalProcessedText || '',
            corrected_text: editedText,
            format_type: document.getElementById('taskType')?.value || 'improve',
            timestamp: new Date().toISOString()
        };
        
        const response = await fetch(`${KNOWLEDGE_BASE_URL}/learn`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    }

    displayResults(result) {
        const resultsDiv = document.getElementById('results');
        const transcriptionDiv = document.getElementById('transcriptionResult');
        const processedDiv = document.getElementById('processedResult');
        const processedSection = document.getElementById('processedSection');
        const copyProcessedBtn = document.getElementById('copyProcessed');
        
        // Hide learning feedback from previous session
        const learningFeedback = document.getElementById('learningFeedback');
        learningFeedback.classList.add('hidden');
        
        // Reset edit mode if active
        this.cancelEditingProcessed();
        
        // Show transcription
        transcriptionDiv.textContent = result.original_text;
        
        // Show processed text if available
        if (result.processed_text) {
            processedDiv.textContent = result.processed_text;
            processedSection.classList.remove('hidden');
            copyProcessedBtn.classList.remove('hidden');
        } else {
            processedSection.classList.add('hidden');
            copyProcessedBtn.classList.add('hidden');
        }
        
        // Store results for download
        this.lastResults = result;
        
        // Show results section
        resultsDiv.classList.remove('hidden');
        resultsDiv.scrollIntoView({ behavior: 'smooth' });
    }
    
    startLevelMonitoring() {
        if (!this.analyser) return;
        
        const bufferLength = this.analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        
        const updateLevels = () => {
            if (!this.isRecording) return;
            
            this.analyser.getByteFrequencyData(dataArray);
            
            // Calculate RMS level
            let sum = 0;
            for (let i = 0; i < bufferLength; i++) {
                sum += dataArray[i] * dataArray[i];
            }
            const rms = Math.sqrt(sum / bufferLength);
            const level = (rms / 255) * 100;
            
            // Update level meters (simplified - same level for both channels)
            document.getElementById('level1').style.width = `${level}%`;
            document.getElementById('level2').style.width = `${level}%`;
            
            // Update waveform
            this.drawWaveform(dataArray);
            
            requestAnimationFrame(updateLevels);
        };
        
        updateLevels();
    }
    
    drawWaveform(dataArray) {
        const canvas = this.waveformCanvas;
        const ctx = this.waveformCtx;
        const width = canvas.width / window.devicePixelRatio;
        const height = canvas.height / window.devicePixelRatio;
        
        ctx.fillStyle = '#111827';
        ctx.fillRect(0, 0, width, height);
        
        ctx.lineWidth = 2;
        ctx.strokeStyle = '#10b981';
        ctx.beginPath();
        
        const sliceWidth = width / dataArray.length;
        let x = 0;
        
        for (let i = 0; i < dataArray.length; i++) {
            const v = dataArray[i] / 128.0;
            const y = v * height / 2;
            
            if (i === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
            
            x += sliceWidth;
        }
        
        ctx.stroke();
    }
    
    stopLevelMonitoring() {
        // Levels will stop updating when isRecording becomes false
    }
    
    startRecordingTimer() {
        let timeLeft = this.recordingDuration;
        const statusDiv = document.getElementById('recordingStatus');
        
        this.recordingTimer = setInterval(() => {
            statusDiv.innerHTML = `<span class="recording-indicator text-red-400"><i class="fas fa-circle mr-2"></i>Recording: ${timeLeft}s remaining</span>`;
            timeLeft--;
            
            if (timeLeft < 0) {
                this.stopRecording();
            }
        }, 1000);
    }
    
    stopRecordingTimer() {
        if (this.recordingTimer) {
            clearInterval(this.recordingTimer);
            this.recordingTimer = null;
        }
        
        document.getElementById('recordingStatus').textContent = 'Recording complete';
    }
    
    updateRecordingUI(isRecording) {
        const recordBtn = document.getElementById('recordBtn');
        const stopBtn = document.getElementById('stopBtn');
        
        recordBtn.disabled = isRecording;
        stopBtn.disabled = !isRecording;
        
        if (isRecording) {
            recordBtn.innerHTML = '<i class="fas fa-circle mr-2"></i>Recording...';
            recordBtn.classList.remove('bg-red-600', 'hover:bg-red-700');
            recordBtn.classList.add('bg-gray-600');
        } else {
            recordBtn.innerHTML = '<i class="fas fa-circle mr-2"></i>Start Recording';
            recordBtn.classList.remove('bg-gray-600');
            recordBtn.classList.add('bg-red-600', 'hover:bg-red-700');
        }
    }
    
    playRecording() {
        const audioPlayer = document.getElementById('audioPlayer');
        audioPlayer.play();
    }
    
    showProcessingStatus(show, message = 'Processing...') {
        const statusDiv = document.getElementById('processingStatus');
        const statusText = document.getElementById('statusText');
        
        if (show) {
            statusText.textContent = message;
            statusDiv.classList.remove('hidden');
        } else {
            statusDiv.classList.add('hidden');
        }
    }
    
    showError(message) {
        alert(`Error: ${message}`);
    }
    
    copyToClipboard(elementId) {
        const element = document.getElementById(elementId);
        const text = element.textContent;
        
        navigator.clipboard.writeText(text).then(() => {
            // Show success feedback
            const originalText = element.innerHTML;
            element.innerHTML = '<i class="fas fa-check mr-2"></i>Copied!';
            element.classList.add('bg-green-600');
            
            setTimeout(() => {
                element.innerHTML = originalText;
                element.classList.remove('bg-green-600');
            }, 2000);
        }).catch(err => {
            console.error('Failed to copy: ', err);
        });
    }
    
    downloadResults() {
        if (!this.lastResults) return;
        
        const data = {
            transcription: this.lastResults.transcription,
            processed_text: this.lastResults.processed_text,
            metadata: this.lastResults.metadata,
            timestamp: new Date().toISOString()
        };
        
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `stt-results-${new Date().toISOString().slice(0, 19)}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        
        URL.revokeObjectURL(url);
    }
    
    async processCustomText() {
        const customText = document.getElementById('customText').value.trim();
        if (!customText) {
            this.showError('Please enter text to process.');
            return;
        }
        
        this.showProcessingStatus(true, 'Processing text with local AI...');
        
        try {
            const formData = new FormData();
            formData.append('text', customText);
            formData.append('task_type', document.getElementById('taskType').value || 'improve');
            formData.append('model', document.getElementById('textModel').value || 'mistral:7b');
            
            const taskType = document.getElementById('taskType').value;
            if (taskType === 'translate') {
                const targetLang = document.getElementById('targetLanguage').value;
                if (targetLang) {
                    formData.append('target_language', targetLang);
                }
            }
            
            const response = await fetch(`${API_BASE_URL}/process-text`, {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`HTTP error! status: ${response.status} - ${errorText}`);
            }
            
            const result = await response.json();
            
            // Display results
            const displayResult = {
                transcription: result.original_text,
                processed_text: result.processed_text,
                metadata: {
                    filename: 'custom_text',
                    task_type: result.metadata.task_type,
                    model: result.metadata.model,
                    timestamp: result.metadata.timestamp
                }
            };
            
            this.displayResults(displayResult);
            
        } catch (error) {
            console.error('Error processing text:', error);
            this.showError(`Failed to process text: ${error.message}`);
        } finally {
            this.showProcessingStatus(false);
        }
    }
    
    showInstallModelsDialog() {
        const recommendedModels = ['llama3', 'mistral', 'aya', 'command-r'];
        const modelList = recommendedModels.map(model => `• ${model}`).join('\n');
        
        const message = `To install local AI models, you need Ollama running.\n\nRecommended models:\n${modelList}\n\nWould you like to open Ollama installation instructions?`;
        
        if (confirm(message)) {
            window.open('https://ollama.ai/', '_blank');
        }
    }
    
    toggleTranslationOptions(show) {
        // This method can be used if we have translation-specific UI
        // For now, the target language is always visible
    }
}

// Initialize the application when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new STTAudioRecorder();
});
