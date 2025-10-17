// docs/assets/js/tooltip.js

document.addEventListener('DOMContentLoaded', function() {
    // We still need a tooltip element to show the text in.
    // This can be created dynamically or placed in your HTML/Markdown.
    const tooltip = document.getElementById('tooltip');
    
    // Find ALL elements anywhere on the page that have a 'data-tooltip' attribute
    const interactiveElements = document.querySelectorAll('[data-tooltip]');

    interactiveElements.forEach(element => {
        
        // When the mouse enters, read the attribute and show the tooltip
        element.addEventListener('mouseover', event => {
            const content = element.getAttribute('data-tooltip'); // Get content from the element itself
            if (content) {
                tooltip.innerHTML = content;
                tooltip.style.display = 'block';
            }
        });

        // This part stays the same: move and hide the tooltip
        element.addEventListener('mousemove', event => {
            tooltip.style.left = (event.pageX + 15) + 'px';
            tooltip.style.top = (event.pageY + 15) + 'px';
        });

        element.addEventListener('mouseout', () => {
            tooltip.style.display = 'none';
        });
    });
});