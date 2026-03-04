const nav = document.querySelector('#site-nav');
const menuToggle = nav ? document.querySelector(`.menu-toggle[aria-controls="${nav.id}"]`) : null;

if (menuToggle && nav) {
  const firstNavLink = nav.querySelector('a');

  const closeMenu = (returnFocus = true) => {
    nav.classList.remove('open');
    menuToggle.setAttribute('aria-expanded', 'false');
    if (returnFocus) {
      menuToggle.focus();
    }
  };

  menuToggle.addEventListener('click', () => {
    const isOpen = nav.classList.toggle('open');
    menuToggle.setAttribute('aria-expanded', String(isOpen));
    if (isOpen) {
      firstNavLink?.focus();
    }
  });

  nav.querySelectorAll('a').forEach((link) => {
    link.addEventListener('click', () => {
      closeMenu(false);
    });
  });

  window.addEventListener('resize', () => {
    if (window.innerWidth > 860) {
      closeMenu(false);
    }
  });

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && nav.classList.contains('open')) {
      closeMenu();
    }
  });

  document.addEventListener('click', (event) => {
    if (!nav.classList.contains('open')) {
      return;
    }

    const target = event.target;
    if (!(target instanceof Node)) {
      return;
    }

    if (!nav.contains(target) && !menuToggle.contains(target)) {
      closeMenu();
    }
  });
}

const ctaMoreTriggers = document.querySelectorAll('[data-cta-more]');

ctaMoreTriggers.forEach((trigger) => {
  trigger.addEventListener('click', () => {
    const parent = trigger.closest('.menu-links[data-collapsible="true"]');
    if (!(parent instanceof HTMLElement)) {
      return;
    }

    const isExpanded = parent.classList.toggle('is-expanded');
    trigger.setAttribute('aria-expanded', String(isExpanded));
    trigger.textContent = isExpanded ? 'Show fewer options' : 'More options';
  });
});

const pitSlideshows = document.querySelectorAll('.pit-slideshow');

pitSlideshows.forEach((slideshow) => {
  const slides = Array.from(slideshow.querySelectorAll('input[type="radio"][name="pit-slide"]'));
  const pickerLabels = Array.from(slideshow.querySelectorAll('.pit-slide-picker label[for]'));
  const autoplayDelayMs = 5000;
  const interactionPauseMs = 12000;
  const reduceMotionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');

  if (slides.length < 2) {
    return;
  }

  let autoplayTimeoutId = null;
  let resumeTimeoutId = null;

  const getActiveSlideIndex = () => {
    const checkedIndex = slides.findIndex((slideInput) => slideInput.checked);
    return checkedIndex >= 0 ? checkedIndex : 0;
  };

  const setActiveSlide = (slideIndex) => {
    const normalizedIndex = ((slideIndex % slides.length) + slides.length) % slides.length;
    slides[normalizedIndex].checked = true;
    syncPickerState();
  };

  const showNextSlide = () => {
    setActiveSlide(getActiveSlideIndex() + 1);
  };

  const clearTimers = () => {
    if (autoplayTimeoutId !== null) {
      window.clearTimeout(autoplayTimeoutId);
      autoplayTimeoutId = null;
    }

    if (resumeTimeoutId !== null) {
      window.clearTimeout(resumeTimeoutId);
      resumeTimeoutId = null;
    }
  };

  const startAutoplay = (delayMs = autoplayDelayMs) => {
    if (reduceMotionQuery.matches) {
      return;
    }

    if (autoplayTimeoutId !== null) {
      window.clearTimeout(autoplayTimeoutId);
    }

    autoplayTimeoutId = window.setTimeout(() => {
      showNextSlide();
      startAutoplay(autoplayDelayMs);
    }, delayMs);
  };

  const deferAutoplayAfterInteraction = () => {
    clearTimers();
    startAutoplay(interactionPauseMs);
  };

  const syncPickerState = () => {
    const activeSlideId = slides[getActiveSlideIndex()]?.id;

    pickerLabels.forEach((label) => {
      const labelTarget = label.getAttribute('for');
      const isActive = labelTarget === activeSlideId;
      label.setAttribute('aria-selected', String(isActive));
      label.setAttribute('tabindex', isActive ? '0' : '-1');
    });
  };

  pickerLabels.forEach((label) => {
    label.addEventListener('keydown', (event) => {
      if (event.key !== 'Enter' && event.key !== ' ') {
        return;
      }

      const targetSlideId = label.getAttribute('for');
      if (!targetSlideId) {
        return;
      }

      event.preventDefault();
      const targetSlide = document.getElementById(targetSlideId);
      if (targetSlide instanceof HTMLInputElement) {
        targetSlide.checked = true;
        syncPickerState();
        deferAutoplayAfterInteraction();
      }
    });

    label.addEventListener('click', () => {
      syncPickerState();
      deferAutoplayAfterInteraction();
    });
  });

  slides.forEach((slideInput) => {
    slideInput.addEventListener('change', syncPickerState);
  });

  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      clearTimers();
      return;
    }

    startAutoplay();
  });

  reduceMotionQuery.addEventListener('change', () => {
    if (reduceMotionQuery.matches) {
      clearTimers();
      return;
    }

    startAutoplay();
  });

  syncPickerState();
  startAutoplay();
});

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
    const defaultTarget = slideButtons[0]?.getAttribute('data-slide-target') || slideFrames[0]?.getAttribute('data-slide-frame');
    if (defaultTarget) {
      showSlide(defaultTarget);
    }
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


const signupForm = document.querySelector('[data-signup-form]');

if (signupForm instanceof HTMLFormElement) {
  const submitButton = signupForm.querySelector('[data-signup-submit]');
  const messageNode = signupForm.querySelector('[data-signup-message]');
  const sourceField = signupForm.querySelector('[data-signup-source]');
  const actionUrl = signupForm.getAttribute('action') || '/api/subscribe';
  const parsedActionUrl = new URL(actionUrl, window.location.origin);
  const isGoogleFormEndpoint =
    parsedActionUrl.hostname === 'docs.google.com' && parsedActionUrl.pathname.includes('/forms/');

  if (isGoogleFormEndpoint) {
    signupForm.querySelectorAll('[data-google-entry]').forEach((field) => {
      if (!(field instanceof HTMLInputElement)) {
        return;
      }

      const googleEntry = field.getAttribute('data-google-entry');
      if (googleEntry && googleEntry.startsWith('entry.')) {
        field.setAttribute('name', googleEntry);
      }
    });
  }

  if (sourceField instanceof HTMLInputElement) {
    sourceField.value = window.location.pathname || '/';
  }

  const setMessage = (message, state = '') => {
    if (!(messageNode instanceof HTMLElement)) {
      return;
    }

    messageNode.textContent = message;
    if (state) {
      messageNode.setAttribute('data-state', state);
    } else {
      messageNode.removeAttribute('data-state');
    }
  };

  signupForm.addEventListener('submit', async (event) => {
    if (!signupForm.reportValidity()) {
      event.preventDefault();
      setMessage('Please complete the required fields to subscribe.', 'error');
      return;
    }

    if (isGoogleFormEndpoint) {
      setMessage('Sending your signup to our newsletter sheet...');
      return;
    }

    event.preventDefault();

    const endpoint = actionUrl;
    const formData = new FormData(signupForm);

    signupForm.setAttribute('data-busy', 'true');
    if (submitButton instanceof HTMLButtonElement) {
      submitButton.disabled = true;
    }
    setMessage('Submitting your request...');

    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          Accept: 'application/json',
        },
        body: formData,
      });
      const payload = await response.json().catch(() => null);
      const responseMessage = payload && typeof payload.message === 'string'
        ? payload.message
        : 'We could not process your signup right now. Please try again.';

      if (!response.ok) {
        setMessage(responseMessage, 'error');
        return;
      }

      signupForm.reset();
      if (sourceField instanceof HTMLInputElement) {
        sourceField.value = window.location.pathname || '/';
      }
      setMessage(responseMessage, 'success');
    } catch (error) {
      setMessage('A network issue prevented signup. Please try again in a moment.', 'error');
    } finally {
      signupForm.removeAttribute('data-busy');
      if (submitButton instanceof HTMLButtonElement) {
        submitButton.disabled = false;
      }
    }
  });
}
