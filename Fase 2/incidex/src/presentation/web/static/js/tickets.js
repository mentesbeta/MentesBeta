(function () {
  const wizard = document.querySelector('.ticket-wizard');
  if (!wizard) return;

  // =============================
  // Spinner IA + bloqueo del wizard
  // =============================
  const aiSpinner = document.getElementById('aiSpinner');

  function toggleNavButtons(disabled) {
    wizard.querySelectorAll('.js-next, .js-prev').forEach(btn => {
      btn.disabled = disabled;
    });
  }

  function showAISpinner() {
    if (aiSpinner) aiSpinner.hidden = false;
    wizard.classList.add('is-busy');   // bloquea el wizard con overlay (CSS)
    toggleNavButtons(true);
  }

  function hideAISpinner() {
    if (aiSpinner) aiSpinner.hidden = true;
    wizard.classList.remove('is-busy');
    toggleNavButtons(false);
  }

  // asegurar estado inicial
  hideAISpinner();

  // =============================
  // 0) Cargar mapa analistas por depto (respeta url_prefix '/app')
  // =============================
  let ANALYSTS_BY_DEPT = {};
  let ABD_READY = false;
  let pendingDept = null;

  fetch('/app/analysts/by-dept')
    .then(r => r.json())
    .then(data => {
      ANALYSTS_BY_DEPT = data || {};
      ABD_READY = true;
      if (pendingDept !== null) {
        applyAssignee(pendingDept);
        pendingDept = null;
      } else {
        const areaSelectInit = document.getElementById('area');
        if (areaSelectInit) applyAssignee(areaSelectInit.value || null);
      }
    })
    .catch(err => {
      console.error('Error cargando analistas:', err);
      ABD_READY = true; // no bloquear flujo si falla
    });

  // =============================
  // 1) ACORDEÓN / WIZARD
  // =============================
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
      const curStep = parseInt(current.dataset.step, 10);

      const goNext = () => {
        openStep(curStep + 1);
        updateSummary();
      };

      // Si estamos en el paso 1, antes de avanzar pedimos sugerencia a la IA
      if (curStep === 1) {
        requestAISuggestion()
          .finally(() => {
            goNext();
          });
      } else {
        goNext();
      }
    });
  });

  wizard.querySelectorAll('.js-prev').forEach(b => {
    b.addEventListener('click', () => {
      const current = b.closest('.step');
      const n = parseInt(current.dataset.step, 10) - 1;
      openStep(n);
    });
  });

  // =============================
  // 2) ADJUNTOS con eliminar (DataTransfer)
  // =============================
  const inputFiles = document.getElementById('files');
  const fileList = document.getElementById('fileList');
  let dt = new DataTransfer();

  function renderFiles() {
    if (!fileList) return;
    fileList.innerHTML = '';
    for (let i = 0; i < dt.files.length; i++) {
      const f = dt.files[i];
      const li = document.createElement('li');
      li.className = 'file-chip';
      li.innerHTML = `
        <span>${f.name}</span>
        <button type="button" class="remove" aria-label="Quitar" data-index="${i}">×</button>
      `;
      fileList.appendChild(li);
    }
  }

  if (inputFiles && fileList) {
    inputFiles.addEventListener('change', () => {
      // Agregar nuevos archivos seleccionados al DataTransfer
      for (let i = 0; i < inputFiles.files.length; i++) {
        dt.items.add(inputFiles.files[i]);
      }

      // Mantener la lista real de archivos que el form va a enviar
      inputFiles.files = dt.files;

      renderFiles();
    });

    fileList.addEventListener('click', (e) => {
      const btn = e.target.closest('.remove');
      if (!btn) return;

      const idx = parseInt(btn.getAttribute('data-index'), 10);
      const newDt = new DataTransfer();

      for (let i = 0; i < dt.files.length; i++) {
        if (i !== idx) newDt.items.add(dt.files[i]);
      }

      dt = newDt;
      inputFiles.files = dt.files;
      renderFiles();
    });
  }

  // =============================
  // 3) RESUMEN (paso 4)
  // =============================
  function val(id){ const el = document.getElementById(id); return el ? el.value.trim() : ''; }
  function sel(id){
    const el = document.getElementById(id);
    if (!el) return '';
    const opt = el.options[el.selectedIndex];
    return opt ? (opt.text || '') : '';
  }

  function updateSummary() {
    const box = document.getElementById('summaryBox');
    if (!box) return;
    const data = {
      'Título': val('title'),
      'Descripción': val('description'),
      'Categoría': sel('category'),
      'Área': sel('area'),
      'Prioridad': sel('priority')
    };
    box.innerHTML = Object.entries(data)
      .map(([k,v]) => `<div><strong>${k}:</strong> ${v || '—'}</div>`)
      .join('');
  }

  ['title','description','category','area','priority'].forEach(id => {
    const el = document.getElementById(id);
    if (!el) return;
    const ev = (id === 'title' || id === 'description') ? 'input' : 'change';
    el.addEventListener(ev, updateSummary);
  });

  // =============================
  // 4) AUTOCOMPLETAR "ASIGNAR A" con mapa del backend
  // =============================
  const areaSelect = document.getElementById('area');
  const assigneeDisplay = document.getElementById('assignee_display'); // deshabilitado (solo visual)
  const assigneeHidden  = document.getElementById('assignee');         // se envía en el form

  function setAssignee(id) {
    if (!assigneeDisplay || !assigneeHidden) return;
    const options = Array.from(assigneeDisplay.querySelectorAll('option'));
    options.forEach(o => { o.selected = (o.value === String(id)); });
    assigneeHidden.value = String(id || 0);
  }

  function applyAssignee(deptId) {
    if (!ABD_READY) { pendingDept = deptId; return; }
    const d = deptId ? String(deptId) : null;
    const list = (d && ANALYSTS_BY_DEPT[d]) ? ANALYSTS_BY_DEPT[d] : [];
    if (list.length > 0) {
      setAssignee(list[0].id); // primer analista del depto
    } else {
      setAssignee(0); // — Sin asignar —
    }
    updateSummary();
  }

  if (areaSelect) {
    areaSelect.addEventListener('change', function() {
      applyAssignee(this.value || null);
    });
    // Al cargar, intenta aplicar con el valor actual (se diferirá si aún no llega el fetch)
    applyAssignee(areaSelect.value || null);
  }

  // =============================
  // 5) IA: pedir sugerencias
  // =============================
  function requestAISuggestion() {
    const title = val('title');
    const description = val('description');

    // Si no hay nada escrito aún, no pedimos nada
    if (!title && !description) {
      return Promise.resolve();
    }

    const payload = { title, description };

    // CSRF de Flask-WTF (tomamos el mismo token del formulario)
    const csrfInput = document.querySelector('#ticketForm input[name="csrf_token"]');
    const headers = { 'Content-Type': 'application/json' };
    if (csrfInput) {
      headers['X-CSRFToken'] = csrfInput.value;
    }

    showAISpinner();

    return fetch('/app/ai/suggest', {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
    })
      .then(async (r) => {
        if (!r.ok) {
          console.error('IA respondio HTTP no-OK:', r.status);
          try {
            const err = await r.json();
            console.error('Detalle error IA:', err);
          } catch(e){}
          return null;
        }
        return r.json();
      })
      .then(data => {
        if (!data || data.error) return;

        // Setear selects con lo sugerido (el usuario los puede cambiar después)
        if (data.category_id) {
          const sel = document.getElementById('category');
          if (sel) sel.value = String(data.category_id);
        }
        if (data.priority_id) {
          const sel = document.getElementById('priority');
          if (sel) sel.value = String(data.priority_id);
        }
        if (data.department_id) {
          const sel = document.getElementById('area');
          if (sel) {
            sel.value = String(data.department_id);
            // dispara change para auto-analista
            sel.dispatchEvent(new Event('change'));
          }
        }

        // Mensaje tipo “Sugerido por IA”
        let hint = document.getElementById('aiHint');
        if (!hint) {
          hint = document.createElement('small');
          hint.id = 'aiHint';
          hint.className = 'muted';
          const step2 = document.querySelector('.step[data-step="2"] .muted');
          if (step2 && step2.parentNode) {
            step2.parentNode.insertBefore(hint, step2.nextSibling);
          }
        }
        hint.textContent = data.reason
          ? `Sugerido por IA: ${data.reason}`
          : 'Valores sugeridos automáticamente por IA (puedes cambiarlos).';

        updateSummary();
      })
      .catch(err => {
        console.error('Error pidiendo sugerencia IA:', err);
      })
      .finally(() => {
        hideAISpinner();
      });
  }

})();