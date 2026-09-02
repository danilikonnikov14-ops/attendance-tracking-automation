"""
Web Site Face Attendance
Веб-интерфейс для системы распознавания лиц
"""

from flask import Flask, render_template, request, jsonify, redirect, session, make_response
import requests
from datetime import datetime, timedelta
import os
import json
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
CORS(app, supports_credentials=True, origins=["http://135.106.186.204", "http://localhost:5001"])

API_BASE_URL = os.getenv('API_BASE_URL', 'http://backend:5000')

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_PATH='/',
    SESSION_COOKIE_DOMAIN=None,
    PERMANENT_SESSION_LIFETIME=timedelta(days=7)
)

def get_groups_from_db():
    """Получение списка групп из БД через API"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/groups",
            timeout=5
        )
        if response.status_code == 200:
            groups = response.json()
            if isinstance(groups, list):
                return groups
        return []
    except Exception as e:
        print(f"Ошибка получения групп: {e}")
        return []


def get_headers():
    """Получение заголовков с токеном"""
    headers = {}
    token = session.get('token')
    if token:
        headers['Authorization'] = f'Bearer {token}'
    return headers

def get_api_data(endpoint):
    """Запрос к API с токеном"""
    try:
        response = requests.get(
            f"{API_BASE_URL}{endpoint}",
            headers=get_headers(),
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            session.clear()
            return None
        return None
    except Exception as e:
        print(f"Ошибка API: {e}")
        return None

def post_api_data(endpoint, data=None, files=None):
    """POST запрос к API с токеном"""
    try:
        headers = get_headers()
        if not files:
            headers['Content-Type'] = 'application/json'
        
        response = requests.post(
            f"{API_BASE_URL}{endpoint}",
            json=data if not files else None,
            data=data if files else None,
            files=files,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 401:
            session.clear()
            return {'error': 'Неавторизован'}
        
        return response.json()
    except Exception as e:
        print(f"Ошибка API POST: {e}")
        return {'error': str(e)}

@app.route('/login', methods=["POST", "GET"])
def login_page():
    if request.method == "POST":
        login = request.form.get("login")
        password = request.form.get("password")
        
        if not login or not password:
            return render_template("login.html", error="Заполните все поля")
        
        try:
            response = requests.post(
                f"{API_BASE_URL}/login",
                json={'username': login, 'password': password},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    user_data = data.get('user')
                    
                    if not isinstance(user_data, dict):
                        user_data = {
                            'username': login,
                            'role': 'admin',
                            'fullName': login
                        }
                    
                    session['user'] = user_data
                    session['token'] = data.get('token')
                    session.permanent = True
                    
                    return redirect('/')
                else:
                    return render_template("login.html", error=data.get('message', 'Неверный логин или пароль'))
            else:
                return render_template("login.html", error="Ошибка сервера")
                
        except requests.exceptions.ConnectionError:
            return render_template("login.html", error="Сервер недоступен")
        except requests.exceptions.Timeout:
            return render_template("login.html", error="Превышено время ожидания")
        except Exception as e:
            print(f"Ошибка входа: {e}")
            return render_template("login.html", error="Внутренняя ошибка")
    
    if session.get('user'):
        return redirect('/')
    
    return render_template("login.html")

@app.route('/logout')
def logout():
    """Выход из системы"""
    session.clear()
    return redirect('/login')

@app.route('/get_token')
def get_token():
    """Получение JWT токена из сессии"""
    token = session.get('token')
    if token:
        return jsonify({'token': token})
    return jsonify({'token': None}), 401

@app.route('/')
def groups_page():
    """Главная страница"""
    user = session.get('user')
    if not user:
        return redirect('/login')
    
    groups = get_groups_from_db()
    
    return render_template('groups.html', groups=groups, user=user)

@app.route('/<group_name>.html')
def group_schedule(group_name):
    user = session.get('user')
    if not user:
        return redirect('/login')

    groups = get_groups_from_db()
    if group_name not in groups:
        return render_template('404.html'), 404
    
    schedule = get_api_data(f"/schedule/{group_name}") or []
    return render_template('group.html', group_name=group_name, schedule=schedule, user=user)

@app.route('/lesson/<group_name>/<date>/<pair_number>')
def lesson_details(group_name, date, pair_number):
    user = session.get('user')
    if not user:
        return redirect('/login')

    groups = get_groups_from_db()
    if group_name not in groups:
        return render_template('404.html'), 404

    schedule = get_api_data(f"/schedule/{group_name}") or []
    lesson = None
    day_name = ""

    for day in schedule:
        for cls in day.get('classes', []):
            if cls.get('number') == pair_number:
                lesson = cls
                day_name = day.get('name', '')
                break
        if lesson:
            break

    if not lesson:
        return render_template('404.html'), 404

    stats_data = get_api_data(f"/attendance_stats/{group_name}/{date}/{pair_number}") or {}

    return render_template('lesson_details.html',
        lesson={
            'subject': lesson.get('subject', '—'),
            'group_name': group_name,
            'pair_number': pair_number,
            'time': lesson.get('time', ''),
            'date': date,
            'day_name': day_name,
            'room': lesson.get('room', '—'),
            'teacher': lesson.get('teacher', '—')
        },
        present_list=stats_data.get('presentList', []),
        absent_list=stats_data.get('absentList', []),
        stats={
            'total': stats_data.get('total', 0),
            'present': stats_data.get('present', 0),
            'absent': stats_data.get('absent', 0)
        },
        user=user
    )

@app.route('/statistics/<group_name>')
def statistics_page(group_name):
    user = session.get('user')
    if not user:
        return redirect('/login')

    groups = get_groups_from_db()
    if group_name not in groups:
        return render_template('404.html'), 404
    
    return render_template('statistics.html', group_name=group_name, user=user)


ADMIN_URL = '/sdfg23j4h5k6j7h8g9f0d1s2a3d4f5g612'

@app.route(ADMIN_URL)
def admin_page():
    """Страница админ-панели (скрытый URL)"""
    user = session.get('user')
    
    if not user or not isinstance(user, dict):
        return redirect('/login')
    
    if user.get('role') != 'admin':
        return redirect('/login')
    
    groups = get_groups_from_db()
    
    return render_template('admin.html', groups=groups, user=user)

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()})


@app.route('/attendance_stats/<group_name>/<date>/<pair_number>')
def attendance_stats_proxy(group_name, date, pair_number):
    try:
        response = requests.get(
            f"{API_BASE_URL}/attendance_stats/{group_name}/{date}/{pair_number}",
            headers=get_headers(),
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if data.get('total', 0) > 0:
                return jsonify({
                    'has_data': True,
                    'total': data.get('total', 0),
                    'present': data.get('present', 0),
                    'absent': data.get('absent', 0),
                    'presentList': data.get('presentList', []),
                    'absentList': data.get('absentList', [])
                })
        elif response.status_code == 401:
            session.clear()
            return jsonify({'has_data': False, 'total': 0, 'present': 0, 'absent': 0, 'error': 'auth'})
        
        return jsonify({'has_data': False, 'total': 0, 'present': 0, 'absent': 0})
    except Exception as e:
        print(f"Ошибка: {e}")
        return jsonify({'has_data': False, 'total': 0, 'present': 0, 'absent': 0})

@app.route('/attendance_trend/<group_name>')
def attendance_trend_proxy(group_name):
    period = request.args.get('period', 'week')
    year = request.args.get('year', '')
    month = request.args.get('month', '')
    semester = request.args.get('semester', '')

    url = f"{API_BASE_URL}/attendance_trend/{group_name}?period={period}"
    if year:
        url += f"&year={year}"
    if month:
        url += f"&month={month}"
    if semester:
        url += f"&semester={semester}"

    try:
        response = requests.get(url, headers=get_headers(), timeout=10)
        if response.status_code == 401:
            session.clear()
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'dates': [], 'rates': []}), 500

@app.route('/student_stats/<group_name>')
def student_stats_proxy(group_name):
    try:
        response = requests.get(
            f"{API_BASE_URL}/student_stats/{group_name}",
            headers=get_headers(),
            timeout=10
        )
        if response.status_code == 401:
            session.clear()
        return jsonify(response.json()), response.status_code
    except Exception as e:
        print(f"Ошибка: {e}")
        return jsonify([]), 500

@app.route('/day_attendance/<group_name>/<date>')
def day_attendance_proxy(group_name, date):
    try:
        response = requests.get(
            f"{API_BASE_URL}/day_attendance/{group_name}/{date}",
            headers=get_headers(),
            timeout=10
        )
        if response.status_code == 401:
            session.clear()
        return jsonify(response.json()), response.status_code
    except Exception as e:
        print(f"Ошибка: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/students/<group_name>', methods=['GET'])
def api_get_students(group_name):
    """Получение списка студентов группы"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/students/{group_name}",
            headers=get_headers(),
            timeout=10
        )
        
        if response.status_code == 401:
            session.clear()
            return jsonify({'error': 'Неавторизован'}), 401
        
        return jsonify(response.json()), response.status_code
    except Exception as e:
        print(f"Ошибка: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/students/<group_name>', methods=['POST'])
def api_add_student(group_name):
    """Добавление студента в группу"""
    try:
        data = request.get_json()
        headers = get_headers()
        
        response = requests.post(
            f"{API_BASE_URL}/students/{group_name}",
            json=data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 401:
            session.clear()
            return jsonify({'error': 'Неавторизован'}), 401
        
        return jsonify(response.json()), response.status_code
    except Exception as e:
        print(f"Ошибка: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/students/<group_name>/<student_name>', methods=['DELETE'])
def api_delete_student(group_name, student_name):
    """Удаление студента из группы"""
    try:
        headers = get_headers()
        
        response = requests.delete(
            f"{API_BASE_URL}/students/{group_name}/{student_name}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 401:
            session.clear()
            return jsonify({'error': 'Неавторизован'}), 401
        
        return jsonify(response.json()), response.status_code
    except Exception as e:
        print(f"Ошибка: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/dashboard/stats')
def dashboard_stats_proxy():
    try:
        response = requests.get(
            f"{API_BASE_URL}/dashboard/stats",
            headers=get_headers(),
            timeout=10
        )
        if response.status_code == 401:
            session.clear()
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard/charts')
def dashboard_charts_proxy():
    try:
        response = requests.get(
            f"{API_BASE_URL}/dashboard/charts",
            headers=get_headers(),
            timeout=10
        )
        if response.status_code == 401:
            session.clear()
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/system_status')
def system_status_proxy():
    try:
        response = requests.get(
            f"{API_BASE_URL}/system_status",
            headers=get_headers(),
            timeout=5
        )
        if response.status_code == 401:
            session.clear()
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/groups', methods=['GET', 'POST'])
def groups_proxy():
    try:
        headers = get_headers()
        if request.method == 'POST':
            response = requests.post(
                f"{API_BASE_URL}/groups",
                json=request.get_json(),
                headers=headers,
                timeout=10
            )
        else:
            response = requests.get(
                f"{API_BASE_URL}/groups",
                headers=headers,
                timeout=10
            )
        if response.status_code == 401:
            session.clear()
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/groups/<group_name>', methods=['DELETE'])
def delete_group_proxy(group_name):
    try:
        headers = get_headers()
        response = requests.delete(
            f"{API_BASE_URL}/groups/{group_name}",
            headers=headers,
            timeout=10
        )
        if response.status_code == 401:
            session.clear()
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/users', methods=['GET', 'POST'])
def users_proxy():
    try:
        headers = get_headers()
        if request.method == 'POST':
            response = requests.post(
                f"{API_BASE_URL}/users",
                json=request.get_json(),
                headers=headers,
                timeout=10
            )
        else:
            response = requests.get(
                f"{API_BASE_URL}/users",
                headers=headers,
                timeout=10
            )
        if response.status_code == 401:
            session.clear()
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/<username>', methods=['DELETE'])
def delete_user_proxy(username):
    try:
        headers = get_headers()
        response = requests.delete(
            f"{API_BASE_URL}/users/{username}",
            headers=headers,
            timeout=10
        )
        if response.status_code == 401:
            session.clear()
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/dashboard/student_ratings')
def student_ratings_proxy():
    try:
        response = requests.get(
            f"{API_BASE_URL}/dashboard/student_ratings",
            headers=get_headers(),
            timeout=10
        )
        if response.status_code == 401:
            session.clear()
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/dashboard/day_time_stats')
def day_time_stats_proxy():
    try:
        response = requests.get(
            f"{API_BASE_URL}/dashboard/day_time_stats",
            headers=get_headers(),
            timeout=10
        )
        if response.status_code == 401:
            session.clear()
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/dashboard/last_update')
def last_update_proxy():
    try:
        response = requests.get(
            f"{API_BASE_URL}/last_update",
            headers=get_headers(),
            timeout=5
        )
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'last_update': None}), 500


@app.route('/api/force_update', methods=['POST'])
def force_update_proxy():
    try:
        response = requests.post(
            f"{API_BASE_URL}/force_update",
            headers=get_headers(),
            timeout=30
        )
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/schedule_interval')
def schedule_interval_proxy():
    try:
        response = requests.get(
            f"{API_BASE_URL}/schedule_interval",
            headers=get_headers(),
            timeout=5
        )
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({'interval': 3600}), 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)