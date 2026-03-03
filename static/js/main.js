// ─── Nav scroll effect ────────────────────────────────────────────
const nav = document.getElementById('nav');
if (nav) {
  window.addEventListener('scroll', () => {
    nav.classList.toggle('scrolled', window.scrollY > 60);
  }, { passive: true });
}

// ─── Reveal on scroll ─────────────────────────────────────────────
const reveals = document.querySelectorAll('.reveal');
const observer = new IntersectionObserver((entries) => {
  entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('visible'); } });
}, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });
reveals.forEach(r => observer.observe(r));

// ─── Skill bar animation ──────────────────────────────────────────
const skillFills = document.querySelectorAll('.skill-fill');
const skillObserver = new IntersectionObserver((entries) => {
  entries.forEach(e => {
    if (e.isIntersecting) {
      const el = e.target;
      el.style.width = el.dataset.width + '%';
      skillObserver.unobserve(el);
    }
  });
}, { threshold: 0.3 });
skillFills.forEach(s => skillObserver.observe(s));

// ─── Smooth active nav links ──────────────────────────────────────
const sections = document.querySelectorAll('section[id]');
const navLinks = document.querySelectorAll('.nav-links a');
const sectionObserver = new IntersectionObserver((entries) => {
  entries.forEach(e => {
    if (e.isIntersecting) {
      navLinks.forEach(l => {
        l.style.color = '';
        if (l.getAttribute('href') === '#' + e.target.id) {
          l.style.color = 'var(--text)';
        }
      });
    }
  });
}, { threshold: 0.4 });
sections.forEach(s => sectionObserver.observe(s));

// ─── Mobile hamburger ─────────────────────────────────────────────
const toggle = document.getElementById('navToggle');
if (toggle) {
  let open = false;
  const links = document.querySelector('.nav-links');
  toggle.addEventListener('click', () => {
    open = !open;
    if (links) links.style.display = open ? 'flex' : '';
    if (links) links.style.flexDirection = open ? 'column' : '';
    if (links) links.style.position = open ? 'fixed' : '';
    if (links) links.style.top = open ? '60px' : '';
    if (links) links.style.left = open ? '0' : '';
    if (links) links.style.right = open ? '0' : '';
    if (links) links.style.background = open ? 'var(--bg-2)' : '';
    if (links) links.style.padding = open ? '2rem' : '';
    if (links) links.style.borderTop = open ? '1px solid var(--border)' : '';
  });
}
