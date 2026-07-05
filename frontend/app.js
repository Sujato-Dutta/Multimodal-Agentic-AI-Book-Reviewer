const API_BASE = window.location.origin + "/api";
let selectedFile = null;
let cameraStream = null;

// ============ Upload Handling ============

const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("file-input");
const previewImage = document.getElementById("preview-image");
const dropzoneContent = document.getElementById("dropzone-content");
const btnAnalyze = document.getElementById("btn-start-analyze");

dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropzone.classList.add("dragover");
});

dropzone.addEventListener("dragleave", () => {
    dropzone.classList.remove("dragover");
});

dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith("image/")) {
        handleFileSelected(file);
    }
});

fileInput.addEventListener("change", (e) => {
    if (e.target.files[0]) {
        handleFileSelected(e.target.files[0]);
    }
});

function handleFileSelected(file) {
    selectedFile = file;
    const reader = new FileReader();
    reader.onload = (e) => {
        previewImage.src = e.target.result;
        previewImage.classList.add("visible");
        dropzoneContent.style.display = "none";
        btnAnalyze.disabled = false;
    };
    reader.readAsDataURL(file);
}

function scrollToUpload() {
    document.getElementById("upload-panel").scrollIntoView({ behavior: "smooth", block: "center" });
}

function highlightUpload() {
    const panel = document.getElementById("upload-panel");
    panel.scrollIntoView({ behavior: "smooth", block: "center" });
    panel.classList.remove("glow");
    // Force reflow so re-adding the class restarts the animation
    void panel.offsetWidth;
    panel.classList.add("glow");
    setTimeout(() => panel.classList.remove("glow"), 3500);
}

function showDemo() {
    highlightUpload();
}

// ============ Camera ============

function openCamera() {
    const modal = document.getElementById("camera-modal");
    const video = document.getElementById("camera-video");
    modal.classList.remove("hidden");

    navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } })
        .then((stream) => {
            cameraStream = stream;
            video.srcObject = stream;
        })
        .catch(() => {
            alert("Camera access denied. Please use file upload instead.");
            closeCamera();
        });
}

function capturePhoto() {
    const video = document.getElementById("camera-video");
    const canvas = document.getElementById("camera-canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d").drawImage(video, 0, 0);
    canvas.toBlob((blob) => {
        const file = new File([blob], "camera-capture.jpg", { type: "image/jpeg" });
        handleFileSelected(file);
        closeCamera();
    }, "image/jpeg", 0.9);
}

function closeCamera() {
    const modal = document.getElementById("camera-modal");
    modal.classList.add("hidden");
    if (cameraStream) {
        cameraStream.getTracks().forEach((t) => t.stop());
        cameraStream = null;
    }
}

// ============ Analysis ============

const progressStages = [
    { text: "Reading cover with AI vision...", pct: 15 },
    { text: "Verifying book identity...", pct: 30 },
    { text: "Searching trusted sources...", pct: 50 },
    { text: "Retrieving and ranking information...", pct: 65 },
    { text: "Generating spoiler-free review...", pct: 80 },
    { text: "Computing confidence score...", pct: 90 },
    { text: "Applying guardrails and finalizing...", pct: 95 },
];

async function startAnalysis() {
    if (!selectedFile) return;

    const uploadPanel = document.getElementById("upload-panel");
    const progressDiv = document.getElementById("upload-progress");
    const progressFill = document.getElementById("progress-fill");
    const progressText = document.getElementById("progress-text");
    const resultsPanel = document.getElementById("results-panel");

    btnAnalyze.disabled = true;
    btnAnalyze.textContent = "Analyzing...";
    progressDiv.classList.add("active");
    resultsPanel.classList.add("hidden");

    let stageIndex = 0;
    const progressInterval = setInterval(() => {
        if (stageIndex < progressStages.length) {
            const stage = progressStages[stageIndex];
            progressFill.style.width = stage.pct + "%";
            progressText.textContent = stage.text;
            stageIndex++;
        }
    }, 2500);

    try {
        const formData = new FormData();
        formData.append("file", selectedFile);

        const response = await fetch(`${API_BASE}/analyze-book`, {
            method: "POST",
            body: formData,
        });

        clearInterval(progressInterval);
        progressFill.style.width = "100%";

        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || "Analysis failed");
        }

        const data = await response.json();
        displayResults(data);
    } catch (error) {
        clearInterval(progressInterval);
        progressText.textContent = `Error: ${error.message}`;
        progressFill.style.width = "0%";
        btnAnalyze.disabled = false;
        btnAnalyze.textContent = "Retry Analysis";
    }
}

function displayResults(data) {
    const uploadPanel = document.getElementById("upload-panel");
    const resultsPanel = document.getElementById("results-panel");

    uploadPanel.style.display = "none";
    resultsPanel.classList.remove("hidden");

    const book = data.book || {};
    const review = data.review || {};
    const rec = data.recommendation || {};
    const conf = data.confidence || {};
    const sources = data.sources || [];
    const citations = data.citations || [];

    document.getElementById("result-title").textContent = book.title || "Unknown Title";
    document.getElementById("result-author").textContent = book.author || "Unknown Author";

    const categoryEl = document.getElementById("result-category");
    if (book.category) {
        categoryEl.textContent = book.category;
        categoryEl.style.display = "inline-block";
    } else {
        categoryEl.style.display = "none";
    }

    document.getElementById("result-summary").textContent = review.summary || "No summary available.";
    document.getElementById("result-best-for").textContent = review.best_for || "—";
    document.getElementById("result-not-ideal").textContent = review.not_ideal_for || "—";
    document.getElementById("result-sentiment").textContent = review.public_sentiment || "—";

    // Confidence ring animation
    const pct = Math.round((conf.overall || 0) * 100);
    document.getElementById("confidence-value").textContent = pct + "%";
    const circumference = 2 * Math.PI * 42;
    const offset = circumference - (pct / 100) * circumference;
    setTimeout(() => {
        document.getElementById("ring-fill").style.strokeDashoffset = offset;
    }, 100);

    // Sources
    const sourcesDiv = document.getElementById("result-sources");
    sourcesDiv.innerHTML = "";
    const uniqueSources = [...new Set(sources)].filter(Boolean);
    const displaySources = uniqueSources.slice(0, 4);
    displaySources.forEach((s) => {
        const tag = document.createElement("span");
        tag.className = "source-tag";
        tag.textContent = s;
        sourcesDiv.appendChild(tag);
    });
    if (uniqueSources.length > 4) {
        const more = document.createElement("span");
        more.className = "source-tag";
        more.textContent = `+${uniqueSources.length - 4}`;
        sourcesDiv.appendChild(more);
    }

    // Recommendation
    const action = (rec.action || "borrow").toLowerCase();
    const icons = { buy: "🛒", borrow: "📖", skip: "⏭️" };
    document.getElementById("rec-icon").textContent = icons[action] || "📖";
    document.getElementById("rec-action").textContent = action.charAt(0).toUpperCase() + action.slice(1);
    document.getElementById("rec-reason").textContent = rec.reason || "Great match for your taste";

    // Store book info for feedback
    resultsPanel.dataset.bookId = book.isbn || "unknown";
}

// ============ Feedback ============

async function sendFeedback(rating) {
    const resultsPanel = document.getElementById("results-panel");
    const bookId = resultsPanel.dataset.bookId || "unknown";

    document.querySelectorAll(".btn-feedback").forEach((btn) => btn.classList.remove("active"));
    document.getElementById(rating === "helpful" ? "btn-helpful" : "btn-not-helpful").classList.add("active");

    try {
        await fetch(`${API_BASE}/feedback`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ book_id: bookId, rating }),
        });
    } catch (e) {
        // Silently fail for feedback
    }
}

// ============ Reset ============

function resetUpload() {
    selectedFile = null;
    fileInput.value = "";
    previewImage.src = "";
    previewImage.classList.remove("visible");
    dropzoneContent.style.display = "flex";
    btnAnalyze.disabled = true;
    btnAnalyze.textContent = "Analyze This Book";
    document.getElementById("upload-progress").classList.remove("active");
    document.getElementById("progress-fill").style.width = "0%";
}

function resetAll() {
    resetUpload();
    document.getElementById("upload-panel").style.display = "block";
    document.getElementById("results-panel").classList.add("hidden");
    document.querySelectorAll(".btn-feedback").forEach((btn) => btn.classList.remove("active"));
    scrollToUpload();
}
