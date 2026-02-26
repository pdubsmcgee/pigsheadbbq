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

const menuTemplate = document.querySelector('#menu-template[data-menu-sheet]');

const isPublishedSheetUrl = (url) =>
  /^https:\/\/docs\.google\.com\/spreadsheets\/d\/e\/.+\/pub\?output=csv(?:&.*)?$/i.test(url);

const parseCsvLine = (line) => {
  const values = [];
  let current = '';
  let inQuotes = false;

  for (let i = 0; i < line.length; i += 1) {
    const char = line[i];
    const next = line[i + 1];

    if (char === '"') {
      if (inQuotes && next === '"') {
        current += '"';
        i += 1;
      } else {
        inQuotes = !inQuotes;
      }
    } else if (char === ',' && !inQuotes) {
      values.push(current.trim());
      current = '';
    } else {
      current += char;
    }
  }

  values.push(current.trim());
  return values;
};

const hydrateMenuFromGoogleSheet = async () => {
  if (!menuTemplate) return;

  const sheetUrl = menuTemplate.dataset.menuSheet || '';
  if (!isPublishedSheetUrl(sheetUrl)) return;

  try {
    const response = await fetch(sheetUrl);
    if (!response.ok) return;

    const csvText = await response.text();
    const lines = csvText.split(/\r?\n/).filter(Boolean);
    const rows = lines.map(parseCsvLine);
    const [header, ...items] = rows;

    if (!header || items.length === 0) return;

    const categoryIx = header.findIndex((value) => value.toLowerCase() === 'category');
    const itemIx = header.findIndex((value) => value.toLowerCase() === 'item');
    const descriptionIx = header.findIndex((value) => value.toLowerCase() === 'description');
    const priceIx = header.findIndex((value) => value.toLowerCase() === 'price');

    if (categoryIx < 0 || itemIx < 0) return;

    const grouped = new Map();
    items.forEach((row) => {
      const category = row[categoryIx] || 'Menu';
      if (!grouped.has(category)) grouped.set(category, []);

      grouped.get(category).push({
        item: row[itemIx],
        description: descriptionIx >= 0 ? row[descriptionIx] : '',
        price: priceIx >= 0 ? row[priceIx] : '',
      });
    });

    const cards = [...grouped.entries()].slice(0, 8);

    if (cards.length > 0) {
      const fragment = document.createDocumentFragment();

      cards.forEach(([category, categoryItems]) => {
        const card = document.createElement('article');
        card.className = 'card';

        const categoryHeading = document.createElement('h3');
        categoryHeading.textContent = category;
        card.appendChild(categoryHeading);

        categoryItems.slice(0, 6).forEach(({ item, description, price }) => {
          const paragraph = document.createElement('p');
          const itemName = document.createElement('strong');
          itemName.textContent = item;
          paragraph.appendChild(itemName);

          const descriptionText = document.createElement('span');
          descriptionText.textContent = description;
          const priceText = document.createElement('span');
          priceText.textContent = price;

          const detailNodes = [descriptionText, priceText].filter((node) => node.textContent);
          if (detailNodes.length > 0) {
            paragraph.appendChild(document.createTextNode(' — '));
            detailNodes.forEach((node, index) => {
              if (index > 0) {
                paragraph.appendChild(document.createTextNode(' • '));
              }
              paragraph.appendChild(node);
            });
          }

          card.appendChild(paragraph);
        });

        fragment.appendChild(card);
      });

      menuTemplate.replaceChildren();
      menuTemplate.appendChild(fragment);
    }
  } catch {
    // Keep fallback template cards if Google Sheets fetch fails.
  }
};

hydrateMenuFromGoogleSheet();

const uploadInput = document.querySelector('#photo-upload-input');
const uploadGallery = document.querySelector('#uploaded-photo-gallery');
const clearUploadsButton = document.querySelector('#clear-uploaded-photos');
const UPLOAD_STORAGE_KEY = 'phbbq_uploaded_photos';
const MAX_STORED_IMAGES = 12;

const readStoredUploads = () => {
  try {
    const storedValue = localStorage.getItem(UPLOAD_STORAGE_KEY);
    const parsed = storedValue ? JSON.parse(storedValue) : [];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
};

const writeStoredUploads = (uploads) => {
  try {
    localStorage.setItem(UPLOAD_STORAGE_KEY, JSON.stringify(uploads.slice(0, MAX_STORED_IMAGES)));
  } catch {
    // Ignore write failures (for example in private mode with limited storage).
  }
};

const renderUploads = () => {
  if (!uploadGallery) return;

  const uploads = readStoredUploads();
  uploadGallery.replaceChildren();

  if (uploads.length === 0) {
    const emptyState = document.createElement('p');
    emptyState.className = 'upload-empty card';
    emptyState.textContent = 'No photos uploaded yet. Use the picker above to add images.';
    uploadGallery.appendChild(emptyState);
    return;
  }

  const fragment = document.createDocumentFragment();
  uploads.forEach((upload) => {
    const figure = document.createElement('figure');
    figure.className = 'uploaded-photo card';

    const image = document.createElement('img');
    image.src = upload.dataUrl;
    image.alt = upload.name ? `Uploaded photo: ${upload.name}` : 'Uploaded customer photo';

    const caption = document.createElement('figcaption');
    caption.textContent = upload.name || 'Uploaded image';

    figure.appendChild(image);
    figure.appendChild(caption);
    fragment.appendChild(figure);
  });

  uploadGallery.appendChild(fragment);
};

if (uploadInput && uploadGallery) {
  renderUploads();

  uploadInput.addEventListener('change', async (event) => {
    const selectedFiles = Array.from(event.target.files || []).filter((file) => file.type.startsWith('image/'));
    if (selectedFiles.length === 0) return;

    const existingUploads = readStoredUploads();
    const availableSlots = Math.max(MAX_STORED_IMAGES - existingUploads.length, 0);
    const filesToStore = selectedFiles.slice(0, availableSlots);

    const newUploads = await Promise.all(
      filesToStore.map(
        (file) =>
          new Promise((resolve) => {
            const reader = new FileReader();
            reader.onload = () => resolve({ name: file.name, dataUrl: reader.result });
            reader.onerror = () => resolve(null);
            reader.readAsDataURL(file);
          }),
      ),
    );

    const validUploads = newUploads.filter(Boolean);
    if (validUploads.length > 0) {
      writeStoredUploads([...validUploads, ...existingUploads]);
      renderUploads();
    }

    uploadInput.value = '';
  });

  clearUploadsButton?.addEventListener('click', () => {
    localStorage.removeItem(UPLOAD_STORAGE_KEY);
    renderUploads();
  });
}
