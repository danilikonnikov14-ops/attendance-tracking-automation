async function loadAttendanceStats() {
    const cells = document.querySelectorAll('.attendance-cell');
    
    const promises = Array.from(cells).map(async (cell) => {
        const group = cell.getAttribute('data-group');
        const date = cell.getAttribute('data-date');
        const pair = cell.getAttribute('data-pair');
        const valueSpan = cell.querySelector('.attendance-value');
        
        try {
            const response = await fetch(`/attendance_stats/${group}/${date}/${pair}`);
            const data = await response.json();
            
            if (data.has_data === true && data.present > 0) {
                valueSpan.innerHTML = `${data.present}/${data.total}`;
                valueSpan.className = 'attendance-value present';
            } else {
                valueSpan.innerHTML = '—';
                valueSpan.className = 'attendance-value';
            }
        } catch(e) {
            console.error('Ошибка:', e);
            valueSpan.innerHTML = '—';
            valueSpan.className = 'attendance-value';
        }
    });
    
    await Promise.all(promises);
}

document.addEventListener('DOMContentLoaded', function() {
    loadAttendanceStats();
});
setInterval(loadAttendanceStats, 30000);