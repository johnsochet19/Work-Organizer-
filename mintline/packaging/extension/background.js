// Clicking the toolbar icon opens Mintline in a tab (or focuses it if already open).
chrome.action.onClicked.addListener(async () => {
  const url = chrome.runtime.getURL('index.html');
  const [tab] = await chrome.tabs.query({ url: url + '*' });
  if (tab) {
    await chrome.tabs.update(tab.id, { active: true });
    await chrome.windows.update(tab.windowId, { focused: true });
  } else {
    await chrome.tabs.create({ url });
  }
});
