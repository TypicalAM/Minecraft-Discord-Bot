import os
from dotenv import load_dotenv
import subprocess

load_dotenv()
cwd = os.getenv('JAVA_WD')
java = '/usr/bin/java -Xmx5G -Xms5G -jar server.jar nogui'
cmd = "tmux new-session -d -s 'java_server' "+java
print('opening')
try:
    out = subprocess.check_output(cmd.split(),cwd=cwd)
except subprocess.CalledProcessError:
    print('Already called')
else:
    print('opened')
    print(out)
#subprocess.Popen(cmd, shell=True,cwd=cwd)
