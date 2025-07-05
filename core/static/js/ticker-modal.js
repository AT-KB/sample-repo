// Fetch tickers on demand and fill the search modal
document.addEventListener('DOMContentLoaded', () => {
  const modal = document.getElementById('tickerModal');
  if (!modal) return;
  const body = modal.querySelector('.modal-body');
  body.innerHTML = `
    <input type="text" id="ticker-search-input" class="form-control mb-2" placeholder="銘柄コードまたは会社名" />
    <ul class="list-group" id="ticker-search-results"></ul>
  `;
  const input = body.querySelector('#ticker-search-input');
  const results = body.querySelector('#ticker-search-results');
  let targetInput = null;
  document.querySelectorAll('.ticker-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      targetInput = document.querySelector(btn.dataset.input);
      input.value = '';
      results.innerHTML = '';
    });
  });
  input.addEventListener('input', () => {
    const q = input.value.trim();
    if (!q) {
      results.innerHTML = '';
      return;
    }
    fetch(`/api/tickers/search/?q=${encodeURIComponent(q)}`)
      .then(r => r.json())
      .then(data => {
        results.innerHTML = '';
        data.forEach(t => {
          const li = document.createElement('li');
          li.className = 'list-group-item list-group-item-action';
          li.textContent = `${t.code} ${t.name}`;
          li.addEventListener('click', () => {
            if (targetInput) targetInput.value = t.code;
            const inst = bootstrap.Modal.getInstance(modal);
            inst.hide();
          });
          results.appendChild(li);
        });
      });
  });
});
