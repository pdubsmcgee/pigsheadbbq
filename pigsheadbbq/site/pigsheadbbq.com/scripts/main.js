const nav = document.querySelector('#site-nav');
const menuToggle = nav ? document.querySelector(`.menu-toggle[aria-controls="${nav.id}"]`) : null;

if (menuToggle && nav) {
  const closeMenu = () => {
    nav.classList.remove('open');
    menuToggle.setAttribute('aria-expanded', 'false');
  };

  menuToggle.addEventListener('click', () => {
    const isOpen = nav.classList.toggle('open');
    menuToggle.setAttribute('aria-expanded', String(isOpen));
  });

  nav.querySelectorAll('a').forEach((link) => {
    link.addEventListener('click', () => {
      closeMenu();
    });
  });

  window.addEventListener('resize', () => {
    if (window.innerWidth > 940) {
      closeMenu();
    }
  });
}

const widgetTriggers = document.querySelectorAll('[data-menu-widget-trigger]');

widgetTriggers.forEach((trigger) => {
  const modalId = trigger.getAttribute('data-menu-widget-trigger');
  if (!modalId) {
    return;
  }

  const modal = document.getElementById(modalId);
  if (!(modal instanceof HTMLDialogElement)) {
    return;
  }

  const closeButton = modal.querySelector('[data-menu-widget-close]');
  const slideButtons = modal.querySelectorAll('[data-slide-target]');
  const slideFrames = modal.querySelectorAll('[data-slide-frame]');

  const showSlide = (targetName) => {
    slideFrames.forEach((slideFrame) => {
      const frameName = slideFrame.getAttribute('data-slide-frame');
      slideFrame.hidden = frameName !== targetName;
    });

    slideButtons.forEach((slideButton) => {
      const buttonName = slideButton.getAttribute('data-slide-target');
      const isActive = buttonName === targetName;
      slideButton.setAttribute('aria-pressed', String(isActive));
    });
  };

  slideButtons.forEach((slideButton) => {
    slideButton.addEventListener('click', () => {
      const targetName = slideButton.getAttribute('data-slide-target');
      if (targetName) {
        showSlide(targetName);
      }
    });
  });

  trigger.addEventListener('click', () => {
    showSlide('webmenu');
    modal.showModal();
  });

  closeButton?.addEventListener('click', () => {
    modal.close();
  });

  modal.addEventListener('click', (event) => {
    const bounds = modal.getBoundingClientRect();
    const clickedOutside =
      event.clientX < bounds.left ||
      event.clientX > bounds.right ||
      event.clientY < bounds.top ||
      event.clientY > bounds.bottom;

    if (clickedOutside) {
      modal.close();
    }
  });
});
