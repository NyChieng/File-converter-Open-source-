(function () {
  'use strict';

  var currentTool = 'image-convert';
  var currentFile = null;
  var selectedFormat = null;

  var dom = {
    dropZone: document.getElementById('dropZone'),
    fileInput: document.getElementById('fileInput'),
    browseBtn: document.getElementById('browseBtn'),
    fileCard: document.getElementById('fileCard'),
    fileThumb: document.getElementById('fileThumb'),
    fileName: document.getElementById('fileName'),
    formatBadge: document.getElementById('formatBadge'),
    fileSize: document.getElementById('fileSize'),
    fileDetail: document.getElementById('fileDetail'),
    fileRemove: document.getElementById('fileRemove'),
    formatSection: document.getElementById('formatSection'),
    formatChips: document.getElementById('formatChips'),
    convertBtn: document.getElementById('convertBtn'),
    progressSection: document.getElementById('progressSection'),
    progressFill: document.getElementById('progressFill'),
    progressText: document.getElementById('progressText'),
    resultSection: document.getElementById('resultSection'),
    resultPreview: document.getElementById('resultPreview'),
    downloadBtn: document.getElementById('downloadBtn'),
    resetBtn: document.getElementById('resetBtn'),
    pdfToolbar: document.getElementById('pdfToolbar'),
    pageStrip: document.getElementById('pageStrip'),
    steps: document.getElementById('steps'),
  };

  var toolFormats = {
    'image-convert': ['JPG', 'PNG', 'WebP'],
    'pdf-to-image': ['JPG', 'PNG'],
    'image-to-pdf': ['PDF'],
    'pdf-toolkit': [],
    'office-to-pdf': ['PDF'],
  };

  function switchTool(tool) {
    currentTool = tool;
    document.querySelectorAll('.tool-btn, .tab-btn').forEach(function (b) {
      b.classList.toggle('active', b.getAttribute('data-tool') === tool);
    });
    resetUI();
    renderFormatChips();
    if (tool === 'pdf-toolkit') {
      dom.pdfToolbar.classList.add('hidden');
      dom.pageStrip.classList.add('hidden');
    }
    updateSteps(1);
  }

  document.querySelectorAll('.tool-btn, .tab-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      switchTool(btn.getAttribute('data-tool'));
    });
  });

  function renderFormatChips() {
    var formats = toolFormats[currentTool] || [];
    dom.formatChips.innerHTML = '';
    formats.forEach(function (fmt) {
      var chip = document.createElement('button');
      chip.className = 'format-chip';
      chip.textContent = fmt;
      chip.addEventListener('click', function () {
        dom.formatChips.querySelectorAll('.format-chip').forEach(function (c) {
          c.classList.remove('selected');
        });
        chip.classList.add('selected');
        selectedFormat = fmt.toLowerCase();
        dom.convertBtn.disabled = false;
      });
      dom.formatChips.appendChild(chip);
    });
    selectedFormat = null;
    dom.convertBtn.disabled = true;
  }

  function getFileKind(file) {
    if (file.type.startsWith('image/')) return 'image';
    if (file.type === 'application/pdf') return 'pdf';
    var ext = file.name.split('.').pop().toLowerCase();
    if (['jpg', 'jpeg', 'png', 'webp', 'heif', 'heic', 'svg', 'bmp', 'tiff'].indexOf(ext) !== -1) return 'image';
    if (ext === 'pdf') return 'pdf';
    if (['docx', 'xlsx', 'pptx'].indexOf(ext) !== -1) return 'office';
    return 'unknown';
  }

  function handleFile(file) {
    if (!file) return;
    currentFile = file;

    var ext = file.name.split('.').pop().toUpperCase();
    var kind = getFileKind(file);
    dom.fileName.textContent = file.name;
    dom.formatBadge.textContent = ext;
    dom.fileSize.textContent = formatSize(file.size);

    if (kind === 'image') {
      var reader = new FileReader();
      reader.onload = function () {
        dom.fileThumb.innerHTML = '<img src="' + reader.result + '" alt="preview">';
      };
      reader.readAsDataURL(file);
      var img = new Image();
      img.onload = function () {
        dom.fileDetail.textContent = img.width + 'x' + img.height;
      };
      img.src = URL.createObjectURL(file);
    } else if (kind === 'pdf') {
      dom.fileThumb.textContent = 'PDF';
      dom.fileDetail.textContent = '';
    } else {
      dom.fileThumb.textContent = ext.substring(0, 3);
      dom.fileDetail.textContent = '';
    }

    dom.dropZone.classList.add('hidden');
    dom.fileCard.classList.remove('hidden');
    dom.formatSection.classList.remove('hidden');
    updateSteps(1);

    if (currentTool === 'pdf-toolkit') {
      loadPdfPages(file);
    }
  }

  function loadPdfPages(file) {
    API.pdfToolkit(file, 'page_count').then(function (result) {
      dom.fileDetail.textContent = result.pageCount + ' pages';
      PDFToolkit.init(result.pageCount);
      dom.pdfToolbar.classList.remove('hidden');
      dom.pageStrip.classList.remove('hidden');
      dom.formatSection.classList.add('hidden');
    }).catch(function (err) {
      console.error('Failed to get page count:', err);
    });
  }

  dom.browseBtn.addEventListener('click', function (e) {
    e.stopPropagation();
    dom.fileInput.click();
  });
  dom.fileInput.addEventListener('change', function () {
    if (dom.fileInput.files[0]) handleFile(dom.fileInput.files[0]);
  });
  dom.dropZone.addEventListener('click', function () { dom.fileInput.click(); });
  dom.dropZone.addEventListener('dragover', function (e) {
    e.preventDefault();
    dom.dropZone.classList.add('drag-over');
  });
  dom.dropZone.addEventListener('dragleave', function () {
    dom.dropZone.classList.remove('drag-over');
  });
  dom.dropZone.addEventListener('drop', function (e) {
    e.preventDefault();
    dom.dropZone.classList.remove('drag-over');
    var file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  });
  dom.fileRemove.addEventListener('click', resetUI);

  dom.pdfToolbar.addEventListener('click', function (e) {
    var btn = e.target.closest('.toolbar-btn');
    if (!btn) return;
    var action = btn.getAttribute('data-action');
    if (action === 'compress') {
      downloadPdfToolkitResult('compress');
    } else if (action === 'rotate-left') {
      PDFToolkit.rotateSelected(-90);
    } else if (action === 'rotate-right') {
      PDFToolkit.rotateSelected(90);
    } else if (action === 'delete') {
      PDFToolkit.markDeleted();
    } else if (action === 'export') {
      downloadPdfToolkitResult('export');
    }
  });

  function downloadPdfToolkitResult(action) {
    if (!currentFile) return;
    showProgress();
    var flow = Promise.resolve({ blob: currentFile });
    if (action === 'compress') {
      flow = API.pdfToolkit(currentFile, 'compress');
    }
    if (action === 'export') {
      var pagesToDelete = PDFToolkit.getPagesToDelete();
      var rotations = PDFToolkit.getRotations();
      var order = PDFToolkit.getOrder();
      if (pagesToDelete.length > 0) {
        flow = flow.then(function (r) {
          var f = r.blob ? new File([r.blob], 'temp.pdf', { type: 'application/pdf' }) : currentFile;
          return API.pdfToolkit(f, 'delete', { pages: pagesToDelete.join(',') });
        });
      }
      if (Object.keys(rotations).length > 0) {
        flow = flow.then(function (r) {
          var f = r.blob ? new File([r.blob], 'temp.pdf', { type: 'application/pdf' }) : currentFile;
          return API.pdfToolkit(f, 'rotate', { rotations: rotations });
        });
      }
      flow = flow.then(function (r) {
        var f = r.blob ? new File([r.blob], 'temp.pdf', { type: 'application/pdf' }) : currentFile;
        return API.pdfToolkit(f, 'reorder', { order: order.join(',') });
      });
    }
    flow.then(function (result) {
      hideProgress();
      showResult(result.blob, result.filename);
    }).catch(function (err) {
      hideProgress();
      alert('Error: ' + err.message);
    });
  }

  dom.convertBtn.addEventListener('click', function () {
    if (!currentFile || !selectedFormat) return;
    showProgress();
    updateSteps(2);
    API.convert(currentFile, selectedFormat).then(function (result) {
      hideProgress();
      updateSteps(3);
      showResult(result.blob, result.filename);
    }).catch(function (err) {
      hideProgress();
      alert('Error: ' + err.message);
    });
  });

  function showResult(blob, filename) {
    var url = URL.createObjectURL(blob);
    dom.resultPreview.innerHTML = '';
    if (blob.type.startsWith('image/')) {
      dom.resultPreview.innerHTML = '<img src="' + url + '" alt="result">';
    } else {
      dom.resultPreview.innerHTML =
        '<p style="color:#64748b">' + filename + '</p>' +
        '<p style="color:#94a3b8;font-size:12px;margin-top:4px">' + formatSize(blob.size) + '</p>';
    }
    dom.resultSection.classList.remove('hidden');
    dom.downloadBtn.onclick = function () {
      var a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.click();
    };
  }

  dom.resetBtn.addEventListener('click', resetUI);

  var _progressInterval = null;
  function showProgress() {
    dom.progressSection.classList.remove('hidden');
    dom.progressFill.style.width = '0%';
    dom.progressText.textContent = 'Converting...';
    var w = 0;
    _progressInterval = setInterval(function () {
      w += Math.random() * 30;
      if (w > 90) { w = 90; clearInterval(_progressInterval); }
      dom.progressFill.style.width = w + '%';
    }, 200);
  }

  function hideProgress() {
    clearInterval(_progressInterval);
    dom.progressFill.style.width = '100%';
    setTimeout(function () {
      dom.progressSection.classList.add('hidden');
      dom.progressFill.style.width = '0%';
    }, 400);
  }

  function updateSteps(active) {
    dom.steps.querySelectorAll('.step').forEach(function (s) {
      var num = parseInt(s.getAttribute('data-step'));
      s.classList.remove('active', 'completed');
      if (num < active) s.classList.add('completed');
      if (num === active) s.classList.add('active');
    });
  }

  function resetUI() {
    currentFile = null;
    selectedFormat = null;
    dom.fileInput.value = '';
    dom.dropZone.classList.remove('hidden');
    dom.fileCard.classList.add('hidden');
    dom.formatSection.classList.add('hidden');
    dom.progressSection.classList.add('hidden');
    dom.resultSection.classList.add('hidden');
    dom.pdfToolbar.classList.add('hidden');
    dom.pageStrip.classList.add('hidden');
    dom.resultPreview.innerHTML = '<p class="placeholder">Your converted file will appear here</p>';
    dom.convertBtn.disabled = true;
    if (typeof PDFToolkit !== 'undefined') PDFToolkit.reset();
    renderFormatChips();
    updateSteps(1);
  }

  function formatSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  }

  renderFormatChips();
  switchTool('image-convert');
})();
