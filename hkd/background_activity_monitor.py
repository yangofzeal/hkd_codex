"""Publish task activity from an explicitly registered local worker, not chat timing.

>>> active('building_and_validating', True)
True
>>> active('failed', True)
False
>>> active('building_and_validating', False)
False
"""
from pathlib import Path
import argparse,json,os,subprocess,tempfile,time,fcntl

def active(stage, matching_worker):
 return stage in {'building_and_validating','waiting_for_existing_build'} and matching_worker

def publish(state_path,destination):
 try:s=json.loads(state_path.read_text())
 except (OSError,ValueError):s={}
 pid=s.get('pid');matched=False
 if isinstance(pid,int) and pid>1:
  r=subprocess.run(['ps','-p',str(pid),'-o','command='],capture_output=True,text=True,timeout=5)
  matched=r.returncode==0 and 'install_when_ready.py' in r.stdout
 state='running' if active(s.get('stage'),matched) else 'idle'
 text=f'v1\n{state}\n{int(time.time())}\nCompile and verify new Codex\n'
 destination.parent.mkdir(parents=True,exist_ok=True)
 fd,name=tempfile.mkstemp(dir=destination.parent,prefix='.activity-')
 with os.fdopen(fd,'w') as f:f.write(text);f.flush();os.fsync(f.fileno())
 os.replace(name,destination)

def main():
 p=argparse.ArgumentParser();p.add_argument('--state',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--once',action='store_true');a=p.parse_args()
 a.output.parent.mkdir(parents=True,exist_ok=True)
 with a.output.with_suffix('.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  while True:
   publish(a.state,a.output)
   if a.once:return
   time.sleep(10)
if __name__=='__main__':main()
