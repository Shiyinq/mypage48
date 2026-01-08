/**
 * Drag and Drop Action
 *
 * Usage:
 * <div use:dragDrop={{
 *   onDrop: (file) => { ... },
 *   onDragChange: (isDragging) => { ... }
 * }}>
 */

export interface DragDropOptions {
    onDrop: (file: File) => void;
    onDragChange?: (isDragging: boolean) => void;
}

export function dragDrop(node: HTMLElement, options: DragDropOptions) {
    let dragCounter = 0;

    const handleDragEnter = (e: DragEvent) => {
        e.preventDefault();
        dragCounter++;
        if (dragCounter === 1) {
            options.onDragChange?.(true);
        }
    };

    const handleDragLeave = (e: DragEvent) => {
        e.preventDefault();
        dragCounter--;
        if (dragCounter === 0) {
            options.onDragChange?.(false);
        }
    };

    const handleDragOver = (e: DragEvent) => {
        e.preventDefault();
    };

    const handleDrop = (e: DragEvent) => {
        e.preventDefault();
        dragCounter = 0;
        options.onDragChange?.(false);

        if (e.dataTransfer?.files && e.dataTransfer.files.length > 0) {
            options.onDrop(e.dataTransfer.files[0]);
        }
    };

    node.addEventListener('dragenter', handleDragEnter);
    node.addEventListener('dragleave', handleDragLeave);
    node.addEventListener('dragover', handleDragOver);
    node.addEventListener('drop', handleDrop);

    return {
        update(newOptions: DragDropOptions) {
            options = newOptions;
        },
        destroy() {
            node.removeEventListener('dragenter', handleDragEnter);
            node.removeEventListener('dragleave', handleDragLeave);
            node.removeEventListener('dragover', handleDragOver);
            node.removeEventListener('drop', handleDrop);
        }
    };
}
