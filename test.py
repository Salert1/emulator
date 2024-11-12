import os
import tarfile
import tkinter as tk
from pathlib import PurePosixPath
from tkinter import scrolledtext


class VirtualShell:
    def __init__(self, tar_path, output_box):
        self.tar_path = tar_path
        self.output_box = output_box
        self.filesystem = {}  # Словарь для хранения структуры файловой системы
        self.current_dir = "/"  # Начальный текущий каталог
        self.load_filesystem()  # Загружаем файловую систему из архива

    def load_filesystem(self):
        # Открываем tar-архив и строим структуру файловой системы
        with tarfile.open(self.tar_path, "r") as tar:
            for member in tar.getmembers():
                # Создаем структуру директорий и файлов
                self.add_to_filesystem(member.name, member.isdir())

    def add_to_filesystem(self, path, is_dir):
        # Разделение пути на части
        parts = path.strip("/").split("/")
        current = self.filesystem

        for part in parts[:-1]:  # Проходим по всем частям пути, кроме последней
            if part not in current:
                current[part] = {}  # Создаем каталог
            current = current[part]  # Переходим в подкаталог

        # Добавляем последний элемент пути как папку или файл
        if is_dir:
            current[parts[-1]] = {}
        else:
            current[parts[-1]] = None  # Файлы обозначены как None

    def print_output(self, text):
        # Вывод текста в поле вывода GUI
        self.output_box.config(state='normal')
        self.output_box.insert(tk.END, text + "\n")
        self.output_box.config(state='disabled')
        self.output_box.see(tk.END)

    def ls(self):
        parts = self.current_dir.strip("/").split("/") if self.current_dir != "/" else []
        current = self.filesystem
        for part in parts:
            if part in current:
                current = current[part]
            else:
                self.print_output("Ошибка: каталог не найден.")
                return

        # Получаем список содержимого текущего каталога
        if isinstance(current, dict):
            contents = sorted(current.keys())
            self.print_output("\n".join(contents) if contents else "Каталог пуст.")
        else:
            self.print_output("Это не каталог.")

    from pathlib import PurePosixPath

    def cd(self, path):
        if path == "/":
            self.current_dir = "/"
            self.print_output(f"Перешли в каталог: {self.current_dir}")
            return
        target_path = PurePosixPath(self.current_dir) / path
        normalized_path = str(target_path)
        parts = normalized_path.strip("/").split("/") if normalized_path != "/" else []
        parts = parts[0:]
        current = self.filesystem
        for part in parts:
            if part in current and isinstance(current[part], dict):
                current = current[part]  # Переходим в подкаталог
            else:
                self.print_output(f"cd: {path}: Нет такого каталога")
                return

        # Если путь корректен, обновляем текущий каталог
        self.current_dir = "/" + "/".join(parts)
        self.print_output(f"Перешли в каталог: {self.current_dir}")

    def mkdir(self, directory):
        # Эмуляция создания новой папки в текущем каталоге
        parts = self.current_dir.strip("/").split("/") if self.current_dir != "/" else []
        current = self.filesystem
        for part in parts:
            current = current.get(part, {})

        if directory in current:
            self.print_output(f"mkdir: каталог {directory} уже существует")
        else:
            current[directory] = {}
            self.print_output(f"mkdir: каталог {directory} создан")

    def chmod(self, mode, filename):
        # Псевдо-выполнение команды chmod
        parts = self.current_dir.strip("/").split("/") if self.current_dir != "/" else []
        current = self.filesystem

        # Идем по пути к текущей папке
        for part in parts:
            current = current.get(part, {})

        if filename in current:
            self.print_output(f"chmod: права доступа для '{filename}' изменены на {mode}")
        else:
            self.print_output(f"chmod: невозможно изменить права '{filename}': файл или каталог не найден")

    def chown(self, user, group, filename):
        # Псевдо-выполнение команды chown
        parts = self.current_dir.strip("/").split("/") if self.current_dir != "/" else []
        current = self.filesystem

        # Идем по пути к текущей папке
        for part in parts:
            current = current.get(part, {})

        if filename in current:
            self.print_output(f"chown: владелец файла '{filename}' изменен на {user}:{group}")
        else:
            self.print_output(f"chown: невозможно изменить владельца '{filename}': файл или каталог не найден")

    def execute_command(self, command):
        # Обработка и выполнение команды
        parts = command.strip().split()

        if not parts:
            return

        cmd, *args = parts

        if cmd == "ls":
            self.ls()
        elif cmd == "cd":
            self.cd(args[0] if args else "/")
        elif cmd == "mkdir":
            self.mkdir(args[0] if args else "")
        elif cmd == "chmod":
            if len(args) >= 2:
                self.chmod(args[0], args[1])
            else:
                self.print_output("chmod: недостаточно аргументов")
        elif cmd == "chown":
            if len(args) >= 3:
                self.chown(args[0], args[1], args[2])
            else:
                self.print_output("chown: недостаточно аргументов")
        elif cmd == "exit":
            self.cleanup()
            exit()
        else:
            self.print_output(f"{cmd}: команда не найдена")

    def cleanup(self):
        # Очистка ресурсов, если нужно (в данном случае нет физического удаления файлов)
        pass


# Интерфейс на tkinter
class ShellApp:
    def __init__(self, tar_path):
        self.root = tk.Tk()
        self.root.title("Virtual Shell Emulator")

        # Поле вывода результата
        self.output_box = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, state='disabled', width=80, height=20)
        self.output_box.pack(padx=10, pady=10)

        # Поле ввода команды
        self.command_entry = tk.Entry(self.root, width=80)
        self.command_entry.pack(padx=10, pady=5)
        self.command_entry.bind("<Return>", self.process_command)

        # Создаем виртуальную оболочку
        self.shell = VirtualShell(tar_path, self.output_box)
        self.shell.print_output(
            "Добро пожаловать в эмулятор Virtual Shell!\nВведите команду (например, ls, cd, mkdir, chmod, chown). Для выхода введите exit.")

    def process_command(self, event):
        # Получение команды из поля ввода и выполнение её
        command = self.command_entry.get()
        self.output_box.config(state='normal')
        self.output_box.insert(tk.END, f"virtual-shell:~$ {command}\n")
        self.output_box.config(state='disabled')
        self.command_entry.delete(0, tk.END)
        self.shell.execute_command(command)

    def run(self):
        # Запуск окна
        self.root.mainloop()


# Основной запуск приложения с постоянным путём к tar-файлу
if __name__ == "__main__":
    tar_path = "Open_world.tar"  # Укажите путь к tar-архиву виртуальной файловой системы
    app = ShellApp(tar_path)
    app.run()
