// Token page: copy buttons (data-copy="<element id>") and the OAuth revoke modal's token field.
(function () {
  document.addEventListener('click', e => {
    const btn = e.target.closest('[data-copy]');
    if (!btn) return;
    const el = document.getElementById(btn.dataset.copy);
    if (!el) return;
    const text = el.tagName === 'INPUT' ? el.value : el.innerText;
    navigator.clipboard.writeText(text).then(() => {
      const orig = btn.textContent;
      btn.textContent = 'Copied';
      setTimeout(() => { btn.textContent = orig; }, 2000);
    });
  });

  const oauthModal = document.getElementById('revoke-oauth-modal');
  if (oauthModal) {
    oauthModal.addEventListener('show.bs.modal', e => {
      document.getElementById('revoke-oauth-token').value = e.relatedTarget.dataset.token;
    });
  }
})();
