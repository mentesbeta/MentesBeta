(function () {
  const wizard = document.querySelector('.ticket-wizard');
  if (!wizard) return;

  // Acordeón: abrir/cerrar
  wizard.querySelectorAll('.step__head').forEach(btn => {
    btn.addEventListener('click', () => {
      const step = btn.closest('.step');
      step.classList.toggle('is-open');
    });
  });

  // Next / Prev control – que sólo deje abierta la fase actual
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

  // Adjuntos: listar nombres
  const inputFiles = document.getElementById('files');
  const fileList = document.getElementById('fileList');
  if (inputFiles && fileList) {
    inputFiles.addEventListener('change', () => {
      fileList.innerHTML = '';
      Array.from(inputFiles.files || []).forEach((f, idx) => {
        const li = document.createElement('li');
        li.innerHTML = `<span>${f.name}</span> <button type="button" aria-label="Eliminar adjunto">&times;</button>`;
        li.querySelector('button').addEventListener('click', () => {
          // Eliminar visualmente (nota: para eliminar real, habría que reconstruir FileList)
          li.remove();
        });
        fileList.appendChild(li);
      });
    });
  }

  // Resumen simple
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
      Prioridad: sel('priority'),
      'Usuario solicitante': val('requester'),
      'Asignar a': val('assignee'),
      'Estado inicial': val('initial_status')
    };
    box.innerHTML = Object.entries(data)
      .map(([k,v]) => `<div><strong>${k}:</strong> ${v || '—'}</div>`)
      .join('');
  }

  // Submit ficticio (quitar al tener backend real)
  const form = document.getElementById('ticketForm');
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    updateSummary();
    alert('✅ Ticket enviado (demo). Integra aquí la lógica de guardado.');
  });
})();