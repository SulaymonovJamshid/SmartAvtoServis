/**
 * SmartAvtoServis - Main JavaScript
 */

// ─── Theme Management ──────────────────────────────────────────────────────

const ThemeManager = {
  init() {
    const saved = localStorage.getItem('theme') || document.documentElement.getAttribute('data-theme') || 'light';
    this.apply(saved);
  },
  apply(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    const toggle = document.getElementById('themeToggle');
    if (toggle) toggle.setAttribute('aria-checked', theme === 'dark');
  },
  toggle() {
    const current = document.documentElement.getAttribute('data-theme') || 'light';
    const next = current === 'light' ? 'dark' : 'light';
    this.apply(next);

    // Save to server
    fetch('/theme/toggle/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-CSRFToken': getCookie('csrftoken'),
      },
      body: `theme=${next}`
    });
  }
};

// ─── OTP / Phone Verification ──────────────────────────────────────────────

const OTPManager = {
  init() {
    const inputs = document.querySelectorAll('.otp-input');
    if (!inputs.length) return;

    inputs.forEach((input, i) => {
      input.addEventListener('input', (e) => {
        const val = e.target.value;
        if (val.length > 1) {
          e.target.value = val.slice(-1);
        }
        if (val && i < inputs.length - 1) {
          inputs[i + 1].focus();
        }
        this.syncHiddenInput();
      });

      input.addEventListener('keydown', (e) => {
        if (e.key === 'Backspace' && !e.target.value && i > 0) {
          inputs[i - 1].focus();
        }
      });

      input.addEventListener('paste', (e) => {
        e.preventDefault();
        const pasted = (e.clipboardData || window.clipboardData).getData('text');
        const digits = pasted.replace(/\D/g, '').slice(0, 6);
        digits.split('').forEach((d, j) => {
          if (inputs[j]) inputs[j].value = d;
        });
        inputs[Math.min(digits.length, inputs.length - 1)]?.focus();
        this.syncHiddenInput();
      });
    });

    // Countdown timer
    this.startCountdown();
  },

  syncHiddenInput() {
    const inputs = document.querySelectorAll('.otp-input');
    const code = Array.from(inputs).map(i => i.value).join('');
    const hidden = document.getElementById('otp-code-hidden');
    if (hidden) hidden.value = code;

    const submitBtn = document.getElementById('otp-submit-btn');
    if (submitBtn) {
      submitBtn.disabled = code.length < 6;
    }
  },

  startCountdown() {
    const el = document.getElementById('resend-countdown');
    const btn = document.getElementById('resend-btn');
    if (!el) return;

    let seconds = 60;
    const interval = setInterval(() => {
      seconds--;
      el.textContent = seconds;
      if (seconds <= 0) {
        clearInterval(interval);
        el.closest('.resend-wrapper').style.display = 'none';
        if (btn) btn.style.display = 'inline-flex';
      }
    }, 1000);
  },

  resend() {
    fetch('/resend-otp/', {
      headers: { 'X-CSRFToken': getCookie('csrftoken') }
    }).then(r => r.json()).then(data => {
      if (data.status === 'sent') {
        showToast('SMS qayta yuborildi!', 'success');
        this.startCountdown();
        document.getElementById('resend-btn').style.display = 'none';
        const wrapper = document.querySelector('.resend-wrapper');
        if (wrapper) wrapper.style.display = 'block';
      }
    });
  }
};

// ─── Star Rating ───────────────────────────────────────────────────────────

const StarRating = {
  init() {
    const container = document.querySelector('.star-rating-input');
    if (!container) return;

    const stars = container.querySelectorAll('.star');
    const input = document.getElementById('rating-input');

    stars.forEach((star, i) => {
      star.addEventListener('click', () => {
        const val = i + 1;
        if (input) input.value = val;
        this.highlight(stars, val);
      });

      star.addEventListener('mouseover', () => {
        this.highlight(stars, i + 1);
      });

      star.addEventListener('mouseout', () => {
        const current = parseInt(input?.value || 0);
        this.highlight(stars, current);
      });
    });
  },

  highlight(stars, count) {
    stars.forEach((s, i) => {
      s.classList.toggle('active', i < count);
    });
  }
};

// ─── Favorite Toggle ───────────────────────────────────────────────────────

function toggleFavorite(btn, serviceId) {
  fetch(`/favorites/${serviceId}/toggle/`, {
    method: 'POST',
    headers: { 'X-CSRFToken': getCookie('csrftoken') }
  })
  .then(r => r.json())
  .then(data => {
    if (data.status === 'added') {
      btn.classList.add('active');
      btn.textContent = '❤️';
    } else {
      btn.classList.remove('active');
      btn.textContent = '🤍';
    }
  });
}

// ─── Geolocation & Nearby Services ────────────────────────────────────────

const GeoManager = {
  lat: null,
  lng: null,

  requestLocation(callback) {
    if (!navigator.geolocation) {
      showToast('Brauzer geolokatsiyani qo\'llab-quvvatlamaydi', 'error');
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        this.lat = pos.coords.latitude;
        this.lng = pos.coords.longitude;
        if (callback) callback(this.lat, this.lng);
      },
      (err) => {
        showToast('Joylashuvni aniqlab bo\'lmadi', 'warning');
      }
    );
  },

  updateURL() {
    if (!this.lat || !this.lng) return;
    const url = new URL(window.location.href);
    url.searchParams.set('lat', this.lat);
    url.searchParams.set('lng', this.lng);
    url.searchParams.set('sort', 'nearest');
    window.location.href = url.toString();
  },

  loadNearbyOnMap() {
    if (!this.lat || !this.lng) return;
    fetch(`/api/nearby/?lat=${this.lat}&lng=${this.lng}&radius=15`)
      .then(r => r.json())
      .then(data => {
        if (window.initMapWithServices) {
          initMapWithServices(data.services, this.lat, this.lng);
        }
      });
  }
};

// ─── Filter Panel ──────────────────────────────────────────────────────────

function loadTumans(viloyat) {
  const tumanSelect = document.getElementById('tuman-select');
  if (!tumanSelect || !viloyat) return;

  fetch(`/api/tumans/?viloyat=${viloyat}`)
    .then(r => r.json())
    .then(data => {
      tumanSelect.innerHTML = '<option value="">— Tuman —</option>';
      data.tumans.forEach(t => {
        const opt = document.createElement('option');
        opt.value = t;
        opt.textContent = t;
        tumanSelect.appendChild(opt);
      });
    });
}

// ─── Image Upload Preview ──────────────────────────────────────────────────

function initImageUpload() {
  const slots = document.querySelectorAll('.image-slot[data-empty]');
  const fileInput = document.getElementById('image-file-input');
  if (!slots.length || !fileInput) return;

  slots.forEach(slot => {
    slot.addEventListener('click', () => {
      fileInput.click();
    });
  });

  fileInput.addEventListener('change', (e) => {
    const files = Array.from(e.target.files).slice(0, slots.length);
    files.forEach((file, i) => {
      const slot = slots[i];
      if (!slot) return;
      const reader = new FileReader();
      reader.onload = (ev) => {
        slot.innerHTML = `<img src="${ev.target.result}" alt="Preview">`;
        slot.removeAttribute('data-empty');
      };
      reader.readAsDataURL(file);
    });
  });
}

// ─── Image Delete ──────────────────────────────────────────────────────────

function deleteServiceImage(imgId, btn) {
  if (!confirm('Rasmni o\'chirishni tasdiqlaysizmi?')) return;

  fetch(`/dashboard/image/${imgId}/delete/`, {
    method: 'POST',
    headers: { 'X-CSRFToken': getCookie('csrftoken') }
  })
  .then(r => r.json())
  .then(data => {
    if (data.status === 'deleted') {
      const slot = btn.closest('.image-slot');
      slot.innerHTML = `
        <div class="add-icon">
          <span>📷</span>
          <span>Rasm qo'shish</span>
        </div>
      `;
      slot.setAttribute('data-empty', '');
      showToast('Rasm o\'chirildi', 'success');
    }
  });
}

// ─── Toast Notifications ───────────────────────────────────────────────────

function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container') || createToastContainer();
  const toast = document.createElement('div');
  const icons = { success: '✓', error: '✕', warning: '⚠', info: 'ℹ' };
  toast.className = `toast-item toast-${type}`;
  toast.innerHTML = `<span>${icons[type] || 'ℹ'}</span> ${message}`;
  container.appendChild(toast);
  requestAnimationFrame(() => toast.classList.add('show'));
  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

function createToastContainer() {
  const div = document.createElement('div');
  div.id = 'toast-container';
  div.style.cssText = 'position:fixed;bottom:1.5rem;right:1.5rem;z-index:9999;display:flex;flex-direction:column;gap:0.5rem;';
  document.body.appendChild(div);

  const style = document.createElement('style');
  style.textContent = `
    .toast-item {
      padding: 0.75rem 1.1rem;
      border-radius: 10px;
      font-size: 0.88rem;
      font-weight: 500;
      display: flex;
      align-items: center;
      gap: 0.5rem;
      opacity: 0;
      transform: translateX(20px);
      transition: all 0.3s ease;
      min-width: 220px;
      max-width: 320px;
      box-shadow: 0 4px 20px rgba(0,0,0,0.15);
    }
    .toast-item.show { opacity: 1; transform: translateX(0); }
    .toast-success { background: #2EC4B6; color: white; }
    .toast-error { background: #E84040; color: white; }
    .toast-warning { background: #FF9F1C; color: white; }
    .toast-info { background: #6366f1; color: white; }
  `;
  document.head.appendChild(style);
  return div;
}

// ─── Helpers ───────────────────────────────────────────────────────────────

function getCookie(name) {
  const val = `; ${document.cookie}`;
  const parts = val.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return '';
}

// ─── Map (Leaflet.js) ──────────────────────────────────────────────────────

function initMap(lat, lng, services) {
  if (!window.L) return;
  const mapEl = document.getElementById('map-container');
  if (!mapEl) return;

  const map = L.map('map-container').setView([lat || 41.2995, lng || 69.2401], 12);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
  }).addTo(map);

  if (lat && lng) {
    const userIcon = L.divIcon({
      className: '',
      html: '<div style="background:#E84040;color:white;width:32px;height:32px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:1rem;border:3px solid white;box-shadow:0 2px 8px rgba(0,0,0,0.3);">📍</div>',
      iconSize: [32, 32],
      iconAnchor: [16, 16]
    });
    L.marker([lat, lng], { icon: userIcon }).addTo(map).bindPopup('Siz shu yerdasiz');
  }

  if (services && services.length) {
    services.forEach(s => {
      const marker = L.marker([s.lat, s.lng]).addTo(map);
      marker.bindPopup(`
        <strong>${s.name}</strong><br>
        ${s.address}<br>
        ⭐ ${s.rating} | ${s.distance} km
        <br><a href="/services/${s.id}/">Ko'rish →</a>
      `);
    });
    const group = L.featureGroup(services.map(s => L.marker([s.lat, s.lng])));
    map.fitBounds(group.getBounds().pad(0.1));
  }

  return map;
}

window.initMapWithServices = initMap;

// ─── Init ──────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  ThemeManager.init();
  OTPManager.init();
  StarRating.init();
  initImageUpload();

  // Auto-dismiss alerts
  document.querySelectorAll('.alert-smart[data-autodismiss]').forEach(el => {
    setTimeout(() => {
      el.style.opacity = '0';
      el.style.transform = 'translateY(-10px)';
      setTimeout(() => el.remove(), 300);
    }, 4000);
  });

  // Role selector in registration
  document.querySelectorAll('.role-option').forEach(option => {
    option.addEventListener('click', () => {
      document.querySelectorAll('.role-option').forEach(o => o.classList.remove('active'));
      option.classList.add('active');
      const role = option.dataset.role;
      document.getElementById('role-input').value = role;
      document.querySelectorAll('.role-form-section').forEach(sec => {
        sec.style.display = sec.dataset.role === role || sec.dataset.role === 'common' ? 'block' : 'none';
      });
    });
  });

  // Viloyat change → load tumans
  const viloyatSelect = document.getElementById('viloyat-select');
  if (viloyatSelect) {
    viloyatSelect.addEventListener('change', (e) => {
      loadTumans(e.target.value);
    });
  }

  // Location button
  const locBtn = document.getElementById('locate-me-btn');
  if (locBtn) {
    locBtn.addEventListener('click', () => {
      locBtn.innerHTML = '<span class="spinner"></span>';
      GeoManager.requestLocation((lat, lng) => {
        locBtn.innerHTML = '📍 Joylashuvingiz topildi';
        GeoManager.updateURL();
      });
    });
  }
});
