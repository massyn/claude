// Registers the root service worker. Loaded as
// <script src=".../pwa.js" data-sw="{{ url_for('pwa.service_worker') }}"></script>
// so the worker URL comes from url_for and no inline script is needed under the CSP.
(function () {
  const swUrl = document.currentScript && document.currentScript.dataset.sw;
  if (!swUrl || !('serviceWorker' in navigator)) return;
  navigator.serviceWorker.register(swUrl);
})();
