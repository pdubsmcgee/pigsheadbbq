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

