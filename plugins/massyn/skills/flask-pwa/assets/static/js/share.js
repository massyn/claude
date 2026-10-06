// Share buttons: <button data-share-url="..." data-share-title="..." data-share-text="...">.
// Opens the phone's share sheet where there is one; otherwise copies the link (or text).
// data-share-fallback="element-id" clicks that element instead of copying (e.g. to open a modal).
// window.pwaToast(message) shows the same toast from other scripts.
(function () {
  let toast = null;
  let toastTimer = null;

  function say(message) {
    if (!toast) {
      toast = document.createElement('div');
      toast.className = 'pwa-toast';
      toast.setAttribute('role', 'status');
      document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove('show'), 2200);
  }

  window.pwaToast = say;

  document.querySelectorAll('[data-share-url], [data-share-text]').forEach(btn => {
    btn.addEventListener('click', async () => {
      const data = {};
      if (btn.dataset.shareTitle) data.title = btn.dataset.shareTitle;
      if (btn.dataset.shareText) data.text = btn.dataset.shareText;
      if (btn.dataset.shareUrl) data.url = btn.dataset.shareUrl;
      if (navigator.share && (!navigator.canShare || navigator.canShare(data))) {
        try {
          await navigator.share(data);
          return;
        } catch (err) {
          if (err && err.name === 'AbortError') return;  // the user closed the share sheet
        }
      }
      const fallback = btn.dataset.shareFallback;
      if (fallback) {
        document.getElementById(fallback).click();
        return;
      }
      try {
        await navigator.clipboard.writeText(data.url || data.text);
        say(data.url ? 'Link copied' : 'Copied');
      } catch (err) {
        say('Could not copy. Long-press the address bar to share.');
      }
    });
  });
})();
