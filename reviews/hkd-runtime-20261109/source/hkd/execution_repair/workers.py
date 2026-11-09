"""Event-driven, bounded, explicitly authorized local command workers.

A one-second watchdog recovers missed wakes. Restarts never replay running work.
>>> runnable({'state':'queued','authorized':True,'approval_required':False,'attempts':0,'retry_limit':0})
True
>>> runnable({'state':'paused','authorized':True,'approval_required':False,'attempts':0,'retry_limit':0})
False
"""
import collections
import codecs
import doctest
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import selectors
import signal
import sqlite3
import subprocess
import threading
import time


def runnable(j):
    return (j['state']=='queued' and j['authorized'] is True and not j['approval_required']
            and j['attempts'] <= j['retry_limit'])


def select_ready(jobs, ready, sling):
    # Dense/singleton work avoids callback overhead observed in matched benchmarks.
    if len(ready) * 2 >= len(jobs):
        return [key for key, job in jobs.items() if runnable(job)]
    return sling.HKD_ALU(len(jobs), list(ready), lambda key: key if runnable(jobs[key]) else None)


def load_sling():
    receipt=json.loads(Path(__file__).with_name('sling-source.json').read_text())
    path=Path(receipt['python_path'])
    if hashlib.sha256(path.read_bytes()).hexdigest()!=receipt['python_sha256']:
        raise RuntimeError('David\'s Sling source changed; review before dispatch')
    spec=importlib.util.spec_from_file_location('hkd_author_sling',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    if doctest.testmod(module, verbose=False).failed:raise RuntimeError('Sling doctest failed')
    return module


class Workers:
    def __init__(self,directory,capacity=2):
        self.directory=Path(directory);self.directory.mkdir(parents=True,exist_ok=True,mode=0o700)
        self.owner=(self.directory/'owner.lock').open('a')
        try:fcntl.flock(self.owner,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BaseException:self.owner.close();raise
        try:self.sling=load_sling()
        except BaseException:self.owner.close();raise
        if type(capacity)!=int or not 1<=capacity<=16:
            self.owner.close();raise ValueError('Capacity must be 1..16')
        self.capacity=capacity
        self.condition=threading.Condition(threading.RLock());self.stopping=False
        self.db=sqlite3.connect(self.directory/'workers.sqlite3',check_same_thread=False)
        self.db.execute('CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY, body TEXT NOT NULL)')
        self.jobs=collections.OrderedDict();self.ready=collections.OrderedDict();self.active={};self.threads=[]
        for key,body in self.db.execute('SELECT id,body FROM jobs ORDER BY rowid'):
            j=json.loads(body)
            if j['state'] in ('running','cancelling'):j['state']='interrupted'
            self.jobs[key]=j
            if runnable(j):self.ready[key]=None
        self._save()
        self.dispatcher=threading.Thread(target=self._dispatch,name='hkd-dispatch',daemon=True);self.dispatcher.start()
    def _save(self, keys=None):
        # Persist exactly the changed indexed jobs; startup/shutdown retain full flush.
        active = self.jobs if keys is None else dict.fromkeys(keys)
        rows = self.sling.HKD_ALU(len(self.jobs), active,
                                  lambda key: (key, json.dumps(self.jobs[key])))
        with self.db:
            self.db.executemany('INSERT OR REPLACE INTO jobs VALUES(?,?)', rows)
        self._publish()
    def _publish(self):
        rows=[{k:j[k] for k in ('id','state','attempts','exit_code','current','total')} for j in self.jobs.values()]
        temporary=self.directory/'status.tmp';temporary.write_text(json.dumps({'updated_at':time.time(),'jobs':rows}));temporary.replace(self.directory/'status.json')
    def submit(self,key,command,cwd,authorized=False,approval_required=True,retry_limit=0,timeout=60):
        if not isinstance(key,str) or not 1<=len(key)<=80:raise ValueError('Stable task ID required')
        if not isinstance(command,list) or not command or not all(isinstance(x,str) and '\0' not in x for x in command):raise ValueError('Command must be argv')
        if type(authorized)!=bool or type(approval_required)!=bool:raise ValueError('Explicit authorization flags required')
        if type(retry_limit)!=int or not 0<=retry_limit<=3:raise ValueError('Retry limit must be 0..3')
        if type(timeout) not in (int,float) or not 0<timeout<=3600:raise ValueError('Timeout must be 0..3600 seconds')
        cwd=str(Path(cwd).resolve(strict=True))
        identity=dict(command=command,cwd=cwd,authorized=authorized,approval_required=approval_required,retry_limit=retry_limit,timeout=timeout)
        with self.condition:
            if self.stopping:raise RuntimeError('Worker is stopping')
            if key in self.jobs:
                if self.jobs[key]['identity']!=identity:raise ValueError('Task ID already binds a different request')
                return self.status(key)
            if len(self.jobs)>=128:raise ValueError('128 task limit; use a new session')
            j=dict(id=key,identity=identity,**identity,state='queued',attempts=0,exit_code=None,current=None,total=None,output='',dropped_characters=0,created_at=time.time())
            if not authorized or approval_required:j['state']='approval_required'
            self.jobs[key]=j
            if runnable(j):self.ready[key]=None
            self._save([key]);self.condition.notify_all();return self.status(key)
    def status(self,key=None):
        with self.condition:
            if key is not None:return json.loads(json.dumps(self.jobs[key]))
            return [json.loads(json.dumps(j)) for j in self.jobs.values()]
    def control(self,key,action):
        with self.condition:
            j=self.jobs[key]
            if action=='pause':
                if j['state'] not in ('queued','paused'):raise ValueError('Pause applies to queued work; cancel a running task')
                j['state']='paused';self.ready.pop(key,None)
            elif action=='resume':
                if j['state']!='paused':raise ValueError('Only explicitly paused work can resume')
                j['state']='queued'
                if runnable(j):self.ready[key]=None
            elif action=='cancel':
                self.ready.pop(key,None)
                if j['state'] in ('running','cancelling'):
                    j['state']='cancelling';self.active[key]['reason']='cancelled';self._kill(self.active[key]['proc'],signal.SIGTERM)
                elif j['state'] not in ('completed','failed','cancelled','timed_out','interrupted'):j['state']='cancelled'
            else:raise ValueError('Unknown action; approvals cannot be granted by this tool')
            self._save([key]);self.condition.notify_all();return self.status(key)
    @staticmethod
    def _kill(proc,sig):
        try:os.killpg(proc.pid,sig)
        except ProcessLookupError:pass
    def _dispatch(self):
        while True:
            with self.condition:
                if self.stopping:return
                self._publish()
                # Author's sparse HKD_ALU visits only active queued IDs, preserving order.
                keys=select_ready(self.jobs,self.ready,self.sling)
                for key in keys:
                    if len(self.active)>=self.capacity:break
                    self.ready.pop(key,None)
                    if key is None:continue
                    j=self.jobs[key];j['state']='running';j['attempts']+=1;j['started_at']=time.time()
                    j.update(previous_exit_code=j['exit_code'],exit_code=None,current=None,total=None)
                    self._save([key]) # Persist claim BEFORE launching; crash => interrupted, never replay.
                    try:proc=subprocess.Popen(j['command'],cwd=j['cwd'],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,start_new_session=True,bufsize=0)
                    except OSError as error:
                        j.update(state='failed',error=str(error));self._save([key]);continue
                    self.active[key]={'proc':proc,'reason':None}
                    thread=threading.Thread(target=self._read,args=(key,proc),daemon=True)
                    self.threads=[t for t in self.threads if t.is_alive()];self.threads.append(thread);thread.start()
                self.condition.wait(timeout=1.0)
    def _read(self,key,proc):
        start=time.monotonic();terminated=None;pending=b''
        decoder=codecs.getincrementaldecoder('utf8')(errors='replace')
        selector=selectors.DefaultSelector();selector.register(proc.stdout,selectors.EVENT_READ)
        try:
            while selector.get_map() or proc.poll() is None:
                with self.condition:
                    j=self.jobs[key];record=self.active[key]
                    if not record['reason'] and time.monotonic()-start>=j['timeout']:record['reason']='timed_out'
                    if record['reason'] and terminated is None:
                        terminated=time.monotonic();self._kill(proc,signal.SIGTERM)
                    if terminated is not None and time.monotonic()-terminated>=.5:self._kill(proc,signal.SIGKILL)
                for stream,_ in selector.select(.05):
                    data=os.read(stream.fileobj.fileno(),8192)
                    if not data:selector.unregister(stream.fileobj);break
                    with self.condition:
                        j=self.jobs[key];text=j['output']+decoder.decode(data);j['dropped_characters']+=max(0,len(text)-65536);j['output']=text[-65536:]
                        pending=(pending+data)[-65536:]
                        while b'\n' in pending:
                            line,pending=pending.split(b'\n',1)
                            if line.startswith(b'@@progress '):
                                try:
                                    progress=json.loads(line[11:]);a,b=progress['current'],progress['total']
                                    if type(a)==int and type(b)==int and 0<=a<=b and b>0:j.update(current=a,total=b)
                                except (ValueError,KeyError,TypeError):pass
                        self._save([key]);self.condition.notify_all()
            tail=decoder.decode(b'',final=True)
            if tail:
                with self.condition:self.jobs[key]['output']=(self.jobs[key]['output']+tail)[-65536:]
            code=proc.wait()
            with self.condition:
                j=self.jobs[key];reason=self.active[key]['reason'];j.update(exit_code=code,finished_at=time.time(),state=reason or (('incomplete' if j['total'] is not None and j['current']<j['total'] else 'completed') if code==0 else 'failed'))
                if j['state']=='failed' and j['attempts']<=j['retry_limit'] and not self.stopping:
                    j['state']='queued';self.ready[key]=None
                del self.active[key];self._save([key]);self.condition.notify_all()
        except Exception as error:
            self._kill(proc,signal.SIGKILL);proc.wait()
            with self.condition:
                self.jobs[key].update(state='failed',error='Worker monitor failed: '+str(error),exit_code=proc.returncode)
                self.active.pop(key,None)
                try:self._save([key])
                except (OSError,sqlite3.Error):pass
                self.condition.notify_all()
        finally:selector.close();proc.stdout.close()
    def close(self):
        with self.condition:
            self.stopping=True
            for key in list(self.active):self.control(key,'cancel')
            self.condition.notify_all()
        self.dispatcher.join(timeout=3)
        for thread in self.threads:thread.join(timeout=5)
        with self.condition:self._save();self.db.close()
        self.owner.close()

if __name__=='__main__':raise SystemExit(doctest.testmod().failed)
