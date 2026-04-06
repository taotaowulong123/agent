/* ── state ── */
let selectedFile = null;
let pollingTimers = {};

/* ── DOM refs ── */
const uploadBox    = document.getElementById('uploadBox');
const fileInput    = document.getElementById('fileInput');
const uploadHint   = document.getElementById('uploadHint');
const uploadProgress = document.getElementById('uploadProgress');
const uploadFilename = document.getElementById('uploadFilename');
const progressFill = document.getElementById('progressFill');
const uploadBtn    = document.getElementById('uploadBtn');
const jobSection   = document.getElementById('jobSection');
const jobList      = document.getElementById('jobList');
const modalOverlay = document.getElementById('modalOverlay');
const modalClose   = document.getElementById('modalClose');
const modalTitle   = document.getElementById('modalTitle');
const modalBody    = document.getElementById('modalBody');

/* ── upload box interactions ── */
uploadBox.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', e => selectFile(e.target.files[0]));

uploadBox.addEventListener('dragover', e => { e.preventDefault(); uploadBox.classList.add('drag-over'); });
uploadBox.addEventListener('dragleave', () => uploadBox.classList.remove('drag-over'));
uploadBox.addEventListener('drop', e => {
  e.preventDefault();
  uploadBox.classList.remove('drag-over');
  if (e.dataTransfer.files[0]) selectFile(e.dataTransfer.files[0]);
});

function selectFile(file) {
  if (!file) return;
  selectedFile = file;
  uploadHint.hidden = true;
  uploadProgress.hidden = false;
  uploadFilename.textContent = file.name;
  progressFill.style.width = '0%';
  uploadBtn.disabled = false;
}

/* ── upload ── */
uploadBtn.addEventListener('click', async () => {
  if (!selectedFile) return;
  uploadBtn.disabled = true;

  const formData = new FormData();
  formData.append('file', selectedFile);

  try {
    // Fake progress animation during upload
    let pct = 0;
    const ticker = setInterval(() => {
      pct = Math.min(pct + 5, 85);
      progressFill.style.width = pct + '%';
    }, 150);

    const resp = await fetch('/api/upload', { method: 'POST', body: formData });
    clearInterval(ticker);

    if (!resp.ok) {
      const err = await resp.json();
      alert('上传失败: ' + (err.detail || resp.statusText));
      resetUploadBox();
      return;
    }

    progressFill.style.width = '100%';
    const job = await resp.json();
    addOrUpdateCard(job);
    jobSection.hidden = false;
    startPolling(job.job_id);
    setTimeout(resetUploadBox, 800);
  } catch (e) {
    alert('网络错误: ' + e.message);
    resetUploadBox();
  }
});

function resetUploadBox() {
  selectedFile = null;
  fileInput.value = '';
  uploadHint.hidden = false;
  uploadProgress.hidden = true;
  progressFill.style.width = '0%';
  uploadBtn.disabled = true;
}

/* ── polling ── */
function startPolling(jobId) {
  if (pollingTimers[jobId]) return;
  pollingTimers[jobId] = setInterval(async () => {
    const job = await fetchJob(jobId);
    if (!job) return;
    addOrUpdateCard(job);
    if (job.status === 'done' || job.status === 'failed') {
      clearInterval(pollingTimers[jobId]);
      delete pollingTimers[jobId];
    }
  }, 3000);
}

async function fetchJob(jobId) {
  try {
    const r = await fetch('/api/jobs/' + jobId);
    if (!r.ok) return null;
    return await r.json();
  } catch { return null; }
}

/* ── job cards ── */
function addOrUpdateCard(job) {
  let card = document.getElementById('card-' + job.job_id);
  if (!card) {
    card = document.createElement('div');
    card.className = 'job-card';
    card.id = 'card-' + job.job_id;
    jobList.prepend(card);
  }
  const badgeClass = 'badge badge-' + job.status;
  const statusLabel = { uploaded: '已上传', processing: '处理中...', done: '完成', failed: '失败' }[job.status] || job.status;
  const viewBtn = job.status === 'done'
    ? `<button class="btn-view" onclick="openModal('${job.job_id}')">查看结果</button>`
    : '';
  const deleteBtn = `<button class="btn-delete" onclick="deleteJob('${job.job_id}')">删除</button>`;
  card.innerHTML = `
    <div class="job-info">
      <div class="job-name">${escHtml(job.filename)}</div>
      <div class="job-meta">${job.media_type} &nbsp;|&nbsp; ${job.job_id.slice(0, 8)}</div>
    </div>
    <div class="job-actions">
      <span class="${badgeClass}">${statusLabel}</span>
      ${viewBtn}
      ${deleteBtn}
    </div>
  `;
}

/* ── modal ── */
async function openModal(jobId) {
  const job = await fetchJob(jobId);
  if (!job) return;
  modalTitle.textContent = job.filename;
  modalBody.innerHTML = buildResultHtml(job);
  modalOverlay.hidden = false;
}

modalClose.addEventListener('click', () => { modalOverlay.hidden = true; });
modalOverlay.addEventListener('click', e => { if (e.target === modalOverlay) modalOverlay.hidden = true; });

function buildResultHtml(job) {
  let html = '';

  if (job.audio_url) {
    html += section('音频', `<audio controls src="${job.audio_url}" style="width:100%"></audio>`);
  }

  if (job.frames && job.frames.length) {
    const imgs = job.frames.map(f =>
      `<img src="${f.file_url}" title="${f.timestamp_sec}s" loading="lazy" />`
    ).join('');
    html += section('视频帧', `<div class="frame-grid">${imgs}</div>`);
  }

  if (job.asr_text) html += section('语音识别 (ASR)', `<pre>${escHtml(job.asr_text)}</pre>`);

  if (job.ocr_texts && job.ocr_texts.length) {
    html += section('图像文字 (OCR)', `<pre>${escHtml(job.ocr_texts.join('\n---\n'))}</pre>`);
  }

  if (job.merged_text) html += section('合并文本', `<pre>${escHtml(job.merged_text)}</pre>`);

  if (job.summary) html += section('摘要', `<p>${escHtml(job.summary)}</p>`);

  if (job.keywords && job.keywords.length) {
    const tags = job.keywords.map(k => `<span class="keyword-tag">${escHtml(k)}</span>`).join('');
    html += section('关键词', `<div class="keywords">${tags}</div>`);
  }

  if (job.error) html += section('错误信息', `<pre style="color:#c62828">${escHtml(job.error)}</pre>`);

  return html;
}

function section(title, content) {
  return `<div class="result-section"><h3>${title}</h3>${content}</div>`;
}

function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

/* ── delete job ── */
async function deleteJob(jobId) {
  if (!confirm('确认删除该任务及所有相关文件？')) return;
  try {
    const r = await fetch('/api/jobs/' + jobId, { method: 'DELETE' });
    if (!r.ok) { alert('删除失败'); return; }
    // Stop polling if active
    if (pollingTimers[jobId]) {
      clearInterval(pollingTimers[jobId]);
      delete pollingTimers[jobId];
    }
    // Remove card from DOM
    const card = document.getElementById('card-' + jobId);
    if (card) card.remove();
    // Hide section if no more jobs
    if (jobList.children.length === 0) jobSection.hidden = true;
  } catch (e) {
    alert('删除失败: ' + e.message);
  }
}

/* ── load existing jobs on page load ── */
(async () => {
  const r = await fetch('/api/jobs');
  if (!r.ok) return;
  const jobs = await r.json();
  if (!jobs.length) return;
  jobSection.hidden = false;
  jobs.reverse().forEach(job => {
    addOrUpdateCard(job);
    if (job.status === 'processing' || job.status === 'uploaded') startPolling(job.job_id);
  });
})();
