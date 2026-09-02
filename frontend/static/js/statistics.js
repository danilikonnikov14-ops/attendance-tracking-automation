let trendChart = null;
let currentPeriod = 'week';
let currentYear = new Date().getFullYear();
let currentMonth = new Date().getMonth() + 1;
let currentSemester = 1;
let currentChartData = { dates: [], rates: [] };
let currentStudentData = [];

async function loadTrendData(groupName) {
    try {
        let url = `/attendance_trend/${groupName}?period=${currentPeriod}&_=${Date.now()}`;
        
        if (currentPeriod === 'month') {
            url += `&year=${currentYear}&month=${currentMonth}`;
        } else if (currentPeriod === 'semester') {
            url += `&year=${currentYear}&semester=${currentSemester}`;
        }
        
        const response = await fetch(url, {
            cache: 'no-store',
            headers: { 'Cache-Control': 'no-cache' }
        });
        const data = await response.json();
        
        console.log('Ответ от API:', data);

        if (data.dates && data.dates.length > 0) {
            const shiftedDates = [];
            for (let i = 0; i < data.dates.length; i++) {
                const parts = data.dates[i].split('.');
                if (parts.length === 2) {
                    let day = parseInt(parts[0]);
                    let month = parseInt(parts[1]);
                    
                    let year = currentYear; 
                    
                    if (currentPeriod === 'week') {
                        year = new Date().getFullYear();
                        const currentMonthNow = new Date().getMonth() + 1;
                        if (month > currentMonthNow + 1) {
                            year = year - 1;
                        }
                    }
                    
                    let dateObj = new Date(year, month - 1, day);
                    
                    const newDay = dateObj.getDate().toString().padStart(2, '0');
                    const newMonth = (dateObj.getMonth() + 1).toString().padStart(2, '0');
                    shiftedDates.push(`${newDay}.${newMonth}`);
                } else {
                    shiftedDates.push(data.dates[i]);
                }
            }
            data.dates = shiftedDates;
        }
        
        currentChartData = data;
        
        if (!data.dates || data.dates.length === 0) {
            document.getElementById('chart-error').style.display = 'block';
            if (trendChart) trendChart.destroy();
            return;
        }
        
        document.getElementById('chart-error').style.display = 'none';
        
        if (trendChart) {
            trendChart.destroy();
        }
        
        const ctx = document.getElementById('trendChart').getContext('2d');
        
        trendChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.dates,
                datasets: [{
                    label: 'Посещаемость (%)',
                    data: data.rates,
                    borderColor: '#e7004c',
                    backgroundColor: 'rgba(231, 0, 76, 0.1)',
                    borderWidth: 3,
                    pointRadius: 3,
                    pointHoverRadius: 5,
                    pointBackgroundColor: '#e7004c',
                    pointBorderColor: 'white',
                    pointBorderWidth: 2,
                    fill: true,
                    tension: 0.3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: { position: 'top' },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `Посещаемость: ${context.raw}%`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: { callback: function(value) { return value + '%'; } },
                        title: { display: true, text: 'Посещаемость (%)' }
                    },
                    x: {
                        title: { display: true, text: 'Дата' },
                        ticks: { maxRotation: 45, minRotation: 45, autoSkip: true, maxTicksLimit: 15 }
                    }
                }
            }
        });
        
    } catch (error) {
        console.error('Ошибка:', error);
        document.getElementById('chart-error').style.display = 'block';
    }
}

async function loadStudentStats(groupName) {
    try {
        const response = await fetch(`/student_stats/${groupName}?_=${Date.now()}`, {
            cache: 'no-store',
            headers: { 'Cache-Control': 'no-cache' }
        });
        const data = await response.json();
        currentStudentData = data;
        
        if (!data || data.length === 0 || data.error) {
            document.getElementById('students-table-body').innerHTML = '<tr><td colspan="5" style="text-align: center;">Нет данных о посещаемости</td></tr>';
            return;
        }
        
        const tbody = document.getElementById('students-table-body');
        tbody.innerHTML = '';
        
        data.forEach(student => {
            const row = tbody.insertRow();
            row.insertCell(0).textContent = student.name;
            row.insertCell(1).textContent = student.total_pairs;
            row.insertCell(2).textContent = student.total_pairs - student.absent;
            row.insertCell(3).textContent = student.absent;
            const percentCell = row.insertCell(4);
            percentCell.textContent = student.percent + '%';
            
            if (student.percent >= 80) percentCell.className = 'percent-high';
            else if (student.percent >= 60) percentCell.className = 'percent-medium';
            else if (student.percent >= 40) percentCell.className = 'percent-low';
            else percentCell.className = 'percent-very-low';
        });
        
    } catch (error) {
        console.error('Ошибка:', error);
        document.getElementById('students-table-body').innerHTML = '<tr><td colspan="5" style="text-align: center; color: red;">Ошибка загрузки</td></tr>';
    }
}

function getPeriodText() {
    if (currentPeriod === 'week') {
        return 'Неделя';
    } else if (currentPeriod === 'month') {
        return `Месяц: ${currentMonth}.${currentYear}`;
    } else {
        return `Семестр: ${currentSemester === 1 ? '1 (сентябрь-декабрь)' : '2 (январь-июнь)'} ${currentYear}`;
    }
}

function updateSelectors() {
    const monthSelector = document.getElementById('month-selector');
    const semesterSelector = document.getElementById('semester-selector');
    
    if (currentPeriod === 'month') {
        monthSelector.style.display = 'flex';
        semesterSelector.style.display = 'none';
    } else if (currentPeriod === 'semester') {
        monthSelector.style.display = 'none';
        semesterSelector.style.display = 'flex';
    } else {
        monthSelector.style.display = 'none';
        semesterSelector.style.display = 'none';
    }
}

function initStatistics(groupName) {
    document.querySelectorAll('.period-btn').forEach(btn => {
        if (btn.id !== 'exportBtn') {
            btn.addEventListener('click', function() {
                document.querySelectorAll('.period-btn').forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                currentPeriod = this.getAttribute('data-period');
                updateSelectors();
                loadTrendData(groupName);
            });
        }
    });
    
    document.getElementById('apply-month').addEventListener('click', function() {
        currentYear = parseInt(document.getElementById('month-year').value);
        currentMonth = parseInt(document.getElementById('month-month').value);
        loadTrendData(groupName);
    });
    
    document.getElementById('apply-semester').addEventListener('click', function() {
        currentYear = parseInt(document.getElementById('semester-year').value);
        currentSemester = parseInt(document.getElementById('semester-type').value);
        loadTrendData(groupName);
    });
    
    loadTrendData(groupName);
    loadStudentStats(groupName);
    updateSelectors();
}