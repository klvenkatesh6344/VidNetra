/**
 * VIDNETRA - SECURING EVERY LEARNING MOMENT
 * Client-side Audio Synthesizer, Real-time Dashboard Polling & Webcam Helpers
 */

// -------------------------------------------------------------
// Web Audio API Synthesizer for High-Tech Sound Effects
// -------------------------------------------------------------
const AudioAlerts = {
    ctx: null,
    
    init() {
        if (!this.ctx) {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            this.ctx = new AudioContext();
        }
    },
    
    // Pleasant double-chime for verified attendance
    playSuccessChime() {
        try {
            this.init();
            const now = this.ctx.currentTime;
            
            // First note (E5)
            const osc1 = this.ctx.createOscillator();
            const gain1 = this.ctx.createGain();
            osc1.type = 'sine';
            osc1.frequency.setValueAtTime(659.25, now);
            gain1.gain.setValueAtTime(0.15, now);
            gain1.gain.exponentialRampToValueAtTime(0.001, now + 0.25);
            osc1.connect(gain1);
            gain1.connect(this.ctx.destination);
            osc1.start(now);
            osc1.stop(now + 0.25);
            
            // Second note (G#5)
            const osc2 = this.ctx.createOscillator();
            const gain2 = this.ctx.createGain();
            osc2.type = 'sine';
            osc2.frequency.setValueAtTime(830.61, now + 0.12);
            gain2.gain.setValueAtTime(0.2, now + 0.12);
            gain2.gain.exponentialRampToValueAtTime(0.001, now + 0.4);
            osc2.connect(gain2);
            gain2.connect(this.ctx.destination);
            osc2.start(now + 0.12);
            osc2.stop(now + 0.4);
        } catch (e) {
            console.log('Audio alert blocked or unsupported:', e);
        }
    },
    
    // Urgent warning buzzer for phone detection or stampede warning
    playWarningBeep() {
        try {
            this.init();
            const now = this.ctx.currentTime;
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();
            
            osc.type = 'sawtooth';
            osc.frequency.setValueAtTime(880, now); // A5
            gain.gain.setValueAtTime(0.2, now);
            gain.gain.exponentialRampToValueAtTime(0.01, now + 0.35);
            
            osc.connect(gain);
            gain.connect(this.ctx.destination);
            osc.start(now);
            osc.stop(now + 0.35);
        } catch (e) {
            console.log('Audio warning blocked:', e);
        }
    }
};

// -------------------------------------------------------------
// Live Digital Clock
// -------------------------------------------------------------
function updateLiveClock() {
    const clockEl = document.getElementById('liveClock');
    if (clockEl) {
        const now = new Date();
        clockEl.textContent = now.toLocaleTimeString('en-US', { 
            hour12: true, 
            hour: '2-digit', 
            minute: '2-digit', 
            second: '2-digit' 
        });
    }
}
setInterval(updateLiveClock, 1000);
updateLiveClock();

// -------------------------------------------------------------
// Webcam Enrollment Studio Helper
// -------------------------------------------------------------
let enrollWebcamStream = null;

function initEnrollWebcam() {
    const video = document.getElementById('enrollVideo');
    if (!video) return;

    navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 480 } })
        .then(stream => {
            enrollWebcamStream = stream;
            video.srcObject = stream;
            video.play();
        })
        .catch(err => {
            console.error("Webcam access error:", err);
            const statusEl = document.getElementById('cameraStatus');
            if (statusEl) {
                statusEl.innerHTML = '<span class="text-danger">Webcam access denied or unavailable. Please use file upload below.</span>';
            }
        });
}

function captureEnrollSnapshot() {
    const video = document.getElementById('enrollVideo');
    const canvas = document.getElementById('enrollCanvas');
    const photoPreview = document.getElementById('photoPreview');
    const b64Input = document.getElementById('imageB64Input');
    
    if (!video || !canvas) return;
    
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    const dataURL = canvas.toDataURL('image/jpeg', 0.9);
    if (photoPreview) {
        photoPreview.src = dataURL;
        photoPreview.style.display = 'block';
    }
    if (video) video.style.display = 'none';
    if (b64Input) b64Input.value = dataURL;
    
    const retakeBtn = document.getElementById('retakeBtn');
    const captureBtn = document.getElementById('captureBtn');
    if (retakeBtn) retakeBtn.style.display = 'inline-flex';
    if (captureBtn) captureBtn.style.display = 'none';
}

function retakeEnrollSnapshot() {
    const video = document.getElementById('enrollVideo');
    const photoPreview = document.getElementById('photoPreview');
    const b64Input = document.getElementById('imageB64Input');
    
    if (photoPreview) photoPreview.style.display = 'none';
    if (video) video.style.display = 'block';
    if (b64Input) b64Input.value = '';
    
    const retakeBtn = document.getElementById('retakeBtn');
    const captureBtn = document.getElementById('captureBtn');
    if (retakeBtn) retakeBtn.style.display = 'none';
    if (captureBtn) captureBtn.style.display = 'inline-flex';
}

// -------------------------------------------------------------
// Attendance Live Poller
// -------------------------------------------------------------
function startAttendanceLivePoller() {
    let seenStudents = new Set();
    
    setInterval(async () => {
        try {
            const res = await fetch('/api/today_attendance');
            if (res.ok) {
                const records = await res.json();
                const tbody = document.getElementById('liveAttendanceTableBody');
                const countBadge = document.getElementById('livePresentCount');
                
                if (countBadge) countBadge.textContent = records.length;
                
                if (tbody && records.length > 0) {
                    // Check for newly recognized student
                    records.forEach(rec => {
                        if (!seenStudents.has(rec.name)) {
                            seenStudents.add(rec.name);
                            AudioAlerts.playSuccessChime();
                        }
                    });
                    
                    tbody.innerHTML = records.map(rec => `
                        <tr>
                            <td><strong class="text-info">${rec.name}</strong></td>
                            <td>${rec.roll_no || 'N/A'}</td>
                            <td>${rec.department || 'N/A'}</td>
                            <td><span class="badge badge-success-custom">${rec.time}</span></td>
                        </tr>
                    `).join('');
                }
            }
        } catch (e) {
            console.error('Error polling attendance:', e);
        }
    }, 2500);
}

// -------------------------------------------------------------
// Classroom Distraction Live Poller
// -------------------------------------------------------------
function startDistractionPoller() {
    let lastAlertTime = 0;
    
    setInterval(async () => {
        try {
            const res = await fetch('/api/live_stats/phone_detection');
            if (res.ok) {
                const stats = await res.json();
                
                const totalEl = document.getElementById('metricTotalStudents');
                const attentiveEl = document.getElementById('metricAttentive');
                const phoneEl = document.getElementById('metricPhoneUsers');
                const rateEl = document.getElementById('metricDistractionRate');
                const alertBanner = document.getElementById('phoneAlertBanner');
                
                if (totalEl && stats.total_students !== undefined) totalEl.textContent = stats.total_students;
                if (attentiveEl && stats.attentive_students !== undefined) attentiveEl.textContent = stats.attentive_students;
                if (phoneEl && stats.phone_users !== undefined) {
                    phoneEl.textContent = stats.phone_users;
                    if (stats.phone_users > 0) {
                        phoneEl.classList.add('text-danger');
                        if (alertBanner) alertBanner.style.display = 'block';
                        
                        // Play alert sound if not spammed
                        const now = Date.now();
                        if (now - lastAlertTime > 5000) {
                            AudioAlerts.playWarningBeep();
                            lastAlertTime = now;
                        }
                    } else {
                        phoneEl.classList.remove('text-danger');
                        if (alertBanner) alertBanner.style.display = 'none';
                    }
                }
                if (rateEl && stats.distraction_rate !== undefined) {
                    rateEl.textContent = stats.distraction_rate + '%';
                    const progressBar = document.getElementById('distractionProgressBar');
                    if (progressBar) progressBar.style.width = stats.distraction_rate + '%';
                }
            }
        } catch (e) {
            console.error('Error polling phone detection:', e);
        }
    }, 1500);
}

// -------------------------------------------------------------
// Crowd Density Poller
// -------------------------------------------------------------
function startCrowdPoller() {
    setInterval(async () => {
        try {
            const res = await fetch('/api/live_stats/crowd_monitoring');
            if (res.ok) {
                const stats = await res.json();
                const countEl = document.getElementById('crowdHeadcount');
                const statusBadge = document.getElementById('crowdStatusBadge');
                
                if (countEl && stats.headcount !== undefined) countEl.textContent = stats.headcount;
                if (statusBadge && stats.status) {
                    statusBadge.textContent = stats.status;
                    statusBadge.className = `badge badge-${stats.color}-custom px-3 py-2 fs-6`;
                    
                    if (stats.color === 'danger') {
                        AudioAlerts.playWarningBeep();
                    }
                }
            }
        } catch (e) {
            console.error('Error polling crowd stats:', e);
        }
    }, 1500);
}
