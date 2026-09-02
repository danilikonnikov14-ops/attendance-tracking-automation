document.addEventListener('DOMContentLoaded', function() {
    const studentItems = document.querySelectorAll('.student-item');
    studentItems.forEach(item => {
        item.addEventListener('mouseenter', function() {
            this.style.backgroundColor = '#f0f8ff';
        });
        item.addEventListener('mouseleave', function() {
            this.style.backgroundColor = '';
        });
    });
});