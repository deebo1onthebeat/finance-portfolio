import matplotlib
# ВАЖНО: Эту строчку нужно писать ДО импорта pyplot
# Она говорит: "Рисуй без экрана"
matplotlib.use('Agg') 

import matplotlib.pyplot as plt
import io

def generate_pie_chart(data: dict) -> io.BytesIO:
    """
    Принимает словарь вида {'Еда': 500, 'Такси': 200}
    Возвращает байтовый буфер с картинкой.
    """
    # Если данных нет или они пустые, возвращаем пустой график или обрабатываем ошибку
    if not data:
        return None

    labels = list(data.keys())
    values = list(data.values())
    
    # Создаем график
    fig, ax = plt.subplots(figsize=(6, 6))
    
    # Рисуем круговую диаграмму
    ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=140)
    
    # Заголовок
    ax.set_title("Расходы по категориям")
    
    # Сохраняем в буфер
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    
    # Очищаем память (обязательно!)
    plt.close(fig)
    
    return buf