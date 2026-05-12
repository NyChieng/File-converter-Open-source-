const PDFToolkit = {
  pages: [],
  selectedPages: new Set(),
  sortable: null,

  init(pageCount) {
    this.pages = Array.from({ length: pageCount }, function (_, i) {
      return { number: i + 1, selected: false, deleted: false, rotation: 0 };
    });
    this.selectedPages.clear();
    this.render();
    this._initSortable();
  },

  render() {
    var strip = document.getElementById('pageStrip');
    strip.innerHTML = '';
    var self = this;
    this.pages.forEach(function (page) {
      var el = document.createElement('div');
      el.className = 'page-thumb';
      el.setAttribute('data-page', page.number);
      if (page.selected) el.classList.add('selected');
      if (page.deleted) el.classList.add('deleted');
      el.innerHTML =
        '<span class="page-thumb-num">' + page.number + '</span>' +
        '<span class="page-thumb-preview">Pg ' + page.number + '</span>' +
        '<span class="deleted-label">deleted</span>';
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

  selectOne(pageNum) {
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

  toggleSelect(pageNum) {
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

  markDeleted() {
    var self = this;
    this.selectedPages.forEach(function (num) {
      var page = self.pages.find(function (p) { return p.number === num; });
      if (page) page.deleted = true;
    });
    this.selectedPages.clear();
    this.render();
  },

  rotateSelected(angle) {
    var self = this;
    this.selectedPages.forEach(function (num) {
      var page = self.pages.find(function (p) { return p.number === num; });
      if (page) page.rotation = (page.rotation || 0) + angle;
    });
    this.render();
  },

  getOrder() {
    return this.pages.map(function (p) { return p.number; });
  },

  getPagesToDelete() {
    return this.pages.filter(function (p) { return p.deleted; }).map(function (p) { return p.number; });
  },

  getRotations() {
    var rots = {};
    this.pages.forEach(function (p) {
      if (p.rotation) rots[String(p.number)] = p.rotation;
    });
    return rots;
  },

  _initSortable() {
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

  _updateToolbarState() {
    var hasSelection = this.selectedPages.size > 0;
    document.querySelectorAll('.toolbar-btn').forEach(function (btn) {
      if (btn.getAttribute('data-action') === 'export') return;
      btn.style.opacity = hasSelection ? '1' : '0.5';
    });
  },

  reset() {
    this.pages = [];
    this.selectedPages.clear();
    if (this.sortable) this.sortable.destroy();
    this.sortable = null;
    document.getElementById('pageStrip').innerHTML = '';
  },
};
