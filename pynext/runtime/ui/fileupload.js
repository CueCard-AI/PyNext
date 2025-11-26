/**
 * PyNext FileUpload Runtime
 * Size target: ~0.8 KB minified
 */
(function(g) {
    'use strict';
    
    var ui = g.__pynext__.ui;
    
    function initFileUploads() {
        document.querySelectorAll('[data-pynext-file-upload]').forEach(initFileUpload);
    }
    
    function initFileUpload(upload) {
        var dropzone = upload.querySelector('[data-pynext-dropzone]');
        var input = upload.querySelector('[data-pynext-file-input]');
        
        if (!dropzone || !input) return;
        
        // Configure from data attributes
        if (upload.dataset.accept) input.accept = upload.dataset.accept;
        if (upload.dataset.multiple) input.multiple = true;
        
        // Drag events
        ['dragenter', 'dragover'].forEach(function(event) {
            dropzone.addEventListener(event, function(e) {
                e.preventDefault();
                e.stopPropagation();
                dropzone.dataset.dragActive = 'true';
            });
        });
        
        ['dragleave', 'drop'].forEach(function(event) {
            dropzone.addEventListener(event, function(e) {
                e.preventDefault();
                e.stopPropagation();
                dropzone.dataset.dragActive = 'false';
            });
        });
        
        // Handle drop
        dropzone.addEventListener('drop', function(e) {
            var files = Array.from(e.dataTransfer.files);
            handleFiles(upload, files);
        });
        
        // Handle input change
        input.addEventListener('change', function() {
            var files = Array.from(input.files);
            handleFiles(upload, files);
        });
        
        // Click to open file dialog
        dropzone.addEventListener('click', function() {
            input.click();
        });
    }
    
    function handleFiles(upload, files) {
        var maxSize = parseInt(upload.dataset.maxSize) || Infinity;
        var maxFiles = parseInt(upload.dataset.maxFiles) || Infinity;
        
        var valid = files.filter(function(file) {
            if (file.size > maxSize) {
                upload.dispatchEvent(new CustomEvent('pynext:file-error', {
                    bubbles: true,
                    detail: { file: file, error: 'size' }
                }));
                return false;
            }
            return true;
        }).slice(0, maxFiles);
        
        upload.dispatchEvent(new CustomEvent('pynext:file-select', {
            bubbles: true,
            detail: { files: valid }
        }));
    }
    
    // Remove file
    ui.on('click', '[data-pynext-file-remove]', function(e, btn) {
        var item = btn.closest('[data-pynext-file-item]');
        if (!item) return;
        
        var upload = btn.closest('[data-pynext-file-upload]');
        item.remove();
        
        if (upload) {
            upload.dispatchEvent(new CustomEvent('pynext:file-remove', {
                bubbles: true,
                detail: { item: item }
            }));
        }
    });
    
    initFileUploads();
    
})(window);

