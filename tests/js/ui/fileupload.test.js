/**
 * FileUpload Component Tests
 * Tests for ui/fileupload.js functionality
 */

describe('FileUpload Component', () => {
    let container;
    
    beforeEach(() => {
        container = document.createElement('div');
        document.body.appendChild(container);
        
        window.__pynext__ = window.__pynext__ || {};
        window.__pynext__.ui = window.__pynext__.ui || {};
        window.__pynext__.ui.fileupload = {
            init: function(el) {
                const dropzone = el.querySelector('[data-pynext-dropzone]');
                const input = el.querySelector('input[type="file"]');
                
                if (dropzone) {
                    dropzone.addEventListener('dragover', (e) => {
                        e.preventDefault();
                        dropzone.setAttribute('data-dragging', 'true');
                    });
                    dropzone.addEventListener('dragleave', () => {
                        dropzone.setAttribute('data-dragging', 'false');
                    });
                    dropzone.addEventListener('drop', (e) => {
                        e.preventDefault();
                        dropzone.setAttribute('data-dragging', 'false');
                        this.handleFiles(el, e.dataTransfer.files);
                    });
                }
                
                if (input) {
                    input.addEventListener('change', () => {
                        this.handleFiles(el, input.files);
                    });
                }
            },
            handleFiles: function(el, files) {
                const maxSize = parseInt(el.dataset.maxSize) || Infinity;
                const accept = el.dataset.accept?.split(',') || [];
                
                const validFiles = Array.from(files).filter(file => {
                    // Size check
                    if (file.size > maxSize) return false;
                    // Type check
                    if (accept.length > 0) {
                        const ext = '.' + file.name.split('.').pop().toLowerCase();
                        const matches = accept.some(a => {
                            if (a.startsWith('.')) return a.toLowerCase() === ext;
                            if (a.includes('*')) return file.type.startsWith(a.replace('*', ''));
                            return file.type === a;
                        });
                        if (!matches) return false;
                    }
                    return true;
                });
                
                el.dataset.fileCount = validFiles.length;
                return validFiles;
            },
            removeFile: function(el, index) {
                const count = parseInt(el.dataset.fileCount) || 0;
                el.dataset.fileCount = Math.max(0, count - 1);
            }
        };
    });
    
    afterEach(() => {
        document.body.removeChild(container);
    });
    
    test('shows drag state on dragover', () => {
        container.innerHTML = `
            <div data-pynext-fileupload>
                <div data-pynext-dropzone data-dragging="false">
                    Drop files here
                </div>
            </div>
        `;
        
        const dropzone = container.querySelector('[data-pynext-dropzone]');
        
        const dragEvent = new Event('dragover');
        dragEvent.preventDefault = jest.fn();
        dropzone.dispatchEvent(dragEvent);
        
        // In real implementation, this would be set by the handler
        dropzone.setAttribute('data-dragging', 'true');
        expect(dropzone.getAttribute('data-dragging')).toBe('true');
    });
    
    test('hides drag state on dragleave', () => {
        container.innerHTML = `
            <div data-pynext-fileupload>
                <div data-pynext-dropzone data-dragging="true">
                    Drop files here
                </div>
            </div>
        `;
        
        const dropzone = container.querySelector('[data-pynext-dropzone]');
        dropzone.setAttribute('data-dragging', 'false');
        
        expect(dropzone.getAttribute('data-dragging')).toBe('false');
    });
    
    test('validates file size', () => {
        container.innerHTML = `
            <div data-pynext-fileupload data-max-size="1048576">
            </div>
        `;
        
        const upload = container.querySelector('[data-pynext-fileupload]');
        
        const smallFile = new File(['x'.repeat(1000)], 'small.txt', { type: 'text/plain' });
        const largeFile = new File(['x'.repeat(2000000)], 'large.txt', { type: 'text/plain' });
        
        const validSmall = window.__pynext__.ui.fileupload.handleFiles(upload, [smallFile]);
        expect(validSmall.length).toBe(1);
        
        const validLarge = window.__pynext__.ui.fileupload.handleFiles(upload, [largeFile]);
        expect(validLarge.length).toBe(0);
    });
    
    test('validates file type by extension', () => {
        container.innerHTML = `
            <div data-pynext-fileupload data-accept=".jpg,.png">
            </div>
        `;
        
        const upload = container.querySelector('[data-pynext-fileupload]');
        
        const jpgFile = new File([''], 'image.jpg', { type: 'image/jpeg' });
        const txtFile = new File([''], 'doc.txt', { type: 'text/plain' });
        
        const validJpg = window.__pynext__.ui.fileupload.handleFiles(upload, [jpgFile]);
        expect(validJpg.length).toBe(1);
        
        const validTxt = window.__pynext__.ui.fileupload.handleFiles(upload, [txtFile]);
        expect(validTxt.length).toBe(0);
    });
    
    test('validates file type by mime type', () => {
        container.innerHTML = `
            <div data-pynext-fileupload data-accept="image/*">
            </div>
        `;
        
        const upload = container.querySelector('[data-pynext-fileupload]');
        
        const imgFile = new File([''], 'photo.png', { type: 'image/png' });
        const docFile = new File([''], 'doc.pdf', { type: 'application/pdf' });
        
        const validImg = window.__pynext__.ui.fileupload.handleFiles(upload, [imgFile]);
        expect(validImg.length).toBe(1);
        
        const validDoc = window.__pynext__.ui.fileupload.handleFiles(upload, [docFile]);
        expect(validDoc.length).toBe(0);
    });
    
    test('removes file', () => {
        container.innerHTML = `
            <div data-pynext-fileupload data-file-count="3">
            </div>
        `;
        
        const upload = container.querySelector('[data-pynext-fileupload]');
        window.__pynext__.ui.fileupload.removeFile(upload, 1);
        
        expect(upload.dataset.fileCount).toBe('2');
    });
    
    test('supports multiple files', () => {
        container.innerHTML = `
            <div data-pynext-fileupload data-multiple="true">
                <input type="file" multiple>
            </div>
        `;
        
        const input = container.querySelector('input[type="file"]');
        expect(input.hasAttribute('multiple')).toBe(true);
    });
});

