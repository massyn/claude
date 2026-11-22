// Makes a whole table row clickable: <tr data-href="...">. Links inside the row still work as normal.
document.querySelectorAll('tr[data-href]').forEach((row) => {
    row.addEventListener('click', (event) => {
        if (event.target.closest('a, button, input, select, label')) return;
        window.location.href = row.dataset.href;
    });
});
