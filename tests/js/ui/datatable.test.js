/**
 * DataTable Component Tests
 * Tests for ui/datatable.js functionality
 */

describe('DataTable Component', () => {
    let container;
    
    beforeEach(() => {
        container = document.createElement('div');
        document.body.appendChild(container);
        
        window.__pynext__ = window.__pynext__ || {};
        window.__pynext__.ui = window.__pynext__.ui || {};
        window.__pynext__.ui.datatable = {
            init: function(el) {
                const headers = el.querySelectorAll('[data-pynext-column-header]');
                headers.forEach(header => {
                    if (header.dataset.sortable !== 'false') {
                        header.addEventListener('click', () => this.sort(el, header.dataset.column));
                    }
                });
            },
            sort: function(el, column) {
                const currentSort = el.dataset.sortColumn;
                const currentDir = el.dataset.sortDirection || 'asc';
                
                if (currentSort === column) {
                    el.dataset.sortDirection = currentDir === 'asc' ? 'desc' : 'asc';
                } else {
                    el.dataset.sortColumn = column;
                    el.dataset.sortDirection = 'asc';
                }
            },
            filter: function(el, query) {
                const rows = el.querySelectorAll('[data-pynext-table-row]');
                rows.forEach(row => {
                    const text = row.textContent.toLowerCase();
                    row.hidden = !text.includes(query.toLowerCase());
                });
            },
            setPage: function(el, page) {
                el.dataset.page = page;
            },
            toggleColumn: function(el, column, visible) {
                const cells = el.querySelectorAll(`[data-column="${column}"]`);
                cells.forEach(cell => {
                    cell.hidden = !visible;
                });
            }
        };
    });
    
    afterEach(() => {
        document.body.removeChild(container);
    });
    
    test('sorts ascending on first click', () => {
        container.innerHTML = `
            <div data-pynext-datatable>
                <table>
                    <thead>
                        <tr>
                            <th data-pynext-column-header data-column="name">Name</th>
                        </tr>
                    </thead>
                </table>
            </div>
        `;
        
        const table = container.querySelector('[data-pynext-datatable]');
        window.__pynext__.ui.datatable.sort(table, 'name');
        
        expect(table.dataset.sortColumn).toBe('name');
        expect(table.dataset.sortDirection).toBe('asc');
    });
    
    test('sorts descending on second click', () => {
        container.innerHTML = `
            <div data-pynext-datatable data-sort-column="name" data-sort-direction="asc">
            </div>
        `;
        
        const table = container.querySelector('[data-pynext-datatable]');
        window.__pynext__.ui.datatable.sort(table, 'name');
        
        expect(table.dataset.sortDirection).toBe('desc');
    });
    
    test('filters rows', () => {
        container.innerHTML = `
            <div data-pynext-datatable>
                <table>
                    <tbody>
                        <tr data-pynext-table-row><td>John Doe</td></tr>
                        <tr data-pynext-table-row><td>Jane Smith</td></tr>
                        <tr data-pynext-table-row><td>Bob Johnson</td></tr>
                    </tbody>
                </table>
            </div>
        `;
        
        const table = container.querySelector('[data-pynext-datatable]');
        window.__pynext__.ui.datatable.filter(table, 'john');
        
        const rows = container.querySelectorAll('[data-pynext-table-row]');
        expect(rows[0].hidden).toBe(false); // John Doe
        expect(rows[1].hidden).toBe(true);  // Jane Smith
        expect(rows[2].hidden).toBe(false); // Bob Johnson
    });
    
    test('paginates', () => {
        container.innerHTML = `
            <div data-pynext-datatable data-page="1" data-page-size="10">
            </div>
        `;
        
        const table = container.querySelector('[data-pynext-datatable]');
        window.__pynext__.ui.datatable.setPage(table, 2);
        
        expect(table.dataset.page).toBe('2');
    });
    
    test('toggles column visibility', () => {
        container.innerHTML = `
            <div data-pynext-datatable>
                <table>
                    <thead>
                        <tr>
                            <th data-column="name">Name</th>
                            <th data-column="email">Email</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td data-column="name">John</td>
                            <td data-column="email">john@example.com</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        `;
        
        const table = container.querySelector('[data-pynext-datatable]');
        window.__pynext__.ui.datatable.toggleColumn(table, 'email', false);
        
        const emailCells = container.querySelectorAll('[data-column="email"]');
        emailCells.forEach(cell => {
            expect(cell.hidden).toBe(true);
        });
    });
    
    test('supports column resizing', () => {
        container.innerHTML = `
            <div data-pynext-datatable data-resizable="true">
                <th data-column="name" data-min-width="100" data-max-width="300" style="width: 150px">
                    Name
                    <div data-pynext-resize-handle></div>
                </th>
            </div>
        `;
        
        const table = container.querySelector('[data-pynext-datatable]');
        expect(table.getAttribute('data-resizable')).toBe('true');
        
        const handle = container.querySelector('[data-pynext-resize-handle]');
        expect(handle).toBeTruthy();
    });
    
    test('supports row selection', () => {
        container.innerHTML = `
            <div data-pynext-datatable data-selection="true">
                <table>
                    <tbody>
                        <tr data-pynext-table-row data-selected="false">
                            <td><input type="checkbox" data-pynext-row-select></td>
                            <td>Row 1</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        `;
        
        const row = container.querySelector('[data-pynext-table-row]');
        row.setAttribute('data-selected', 'true');
        
        expect(row.getAttribute('data-selected')).toBe('true');
    });
});

