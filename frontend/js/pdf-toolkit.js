var PDFToolkit = {
  pages: [],
  selectedPages: new Set(),
  sortable: null,
  _thumbnails: {},

  init: function (pageCount, file) {
    var self = this;
    this.pages = Array.from({ length: pageCount }, function (_, i) {
      return { number: i + 1, selected: false, deleted: false, rotation: 0 };
    });
    this.selectedPages.clear();
    this._thumbnails = {};
    this._renderThumbnails(file);
    this.render();
    this._initSortable();
  },

  _renderThumbnails: function (file) {
    var self = this;
    if (typeof pdfjsLib === 'undefined') {
      self.render();
      return;
    }
    pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
    var reader = new FileReader();
    reader.onload = function () {
      pdfjsLib.getDocument({ data: reader.result }).promise.then(function (doc) {
        var remaining = self.pages.length;
        self.pages.forEach(function (page) {
          doc.getPage(page.number).then(function (pdfPage) {
            var scale = 0.3;
            var viewport = pdfPage.getViewport({ scale: scale });
            var canvas = document.createElement('canvas');
            canvas.width = viewport.width;
            canvas.height = viewport.height;
            var ctx = canvas.getContext('2d');
            pdfPage.render({ canvasContext: ctx, viewport: viewport }).promise.then(function () {
              self._thumbnails[page.number] = canvas.toDataURL();
              remaining--;
              if (remaining === 0) self.render();
            });
          });
        });
      });
    };
    reader.readAsArrayBuffer(file);
  },

  render: function () {
    var strip = document.getElementById('pageStrip');
    strip.innerHTML = '';
    var self = this;
    this.pages.forEach(function (page) {
      var el = document.createElement('div');
      el.className = 'page-thumb';
      el.setAttribute('data-page', page.number);
      if (page.selected) el.classList.add('selected');
      if (page.deleted) el.classList.add('deleted');

      var img = self._thumbnails[page.number];
      if (img) {
        el.innerHTML =
          '<img src="' + img + '" alt="Page ' + page.number + '" class="thumb-img">' +
          '<span class="page-thumb-num">' + page.number + '</span>';
      } else {
        el.innerHTML =
          '<span class="page-thumb-preview">Pg ' + page.number + '</span>' +
          '<span class="page-thumb-num">' + page.number + '</span>';
      }
      if (page.deleted) {
        el.innerHTML += '<span class="deleted-label">deleted</span>';
      }

      el.addEventListener('click', function (e) {
        if (e.shiftKey || e.ctrlKey) {
          self.toggleSelect(page.number);
        } else {
          self.selectOne(page.number);
        }
      });
      strip.appendChild(el);
    });
    this._updateToolbarState();
  },

  selectOne: function (pageNum) {
    var self = this;
    this.pages.forEach(function (p) { p.selected = false; });
    this.selectedPages.clear();
    var page = this.pages.find(function (p) { return p.number === pageNum; });
    if (page && !page.deleted) {
      page.selected = true;
      this.selectedPages.add(pageNum);
    }
    this.render();
  },

  toggleSelect: function (pageNum) {
    var page = this.pages.find(function (p) { return p.number === pageNum; });
    if (!page || page.deleted) return;
    page.selected = !page.selected;
    if (page.selected) {
      this.selectedPages.add(pageNum);
    } else {
      this.selectedPages.delete(pageNum);
    }
    this.render();
  },

  markDeleted: function () {
    var self = this;
    this.selectedPages.forEach(function (num) {
      var page = self.pages.find(function (p) { return p.number === num; });
      if (page) page.deleted = true;
    });
    this.selectedPages.clear();
    this.render();
  },

  rotateSelected: function (angle) {
    var self = this;
    this.selectedPages.forEach(function (num) {
      var page = self.pages.find(function (p) { return p.number === num; });
      if (page) page.rotation = (page.rotation || 0) + angle;
    });
    this.render();
  },

  getOrder: function () {
    return this.pages.map(function (p) { return p.number; });
  },

  getPagesToDelete: function () {
    return this.pages.filter(function (p) { return p.deleted; }).map(function (p) { return p.number; });
  },

  getRotations: function () {
    var rots = {};
    this.pages.forEach(function (p) {
      if (p.rotation) rots[String(p.number)] = p.rotation;
    });
    return rots;
  },

  _initSortable: function () {
    var strip = document.getElementById('pageStrip');
    if (this.sortable) this.sortable.destroy();
    var self = this;
    if (typeof Sortable !== 'undefined') {
      this.sortable = Sortable.create(strip, {
        animation: 150,
        onEnd: function (evt) {
          var moved = self.pages.splice(evt.oldIndex, 1)[0];
          self.pages.splice(evt.newIndex, 0, moved);
          self.render();
        },
      });
    }
  },

  _updateToolbarState: function () {
    var hasSelection = this.selectedPages.size > 0;
    document.querySelectorAll('.toolbar-btn').forEach(function (btn) {
      if (btn.getAttribute('data-action') === 'export') return;
      btn.style.opacity = hasSelection ? '1' : '0.5';
    });
  },

  reset: function () {
    this.pages = [];
    this.selectedPages.clear();
    this._thumbnails = {};
    if (this.sortable) this.sortable.destroy();
    this.sortable = null;
    document.getElementById('pageStrip').innerHTML = '';
  },
};
