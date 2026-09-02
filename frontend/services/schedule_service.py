"""
Сервис для работы с расписанием
"""

from datetime import datetime


class ScheduleService:
    """Сервис для работы с расписанием"""
    
    def __init__(self, api_client):
        self.api_client = api_client
    
    def get_schedule(self, group_name):
        """Получение расписания с преобразованием дат"""
        schedule = self.api_client.get_schedule(group_name)
        
        if not schedule:
            return []
        
        for day in schedule:
            day_date = day.get('date', '')
            if day_date and day_date.isdigit() and len(day_date) >= 10:
                try:
                    timestamp_ms = int(day_date)
                    date_obj = datetime.fromtimestamp(timestamp_ms / 1000)
                    day['date'] = date_obj.strftime('%Y-%m-%d')
                except:
                    pass
        
        return schedule
    
    def get_lesson(self, group_name, date, pair_number):
        """Получение информации о конкретной паре"""
        schedule = self.get_schedule(group_name)
        
        for day in schedule:
            for cls in day.get('classes', []):
                if cls.get('number') == pair_number:
                    return {
                        'lesson': cls,
                        'day_name': day.get('name', ''),
                        'day_date': day.get('date', '')
                    }
        return None
    
    def get_lesson_with_attendance(self, group_name, date, pair_number):
        """Получение пары с посещаемостью"""
        lesson_info = self.get_lesson(group_name, date, pair_number)
        
        if not lesson_info:
            return None
        
        stats = self.api_client.get_attendance_stats(group_name, date, pair_number) or {}
        
        return {
            'lesson': lesson_info['lesson'],
            'day_name': lesson_info['day_name'],
            'stats': stats
        }
    
    def format_attendance_data(self, group_name, date, pair_number):
        """Форматирование данных посещаемости для отображения"""
        stats = self.api_client.get_attendance_stats(group_name, date, pair_number) or {}
        
        return {
            'has_data': stats.get('total', 0) > 0,
            'total': stats.get('total', 0),
            'present': stats.get('present', 0),
            'absent': stats.get('absent', 0),
            'present_list': stats.get('presentList', []),
            'absent_list': stats.get('absentList', [])
        }
    
    def get_group_stats(self, group_name):
        """Получение полной статистики по группе"""
        student_stats = self.api_client.get_student_stats(group_name) or []
        
        total_pairs = 0
        total_present = 0
        
        for stat in student_stats:
            total_pairs += stat.get('total_pairs', 0)
            total_present += stat.get('total_pairs', 0) - stat.get('absent', 0)
        
        return {
            'students': student_stats,
            'total_students': len(student_stats),
            'total_pairs': total_pairs,
            'total_present': total_present,
            'total_absent': total_pairs - total_present,
            'overall_percent': round((total_present / total_pairs * 100), 1) if total_pairs > 0 else 0
        }