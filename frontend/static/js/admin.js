let chartInstances = {};
let updateTimerInterval = null;
let dashboardUpdateInterval = null;

async function fetchWithToken(url, options = {}) {
    try {
        const tokenResponse = await fetch('/get_token', { credentials: 'include' });
        const tokenData = await tokenResponse.json();
        const token = tokenData.token;
        if (!token) {
            throw new Error('Токен не получен');
        }
        options.headers = options.headers || {};
        options.headers['Authorization'] = 'Bearer ' + token;
        options.credentials = 'include';
        const response = await fetch(url, options);
        if (!response.ok) {
            const text = await response.text();
            throw new Error(`Ошибка ${response.status}: ${text}`);
        }
        return response;
    } catch (error) {
        console.error('fetchWithToken error:', error);
        showAlert('Ошибка авторизации или соединения. Пожалуйста, войдите заново.', 'error');
        throw error;
    }
}

function showAlert(message, type = 'success') {
    const container = document.getElementById('alertContainer');
    const alertClass = type === 'success' ? 'alert-success' :
                       type === 'error' ? 'alert-error' : 'alert-info';
    container.innerHTML = `<div class="alert ${alertClass}">${message}</div>`;
    setTimeout(() => { container.innerHTML = ''; }, 5000);
}

function formatDate(ts) {
    if (!ts) return '—';
    const d = new Date(ts);
    return d.toLocaleDateString('ru-RU') + ' ' + d.toLocaleTimeString('ru-RU');
}

function initTabs() {
    const btns = document.querySelectorAll('.tab-btn');
    const contents = document.querySelectorAll('.tab-content');
    btns.forEach(btn => {
        btn.addEventListener('click', function() {
            btns.forEach(b => b.classList.remove('active'));
            contents.forEach(c => c.classList.remove('active'));
            this.classList.add('active');
            const tabId = this.getAttribute('data-tab');
            document.getElementById('tab-' + tabId).classList.add('active');
            if (tabId === 'dashboard') loadDashboard(false);
            else if (tabId === 'groups') loadGroups();
            else if (tabId === 'users') loadUsers();
            else if (tabId === 'students') loadStudentGroups();
        });
    });
}

async function loadDashboard(updateStats = true) {
    try {
        if (updateStats) {
            const respStats = await fetchWithToken('/api/dashboard/stats');
            const stats = await respStats.json();
            document.getElementById('metricGroups').textContent = stats.total_groups ?? '—';
            document.getElementById('metricStudents').textContent = stats.total_students ?? '—';
            document.getElementById('metricPairs').textContent = stats.total_pairs ?? '—';
            document.getElementById('metricPresent').textContent = stats.total_present ?? '—';
            document.getElementById('metricAttendance').textContent = (stats.overall_attendance ?? 0) + '%';
            
            await loadStudentRatings();
            await loadDayTimeStats();
            await loadLastUpdateTime();
        }

        if (updateStats) {
            await loadSystemStatus();
        }

        await loadCharts();

    } catch (e) {
        console.error('loadDashboard error:', e);
        if (updateStats) {
            showAlert('Ошибка загрузки дашборда', 'error');
        }
    }
}

async function loadSystemStatus() {
    try {
        const resp = await fetchWithToken('/api/system_status');
        const data = await resp.json();
        const dbDot = document.getElementById('dbDot');
        const modelDot = document.getElementById('modelDot');

        if (data.database) {
            dbDot.className = 'dot online';
        } else {
            dbDot.className = 'dot offline';
        }

        if (data.model) {
            modelDot.className = 'dot online';
        } else {
            modelDot.className = 'dot offline';
        }

        document.getElementById('apiDot').className = 'dot online';

        
        try {
            const intervalResp = await fetchWithToken('/api/schedule_interval');
            const intervalData = await intervalResp.json();
            const interval = intervalData.interval || 3600;
            startUpdateTimer(interval);
        } catch (e) {
            console.error('Ошибка получения интервала:', e);
            startUpdateTimer(3600);
        }

    } catch (e) {
        console.error('loadSystemStatus error:', e);
        startUpdateTimer(3600);
        document.getElementById('dbDot').className = 'dot offline';
        document.getElementById('modelDot').className = 'dot offline';
        document.getElementById('apiDot').className = 'dot offline';
    }
}


let timerTotalSeconds = 3600;
let timerStartTime = null;

function startUpdateTimer(seconds) {
    if (updateTimerInterval) clearInterval(updateTimerInterval);
    
    timerTotalSeconds = seconds;
    timerStartTime = Date.now();
    
    localStorage.setItem('updateTimerTotal', seconds.toString());
    localStorage.setItem('updateTimerStart', timerStartTime.toString());
    
    updateTimerDisplay();
    
    updateTimerInterval = setInterval(() => {
        const elapsed = Math.floor((Date.now() - timerStartTime) / 1000);
        const remaining = Math.max(0, timerTotalSeconds - elapsed);
        updateTimerDisplay();
        
        if (remaining <= 0) {
            clearInterval(updateTimerInterval);
            refreshSchedule();
        }
    }, 1000);
}

function updateTimerDisplay() {
    if (!timerStartTime) return;
    const elapsed = Math.floor((Date.now() - timerStartTime) / 1000);
    const remaining = Math.max(0, timerTotalSeconds - elapsed);
    
    const h = Math.floor(remaining / 3600);
    const m = Math.floor((remaining % 3600) / 60);
    const s = remaining % 60;
    const el = document.getElementById('updateTimer');
    if (el) {
        el.textContent = 
            String(h).padStart(2, '0') + ':' +
            String(m).padStart(2, '0') + ':' +
            String(s).padStart(2, '0');
    }
}

function refreshSchedule() {
    console.log('Обновление расписания...');
    showAlert('Расписание обновляется...', 'info');
    
    fetchWithToken('/api/force_update', { method: 'POST' })
        .then(() => {
            showAlert('Расписание обновлено!', 'success');
            startUpdateTimer(timerTotalSeconds);
            loadDashboard(true);
        })
        .catch(() => {
            showAlert('Ошибка обновления расписания', 'error');
            startUpdateTimer(timerTotalSeconds);
        });
}

function restoreTimer() {
    const savedTotal = localStorage.getItem('updateTimerTotal');
    const savedStart = localStorage.getItem('updateTimerStart');
    
    if (savedTotal && savedStart) {
        const total = parseInt(savedTotal);
        const start = parseInt(savedStart);
        const elapsed = Math.floor((Date.now() - start) / 1000);
        const remaining = Math.max(0, total - elapsed);
        
        if (remaining > 0) {
            timerTotalSeconds = total;
            timerStartTime = start;
            updateTimerDisplay();
            
            if (updateTimerInterval) clearInterval(updateTimerInterval);
            updateTimerInterval = setInterval(() => {
                const newElapsed = Math.floor((Date.now() - timerStartTime) / 1000);
                const newRemaining = Math.max(0, timerTotalSeconds - newElapsed);
                updateTimerDisplay();
                
                if (newRemaining <= 0) {
                    clearInterval(updateTimerInterval);
                    refreshSchedule();
                }
            }, 1000);
            return true;
        }
    }
    return false;
}

let chartsLoaded = false;

async function loadCharts() {
    try {
        const resp = await fetchWithToken('/api/dashboard/charts');
        const data = await resp.json();

        if (chartInstances.bar) {
            chartInstances.bar.data.labels = data.bar.labels;
            chartInstances.bar.data.datasets[0].data = data.bar.data;
            chartInstances.bar.update('none');  // Без анимации
            
            chartInstances.line.data.labels = data.line.labels;
            chartInstances.line.data.datasets[0].data = data.line.data;
            chartInstances.line.update('none');
            
            chartInstances.pie.data.labels = data.pie.labels;
            chartInstances.pie.data.datasets[0].data = data.pie.data;
            chartInstances.pie.update('none');
            return;
        }

        chartsLoaded = true;

        const barCtx = document.getElementById('barChart').getContext('2d');
        chartInstances.bar = new Chart(barCtx, {
            type: 'bar',
            data: {
                labels: data.bar.labels,
                datasets: [{
                    label: 'Посещаемость %',
                    data: data.bar.data,
                    backgroundColor: 'rgba(231, 0, 76, 0.6)',
                    borderColor: 'rgba(231, 0, 76, 1)',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true, max: 100 } }
            }
        });

        const lineCtx = document.getElementById('lineChart').getContext('2d');
        chartInstances.line = new Chart(lineCtx, {
            type: 'line',
            data: {
                labels: data.line.labels,
                datasets: [{
                    label: 'Посещаемость %',
                    data: data.line.data,
                    borderColor: '#e7004c',
                    backgroundColor: 'rgba(231, 0, 76, 0.1)',
                    fill: true,
                    tension: 0.3,
                    pointRadius: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true, max: 100 } }
            }
        });

        const pieCtx = document.getElementById('pieChart').getContext('2d');
        const colors = ['#e7004c', '#ff6b6b', '#ffb347', '#4ecdc4', '#45b7d1', '#96ceb4', '#ffcc5c', '#ff6f69'];
        chartInstances.pie = new Chart(pieCtx, {
            type: 'pie',
            data: {
                labels: data.pie.labels,
                datasets: [{
                    data: data.pie.data,
                    backgroundColor: colors.slice(0, data.pie.labels.length),
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: { legend: { position: 'bottom' } }
            }
        });

    } catch (e) {
        console.error('loadCharts error:', e);
        chartsLoaded = false;
    }
}


async function loadGroups() {
    try {
        const resp = await fetchWithToken('/api/groups');
        const groups = await resp.json();

        const tbody = document.getElementById('groupsTableBody');
        if (!Array.isArray(groups) || groups.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="text-center">Нет групп</td></tr>';
            return;
        }

        let html = '';
        for (let idx = 0; idx < groups.length; idx++) {
            const name = groups[idx];
            let studentCount = '0';
            try {
                const respStudents = await fetchWithToken(`/api/students/${encodeURIComponent(name)}`);
                const students = await respStudents.json();
                if (Array.isArray(students)) {
                    studentCount = students.length;
                }
            } catch (e) {
                console.error(`Ошибка получения студентов для ${name}:`, e);
                studentCount = '?';
            }
            
            html += `
                <tr>
                    <td>${idx + 1}</td>
                    <td><strong>${name}</strong></td>
                    <td>${studentCount}</td>
                    <td>
                        <button class="btn btn-danger btn-sm delete-group" data-group="${name}">x</button>
                    </td>
                </tr>
            `;
        }
        tbody.innerHTML = html;

        document.querySelectorAll('.delete-group').forEach(btn => {
            btn.addEventListener('click', function() {
                const groupName = this.getAttribute('data-group');
                deleteGroup(groupName);
            });
        });

        populateGroupSelects(groups);

    } catch (e) {
        console.error('loadGroups error:', e);
        showAlert('Ошибка загрузки групп', 'error');
    }
}

function populateGroupSelects(groups) {
    const selects = ['studentGroupSelect', 'userGroup'];
    selects.forEach(id => {
        const sel = document.getElementById(id);
        if (!sel) return;
        const currentVal = sel.value;
        sel.innerHTML = '<option value="">Без группы</option>';
        groups.forEach(g => {
            const opt = document.createElement('option');
            opt.value = g;
            opt.textContent = g;
            sel.appendChild(opt);
        });
        if (currentVal && groups.includes(currentVal)) {
            sel.value = currentVal;
        }
    });
}

async function addGroup() {
    const input = document.getElementById('newGroupName');
    const name = input.value.trim();
    if (!name) {
        showAlert('Введите название группы', 'error');
        return;
    }
    try {
        const resp = await fetchWithToken('/api/groups', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name })
        });
        const data = await resp.json();
        if (data.success) {
            showAlert(`Группа "${name}" добавлена`, 'success');
            input.value = '';
            loadGroups();
        } else {
            showAlert(data.error || 'Ошибка добавления', 'error');
        }
    } catch (e) {
        console.error(e);
        showAlert('Ошибка добавления группы', 'error');
    }
}

async function deleteGroup(groupName) {
    if (!confirm(`Удалить группу "${groupName}" и все связанные данные?`)) return;
    try {
        const resp = await fetchWithToken(`/api/groups/${encodeURIComponent(groupName)}`, {
            method: 'DELETE'
        });
        const data = await resp.json();
        if (data.success) {
            showAlert(`Группа "${groupName}" удалена`, 'success');
            loadGroups();
        } else {
            showAlert(data.error || 'Ошибка удаления', 'error');
        }
    } catch (e) {
        console.error(e);
        showAlert('Ошибка удаления группы', 'error');
    }
}

async function loadUsers() {
    try {
        const resp = await fetchWithToken('/api/users');
        const users = await resp.json();

        const tbody = document.getElementById('usersTableBody');
        if (!Array.isArray(users) || users.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center">Нет пользователей</td></tr>';
            return;
        }

        let html = '';
        users.forEach(u => {
            html += `
                <tr>
                    <td>${u.id}</td>
                    <td><strong>${u.username}</strong></td>
                    <td>${u.full_name || '—'}</td>
                    <td>${u.group_name || '—'}</td>
                    <td>${u.role}</td>
                    <td>
                        ${u.username !== 'admin' ? `<button class="btn btn-danger btn-sm delete-user" data-user="${u.username}">x</button>` : '—'}
                    </td>
                </tr>
            `;
        });
        tbody.innerHTML = html;

        document.querySelectorAll('.delete-user').forEach(btn => {
            btn.addEventListener('click', function() {
                const username = this.getAttribute('data-user');
                deleteUser(username);
            });
        });

    } catch (e) {
        console.error('loadUsers error:', e);
        showAlert('Ошибка загрузки пользователей', 'error');
    }
}

async function addUser() {
    const username = document.getElementById('userUsername').value.trim();
    const password = document.getElementById('userPassword').value.trim();
    const fullName = document.getElementById('userFullName').value.trim();
    const group = document.getElementById('userGroup').value;
    const role = document.getElementById('userRole').value;

    if (!username || !password) {
        showAlert('Логин и пароль обязательны', 'error');
        return;
    }
    if (password.length < 4) {
        showAlert('Пароль должен быть минимум 4 символа', 'error');
        return;
    }

    try {
        const resp = await fetchWithToken('/api/users', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password, full_name: fullName, group_name: group || '', role })
        });
        const data = await resp.json();
        if (data.success) {
            showAlert(`Пользователь "${username}" создан`, 'success');
            document.getElementById('userUsername').value = '';
            document.getElementById('userPassword').value = '';
            document.getElementById('userFullName').value = '';
            loadUsers();
        } else {
            showAlert(data.error || 'Ошибка создания', 'error');
        }
    } catch (e) {
        console.error(e);
        showAlert('Ошибка создания пользователя', 'error');
    }
}

async function deleteUser(username) {
    if (!confirm(`Удалить пользователя "${username}"?`)) return;
    try {
        const resp = await fetchWithToken(`/api/users/${encodeURIComponent(username)}`, {
            method: 'DELETE'
        });
        const data = await resp.json();
        if (data.success) {
            showAlert(`Пользователь "${username}" удалён`, 'success');
            loadUsers();
        } else {
            showAlert(data.error || 'Ошибка удаления', 'error');
        }
    } catch (e) {
        console.error(e);
        showAlert('Ошибка удаления пользователя', 'error');
    }
}

async function loadStudentGroups() {
    try {
        const resp = await fetchWithToken('/api/groups');
        const groups = await resp.json();
        populateGroupSelects(groups);
        const sel = document.getElementById('studentGroupSelect');
        if (sel.value) {
            loadStudentsForGroup(sel.value);
        } else {
            document.getElementById('studentsTableBody').innerHTML = '<tr><td colspan="3" class="text-center">Выберите группу</td></tr>';
            document.getElementById('studentGroupLabel').textContent = '—';
        }
    } catch (e) {
        console.error(e);
    }
}

async function loadStudentsForGroup(groupName) {
    if (!groupName) return;
    document.getElementById('studentGroupLabel').textContent = groupName;

    try {
        const resp = await fetchWithToken(`/api/students/${encodeURIComponent(groupName)}`);
        const students = await resp.json();
        const tbody = document.getElementById('studentsTableBody');

        if (!Array.isArray(students) || students.length === 0) {
            tbody.innerHTML = '<tr><td colspan="3" class="text-center">В группе нет студентов</td></tr>';
            return;
        }

        let html = '';
        students.forEach((s, idx) => {
            html += `
                <tr>
                    <td>${idx + 1}</td>
                    <td>${s.name}</td>
                    <td>
                        <button class="btn btn-danger btn-sm delete-student" data-student="${s.name}" data-group="${groupName}">x</button>
                    </td>
                </tr>
            `;
        });
        tbody.innerHTML = html;

        document.querySelectorAll('.delete-student').forEach(btn => {
            btn.addEventListener('click', function() {
                const student = this.getAttribute('data-student');
                const group = this.getAttribute('data-group');
                deleteStudent(group, student);
            });
        });

    } catch (e) {
        console.error('loadStudentsForGroup error:', e);
        showAlert('Ошибка загрузки студентов', 'error');
    }
}

async function addStudent() {
    const group = document.getElementById('studentGroupSelect').value;
    const name = document.getElementById('studentNameInput').value.trim();
    if (!group) { showAlert('Выберите группу', 'error'); return; }
    if (!name) { showAlert('Введите ФИО студента', 'error'); return; }

    try {
        const resp = await fetchWithToken(`/api/students/${encodeURIComponent(group)}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ student_name: name })
        });
        const data = await resp.json();
        if (data.success) {
            showAlert(`Студент "${name}" добавлен`, 'success');
            document.getElementById('studentNameInput').value = '';
            loadStudentsForGroup(group);
        } else {
            showAlert(data.error || 'Ошибка добавления', 'error');
        }
    } catch (e) {
        console.error(e);
        showAlert('Ошибка добавления студента', 'error');
    }
}

async function deleteStudent(group, student) {
    if (!confirm(`Удалить студента "${student}"?`)) return;
    try {
        const resp = await fetchWithToken(`/api/students/${encodeURIComponent(group)}/${encodeURIComponent(student)}`, {
            method: 'DELETE'
        });
        const data = await resp.json();
        if (data.success) {
            showAlert(`Студент "${student}" удалён`, 'success');
            loadStudentsForGroup(group);
        } else {
            showAlert(data.error || 'Ошибка удаления', 'error');
        }
    } catch (e) {
        console.error(e);
        showAlert('Ошибка удаления студента', 'error');
    }
}

async function loadStudentRatings() {
    try {
        const resp = await fetchWithToken('/api/dashboard/student_ratings');
        const data = await resp.json();
        
        const bestContainer = document.getElementById('bestStudentsList');
        if (data.best && data.best.length > 0) {
            let html = '';
            data.best.forEach((student) => {
                html += `
                    <div class="student-rating-item">
                        <span class="name">${student.name}</span>
                        <span class="percent good">${student.percent}%</span>
                    </div>
                `;
            });
            bestContainer.innerHTML = html;
        } else {
            bestContainer.innerHTML = '<p class="text-muted text-center">Нет данных</p>';
        }
        
        const worstContainer = document.getElementById('worstStudentsList');
        if (data.worst && data.worst.length > 0) {
            const sortedWorst = [...data.worst].sort((a, b) => a.percent - b.percent);
            let html = '';
            sortedWorst.forEach((student) => {
                html += `
                    <div class="student-rating-item">
                        <span class="name">${student.name}</span>
                        <span class="percent bad">${student.percent}%</span>
                    </div>
                `;
            });
            worstContainer.innerHTML = html;
        } else {
            worstContainer.innerHTML = '<p class="text-muted text-center">Нет данных</p>';
        }
    } catch (e) {
        console.error('loadStudentRatings error:', e);
        document.getElementById('bestStudentsList').innerHTML = '<p class="text-muted text-center">Ошибка загрузки</p>';
        document.getElementById('worstStudentsList').innerHTML = '<p class="text-muted text-center">Ошибка загрузки</p>';
    }
}

async function loadDayTimeStats() {
    try {
        const resp = await fetchWithToken('/api/dashboard/day_time_stats');
        const data = await resp.json();
        
        const dayContainer = document.getElementById('dayStats');
        if (data.days && data.days.length > 0) {
            const maxPercent = Math.max(...data.days.map(d => d.percent));
            let html = '';
            data.days.forEach(day => {
                const isBest = day.percent === maxPercent && maxPercent > 0;
                const isWorst = day.percent === Math.min(...data.days.map(d => d.percent)) && maxPercent > 0;
                let barClass = 'medium';
                if (day.percent >= 80) barClass = 'good';
                else if (day.percent < 50) barClass = 'bad';
                
                html += `
                    <div class="stat-bar">
                        <span class="label">${day.day}</span>
                        <div class="bar-bg">
                            <div class="bar-fill ${barClass}" style="width: ${day.percent}%;"></div>
                        </div>
                        <span class="value">${day.percent}%</span>
                        ${isBest ? '<span class="best-label">лучший</span>' : ''}
                        ${isWorst ? '<span class="worst-label">худший</span>' : ''}
                    </div>
                `;
            });
            dayContainer.innerHTML = html;
        } else {
            dayContainer.innerHTML = '<p class="text-muted text-center">Нет данных</p>';
        }
        
        // Пары
        const pairContainer = document.getElementById('pairStats');
        if (data.pairs && data.pairs.length > 0) {
            const maxPercent = Math.max(...data.pairs.map(p => p.percent));
            let html = '';
            data.pairs.forEach(pair => {
                const isBest = pair.percent === maxPercent && maxPercent > 0;
                let barClass = 'medium';
                if (pair.percent >= 80) barClass = 'good';
                else if (pair.percent < 50) barClass = 'bad';
                
                const pairNumber = parseInt(pair.pair);
                html += `
                    <div class="stat-bar">
                        <span class="label">${pairNumber}-я</span>
                        <div class="bar-bg">
                            <div class="bar-fill ${barClass}" style="width: ${pair.percent}%;"></div>
                        </div>
                        <span class="value">${pair.percent}%</span>
                        ${isBest ? '<span class="best-label">лучшая</span>' : ''}
                    </div>
                `;
            });
            pairContainer.innerHTML = html;
        } else {
            pairContainer.innerHTML = '<p class="text-muted text-center">Нет данных</p>';
        }
    } catch (e) {
        console.error('loadDayTimeStats error:', e);
        document.getElementById('dayStats').innerHTML = '<p class="text-muted text-center">Ошибка загрузки</p>';
        document.getElementById('pairStats').innerHTML = '<p class="text-muted text-center">Ошибка загрузки</p>';
    }
}

async function loadLastUpdateTime() {
    try {
        const resp = await fetchWithToken('/api/dashboard/last_update');
        const data = await resp.json();
        const el = document.getElementById('lastUpdateTime');
        if (data.last_update) {
            const date = new Date(data.last_update);
            el.textContent = date.toLocaleString('ru-RU', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        } else {
            el.textContent = '—';
        }
    } catch (e) {
        console.error('loadLastUpdateTime error:', e);
        document.getElementById('lastUpdateTime').textContent = '—';
    }
}

async function forceUpdateSchedule() {
    const btn = document.getElementById('btnForceUpdate');
    const originalText = btn.textContent;
    btn.disabled = true;
    btn.textContent = 'Обновление...';
    
    try {
        const resp = await fetchWithToken('/api/force_update', {
            method: 'POST'
        });
        const data = await resp.json();
        if (data.success) {
            showAlert('Расписание обновлено! Сохранено ' + data.saved + ' пар', 'success');
            await loadLastUpdateTime();
            await loadDashboard(true);
        } else {
            showAlert('Ошибка обновления: ' + (data.error || 'Неизвестная ошибка'), 'error');
        }
    } catch (e) {
        console.error('forceUpdateSchedule error:', e);
        showAlert('Ошибка при обновлении расписания', 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = originalText;
    }
}

function initAdmin() {
    initTabs();

    document.getElementById('addGroupBtn').addEventListener('click', addGroup);
    document.getElementById('addUserBtn').addEventListener('click', addUser);
    document.getElementById('addStudentBtn').addEventListener('click', addStudent);
    document.getElementById('studentGroupSelect').addEventListener('change', function() {
        if (this.value) loadStudentsForGroup(this.value);
        else {
            document.getElementById('studentsTableBody').innerHTML = '<tr><td colspan="3" class="text-center">Выберите группу</td></tr>';
            document.getElementById('studentGroupLabel').textContent = '—';
        }
    });
    
    const forceUpdateBtn = document.getElementById('btnForceUpdate');
    if (forceUpdateBtn) {
        forceUpdateBtn.addEventListener('click', forceUpdateSchedule);
    }

    loadDashboard(true);
    loadGroups();

    setInterval(() => {
        const activeTab = document.querySelector('.tab-content.active');
        if (activeTab && activeTab.id === 'tab-dashboard') {
            loadDashboard(true);
        }
    }, 60000);

}

window.initAdmin = initAdmin;