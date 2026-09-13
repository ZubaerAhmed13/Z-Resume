(() => {
  'use strict';

  const FIELD_NAMES = Object.freeze({
    jobTitle: 'Job title',
    company: 'Company',
    location: 'Location',
    startDate: 'Start date',
    endDate: 'End date',
    degree: 'Degree',
    school: 'School',
    description: 'Description',
    name: 'Name',
    title: 'Title',
    role: 'Role',
    organization: 'Organization',
    institution: 'Institution',
    issuer: 'Issuer',
    year: 'Year',
    dates: 'Dates',
    link: 'Link',
    credentialURL: 'Credential URL',
    contact: 'Contact',
    level: 'Proficiency level'
  });

  function humanizeField(field) {
    if (!field) return 'Resume field';
    if (FIELD_NAMES[field]) return FIELD_NAMES[field];
    return field
      .replace(/([a-z0-9])([A-Z])/g, '$1 $2')
      .replace(/[_-]+/g, ' ')
      .replace(/^./, c => c.toUpperCase());
  }

  function entryContext(control) {
    const entry = control.closest('.entry');
    if (!entry) return '';
    const title = entry.querySelector('.entry-title');
    const text = title && title.textContent ? title.textContent.trim() : '';
    return text && !/^entry\s*\d*$/i.test(text) ? text : '';
  }

  function accessibleNameFor(control) {
    const field = control.dataset.field || '';
    if (field === 'level' && control.closest('#languages-list')) {
      const entry = control.closest('.entry');
      const language = entry && entry.querySelector('input[data-field="name"]');
      const value = language && language.value ? language.value.trim() : '';
      return value ? `${value} proficiency level` : 'Language proficiency level';
    }
    const base = humanizeField(field);
    const context = entryContext(control);
    return context ? `${context}: ${base}` : base;
  }

  function labelDynamicControls(root = document) {
    const controls = root.querySelectorAll
      ? root.querySelectorAll('input[data-field], textarea[data-field], select[data-field]')
      : [];
    controls.forEach(control => {
      if (control.type === 'checkbox' || control.type === 'radio') return;
      if (control.getAttribute('aria-label') || control.getAttribute('aria-labelledby')) return;
      if (control.labels && control.labels.length) return;
      control.setAttribute('aria-label', accessibleNameFor(control));
    });
  }

  labelDynamicControls();

  if (document.body && typeof MutationObserver !== 'undefined') {
    const observer = new MutationObserver(records => {
      for (const record of records) {
        for (const node of record.addedNodes) {
          if (node.nodeType !== Node.ELEMENT_NODE) continue;
          if (node.matches && node.matches('input[data-field], textarea[data-field], select[data-field]')) {
            labelDynamicControls(node.parentElement || document);
          } else {
            labelDynamicControls(node);
          }
        }
      }
    });
    observer.observe(document.body, { childList: true, subtree: true });
  }
})();
