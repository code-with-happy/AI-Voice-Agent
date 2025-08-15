// === Conversational Agent UI ===

let mediaRecorder;
let audioChunks = [];
let sessionId = null;
let isRecording = false;

function ensureSessionId() {
	const url = new URL(window.location.href);
	let id = url.searchParams.get('session');
	if (!id) {
		id = Math.random().toString(36).slice(2);
		url.searchParams.set('session', id);
		window.history.replaceState({}, '', url.toString());
	}
	sessionId = id;
}

ensureSessionId();

const recordBtn = document.getElementById('recordBtn');
const statusDot = document.getElementById('statusDot');
const statusText = document.getElementById('status');
const agentAudio = document.getElementById('agentAudio');

function setStatus(text, recording) {
	statusText.textContent = text;
	if (recording) {
		statusDot.classList.add('recording');
		recordBtn.classList.add('recording');
		recordBtn.textContent = 'Stop';
    } else {
		statusDot.classList.remove('recording');
		recordBtn.classList.remove('recording');
		recordBtn.textContent = 'Record';
	}
}

async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];
		mediaRecorder.ondataavailable = event => { audioChunks.push(event.data); };
        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
			await sendAudioAndPlay(audioBlob);
		};
		mediaRecorder.start();
		isRecording = true;
		setStatus('Listening...', true);
	} catch (err) {
		alert('Microphone access denied or not available.');
		isRecording = false;
		setStatus('Idle', false);
	}
}

function stopRecording() {
	if (mediaRecorder && mediaRecorder.state === 'recording') {
		mediaRecorder.stop();
		isRecording = false;
		setStatus('Processing...', false);
	}
}

async function sendAudioAndPlay(audioBlob) {
            const formData = new FormData();
            const fileName = `recording_${Date.now()}.webm`;
            formData.append('file', audioBlob, fileName);

            try {
		const response = await fetch(`/agent/chat/${encodeURIComponent(sessionId)}`, {
                    method: 'POST',
                    body: formData
                });
                const result = await response.json();
		if (response.ok && result.success !== false) {
			const urls = result.audioUrls && result.audioUrls.length ? result.audioUrls : [result.audioUrl];
			await playSequential(urls);
                } else {
			const fallback = result && result.fallbackText ? result.fallbackText : "I'm having trouble connecting right now. Please try again.";
			const utter = new SpeechSynthesisUtterance(fallback);
			window.speechSynthesis.speak(utter);
			setStatus('Idle', false);
                }
            } catch (err) {
		const utter = new SpeechSynthesisUtterance("I'm having trouble connecting right now. Please try again.");
		window.speechSynthesis.speak(utter);
		setStatus('Idle', false);
	}
}

async function playSequential(urls) {
	return new Promise(resolve => {
		let idx = 0;
		const playNext = () => {
			if (idx >= urls.length) {
				// Auto-start next user turn
				startRecording();
				return resolve();
			}
			agentAudio.src = urls[idx];
			agentAudio.onerror = () => {
				// If playback breaks, attempt opening link; then continue
				try { window.open(urls[idx], '_blank'); } catch (e) {}
				idx += 1;
				playNext();
			};
			agentAudio.onended = () => {
				idx += 1;
				playNext();
			};
			agentAudio.play().catch(() => {
				idx += 1;
				playNext();
			});
		};
		setStatus('Responding...', false);
		playNext();
	});
}

recordBtn.addEventListener('click', () => {
	if (!isRecording) {
		startRecording();
	} else {
		stopRecording();
    }
});