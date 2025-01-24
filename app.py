from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
import os
from seg import *
from database import *
from path_extractor import collect_paths

UPLOAD_FOLDER = 'uploads'  # Папка буфера для хранения загруженных с клиентской стороны сег-файлов
ALLOWED_EXTENSIONS = {'seg_B1', 'seg_Y1', 'seg_G1'}  
DBname = "seg.db"  # Имя для создаваемой SQLite датабазы

# Ф-ция проверки загружаемых файлов на их разрешение
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS  # Возвращает значение, только если разрешение находится в списке

# Работа с сайтом
app = Flask(__name__)  # переменная-хранилище для фласка
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER  # Конфиг с информацией о папке-буфере

# Главная страница
@app.route('/')  # Путь к начальной странице
def index():
    _, filenames = collect_paths(UPLOAD_FOLDER)  # Подгрузка информации о буфере
    return render_template('index.html',filenames=filenames)  # Рендер html документа с информацией о буфере

# Подадрес, осуществляющий загрузку файлов
@app.route('/upload', methods=['GET', 'POST'])
def upload():  # Ф-ция загрузки файлов на сервер
    if request.method == 'POST':  # Если метод == ПОСТ
        if 'file' not in request.files:  # Проферка на наличие файла в request
            upload_message = "No file-part"  # Инициализация сообщения об ошибке
        file = request.files['file']
        if file.filename == '':  # Если получен пустой файл с пустым именем
            upload_message = 'File is not selected'  # Инициализация сообщения об ошибке
        if file and allowed_file(file.filename):  # Если есть непустой файл с одобренным разрешением, то...
            filename = secure_filename(file.filename)  # Прогон пути файла через ф-цию безопаности
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))  # Сохранение файла во внутренней папке-буфере сервера
            name = filename.rsplit('.', 1)[1]  # Отделение имени от пути
            upload_message = f'{name} uploaded successfully'  # Инициализация сообщения об успехе
        if file and not allowed_file(file.filename):  # Необходимо поймать исключение для неправильного типа файла
            upload_message = 'Wrong file-type'  # Инициализация сообщения об ошибке
        _, filenames = collect_paths(UPLOAD_FOLDER)  # Проверка состояния внутреннего буфера сервера
        return render_template('index.html', upload_message=upload_message, filenames=filenames)  # Рендер html, в который передается сообщение и состояние буфера

@app.route('/handle_actions', methods=['GET', 'POST'])  # Обработка кнопок управления буфером сервера
def handle_actions():  # Ф-ция обработки
    action = request.form.get('action')
    if action == 'erasefiles':  # Если нажата кнопка "удалить файлы"
        print('Action "erasefiles" happened')  # Печать лога в терминал о нажатой кнопке
        paths, _ = collect_paths(UPLOAD_FOLDER)  # Сбор путей к файлам в буфере сервера
        for path in paths:
            os.unlink(path)  # Удаление каждого из путей
        _, filenames = collect_paths(UPLOAD_FOLDER)  # Получение актуального состояния буфера сервера
        return render_template('index.html', filenames=filenames)  # Рендер html документа с актуальным состоянием буфера сервера
    elif action == 'erasedb':  # Если нажата кнопка "удалить ДБ"
        print('Action "erasedb" happened')  # Печать лога в терминал о нажатой кнопке
        _, filenames = collect_paths(UPLOAD_FOLDER)  # Получение актуального состояния буфера сервера
        if os.path.exists(DBname):  # Проверка наличия ДБ в папке проекта
            os.unlink(DBname)  # Удаление ДБ
            DBmessage=""  # Сообщение-заглушка
        else:
            DBmessage="DB does not exist"  # Сообщение об ошибке
        return render_template('index.html', filenames=filenames, DBmessage=DBmessage)
    elif action == 'add':  # Если нажата кнопка "добавить"
        print('Action "add" happened')  # Печать лога в терминал о нажатой кнопке

        # Обработка информации и добавление ее в таблицу
        paths, filenames = collect_paths(UPLOAD_FOLDER)  # Сбор путей и имен файлов
        if len(paths) < 3:
            DBmessage = "Not enough files"
            return render_template('index.html', filenames=filenames, DBmessage=DBmessage)
        elif len(paths) > 3:
            DBmessage = "Too many files"
            return render_template('index.html', filenames=filenames, DBmessage=DBmessage)
        else:
            create_table(DBname)  # Создание датабазы и таблицы для данных из seg файлов
            key_part1 = str(filenames[5] + filenames[6])  # Создание первой части уникального ключа для строки таблицы
                                                        # Данная часть соответсвует номеру seg файла
            for path in paths:  # Упаковка файлов в буфере сервера в соответств. переменные по их меткам
                if 'B1' in path:
                    B1 = path
                elif 'Y1' in path:
                    Y1 = path
                elif 'G1' in path:
                    G1 = path

            words = list()  # Инициализация переменной, которая будет хранить слова
            _, labels = read_seg(Y1, encoding="cp1251")  # Запись слов из seg_Y1
            for label in labels:
                if label['name'] != "":  # Если метка не пустая, то в ней содержится слово
                    words.append(label['name'])

            phonemes, phoneme_positions = match_words_to_sounds(Y1, B1)  # Сбор фонем и их позиций, объединенных в листы для каждого слова
            f0_times, f0_values = get_f0(G1, Y1)  # Сбор значений ЧОТ и их позиций, объединенных в лситы для каждого слова
            middle_points = words_middle(Y1)  # Сбор середин каждого слова

            key_part2 = 0  # Инициализация второй части ключа, который подразумевает индекс слова по seg_Y1
            for i in range(len(words)):  # Обработка каждого слова в списке слов
                key_part2 += 1  # первое слово -- ключ 1, второе слово -- ключ 2
                unique_key = str(key_part1) + str(key_part2)  # Соединение (но не сложение) двух половинок ключей
                one_word = words[i]  # Отбор i-го слова
                if len(one_word) < 3:  # Слишком короткие слова отбрасываем, нерелевантно
                    continue
                transcription = phonemes[i]  # Отбор набора фонем для i-го слова
                middle = middle_points[i]  # Отбор середины i-го слова
                f0_times_word = f0_times[i]  # Отбор отсчетов f0 i-го слова
                f0_values_word = f0_values[i]  # Отбор значений f0 i-го слова
                if len(f0_values_word) == 0:  # Если ни одно из значений не попало в рамки слова, ставим 0
                    f0_values_word.append(0)

                positions = phoneme_positions[i]  # Отбор позиций фонем в отсчетах для i-го слова
                for border_left, border_right, phoneme in zip(positions, positions[1:], transcription):  # Поиск срединной фонемы
                    if border_left <= middle >= border_right:  # Если середина слова попадает в окно фонемы
                        middle_phoneme = phoneme  # То это срединная фонема
                try:
                    if middle_phoneme == "":  # Ловится исключение, когда срединная фонема не может быть найдена
                        print("No phoneme")
                except:
                    middle_phoneme = transcription[0]  # Если срединная фонема не может быть найдена, ставим первую фонему
                
                # Поиск срединного значения f0
                minimum_length = 999  # Инициализация миним. дистанции между серединой слова и временной позицией метки f0 
                for time, value in zip(f0_times_word, f0_values_word):
                    distance = abs(middle - time)  # находим дистанцию между меткой середины слова и меткой f0
                    if distance < minimum_length:  # Если дистанция короче минимальной 
                        minimum_length = distance  # То это новая минимальная дистанция
                        middle_value = value  # У временной метки с минимальной дистанцией есть свое значение f0, записываем

                f0_start = f"{f0_values_word[0]}({transcription[0]})"  # Значение f0 в начале слова и аллофон, которому это значение принадлежит
                f0_middle = f"{middle_value}({middle_phoneme})"  # Значение f0 в середине слова и аллофон, которому это значение принадлежит
                f0_end = f"{f0_values_word[-1]}({transcription[-1]})"  # Значение f0 в конце слова и аллофон, которому это значение принадлежит
                transcription_in_text = ''.join(transcription)  # Конкатенация списка аллофонов в одну строку
                flag = add_info(DBname, unique_key, one_word, transcription_in_text, f0_start, f0_middle, f0_end)  # Добавление всех значений в датабазу
                if flag == True:  # Если от SQLite пришла ошибка
                    DBmessage = "These items are already in DB"  # То инициализация сообщения о том, что данные уже есть
                else:
                    DBmessage = "Items added successfully"  # Иначе, сообщение об успехе

            sentences = read_sqlite_table(DBname)  # Читаем всю датабазу по строчкам

            # Передваем html состояние буфера, строки датабазы и информацию об ошибках
            return render_template('index.html', filenames=filenames, sentences=sentences, DBmessage=DBmessage)

# Запуск веб-формы
if __name__ == '__main__':
    app.run(debug=True)