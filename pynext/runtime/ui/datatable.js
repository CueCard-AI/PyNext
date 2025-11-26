/**
 * PyNext DataTable Runtime
 * Size target: ~2 KB minified
 */
(function(g) {
    'use strict';
    
    var ui = g.__pynext__.ui;
    
    function initDataTables() {
        document.querySelectorAll('[data-pynext-datatable]').forEach(initDataTable);
    }
    
    function initDataTable(table) {
        initSorting(table);
        initFiltering(table);
        initPagination(table);
        initRowSelection(table);
        initColumnVisibility(table);
        initColumnResize(table);
    }
    
    function initSorting(table) {
        ui.on('click', '[data-pynext-datatable-sort]', function(e, header) {
            if (!table.contains(header)) return;
            
            var column = header.dataset.pynextDatatableSort;
            var current = header.dataset.sortDir || 'none';
            var next = current === 'none' ? 'asc' : current === 'asc' ? 'desc' : 'none';
            
            // Reset other headers
            table.querySelectorAll('[data-pynext-datatable-sort]').forEach(function(h) {
                h.dataset.sortDir = 'none';
            });
            
            header.dataset.sortDir = next;
            
            table.dispatchEvent(new CustomEvent('pynext:datatable-sort', {
                bubbles: true,
                detail: { column: column, direction: next }
            }));
        });
    }
    
    function initFiltering(table) {
        var input = table.querySelector('[data-pynext-datatable-filter]');
        if (!input) return;
        
        var timeout = null;
        input.addEventListener('input', function() {
            clearTimeout(timeout);
            timeout = setTimeout(function() {
                var query = input.value.toLowerCase();
                
                table.querySelectorAll('[data-pynext-datatable-row]').forEach(function(row) {
                    var text = (row.textContent || '').toLowerCase();
                    row.style.display = text.includes(query) ? '' : 'none';
                });
                
                table.dispatchEvent(new CustomEvent('pynext:datatable-filter', {
                    bubbles: true,
                    detail: { query: input.value }
                }));
            }, 300);
        });
    }
    
    function initPagination(table) {
        ui.on('click', '[data-pynext-datatable-page]', function(e, btn) {
            if (!table.contains(btn)) return;
            
            var page = parseInt(btn.dataset.pynextDatatablePage);
            
            table.querySelectorAll('[data-pynext-datatable-page]').forEach(function(b) {
                b.setAttribute('data-active', 'false');
            });
            btn.setAttribute('data-active', 'true');
            
            table.dispatchEvent(new CustomEvent('pynext:datatable-page', {
                bubbles: true,
                detail: { page: page }
            }));
        });
        
        ui.on('click', '[data-pynext-datatable-prev]', function(e, btn) {
            if (!table.contains(btn)) return;
            navigatePage(table, -1);
        });
        
        ui.on('click', '[data-pynext-datatable-next]', function(e, btn) {
            if (!table.contains(btn)) return;
            navigatePage(table, 1);
        });
    }
    
    function navigatePage(table, dir) {
        var current = table.querySelector('[data-pynext-datatable-page][data-active="true"]');
        if (!current) return;
        
        var pages = Array.from(table.querySelectorAll('[data-pynext-datatable-page]'));
        var index = pages.indexOf(current);
        var next = pages[index + dir];
        
        if (next) next.click();
    }
    
    function initRowSelection(table) {
        // Select all
        ui.on('change', '[data-pynext-datatable-select-all]', function(e, checkbox) {
            if (!table.contains(checkbox)) return;
            
            var checked = checkbox.checked;
            table.querySelectorAll('[data-pynext-datatable-select]').forEach(function(cb) {
                cb.checked = checked;
                var row = cb.closest('[data-pynext-datatable-row]');
                if (row) row.dataset.selected = checked;
            });
            
            table.dispatchEvent(new CustomEvent('pynext:datatable-select-all', {
                bubbles: true,
                detail: { selected: checked }
            }));
        });
        
        // Individual row
        ui.on('change', '[data-pynext-datatable-select]', function(e, checkbox) {
            if (!table.contains(checkbox)) return;
            
            var row = checkbox.closest('[data-pynext-datatable-row]');
            if (row) row.dataset.selected = checkbox.checked;
            
            // Update select all state
            var all = table.querySelectorAll('[data-pynext-datatable-select]');
            var checked = table.querySelectorAll('[data-pynext-datatable-select]:checked');
            var selectAll = table.querySelector('[data-pynext-datatable-select-all]');
            
            if (selectAll) {
                selectAll.checked = all.length === checked.length;
                selectAll.indeterminate = checked.length > 0 && checked.length < all.length;
            }
        });
    }
    
    function initColumnVisibility(table) {
        ui.on('change', '[data-pynext-datatable-column-toggle]', function(e, checkbox) {
            if (!table.contains(checkbox)) return;
            
            var column = checkbox.dataset.pynextDatatableColumnToggle;
            var visible = checkbox.checked;
            
            table.querySelectorAll('[data-column="' + column + '"]').forEach(function(cell) {
                cell.style.display = visible ? '' : 'none';
            });
            
            table.dispatchEvent(new CustomEvent('pynext:datatable-column-visibility', {
                bubbles: true,
                detail: { column: column, visible: visible }
            }));
        });
    }
    
    function initColumnResize(table) {
        if (table.dataset.pynextDatatableResizable !== 'true') return;
        
        var resizing = null;
        
        table.querySelectorAll('[data-resizable-col]').forEach(function(th) {
            var handle = document.createElement('div');
            handle.className = 'resize-handle';
            handle.style.cssText = 'position:absolute;right:0;top:0;bottom:0;width:4px;cursor:col-resize';
            th.style.position = 'relative';
            th.appendChild(handle);
        });
        
        document.addEventListener('mousedown', function(e) {
            if (!e.target.classList.contains('resize-handle')) return;
            var th = e.target.parentElement;
            resizing = { th: th, startX: e.clientX, startWidth: th.offsetWidth };
            e.preventDefault();
        });
        
        document.addEventListener('mousemove', function(e) {
            if (!resizing) return;
            var newWidth = resizing.startWidth + (e.clientX - resizing.startX);
            var min = parseInt(resizing.th.dataset.minWidth) || 50;
            var max = parseInt(resizing.th.dataset.maxWidth) || 500;
            newWidth = Math.max(min, Math.min(max, newWidth));
            resizing.th.style.width = newWidth + 'px';
        });
        
        document.addEventListener('mouseup', function() {
            if (resizing) {
                table.dispatchEvent(new CustomEvent('pynext:datatable-column-resize', {
                    bubbles: true,
                    detail: { column: resizing.th.dataset.resizableCol, width: resizing.th.style.width }
                }));
                resizing = null;
            }
        });
    }
    
    initDataTables();
    
})(window);

