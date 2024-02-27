import sys
import os
import requests
import zipfile
import shutil
import subprocess

def download_and_extract(url):
    # Получаем содержимое архива по ссылке
    response = requests.get(url)
    if response.status_code == 200:
        # Создаем временный файл для записи архива
        with open('update.zip', 'wb') as f:
            f.write(response.content)
        # Распаковываем архив
        with zipfile.ZipFile('update.zip', 'r') as zip_ref:
            zip_ref.extractall('.')
        # Получаем имя директории, куда было распаковано содержимое архива
        extracted_folder_name = zip_ref.namelist()[0].split('/')[0]
        # Перемещаем содержимое распакованной папки в корневую директорию
        for item in os.listdir(extracted_folder_name):
            s = os.path.join(extracted_folder_name, item)
            d = os.path.join('.', item)
            if os.path.isdir(s):
                shutil.move(s, d)
            else:
                shutil.copy2(s, d)
        # Удаляем временный файл архива
        os.remove('update.zip')
        print("Обновление завершено.")
    else:
        print("Ошибка при загрузке архива.")

def main():
    # Получаем аргументы командной строки
    if len(sys.argv) != 2:
        print("Использование: python ipsbupdate.py <текст>")
        return
    text = sys.argv[1]
    # Формируем URL для загрузки архива
    url = "https://github.com/" + text + "/archive/main.zip"
    # Скачиваем и распаковываем архив
    download_and_extract(url)
    # Перезапускаем main.py
    subprocess.Popen(['python', 'main.py'])

if __name__ == "__main__":
    main()
