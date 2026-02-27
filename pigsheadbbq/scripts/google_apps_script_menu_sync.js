/**
 * Google Apps Script: Sync Menu sheet tabs into two Slides decks.
 *
 * Required Script Properties:
 * - MENU_SPREADSHEET_ID
 * - WEBMENU_PRESENTATION_ID
 * - TRUCKMENU_PRESENTATION_ID
 */

function syncAllMenus() {
  syncWebMenu();
  syncTruckMenu();
}

function syncWebMenu() {
  var propertyStore = PropertiesService.getScriptProperties();
  var spreadsheetId = propertyStore.getProperty('MENU_SPREADSHEET_ID');
  var webmenuPresentationId = propertyStore.getProperty('WEBMENU_PRESENTATION_ID');

  var menuText = buildSectionText(spreadsheetId, 'Menu');
  var cateringText = buildSectionText(spreadsheetId, 'Catering');

  var presentation = SlidesApp.openById(webmenuPresentationId);
  presentation.replaceAllText('{{MENU_ITEMS}}', menuText);
  presentation.replaceAllText('{{CATERING_ITEMS}}', cateringText);
  presentation.saveAndClose();
}

function syncTruckMenu() {
  var propertyStore = PropertiesService.getScriptProperties();
  var spreadsheetId = propertyStore.getProperty('MENU_SPREADSHEET_ID');
  var truckmenuPresentationId = propertyStore.getProperty('TRUCKMENU_PRESENTATION_ID');

  var menuText = buildSectionText(spreadsheetId, 'Menu');

  var presentation = SlidesApp.openById(truckmenuPresentationId);
  presentation.replaceAllText('{{MENU_ITEMS}}', menuText);
  presentation.saveAndClose();
}

function buildSectionText(spreadsheetId, tabName) {
  var sheet = SpreadsheetApp.openById(spreadsheetId).getSheetByName(tabName);
  if (!sheet) {
    return tabName + ' tab not found.';
  }

  var values = sheet.getDataRange().getDisplayValues();
  if (values.length <= 1) {
    return tabName + ' is empty.';
  }

  var headers = values[0].map(function(header) {
    return String(header).trim().toLowerCase();
  });

  var categoryIndex = headers.indexOf('category');
  var itemIndex = headers.indexOf('item');
  var descriptionIndex = headers.indexOf('description');
  var priceIndex = headers.indexOf('price');

  var rows = values.slice(1).filter(function(row) {
    return row[itemIndex] && String(row[itemIndex]).trim() !== '';
  });

  var grouped = {};

  rows.forEach(function(row) {
    var category = categoryIndex >= 0 ? String(row[categoryIndex]).trim() : 'Menu Items';
    if (!category) {
      category = 'Menu Items';
    }

    var item = itemIndex >= 0 ? String(row[itemIndex]).trim() : '';
    var description = descriptionIndex >= 0 ? String(row[descriptionIndex]).trim() : '';
    var price = priceIndex >= 0 ? String(row[priceIndex]).trim() : '';

    if (!grouped[category]) {
      grouped[category] = [];
    }

    var rowText = item;
    if (price) {
      rowText += ' — $' + price.replace(/^\$/, '');
    }
    if (description) {
      rowText += ' (' + description + ')';
    }

    grouped[category].push(rowText);
  });

  var output = [];
  Object.keys(grouped).forEach(function(category) {
    output.push(category.toUpperCase());
    grouped[category].forEach(function(lineItem) {
      output.push('• ' + lineItem);
    });
    output.push('');
  });

  return output.join('\n').trim();
}
