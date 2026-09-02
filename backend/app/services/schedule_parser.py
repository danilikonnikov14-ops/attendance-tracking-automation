"""
Парсинг расписания с сайта
"""

import requests
from bs4 import BeautifulSoup
import re
from app.utils.logger import get_logger
from app.models.schedule import save_schedule

logger = get_logger(__name__)


def parse_schedule_from_site(group_name: str):
    """
    Парсит расписание с сайта для указанной группы
    """
    url = f"https://расписание.нхтк.рф/{group_name}.html"
    
    try:
        logger.info(f"Парсинг расписания для {group_name} с {url}")
        
        response = requests.get(url, timeout=15)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        days = []
        current_day = None
        current_date = None
        current_classes = []
        
        for row in soup.find_all('tr', class_=lambda c: c and 'занятие' in c):
            prev_row = row.find_previous_sibling('tr', class_=lambda c: c and 'дата' in c)
            if prev_row:
                day_div = prev_row.find('div', class_=lambda c: c and 'день-недели' in c) if prev_row else None
                if not day_div:
                    day_text = prev_row.get_text(strip=True)
                    day_div = prev_row  
                else:
                    day_text = day_div.get_text(strip=True)
                
                if current_day != day_text:
                    if current_day and current_classes:
                        days.append({
                            'name': current_day,
                            'date': current_date or '',
                            'classes': current_classes.copy()
                        })
                    current_day = day_text
                    if day_div and day_div.get('data-id'):
                        current_date = day_div.get('data-id', '')
                    else:
                        date_match = re.search(r'(\d{2}\.\d{2}\.\d{4})', day_text)
                        if date_match:
                            current_date = date_match.group(1)
                        else:
                            current_date = ''
                    current_classes = []
            
            cells = row.find_all('td')
            if len(cells) >= 4:
                pair_num = row.get('data-pair-number', '')
                if pair_num:
                    pair_num = re.sub(r'[^0-9]', '', pair_num)
                    if len(pair_num) > 1:
                        pair_num = pair_num[0]
                else:
                    pair_text = cells[0].get_text(strip=True)
                    nums = re.findall(r'\d', pair_text)
                    pair_num = nums[0] if nums else '?'
                
                time_range = cells[1].get_text(strip=True) if len(cells) > 1 else ''
                time_range = re.sub(r'\s+', ' ', time_range).strip()
                
                subject = cells[2].get_text(strip=True) if len(cells) > 2 else ''
                
                teacher = cells[3].get_text(strip=True) if len(cells) > 3 else ''
                
                room = cells[4].get_text(strip=True) if len(cells) >= 5 else ''
                
                if pair_num and subject and subject != '—' and subject != '':
                    current_classes.append({
                        'number': pair_num,
                        'time': time_range,
                        'subject': subject,
                        'teacher': teacher if teacher and teacher != '—' else '—',
                        'room': room if room and room != '—' else '—'
                    })
        
        if current_day and current_classes:
            days.append({
                'name': current_day,
                'date': current_date or '',
                'classes': current_classes
            })
        
        total_classes = sum(len(d['classes']) for d in days)
        logger.info(f"Расписание для {group_name}: {len(days)} дней, {total_classes} пар")
        
        return days
        
    except requests.exceptions.Timeout:
        logger.error(f"Таймаут при парсинге {group_name}")
        return []
    except requests.exceptions.ConnectionError:
        logger.error(f"Ошибка соединения при парсинге {group_name}")
        return []
    except Exception as e:
        logger.error(f"Ошибка парсинга {group_name}: {e}")
        return []


def update_schedule_for_group(group_name):
    """Обновление расписания для одной группы"""
    days = parse_schedule_from_site(group_name)
    if days:
        return save_schedule(group_name, days)
    return 0


def update_all_schedules(groups):
    """Обновление расписания для всех групп"""
    logger.info("Запуск обновления расписания для всех групп...")
    
    total_saved = 0
    for group in groups:
        saved = update_schedule_for_group(group)
        total_saved += saved
    
    logger.info(f"Обновление расписания завершено. Сохранено {total_saved} пар")
    return total_saved