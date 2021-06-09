import subprocess

result = subprocess.run(
    ['echo', 'Hello from Child'],
    capture_output=True,
    encoding='utf-8')

result.check_returncode()
print(result.stdout)

proc = subprocess.Popen(['sleep', '0.1'])
while proc.poll() is None:
    print('working .....')
print('Exit statut', proc.poll())

# Decoupling child process from parent
import time

start = time.time()
sleep_procs = list()
for _ in range(100):
    proc = subprocess.Popen(['sleep', '1'])
    sleep_procs.append(proc)

for proc in sleep_procs:
    proc.communicate()

end = time.time()
delta = end - start
print(f'Finished in {delta:.3} seconds')

import os

def run_encrypt(data):
    env = os.environ.copy()
    env['password'] = 'toto'
    proc = subprocess.Popen(['openssl', 'enc', '-pbkdf2', '-pass', 'env:password'],
                            env = env,
                            stdin = subprocess.PIPE,
                            stdout = subprocess.PIPE)

    proc.stdin.write(data)
    proc.stdin.flush()
    return proc

procs = list()
for _ in range(3):
    data = os.urandom(10)
    proc = run_encrypt(data)
    procs.append(proc)

for proc in procs:
    out, _ = proc.communicate()
    print(out)

def run_hash(input_stdin):
    return subprocess.Popen(['openssl', 'dgst', '-whirlpool', '-binary'],
                            stdin=input_stdin,
                            stdout=subprocess.PIPE)

encrypt_procs = list()
hash_procs = list()
for _ in range(3):
    data = os.urandom(100)

    encrypt_proc = run_encrypt(data)
    encrypt_procs.append(encrypt_proc)

    hash_proc = run_hash(encrypt_proc.stdout)
    hash_procs.append(hash_proc)

    encrypt_proc.stdout.close()
    encrypt_proc.stdout = None

for proc in encrypt_procs:
    proc.communicate()
    assert proc.returncode == 0

for proc in hash_procs:
    out, _ = proc.communicate()
    print(out)
    assert proc.returncode == 0

proc = subprocess.Popen(['sleep', '1'])
try:
    proc.communicate(timeout=0.1)
except subprocess.TimeoutExpired:
    proc.terminate()
    proc.wait()

print('Wait status', proc.poll())
