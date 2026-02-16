// ============ STATE ============
let coverUrl = document.getElementById('cover_url').value || '';
let galleryUrls = [];

// Init gallery URLs from existing thumbs
document.querySelectorAll('#galleryPreviews .gallery-thumb').forEach(el => {
  galleryUrls.push(el.dataset.url);
});

const statusEl = document.getElementById('formStatus');
const submitBtn = document.getElementById('submitBtn');

// ============ HELPER: presigned upload ============
async function uploadFile(file, folder) {
  statusEl.textContent = `Uploading ${file.name}...`;
  statusEl.className = 'form-status';

  // 1. Get presigned URL
  const presignRes = await fetch('/api/admin/uploads/presign', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      filename: file.name,
      content_type: file.type,
      folder: folder,
    }),
  });

  if (!presignRes.ok) {
    const err = await presignRes.json();
    throw new Error(err.detail || 'Failed to get upload URL');
  }

  const { upload_url, public_url } = await presignRes.json();

  // 2. Upload directly to S3/bucket
  const uploadRes = await fetch(upload_url, {
    method: 'PUT',
    headers: { 'Content-Type': file.type },
    body: file,
  });

  if (!uploadRes.ok) {
    throw new Error('Upload to storage failed');
  }

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

    // Show preview
    coverPreview.innerHTML = `
      <img src="${URL.createObjectURL(file)}" alt="Cover preview">
      <button type="button" class="remove-btn" onclick="removeCover()">×</button>
    `;
  } catch (err) {
    statusEl.textContent = err.message;
    statusEl.className = 'form-status error';
  }
});

// Drag & drop for cover
coverZone.addEventListener('dragover', (e) => { e.preventDefault(); coverZone.classList.add('dragover'); });
coverZone.addEventListener('dragleave', () => coverZone.classList.remove('dragover'));
coverZone.addEventListener('drop', (e) => {
  e.preventDefault();
  coverZone.classList.remove('dragover');
  const file = e.dataTransfer.files[0];
  if (file && file.type.startsWith('image/')) {
    // Trigger same logic as file input
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

      // Add preview thumb
      const thumb = document.createElement('div');
      thumb.className = 'gallery-thumb';
      thumb.dataset.url = url;
      thumb.innerHTML = `
        <img src="${URL.createObjectURL(file)}" alt="Gallery image">
        <button type="button" class="remove-btn" onclick="removeGalleryImage(this)">×</button>
      `;
      galleryPreviews.appendChild(thumb);
    } catch (err) {
      statusEl.textContent = `Failed to upload ${file.name}: ${err.message}`;
      statusEl.className = 'form-status error';
    }
  }

  // Reset input so same files can be re-selected
  galleryInput.value = '';
});

// Drag & drop for gallery
galleryZone.addEventListener('dragover', (e) => { e.preventDefault(); galleryZone.classList.add('dragover'); });
galleryZone.addEventListener('dragleave', () => galleryZone.classList.remove('dragover'));
galleryZone.addEventListener('drop', (e) => {
  e.preventDefault();
  galleryZone.classList.remove('dragover');
  const files = e.dataTransfer.files;
  if (files.length) {
    const dt = new DataTransfer();
    for (const f of files) {
      if (f.type.startsWith('image/')) dt.items.add(f);
    }
    galleryInput.files = dt.files;
    galleryInput.dispatchEvent(new Event('change'));
  }
});

function removeGalleryImage(btn) {
  const thumb = btn.closest('.gallery-thumb');
  const url = thumb.dataset.url;
  galleryUrls = galleryUrls.filter(u => u !== url);
  thumb.remove();
}

// ============ AUTO-SLUG FROM TITLE ============
const titleInput = document.getElementById('title');
const slugInput = document.getElementById('slug');

if (!IS_EDIT) {
  titleInput.addEventListener('input', () => {
    const val = titleInput.value
      .toLowerCase()
      .replace(/[^a-z0-9\s-]/g, '')
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-')
      .slice(0, 120);
    slugInput.value = val;
  });
}

// ============ FORM SUBMIT ============
document.getElementById('workForm').addEventListener('submit', async (e) => {
  e.preventDefault();

  submitBtn.disabled = true;
  statusEl.textContent = 'Saving...';
  statusEl.className = 'form-status';

  const tags = document.getElementById('tags').value
    .split(',')
    .map(t => t.trim())
    .filter(Boolean);

  const body = {
    title: document.getElementById('title').value,
    slug: document.getElementById('slug').value,
    description: document.getElementById('description').value || null,
    year: document.getElementById('year').value ? parseInt(document.getElementById('year').value) : null,
    tags: tags,
    cover_url: coverUrl,
    gallery_urls: galleryUrls,
    span_class: document.getElementById('span_class').value,
    is_tall: document.getElementById('is_tall').checked,
    sort_order: parseInt(document.getElementById('sort_order').value) || 0,
  };

  try {
    let url, method;

    if (IS_EDIT) {
      url = `/api/admin/works/${WORK_ID}`;
      method = 'PATCH';
    } else {
      url = '/api/admin/works';
      method = 'POST';
    }

    const res = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to save');
    }

    statusEl.textContent = 'Saved!';
    statusEl.className = 'form-status success';

    if (!IS_EDIT) {
      // Redirect to dashboard after create
      setTimeout(() => window.location.href = '/admin/', 800);
    }
  } catch (err) {
    statusEl.textContent = err.message;
    statusEl.className = 'form-status error';
  } finally {
    submitBtn.disabled = false;
  }
});
