// ============ STATE ============
let coverUrl = document.getElementById('cover_url').value || '';
let galleryUrls = [];

document.querySelectorAll('#galleryPreviews .gallery-thumb').forEach(el => {
  galleryUrls.push(el.dataset.url);
});

const statusEl = document.getElementById('formStatus');
const submitBtn = document.getElementById('submitBtn');

// ============ HELPER: server-side upload ============
async function uploadFile(file, folder) {
  statusEl.textContent = `Uploading ${file.name}...`;
  statusEl.className = 'form-status';

  const formData = new FormData();
  formData.append('file', file);
  formData.append('folder', folder);

  const res = await fetch('/api/admin/upload', {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Upload failed');
  }

  const { public_url } = await res.json();
  statusEl.textContent = '';
  return public_url;
}

// ============ COVER UPLOAD ============
const coverInput = document.getElementById('coverInput');
const coverZone = document.getElementById('coverZone');
const coverPreview = document.getElementById('coverPreview');

coverInput.addEventListener('change', async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  try {
    const slug = document.getElementById('slug').value || 'draft';
    const url = await uploadFile(file, `works/${slug}/`);
    coverUrl = url;
    document.getElementById('cover_url').value = url;
    coverPreview.innerHTML = `
      <img src="${URL.createObjectURL(file)}" alt="Cover preview">
      <button type="button" class="remove-btn" onclick="removeCover()">×</button>
    `;
  } catch (err) {
    statusEl.textContent = err.message;
    statusEl.className = 'form-status error';
  }
});

coverZone.addEventListener('dragover', (e) => { e.preventDefault(); coverZone.classList.add('dragover'); });
coverZone.addEventListener('dragleave', () => coverZone.classList.remove('dragover'));
coverZone.addEventListener('drop', (e) => {
  e.preventDefault();
  coverZone.classList.remove('dragover');
  const file = e.dataTransfer.files[0];
  if (file && file.type.startsWith('image/')) {
    const dt = new DataTransfer();
    dt.items.add(file);
    coverInput.files = dt.files;
    coverInput.dispatchEvent(new Event('change'));
  }
});

function removeCover() {
  coverUrl = '';
  document.getElementById('cover_url').value = '';
  coverPreview.innerHTML = '<p class="upload-hint">Click or drag to upload cover image</p>';
}

// ============ GALLERY UPLOAD ============
const galleryInput = document.getElementById('galleryInput');
const galleryZone = document.getElementById('galleryZone');
const galleryPreviews = document.getElementById('galleryPreviews');

galleryInput.addEventListener('change', async (e) => {
  const files = Array.from(e.target.files);
  if (!files.length) return;
  for (const file of files) {
    try {
      const slug = document.getElementById('slug').value || 'draft';
      const url = await uploadFile(file, `works/${slug}/gallery/`);
      galleryUrls.push(url);
      const thumb = document.createElement('div');
      thumb.className = 'gallery-thumb';
      thumb.dataset.url = url;
      thumb.innerHTML = `
        <img src="${URL.createObjectURL(file)}" alt="Gallery image">
        <button type="button" class="remove-btn" onclick="removeGalleryImage(this)">×</button>
      `;
      galleryPreviews.appendChild(thumb);
    } catch (err) {
      statusEl.textContent = `Failed: ${file.name}: ${err.message}`;
      statusEl.className = 'form-status error';
    }
  }
  galleryInput.value = '';
});

galleryZone.addEventListener('dragover', (e) => { e.preventDefault(); galleryZone.classList.add('dragover'); });
galleryZone.addEventListener('dragleave', () => galleryZone.classList.remove('dragover'));
galleryZone.addEventListener('drop', (e) => {
  e.preventDefault();
  galleryZone.classList.remove('dragover');
  const files = e.dataTransfer.files;
  if (files.length) {
    const dt = new DataTransfer();
    for (const f of files) { if (f.type.startsWith('image/')) dt.items.add(f); }
    galleryInput.files = dt.files;
    galleryInput.dispatchEvent(new Event('change'));
  }
});

function removeGalleryImage(btn) {
  const thumb = btn.closest('.gallery-thumb');
  galleryUrls = galleryUrls.filter(u => u !== thumb.dataset.url);
  thumb.remove();
}

// ============ AUTO-SLUG FROM TITLE ============
const titleInput = document.getElementById('title');
const slugInput = document.getElementById('slug');

if (!IS_EDIT) {
  titleInput.addEventListener('input', () => {
    slugInput.value = titleInput.value
      .toLowerCase()
      .replace(/[^a-z0-9\s-]/g, '')
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-')
      .slice(0, 120);
  });
}

// ============ FORM SUBMIT ============
document.getElementById('workForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  submitBtn.disabled = true;
  statusEl.textContent = 'Saving...';
  statusEl.className = 'form-status';

  const tags = document.getElementById('tags').value
    .split(',').map(t => t.trim()).filter(Boolean);

  const body = {
    title: document.getElementById('title').value,
    slug: document.getElementById('slug').value,
    description: document.getElementById('description').value || null,
    year: document.getElementById('year').value ? parseInt(document.getElementById('year').value) : null,
    tags, cover_url: coverUrl, gallery_urls: galleryUrls,
    span_class: document.getElementById('span_class').value,
    is_tall: document.getElementById('is_tall').checked,
    sort_order: parseInt(document.getElementById('sort_order').value) || 0,
  };

  try {
    const url = IS_EDIT ? `/api/admin/works/${WORK_ID}` : '/api/admin/works';
    const res = await fetch(url, {
      method: IS_EDIT ? 'PATCH' : 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to save');
    }
    statusEl.textContent = 'Saved!';
    statusEl.className = 'form-status success';
    if (!IS_EDIT) setTimeout(() => window.location.href = '/admin/', 800);
  } catch (err) {
    statusEl.textContent = err.message;
    statusEl.className = 'form-status error';
  } finally {
    submitBtn.disabled = false;
  }
});
