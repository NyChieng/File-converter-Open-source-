const API = {
  async convert(file, outputFormat, options = {}) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('output_format', outputFormat);
    if (options.quality) formData.append('quality', options.quality);
    if (options.pages) formData.append('pages', options.pages);

    const response = await fetch('/api/convert', {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: 'Conversion failed' }));
      throw new Error(err.detail || 'HTTP ' + response.status);
    }

    const blob = await response.blob();
    const disposition = response.headers.get('Content-Disposition') || '';
    const filenameMatch = disposition.match(/filename="?(.+?)"?$/);
    const filename = filenameMatch ? filenameMatch[1] : 'converted.' + outputFormat;
    return { blob, filename };
  },

  async pdfToolkit(file, action, options = {}) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('action', action);
    if (options.pages) formData.append('pages', options.pages);
    if (options.order) formData.append('order', options.order);
    if (options.rotations) formData.append('rotations', JSON.stringify(options.rotations));

    const response = await fetch('/api/pdf/toolkit', {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: 'Toolkit action failed' }));
      throw new Error(err.detail || 'HTTP ' + response.status);
    }

    if (action === 'page_count') {
      const data = await response.json();
      return { pageCount: data.pages };
    }

    const blob = await response.blob();
    const disposition = response.headers.get('Content-Disposition') || '';
    const filenameMatch = disposition.match(/filename="?(.+?)"?$/);
    const filename = filenameMatch ? filenameMatch[1] : 'output.pdf';
    return { blob, filename };
  },

  async getFormats() {
    const response = await fetch('/api/formats');
    return response.json();
  },
};
