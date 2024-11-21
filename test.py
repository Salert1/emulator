import os
import tarfile
import tkinter as tk
from pathlib import PurePosixPath
from tkinter import scrolledtext
import argparse

class VirtualShell:
    def __init__(self, tar_path, output_box=None, username="user"):
        self.tar_path = tar_path
        self.output_box = output_box
        self.username = username
        self.filesystem = {}
        self.current_dir = "/"
        self.load_filesystem()

    def load_filesystem(self):
        with tarfile.open(self.tar_path, "r") as tar:
            for member in tar.getmembers():
                self.add_to_filesystem(member.name, member.isdir())

    def add_to_filesystem(self, path, is_dir):
        parts = path.strip("/").split("/")
        current = self.filesystem

        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        if is_dir:
            current[parts[-1]] = {}
        else:
            current[parts[-1]] = None

    def print_output(self, text):
        if self.output_box:
            self.output_box.config(state='normal')
            self.output_box.insert(tk.END, text + "\n")
            self.output_box.config(state='disabled')
            self.output_box.see(tk.END)
        else:
            print(text)

    def prompt(self):
        return f"{self.username}@virtual-shell:~$ "

    def ls(self):
        parts = self.current_dir.strip("/").split("/") if self.current_dir != "/" else []
        current = self.filesystem
        for part in parts:
            if part in current:
                current = current[part]
            else:
                self.print_output("Ошибка: каталог не найден.")
                return

        if isinstance(current, dict):
            contents = sorted(current.keys())
            self.print_output("\n".join(contents) if contents else "Каталог пуст.")
        else:
            self.print_output("Это не каталог.")

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
                current = current[part]
            else:
                self.print_output(f"cd: {path}: Нет такого каталога")
                return

        self.current_dir = "/" + "/".join(parts)
        self.print_output(f"Перешли в каталог: {self.current_dir}")

    def mkdir(self, directory):
        parts = self.current_dir.strip("/").split("/") if self.current_dir != "/" else []
        current = self.filesystem
        for part in parts:
            current = current.get(part, {})

        if directory in current:
            self.print_output(f"mkdir: каталог {directory} уже существует")
        else:
            current[directory] = {}
            self.print_output(f"mkdir: каталог {directory} создан")

    def execute_command(self, command):
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
        elif cmd == "exit":
            self.cleanup()
            exit()
        else:
            self.print_output(f"{cmd}: команда не найдена")

    def cleanup(self):
        pass


# Интерфейс на tkinter
class ShellApp:
    def __init__(self, tar_path, username, script_path=None):
        self.root = tk.Tk()
        self.root.title("Virtual Shell Emulator")

        self.output_box = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, state='disabled', width=80, height=20)
        self.output_box.pack(padx=10, pady=10)

        self.command_entry = tk.Entry(self.root, width=80)
        self.command_entry.pack(padx=10, pady=5)
        self.command_entry.bind("<Return>", self.process_command)

        self.shell = VirtualShell(tar_path, self.output_box, username)
        self.shell.print_output(
            "Добро пожаловать в эмулятор Virtual Shell!\nВведите команду (например, ls, cd, mkdir). Для выхода введите exit."
        )

        if script_path and os.path.exists(script_path):
            with open(script_path, "r") as script:
                for line in script:
                    self.shell.execute_command(line.strip())

    def process_command(self, event):
        command = self.command_entry.get()
        self.output_box.config(state='normal')
        self.output_box.insert(tk.END, f"{self.shell.prompt()}{command}\n")
        self.output_box.config(state='disabled')
        self.command_entry.delete(0, tk.END)
        self.shell.execute_command(command)

    def run(self):
        self.root.mainloop()


def run_tests():
    print("Running tests...")
    output = []
    shell = VirtualShell("test_fs.tar", output_box=None, username="tester")
    shell.print_output = lambda message: output.append(message)

    # Создаем тестовую файловую систему
    with tarfile.open("test_fs.tar", "w") as tar:
        for name in ["fs/demo1", "fs/demo2", "fs/inner/subfile"]:
            tarinfo = tarfile.TarInfo(name)
            tarinfo.type = tarfile.DIRTYPE if name.endswith('/') else tarfile.REGTYPE
            tar.addfile(tarinfo)

    shell.execute_command('cd fs')
    shell.execute_command('ls')
    assert output == [
        'Перешли в каталог: /fs',
        'demo1\ndemo2\ninner',
    ]

    print("Test 1 passed")

    output.clear()
    shell.execute_command('mkdir new_folder')
    shell.execute_command('ls')
    assert output == [
        'mkdir: каталог new_folder создан',
        'demo1\ndemo2\ninner\nnew_folder',
    ]

    print("Test 2 passed")

    output.clear()
    shell.execute_command('cd non_existing_dir')
    assert output == ["cd: non_existing_dir: Нет такого каталога"]

    print("Test 3 passed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Эмулятор Virtual Shell с виртуальной файловой системой")
    parser.add_argument("--username", required=True, help="Имя пользователя для отображения в приглашении")
    parser.add_argument("--tar_path", required=True, help="Путь к tar-архиву виртуальной файловой системы")
    parser.add_argument("--script_path", required=False, help="Путь к стартовому скрипту для выполнения")
    args = parser.parse_args()
    app = ShellApp(args.tar_path, args.username, args.script_path)
    app.run()
