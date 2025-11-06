/**
 * VERITAS SSE Client
 * ==================
 * 
 * EventSource-based client for Server-Sent Events.
 * 
 * Features:
 * - Auto-reconnect (built-in)
 * - Event replay (Last-Event-ID)
 * - Multiple event types
 * - Error handling
 * 
 * Usage:
 *   import { VeritasSSEClient } from './services/sse_client.js';
 *   
 *   const client = new VeritasSSEClient('session_123');
 *   client.onProgress((data) => console.log(data));
 *   client.connect();
 * 
 * Created: 2025-10-31
 */

export class VeritasSSEClient {
    constructor(sessionId, options = {}) {
        this.sessionId = sessionId;
        this.baseUrl = options.baseUrl || 'http://localhost:5000';
        this.eventSource = null;
        this.handlers = {
            progress: [],
            quality: [],
            error: [],
            complete: []
        };
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = options.maxReconnectAttempts || 10;
        this.connected = false;
    }
    
    /**
     * Connect to SSE stream.
     */
    connect() {
        const url = `${this.baseUrl}/api/sse/progress/${this.sessionId}`;
        
        console.log('[SSE] Connecting to', url);
        
        this.eventSource = new EventSource(url);
        
        // Plan Events
        this.eventSource.addEventListener('plan_started', (e) => {
            const data = JSON.parse(e.data);
            console.log('[SSE] Plan started', data);
            this.handlers.progress.forEach(h => h({
                type: 'plan_started',
                ...data
            }));
        });
        
        this.eventSource.addEventListener('plan_completed', (e) => {
            const data = JSON.parse(e.data);
            console.log('[SSE] Plan completed', data);
            this.handlers.progress.forEach(h => h({
                type: 'plan_completed',
                ...data
            }));
            this.handlers.complete.forEach(h => h(data));
        });
        
        // Step Events
        this.eventSource.addEventListener('step_started', (e) => {
            const data = JSON.parse(e.data);
            console.log('[SSE] Step started', data);
            this.handlers.progress.forEach(h => h({
                type: 'step_started',
                ...data
            }));
        });
        
        this.eventSource.addEventListener('step_progress', (e) => {
            const data = JSON.parse(e.data);
            console.log('[SSE] Step progress', data);
            this.handlers.progress.forEach(h => h({
                type: 'step_progress',
                ...data
            }));
        });
        
        this.eventSource.addEventListener('step_completed', (e) => {
            const data = JSON.parse(e.data);
            console.log('[SSE] Step completed', data);
            this.handlers.progress.forEach(h => h({
                type: 'step_completed',
                ...data
            }));
        });
        
        // Quality Events
        this.eventSource.addEventListener('quality_check', (e) => {
            const data = JSON.parse(e.data);
            console.log('[SSE] Quality check', data);
            this.handlers.quality.forEach(h => h(data));
        });
        
        // Error Events
        this.eventSource.addEventListener('error', (e) => {
            const data = e.data ? JSON.parse(e.data) : {error: 'Unknown error'};
            console.error('[SSE] Error event', data);
            this.handlers.error.forEach(h => h(data));
        });
        
        // Connection Events
        this.eventSource.onopen = () => {
            console.log('[SSE] Connected to', url);
            this.connected = true;
            this.reconnectAttempts = 0;
        };
        
        this.eventSource.onerror = (e) => {
            console.error('[SSE] Connection error', e);
            this.connected = false;
            this.reconnectAttempts++;
            
            if (this.reconnectAttempts >= this.maxReconnectAttempts) {
                console.error('[SSE] Max reconnect attempts reached');
                this.disconnect();
                this.handlers.error.forEach(h => h({
                    error: 'Max reconnect attempts reached',
                    attempts: this.reconnectAttempts
                }));
            } else {
                console.log(`[SSE] Reconnecting (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
                // EventSource auto-reconnects, no manual intervention needed
            }
        };
    }
    
    /**
     * Register progress handler.
     * 
     * @param {Function} handler - Callback function
     * @returns {VeritasSSEClient} - This instance for chaining
     */
    onProgress(handler) {
        this.handlers.progress.push(handler);
        return this;
    }
    
    /**
     * Register quality gate handler.
     * 
     * @param {Function} handler - Callback function
     * @returns {VeritasSSEClient} - This instance for chaining
     */
    onQuality(handler) {
        this.handlers.quality.push(handler);
        return this;
    }
    
    /**
     * Register error handler.
     * 
     * @param {Function} handler - Callback function
     * @returns {VeritasSSEClient} - This instance for chaining
     */
    onError(handler) {
        this.handlers.error.push(handler);
        return this;
    }
    
    /**
     * Register completion handler.
     * 
     * @param {Function} handler - Callback function
     * @returns {VeritasSSEClient} - This instance for chaining
     */
    onComplete(handler) {
        this.handlers.complete.push(handler);
        return this;
    }
    
    /**
     * Disconnect from SSE stream.
     */
    disconnect() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
            this.connected = false;
            console.log('[SSE] Disconnected');
        }
    }
    
    /**
     * Check if connected.
     * 
     * @returns {boolean} - Connection status
     */
    isConnected() {
        return this.connected;
    }
}


/**
 * VERITAS Metrics SSE Client
 * ==========================
 * 
 * Stream system metrics (CPU, Memory, Database status).
 * 
 * Usage:
 *   const metrics = new VeritasMetricsSSEClient();
 *   metrics.onMetrics((data) => {
 *       console.log('CPU:', data.cpu_percent, '%');
 *       console.log('Memory:', data.memory_mb, 'MB');
 *   });
 *   metrics.connect();
 */
export class VeritasMetricsSSEClient {
    constructor(options = {}) {
        this.baseUrl = options.baseUrl || 'http://localhost:5000';
        this.interval = options.interval || 2;  // Update interval in seconds
        this.eventSource = null;
        this.handlers = [];
        this.connected = false;
    }
    
    /**
     * Connect to metrics stream.
     */
    connect() {
        const url = `${this.baseUrl}/api/sse/metrics?interval=${this.interval}`;
        
        console.log('[SSE Metrics] Connecting to', url);
        
        this.eventSource = new EventSource(url);
        
        this.eventSource.addEventListener('metrics_update', (e) => {
            const metrics = JSON.parse(e.data);
            this.handlers.forEach(h => h(metrics));
        });
        
        this.eventSource.onopen = () => {
            console.log('[SSE Metrics] Connected');
            this.connected = true;
        };
        
        this.eventSource.onerror = (e) => {
            console.error('[SSE Metrics] Connection error', e);
            this.connected = false;
        };
    }
    
    /**
     * Register metrics handler.
     * 
     * @param {Function} handler - Callback function
     * @returns {VeritasMetricsSSEClient} - This instance for chaining
     */
    onMetrics(handler) {
        this.handlers.push(handler);
        return this;
    }
    
    /**
     * Disconnect from metrics stream.
     */
    disconnect() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
            this.connected = false;
            console.log('[SSE Metrics] Disconnected');
        }
    }
    
    /**
     * Check if connected.
     * 
     * @returns {boolean} - Connection status
     */
    isConnected() {
        return this.connected;
    }
}


/**
 * VERITAS Job Progress SSE Client
 * ================================
 * 
 * Stream UDS3 job progress (file upload/processing).
 * 
 * Usage:
 *   const job = new VeritasJobProgressSSEClient('job_123');
 *   job.onProgress((data) => {
 *       updateProgressBar(data.percentage);
 *       console.log(`${data.files_processed}/${data.files_total} files`);
 *   });
 *   job.connect();
 */
export class VeritasJobProgressSSEClient {
    constructor(jobId, options = {}) {
        this.jobId = jobId;
        this.baseUrl = options.baseUrl || 'http://localhost:5000';
        this.eventSource = null;
        this.handlers = {
            progress: [],
            completed: [],
            failed: [],
            error: []
        };
        this.connected = false;
    }
    
    /**
     * Connect to job progress stream.
     */
    connect() {
        const url = `${this.baseUrl}/api/sse/jobs/${this.jobId}`;
        
        console.log('[SSE Job] Connecting to', url);
        
        this.eventSource = new EventSource(url);
        
        this.eventSource.addEventListener('job_progress', (e) => {
            const data = JSON.parse(e.data);
            console.log('[SSE Job] Progress', data);
            this.handlers.progress.forEach(h => h(data));
        });
        
        this.eventSource.addEventListener('job_completed', (e) => {
            const data = JSON.parse(e.data);
            console.log('[SSE Job] Completed', data);
            this.handlers.completed.forEach(h => h(data));
            this.disconnect();  // Auto-disconnect on completion
        });
        
        this.eventSource.addEventListener('job_failed', (e) => {
            const data = JSON.parse(e.data);
            console.error('[SSE Job] Failed', data);
            this.handlers.failed.forEach(h => h(data));
            this.disconnect();  // Auto-disconnect on failure
        });
        
        this.eventSource.addEventListener('error', (e) => {
            const data = e.data ? JSON.parse(e.data) : {error: 'Unknown error'};
            console.error('[SSE Job] Error', data);
            this.handlers.error.forEach(h => h(data));
        });
        
        this.eventSource.onopen = () => {
            console.log('[SSE Job] Connected');
            this.connected = true;
        };
        
        this.eventSource.onerror = (e) => {
            console.error('[SSE Job] Connection error', e);
            this.connected = false;
        };
    }
    
    /**
     * Register progress handler.
     */
    onProgress(handler) {
        this.handlers.progress.push(handler);
        return this;
    }
    
    /**
     * Register completion handler.
     */
    onCompleted(handler) {
        this.handlers.completed.push(handler);
        return this;
    }
    
    /**
     * Register failure handler.
     */
    onFailed(handler) {
        this.handlers.failed.push(handler);
        return this;
    }
    
    /**
     * Register error handler.
     */
    onError(handler) {
        this.handlers.error.push(handler);
        return this;
    }
    
    /**
     * Disconnect from job stream.
     */
    disconnect() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
            this.connected = false;
            console.log('[SSE Job] Disconnected');
        }
    }
    
    /**
     * Check if connected.
     */
    isConnected() {
        return this.connected;
    }
}
