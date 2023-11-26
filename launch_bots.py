import subprocess
# import keyboard


INSTANCES: int = 5

processes: list[subprocess.Popen] = []
for _ in range(INSTANCES):
    process = subprocess.Popen("python ./bot.py", shell=True)
    processes.append(process)

# TODO: kill processes
# while True:
#     if keyboard.is_pressed("esc"):
#         for process in processes:
#             process.kill()
#         break
