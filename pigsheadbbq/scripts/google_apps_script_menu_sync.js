/**
 * Google Apps Script: Build polished web and truck menu slide decks from sheet tabs.
 *
 * Required Script Properties:
 * - MENU_SPREADSHEET_ID
 * - WEBMENU_PRESENTATION_ID
 * - TRUCKMENU_PRESENTATION_ID
 *
 * Expected sheet columns:
 * - category
 * - item
 * - description
 * - price
 */

var BRAND = {
  background: '#120706',
  panel: '#22100e',
  accent: '#ff5f2a',
  accentAlt: '#ffc857',
  text: '#fff5ee',
  muted: '#e7d2c7'
};

var LAYOUT = {
  width: 960,
  height: 540,
  margin: 36,
  titleTop: 26,
  subtitleTop: 78,
  contentTop: 114,
  columnGap: 20,
  columns: 2,
  cardPadding: 16,
  cardGap: 10,
  cardHeight: 172
};

function syncAllMenus() {
  syncWebMenu();
  syncTruckMenu();
}

function syncWebMenu() {
  var propertyStore = PropertiesService.getScriptProperties();
  var spreadsheetId = propertyStore.getProperty('MENU_SPREADSHEET_ID');
  var presentationId = propertyStore.getProperty('WEBMENU_PRESENTATION_ID');

  var menuGroups = readTabAsGroups(spreadsheetId, 'Menu');
  var cateringGroups = readTabAsGroups(spreadsheetId, 'Catering');

  var sections = [
    { title: 'Weekly Menu', subtitle: 'From Menu tab', groups: menuGroups },
    { title: 'Catering', subtitle: 'From Catering tab', groups: cateringGroups }
  ];

  buildDeckFromSections(presentationId, 'Pigs Head BBQ Web Menu', sections, {
    audienceLabel: 'Website Menu',
    heroImageUrl: 'https://pigsheadbbq.com/images/siteimages/brisket.jpg'
  });
}

function syncTruckMenu() {
  var propertyStore = PropertiesService.getScriptProperties();
  var spreadsheetId = propertyStore.getProperty('MENU_SPREADSHEET_ID');
  var presentationId = propertyStore.getProperty('TRUCKMENU_PRESENTATION_ID');

  var menuGroups = readTabAsGroups(spreadsheetId, 'Menu');

  var sections = [
    { title: 'Food Truck Menu', subtitle: 'From Menu tab', groups: menuGroups }
  ];

  buildDeckFromSections(presentationId, 'Pigs Head BBQ Truck Menu', sections, {
    audienceLabel: 'Truck TV Menu',
    heroImageUrl: 'https://pigsheadbbq.com/images/siteimages/foodtruck.jpg'
  });
}

function buildDeckFromSections(presentationId, deckTitle, sections, options) {
  var presentation = SlidesApp.openById(presentationId);
  clearDeck(presentation);

  addHeroSlide(presentation, deckTitle, options.audienceLabel, options.heroImageUrl);

  sections.forEach(function(section) {
    var slideChunks = chunkGroupsForSlides(section.groups, 4);
    if (slideChunks.length === 0) {
      slideChunks = [[{ category: 'Coming Soon', items: ['Menu updates will appear soon.'] }]];
    }

    slideChunks.forEach(function(groupChunk, index) {
      var pageTitle = section.title;
      if (slideChunks.length > 1) {
        pageTitle += ' · Page ' + (index + 1);
      }
      addContentSlide(presentation, pageTitle, section.subtitle, groupChunk);
    });
  });

  presentation.saveAndClose();
}

function clearDeck(presentation) {
  var slides = presentation.getSlides();
  slides.forEach(function(slide, index) {
    if (index > 0) {
      slide.remove();
    }
  });

  var firstSlide = presentation.getSlides()[0];
  firstSlide.getPageElements().forEach(function(element) {
    element.remove();
  });
}

function addHeroSlide(presentation, titleText, audienceText, heroImageUrl) {
  var slide = presentation.getSlides()[0];
  applyDarkBackground(slide);
  addAccentBar(slide);

  insertTextBox(slide, titleText, LAYOUT.margin, LAYOUT.titleTop, 760, 46, {
    fontSize: 34,
    color: BRAND.text,
    bold: true
  });

  insertTextBox(slide, audienceText, LAYOUT.margin, LAYOUT.subtitleTop, 360, 30, {
    fontSize: 18,
    color: BRAND.accentAlt,
    bold: true
  });

  insertTextBox(slide, 'Slow-smoked in Southwest Michigan', LAYOUT.margin, LAYOUT.subtitleTop + 34, 420, 26, {
    fontSize: 14,
    color: BRAND.muted,
    bold: false
  });

  if (heroImageUrl) {
    var imageLeft = 560;
    var imageTop = 30;
    var imageWidth = 360;
    var imageHeight = 220;
    safelyInsertImage(slide, heroImageUrl, imageLeft, imageTop, imageWidth, imageHeight);
  }

  insertFooterPill(slide, 'Auto-synced from Google Sheets');
}

function addContentSlide(presentation, heading, subtitle, groupChunk) {
  var slide = presentation.appendSlide(SlidesApp.PredefinedLayout.BLANK);
  applyDarkBackground(slide);
  addAccentBar(slide);

  insertTextBox(slide, heading, LAYOUT.margin, LAYOUT.titleTop, 760, 42, {
    fontSize: 30,
    color: BRAND.text,
    bold: true
  });

  insertTextBox(slide, subtitle, LAYOUT.margin, LAYOUT.subtitleTop, 700, 24, {
    fontSize: 13,
    color: BRAND.muted,
    bold: false
  });

  insertFooterPill(slide, 'Pigs Head BBQ · Updated ' + Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'MMM d, h:mm a'));

  var columnWidth = (LAYOUT.width - (LAYOUT.margin * 2) - LAYOUT.columnGap) / LAYOUT.columns;
  var cardWidth = columnWidth;

  groupChunk.forEach(function(group, index) {
    var columnIndex = index % LAYOUT.columns;
    var rowIndex = Math.floor(index / LAYOUT.columns);
    var left = LAYOUT.margin + (columnIndex * (columnWidth + LAYOUT.columnGap));
    var top = LAYOUT.contentTop + (rowIndex * (LAYOUT.cardHeight + LAYOUT.cardGap));

    insertCategoryCard(slide, group, left, top, cardWidth, LAYOUT.cardHeight);
  });
}

function insertCategoryCard(slide, group, left, top, width, height) {
  var card = slide.insertShape(SlidesApp.ShapeType.ROUNDED_RECTANGLE, left, top, width, height);
  card.getFill().setSolidFill(BRAND.panel);
  card.getBorder().getLineFill().setSolidFill(BRAND.accent);
  card.getBorder().setWeight(1.25);

  insertTextBox(slide, group.category, left + LAYOUT.cardPadding, top + 10, width - (LAYOUT.cardPadding * 2), 24, {
    fontSize: 16,
    color: BRAND.accentAlt,
    bold: true
  });

  var menuLines = [];
  group.items.slice(0, 6).forEach(function(itemText) {
    menuLines.push('• ' + itemText);
  });

  if (group.items.length > 6) {
    menuLines.push('• …and more');
  }

  insertTextBox(
    slide,
    menuLines.join('\n'),
    left + LAYOUT.cardPadding,
    top + 36,
    width - (LAYOUT.cardPadding * 2),
    height - 48,
    {
      fontSize: 12,
      color: BRAND.text,
      bold: false
    }
  );
}

function applyDarkBackground(slide) {
  slide.getBackground().setSolidFill(BRAND.background);
}

function addAccentBar(slide) {
  var bar = slide.insertShape(SlidesApp.ShapeType.RECTANGLE, 0, 0, LAYOUT.width, 8);
  bar.getFill().setSolidFill(BRAND.accent);
  bar.getBorder().setTransparent();
}

function insertFooterPill(slide, text) {
  var pill = slide.insertShape(SlidesApp.ShapeType.ROUNDED_RECTANGLE, LAYOUT.margin, 500, 360, 24);
  pill.getFill().setSolidFill('#1b0b0a');
  pill.getBorder().setTransparent();

  insertTextBox(slide, text, LAYOUT.margin + 12, 505, 338, 16, {
    fontSize: 10,
    color: BRAND.muted,
    bold: false
  });
}

function insertTextBox(slide, text, left, top, width, height, style) {
  var shape = slide.insertShape(SlidesApp.ShapeType.TEXT_BOX, left, top, width, height);
  shape.getBorder().setTransparent();
  shape.getFill().setTransparent();
  shape.getText().setText(text);

  var textStyle = shape.getText().getTextStyle();
  textStyle.setFontFamily('Arial');
  textStyle.setFontSize(style.fontSize);
  textStyle.setForegroundColor(style.color);
  textStyle.setBold(style.bold);
}

function safelyInsertImage(slide, imageUrl, left, top, width, height) {
  try {
    slide.insertImage(imageUrl, left, top, width, height);
  } catch (imageError) {
    insertTextBox(slide, 'Pigs Head BBQ', left + 18, top + 90, width - 36, 34, {
      fontSize: 26,
      color: BRAND.accentAlt,
      bold: true
    });
  }
}

function chunkGroupsForSlides(groups, maxGroupsPerSlide) {
  var chunks = [];
  for (var index = 0; index < groups.length; index += maxGroupsPerSlide) {
    chunks.push(groups.slice(index, index + maxGroupsPerSlide));
  }
  return chunks;
}

function readTabAsGroups(spreadsheetId, tabName) {
  var sheet = SpreadsheetApp.openById(spreadsheetId).getSheetByName(tabName);
  if (!sheet) {
    return [];
  }

  var data = sheet.getDataRange().getDisplayValues();
  if (data.length < 2) {
    return [];
  }

  var headers = data[0].map(function(headerText) {
    return String(headerText).trim().toLowerCase();
  });

  var categoryIndex = headers.indexOf('category');
  var itemIndex = headers.indexOf('item');
  var descriptionIndex = headers.indexOf('description');
  var priceIndex = headers.indexOf('price');

  var groupedMap = {};
  data.slice(1).forEach(function(rowValues) {
    var itemName = itemIndex >= 0 ? String(rowValues[itemIndex]).trim() : '';
    if (!itemName) {
      return;
    }

    var categoryName = categoryIndex >= 0 ? String(rowValues[categoryIndex]).trim() : 'Menu Items';
    if (!categoryName) {
      categoryName = 'Menu Items';
    }

    var description = descriptionIndex >= 0 ? String(rowValues[descriptionIndex]).trim() : '';
    var rawPrice = priceIndex >= 0 ? String(rowValues[priceIndex]).trim() : '';
    var displayPrice = rawPrice ? '$' + rawPrice.replace(/^\$/, '') : '';

    var lineText = itemName;
    if (displayPrice) {
      lineText += ' — ' + displayPrice;
    }
    if (description) {
      lineText += ' · ' + description;
    }

    if (!groupedMap[categoryName]) {
      groupedMap[categoryName] = [];
    }
    groupedMap[categoryName].push(lineText);
  });

  return Object.keys(groupedMap).map(function(categoryName) {
    return {
      category: categoryName,
      items: groupedMap[categoryName]
    };
  });
}
