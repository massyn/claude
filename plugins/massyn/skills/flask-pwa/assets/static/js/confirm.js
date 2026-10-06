// Confirm before submitting any <form data-confirm="Question?">, using a page modal rather than
// window.confirm(), which embedded browsers can block (it then returns false and the form never submits).
// Needs templates/partials/confirm_modal.html on the page.
(function () {
  const modalEl = document.getElementById('confirm-modal');
  if (!modalEl) return;
  const modal = new bootstrap.Modal(modalEl);
  const message = document.getElementById('confirm-message');
  const ok = document.getElementById('confirm-ok');
  let pending = null;

  document.addEventListener('submit', e => {
    const form = e.target;
    if (!form.dataset.confirm) return;
    e.preventDefault();
    pending = form;
    message.textContent = form.dataset.confirm;
    // The confirm button repeats the action ("Delete trip") and keeps its danger styling.
    const submitter = e.submitter;
    ok.textContent = (submitter && submitter.textContent.trim()) || 'OK';
    const danger = submitter && /btn-(outline-)?danger/.test(submitter.className);
    ok.className = `btn ${danger ? 'btn-danger' : 'btn-primary'}`;
    modal.show();
  });

  ok.addEventListener('click', () => {
    modal.hide();
    if (pending) pending.submit();  // form.submit() skips the submit event, so this does not re-prompt
    pending = null;
  });
})();
