const вверх = document.getElementById('вверх');
const доляПрокрутки = document.getElementById('доля прокрутки');

document.addEventListener('scroll', () => {
    const высотаДокумента = document.documentElement.scrollHeight;
    const высотаОбласти = window.visualViewport ? window.visualViewport.height : window.innerHeight;
    const вертикальноеСмещение = window.scrollY;
    const коэффициентПрокрутки = вертикальноеСмещение / (высотаДокумента - высотаОбласти);
    
    if (вертикальноеСмещение > 100) {
        вверх.style.bottom = '20px';
    } else {
        вверх.style.bottom = '-80px';
    }
    
    if (доляПрокрутки) {
        доляПрокрутки.style.strokeDashoffset = (1 - коэффициентПрокрутки) * 100.531;
    }
});

вверх.addEventListener('click', () => {
    document.body.scrollIntoView({behavior: 'smooth'});
});

window.кликПара = function(event, выключение) {
    const элемент = event.target;
    const всплывашка = элемент.childNodes[1];
    if (!всплывашка) return;
    
    if (выключение) {
        всплывашка.classList.remove('показать');
    } else {
        всплывашка.classList.add('показать');
        setTimeout(() => {
            кликПара(event, true);
        }, 5000);
    }
};