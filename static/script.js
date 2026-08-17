(function () {
  // --- Tema geçişi ---
  var root = document.documentElement;
  var toggleBtn = document.getElementById('theme-toggle');

  if (toggleBtn) {
    toggleBtn.addEventListener('click', function () {
      var current = root.getAttribute('data-theme') || 'dark';
      var next = current === 'dark' ? 'light' : 'dark';
      root.setAttribute('data-theme', next);
      localStorage.setItem('theme', next);
    });
  }

  // --- Detay modalı ---
  var dataEl = document.getElementById('recs-data');
  if (!dataEl) return;

  var items;
  try {
    items = JSON.parse(dataEl.textContent);
  } catch (e) {
    return;
  }

  var modal = document.getElementById('detail-modal');
  var closeBtn = document.getElementById('modal-close');
  var posterImg = document.getElementById('modal-poster-img');
  var titleEl = document.getElementById('modal-title');
  var eyebrowEl = document.getElementById('modal-eyebrow');
  var genresEl = document.getElementById('modal-genres');
  var overviewEl = document.getElementById('modal-overview');
  var lastFocused = null;

  function openModal(item) {
    if (item.poster) {
      posterImg.src = item.poster;
      posterImg.alt = item.title;
      posterImg.style.display = '';
    } else {
      posterImg.style.display = 'none';
    }
    titleEl.textContent = item.title + ' (' + item.year + ')';
    eyebrowEl.textContent = item.media_type;
    genresEl.innerHTML = '';
    (item.genres || []).forEach(function (g) {
      var span = document.createElement('span');
      span.className = 'tag';
      span.textContent = g;
      genresEl.appendChild(span);
    });
    overviewEl.textContent = item.overview;

    lastFocused = document.activeElement;
    modal.hidden = false;
    document.body.style.overflow = 'hidden';
    closeBtn.focus();
  }

  function closeModal() {
    modal.hidden = true;
    document.body.style.overflow = '';
    if (lastFocused) lastFocused.focus();
  }

  document.querySelectorAll('.frame-card').forEach(function (card) {
    var idx = parseInt(card.getAttribute('data-idx'), 10);
    var item = items[idx];
    if (!item) return;

    card.addEventListener('click', function () {
      openModal(item);
    });
    card.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        openModal(item);
      }
    });
  });

  closeBtn.addEventListener('click', closeModal);
  modal.addEventListener('click', function (e) {
    if (e.target === modal) closeModal();
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && !modal.hidden) closeModal();
  });
})();
