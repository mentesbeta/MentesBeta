(function () {
  const wizard = document.querySelector('.ticket-wizard');
  if (!wizard) return;

  wizard.querySelectorAll('.step__head').forEach(btn => {
    btn.addEventListener('click', () => btn.closest('.step').classList.toggle('is-open'));
  });

  function openStep(n) {
    wizard.querySelectorAll('.step').forEach(s => s.classList.remove('is-open'));
    const step = wizard.querySelector(`.step[data-step="${n}"]`);
    if (step) step.classList.add('is-open');
  }

  wizard.querySelectorAll('.js-next').forEach(b => {
    b.addEventListener('click', () => {
      const current = b.closest('.step');
      const n = parseInt(current.dataset.step, 10) + 1;
      openStep(n);
      updateSummary();
    });
  });

  wizard.querySelectorAll('.js-prev').forEach(b => {
    b.addEventListener('click', () => {
      const current = b.closest('.step');
      const n = parseInt(current.dataset.step, 10) - 1;
      openStep(n);
    });
  });

  const inputFiles = document.getElementById('files');
  const fileList = document.getElementById('fileList');
  if (inputFiles && fileList) {
    inputFiles.addEventListener('change', () => {
      fileList.innerHTML = '';
      Array.from(inputFiles.files || []).forEach((f) => {
        const li = document.createElement('li');
        li.innerHTML = `<span>${f.name}</span>`;
        fileList.appendChild(li);
      });
    });
  }

  function val(id){ const el = document.getElementById(id); return el ? el.value.trim() : ''; }
  function sel(id){ const el = document.getElementById(id); return el ? el.options[el.selectedIndex]?.text || '' : ''; }

  function updateSummary() {
    const box = document.getElementById('summaryBox');
    if (!box) return;
    const data = {
      Título: val('title'),
      Descripción: val('description'),
      Categoría: sel('category'),
      Área: sel('area'),
      Prioridad: sel('priority')
    };
    box.innerHTML = Object.entries(data)
      .map(([k,v]) => `<div><strong>${k}:</strong> ${v || '—'}</div>`)
      .join('');
  }

  // deja que el form haga submit real al servidor
})();
