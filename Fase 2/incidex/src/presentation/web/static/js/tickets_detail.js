(function(){
  // Utilidad para modales (abrir/cerrar + confirm)
  function wireModal(modalId, onConfirm){
    const modal = document.getElementById(modalId);
    if (!modal) return { open: ()=>{}, close: ()=>{} };

    const closeBtn   = modal.querySelector('.modal__close');
    const cancelBtn  = modal.querySelector('.modal__cancel, .assign__cancel') || modal.querySelector('.modal__cancel') || modal.querySelector('.assign__cancel');
    const confirmBtn = modal.querySelector('.modal__confirm, .assign__confirm');
    const input      = modal.querySelector('input, textarea');

    const open = () => { modal.hidden = false; document.body.style.overflow = 'hidden'; input && input.focus(); }
    const close = () => { modal.hidden = true;  document.body.style.overflow = ''; }

    closeBtn?.addEventListener('click', close);
    cancelBtn?.addEventListener('click', close);
    modal.addEventListener('click', (e)=>{ if (e.target.classList.contains('modal__backdrop')) close(); });
    confirmBtn?.addEventListener('click', ()=>{ onConfirm(input ? input.value : ''); close(); });

    return { open, close };
  }

  // ===== Cambio de estado =====
  const stateSelect = document.getElementById('to_status_id_select');
  const stateForm   = document.getElementById('stateForm');
  const hiddenTo    = document.getElementById('hidden_to_status_id');
  const hiddenNote  = document.getElementById('hidden_note');
  const initialState= stateSelect?.getAttribute('data-prev') || '';

  const stateModal = wireModal('noteModal', function(noteValue){
    hiddenTo.value   = stateSelect.value;
    hiddenNote.value = noteValue || '';
    stateForm.submit();
  });

  stateSelect?.addEventListener('change', function(){
    // Si quedó vacío o igual al valor anterior, no abrir
    const prev = this.getAttribute('data-prev') || '';
    if (!this.value || this.value === prev) return;

    // Abrir modal; si cancelan, volver al valor anterior
    const revert = () => { this.value = prev; };
    const cancelBtn = document.querySelector('#noteModal .modal__cancel');
    const closeBtn  = document.querySelector('#noteModal .modal__close');
    const backdrop  = document.querySelector('#noteModal .modal__backdrop');

    const attachRevert = () => {
      const handler = ()=>{ this.value = prev; cancelBtn?.removeEventListener('click', handler); closeBtn?.removeEventListener('click', handler); backdrop?.removeEventListener('click', backdropHandler); };
      const backdropHandler = (e)=>{ if (e.target.classList.contains('modal__backdrop')) handler(); }
      cancelBtn?.addEventListener('click', handler);
      closeBtn?.addEventListener('click', handler);
      backdrop?.addEventListener('click', backdropHandler);
    };

    attachRevert();
    stateModal.open();
    // Si confirman, actualizamos el prev para siguientes cambios
    const oldSubmit = stateForm.onsubmit;
    stateForm.onsubmit = ()=>{ this.setAttribute('data-prev', this.value); if (oldSubmit) oldSubmit(); };
  });

  // ===== Reasignación =====
  const assignSelect     = document.getElementById('assignee_id_select');
  const assignForm       = document.getElementById('assignForm');
  const hiddenAssignee   = document.getElementById('hidden_assignee_id');
  const hiddenAssignNote = document.getElementById('hidden_assign_note');

  const assignModal = wireModal('assignModal', function(noteValue){
    hiddenAssignee.value   = assignSelect.value;
    hiddenAssignNote.value = noteValue || '';
    assignForm.submit();
  });

  assignSelect?.addEventListener('change', function(){
    const prev = this.getAttribute('data-prev') || '';
    if (!this.value || this.value === prev) return;

    const cancelBtn = document.querySelector('#assignModal .assign__cancel');
    const closeBtn  = document.querySelector('#assignModal .modal__close');
    const backdrop  = document.querySelector('#assignModal .modal__backdrop');

    const handler = ()=>{ this.value = prev; cancelBtn?.removeEventListener('click', handler); closeBtn?.removeEventListener('click', handler); backdrop?.removeEventListener('click', backdropHandler); };
    const backdropHandler = (e)=>{ if (e.target.classList.contains('modal__backdrop')) handler(); }

    cancelBtn?.addEventListener('click', handler);
    closeBtn?.addEventListener('click', handler);
    backdrop?.addEventListener('click', backdropHandler);

    assignModal.open();
    const oldSubmit = assignForm.onsubmit;
    assignForm.onsubmit = ()=>{ this.setAttribute('data-prev', this.value); if (oldSubmit) oldSubmit(); };
  });

  // ===== Custom file input (se mantiene) =====
  const fileInput = document.getElementById('fileInput');
  const list = document.getElementById('uploadFiles');
  fileInput?.addEventListener('change', function(){
    list.innerHTML = '';
    if (!this.files || !this.files.length) return;
    const f = this.files[0];
    const li = document.createElement('li');
    li.textContent = `${f.name} (${f.size} bytes)`;
    list.appendChild(li);
  });
})();