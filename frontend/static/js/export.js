async function exportToPDF(groupName) {
    const printContainer = document.createElement('div');
    printContainer.style.padding = '20px';
    printContainer.style.fontFamily = 'Arial, sans-serif';
    printContainer.style.backgroundColor = 'white';
    
    const title = document.createElement('h1');
    title.style.textAlign = 'center';
    title.style.color = '#e7004c';
    title.style.fontSize = '24px';
    title.style.marginBottom = '10px';
    title.innerText = `Статистика группы ${groupName}`;
    printContainer.appendChild(title);
    
    const periodInfo = document.createElement('p');
    periodInfo.style.textAlign = 'center';
    periodInfo.style.fontSize = '14px';
    periodInfo.style.color = '#666';
    periodInfo.style.marginBottom = '30px';
    periodInfo.innerText = getPeriodText();
    printContainer.appendChild(periodInfo);
    
    if (currentChartData.dates && currentChartData.dates.length > 0) {
        const chartTitle = document.createElement('h3');
        chartTitle.style.fontSize = '18px';
        chartTitle.style.marginBottom = '15px';
        chartTitle.style.color = '#333';
        chartTitle.innerText = 'Посещаемость по дням';
        printContainer.appendChild(chartTitle);
        
        const chartTable = document.createElement('table');
        chartTable.style.width = '100%';
        chartTable.style.borderCollapse = 'collapse';
        chartTable.style.marginBottom = '30px';
        chartTable.style.fontSize = '12px';
        
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        headerRow.style.backgroundColor = '#e7004c';
        headerRow.style.color = 'white';
        
        ['Дата', 'Посещаемость (%)'].forEach(text => {
            const th = document.createElement('th');
            th.textContent = text;
            th.style.border = '1px solid #ddd';
            th.style.padding = '10px';
            th.style.textAlign = 'center';
            headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);
        chartTable.appendChild(thead);
        
        const tbody = document.createElement('tbody');
        for (let i = 0; i < currentChartData.dates.length; i++) {
            const row = document.createElement('tr');
            const tdDate = document.createElement('td');
            tdDate.textContent = currentChartData.dates[i];
            tdDate.style.border = '1px solid #ddd';
            tdDate.style.padding = '8px';
            tdDate.style.textAlign = 'center';
            const tdRate = document.createElement('td');
            tdRate.textContent = currentChartData.rates[i] + '%';
            tdRate.style.border = '1px solid #ddd';
            tdRate.style.padding = '8px';
            tdRate.style.textAlign = 'center';
            if (currentChartData.rates[i] >= 80) tdRate.style.color = '#28a745';
            else if (currentChartData.rates[i] >= 60) tdRate.style.color = '#ffc107';
            else if (currentChartData.rates[i] >= 40) tdRate.style.color = '#fd7e14';
            else tdRate.style.color = '#dc3545';
            tdRate.style.fontWeight = 'bold';
            row.appendChild(tdDate);
            row.appendChild(tdRate);
            tbody.appendChild(row);
        }
        chartTable.appendChild(tbody);
        printContainer.appendChild(chartTable);
    }
    
    if (currentStudentData && currentStudentData.length > 0) {
        const studentTitle = document.createElement('h3');
        studentTitle.style.fontSize = '18px';
        studentTitle.style.marginBottom = '15px';
        studentTitle.style.marginTop = '20px';
        studentTitle.style.color = '#333';
        studentTitle.innerText = 'Посещаемость студентов';
        printContainer.appendChild(studentTitle);
        
        const studentTable = document.createElement('table');
        studentTable.style.width = '100%';
        studentTable.style.borderCollapse = 'collapse';
        studentTable.style.fontSize = '12px';
        
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        headerRow.style.backgroundColor = '#e7004c';
        headerRow.style.color = 'white';
        
        ['Студент', 'Всего пар', 'Присутствовал', 'Пропуски', '%'].forEach(text => {
            const th = document.createElement('th');
            th.textContent = text;
            th.style.border = '1px solid #ddd';
            th.style.padding = '10px';
            th.style.textAlign = 'center';
            headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);
        studentTable.appendChild(thead);
        
        const tbody = document.createElement('tbody');
        currentStudentData.forEach(student => {
            const row = document.createElement('tr');
            const present = student.total_pairs - student.absent;
            const tdName = document.createElement('td');
            tdName.textContent = student.name;
            tdName.style.border = '1px solid #ddd';
            tdName.style.padding = '8px';
            const tdTotal = document.createElement('td');
            tdTotal.textContent = student.total_pairs;
            tdTotal.style.border = '1px solid #ddd';
            tdTotal.style.padding = '8px';
            tdTotal.style.textAlign = 'center';
            const tdPresent = document.createElement('td');
            tdPresent.textContent = present;
            tdPresent.style.border = '1px solid #ddd';
            tdPresent.style.padding = '8px';
            tdPresent.style.textAlign = 'center';
            const tdAbsent = document.createElement('td');
            tdAbsent.textContent = student.absent;
            tdAbsent.style.border = '1px solid #ddd';
            tdAbsent.style.padding = '8px';
            tdAbsent.style.textAlign = 'center';
            const tdPercent = document.createElement('td');
            tdPercent.textContent = student.percent + '%';
            tdPercent.style.border = '1px solid #ddd';
            tdPercent.style.padding = '8px';
            tdPercent.style.textAlign = 'center';
            if (student.percent >= 80) tdPercent.style.color = '#28a745';
            else if (student.percent >= 60) tdPercent.style.color = '#ffc107';
            else if (student.percent >= 40) tdPercent.style.color = '#fd7e14';
            else tdPercent.style.color = '#dc3545';
            tdPercent.style.fontWeight = 'bold';
            
            row.appendChild(tdName);
            row.appendChild(tdTotal);
            row.appendChild(tdPresent);
            row.appendChild(tdAbsent);
            row.appendChild(tdPercent);
            tbody.appendChild(row);
        });
        studentTable.appendChild(tbody);
        printContainer.appendChild(studentTable);
    }
    
    const opt = {
        margin: [10, 10, 10, 10],
        filename: `statistika_${currentPeriod}_${currentYear}.pdf`,
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { scale: 2, useCORS: true, logging: false },
        jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
    };
    
    html2pdf().set(opt).from(printContainer).save();
}

function exportToExcel(groupName) {
    const workbook = XLSX.utils.book_new();
    const periodText = getPeriodText();
    
    if (currentChartData.dates && currentChartData.dates.length > 0) {
        const trendData = [];
        trendData.push(['ГРУППА:', groupName]);
        trendData.push(['ПЕРИОД:', periodText]);
        trendData.push([]);
        trendData.push(['Дата', 'Посещаемость (%)']);
        for (let i = 0; i < currentChartData.dates.length; i++) {
            trendData.push([currentChartData.dates[i], currentChartData.rates[i]]);
        }
        const trendSheet = XLSX.utils.aoa_to_sheet(trendData);
        trendSheet['!cols'] = [{wch:20}, {wch:25}];
        XLSX.utils.book_append_sheet(workbook, trendSheet, 'Посещаемость по дням');
    }
    
    if (currentStudentData && currentStudentData.length > 0) {
        const studentData = [];
        studentData.push(['ГРУППА:', groupName]);
        studentData.push(['ПЕРИОД:', periodText]);
        studentData.push(['Дата выгрузки:', new Date().toLocaleString('ru-RU')]);
        studentData.push([]);
        studentData.push(['Студент', 'Всего пар', 'Присутствовал', 'Пропуски', 'Процент посещаемости']);
        currentStudentData.forEach(student => {
            studentData.push([
                student.name,
                student.total_pairs,
                student.total_pairs - student.absent,
                student.absent,
                student.percent + '%'
            ]);
        });
        const studentSheet = XLSX.utils.aoa_to_sheet(studentData);
        studentSheet['!cols'] = [{wch:30}, {wch:12}, {wch:12}, {wch:12}, {wch:20}];
        XLSX.utils.book_append_sheet(workbook, studentSheet, 'Студенты');
    }
    
    XLSX.writeFile(workbook, `statistika_${groupName}_${currentPeriod}_${currentYear}.xlsx`);
}

function initExportModal(groupName) {
    const modal = document.getElementById('exportModal');
    const exportBtn = document.getElementById('exportBtn');
    const closeModalBtn = document.getElementById('closeModalBtn');
    const exportPdfBtn = document.getElementById('exportPdfBtn');
    const exportExcelBtn = document.getElementById('exportExcelBtn');
    
    exportBtn.addEventListener('click', function() {
        modal.style.display = 'flex';
    });
    
    closeModalBtn.addEventListener('click', function() {
        modal.style.display = 'none';
    });
    
    window.addEventListener('click', function(event) {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
    
    exportPdfBtn.addEventListener('click', function() {
        modal.style.display = 'none';
        exportToPDF(groupName);
    });
    
    exportExcelBtn.addEventListener('click', function() {
        modal.style.display = 'none';
        exportToExcel(groupName);
    });
}