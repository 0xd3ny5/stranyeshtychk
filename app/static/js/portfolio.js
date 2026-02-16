// ============ NAVIGATION ============
function showSection(name) {
  // Hide artwork detail
  const detail = document.getElementById('artwork-detail');
  detail.style.display = 'none';
  detail.classList.remove('visible');

  // Hide all page sections
  document.querySelectorAll('.page-section').forEach(s => s.classList.remove('visible'));

  // Show target
  const target = document.getElementById(`section-${name}`);
  if (target) {
    target.classList.add('visible');
    target.style.animation = 'none';
    target.offsetHeight; // reflow
    target.style.animation = '';
  }

  // Update nav active state
  document.querySelectorAll('#mainNav a').forEach(a => {
    a.classList.toggle('active', a.dataset.section === name);
  });
}

// Nav click handlers
document.querySelectorAll('#mainNav a[data-section]').forEach(link => {
  link.addEventListener('click', (e) => {
    e.preventDefault();
    showSection(link.dataset.section);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
});

// ============ GRID ITEM CLICKS ============
document.querySelectorAll('.grid-item[data-slug]').forEach(item => {
  const slug = item.dataset.slug;

  item.addEventListener('click', () => openArtwork(slug));
  item.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      openArtwork(slug);
    }
  });
});

// ============ OPEN ARTWORK (fetch from API) ============
async function openArtwork(slug) {
  try {
    const res = await fetch(`/api/works/${slug}`);
    if (!res.ok) return;
    const art = await res.json();

    document.getElementById('detailImg').src = art.cover_url || '';
    document.getElementById('detailImg').alt = art.title;
    document.getElementById('detailTitle').textContent = art.title;

    const metaParts = [];
    if (art.tags && art.tags.length) metaParts.push(art.tags.join(', '));
    if (art.year) metaParts.push(art.year);
    document.getElementById('detailMeta').textContent = metaParts.join(' · ');

    document.getElementById('detailDesc').textContent = art.description || '';

    // Gallery images
    const gallery = document.getElementById('detailGallery');
    gallery.innerHTML = '';
    if (art.gallery_urls && art.gallery_urls.length) {
      art.gallery_urls.forEach((url, i) => {
        const wrap = document.createElement('div');
        wrap.className = 'gallery-image-wrap';
        wrap.innerHTML = `<img src="${url}" alt="${art.title} — gallery ${i + 1}" loading="lazy">`;
        gallery.appendChild(wrap);
      });
    }

    // Hide all sections, show detail
    document.querySelectorAll('.page-section').forEach(s => s.classList.remove('visible'));
    const detail = document.getElementById('artwork-detail');
    detail.classList.add('visible');
    detail.style.display = 'block';

    // Update nav
    document.querySelectorAll('#mainNav a').forEach(a => a.classList.remove('active'));
    document.querySelector('[data-section="work"]')?.classList.add('active');

    window.scrollTo({ top: 0, behavior: 'smooth' });
  } catch (err) {
    console.error('Failed to load artwork:', err);
  }
}

// ============ BACK TO GRID ============
const backBtn = document.getElementById('backToGrid');
if (backBtn) {
  backBtn.addEventListener('click', (e) => {
    e.preventDefault();
    const detail = document.getElementById('artwork-detail');
    detail.style.display = 'none';
    detail.classList.remove('visible');
    showSection('work');
  });
}
