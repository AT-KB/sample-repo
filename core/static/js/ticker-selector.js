const industriesUrl = "{% url 'api-industries' %}";
fetch(industriesUrl)
  .then(r => r.json())
  .then(data => {
    const ilist = document.getElementById('industry-list');
    data.forEach(ind => {
      const li = document.createElement('li');
      li.textContent = ind.name;
      li.style.cursor = 'pointer';
      li.addEventListener('click', () => {
        const tickersUrl = (id) => "{% url 'api-industry-tickers' 0 %}".replace("0", id);
        fetch(tickersUrl(ind.id))
          .then(r => r.json())
          .then(tickers => {
            const tlist = document.getElementById('ticker-list');
            tlist.innerHTML = '';
            tickers.forEach(t => {
              const ti = document.createElement('li');
              ti.textContent = `${t.code} ${t.name}`;
              ti.style.cursor = 'pointer';
              ti.addEventListener('click', () => {
                document.getElementById('ticker-code').value = t.code;
              });
              tlist.appendChild(ti);
            });
          });
      });
      ilist.appendChild(li);
    });
  });
