#!/usr/bin/env python3
"""Bounded transitions/async handler; the 1 ms value is a measured local target.

A local queue acknowledgment is not a generated model reply or durable receipt.
The handler retains exact indexed state; no history thinning is performed.

>>> within_target(0)
True
>>> within_target(999999)
True
>>> within_target(1000000)
True
>>> within_target(1000001)
False
>>> within_target(-1)
Traceback (most recent call last):
...
ValueError: elapsed_ns must be a nonnegative integer
>>> index = ProgressIndex()
>>> index.update('a', False)
(0, 1)
>>> index.update('a', True)
(1, 1)
>>> index.update('a', True)
(1, 1)
>>> index.update('b', False)
(1, 2)
"""
import argparse,asyncio,hashlib,json,time
from transitions import Machine
TARGET_NS=1_000_000

def within_target(elapsed_ns):
    if type(elapsed_ns) is not int or elapsed_ns<0:raise ValueError('elapsed_ns must be a nonnegative integer')
    return elapsed_ns<=TARGET_NS

class ProgressIndex:
    def __init__(self):self.steps={};self.done=0
    def update(self,key,done):
        if type(key) is not str or not key or type(done) is not bool:raise ValueError('Invalid step')
        old=self.steps.get(key,False);self.steps[key]=done;self.done+=int(done)-int(old)
        return self.done,len(self.steps)
    def snapshot(self):return self.done,len(self.steps)

class Cursor:
    def __init__(self):self.state='received'

class Collector:
    """Single-event-loop owner. Full queues reject admission; no silent drops."""
    def __init__(self,capacity=256,max_history=10000):
        if type(capacity) is not int or capacity<1 or type(max_history) is not int or max_history<capacity:raise ValueError('Invalid capacity')
        self.queue=asyncio.Queue(maxsize=capacity);self.jobs={};self.max_history=max_history;self.progress=ProgressIndex()
        self.machine=Machine(model=None,states=['received','accepted','running','completed','failed','interrupted'],initial='received',auto_transitions=False,transitions=[{'trigger':'accept','source':'received','dest':'accepted'},{'trigger':'start','source':'accepted','dest':'running'},{'trigger':'finish','source':'running','dest':'completed'},{'trigger':'fail','source':['accepted','running'],'dest':'failed'},{'trigger':'interrupt','source':['accepted','running'],'dest':'interrupted'}])
    def event(self,cursor,name):self.machine.events[name].trigger(cursor)
    def accept(self,key,payload):
        started=time.perf_counter_ns()
        if type(key) is not str or not 1<=len(key)<=128 or type(payload) is not str or len(payload.encode())>32768:raise ValueError('Invalid request')
        digest=hashlib.sha256(payload.encode()).hexdigest()
        if key in self.jobs:
            if self.jobs[key]['digest']!=digest:raise ValueError('Conflicting request identity')
            return dict(self.jobs[key]['ack'],reused=True)
        if len(self.jobs)>=self.max_history:raise OverflowError('History capacity reached; archive explicitly')
        if self.queue.full():raise asyncio.QueueFull
        cursor=Cursor();self.event(cursor,'accept');self.progress.update(key,False)
        self.jobs[key]={'cursor':cursor,'digest':digest,'result':None};self.queue.put_nowait((key,payload))
        elapsed=time.perf_counter_ns()-started;ack={'id':key,'state':'accepted','elapsed_ns':elapsed,'within_1ms_target':within_target(elapsed),'durable':False,'model_reply':False,'reused':False};self.jobs[key]['ack']=ack;return dict(ack)
    async def collect_one(self,handler,sink):
        key,payload=await self.queue.get();job=self.jobs[key];cursor=job['cursor']
        try:
            self.event(cursor,'start');await sink({'id':key,'state':'running'})
            result=await handler(payload);await sink({'id':key,'state':'completed','result':result})
            job['result']=result;self.event(cursor,'finish');self.progress.update(key,True);return result
        except asyncio.CancelledError:
            self.event(cursor,'interrupt');raise
        except Exception:
            self.event(cursor,'fail');raise
        finally:self.queue.task_done()

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--self-test',action='store_true');parser.add_argument('--legacy',action='store_true',help='Explicitly delegate remaining arguments to the unchanged legacy handler');args,rest=parser.parse_known_args()
    if args.legacy:
        import hkd_handler,sys
        sys.argv=[sys.argv[0]]+rest;return hkd_handler.main()
    if rest:parser.error('Legacy flags require --legacy')
    if args.self_test:
        import doctest
        r=doctest.testmod();print(json.dumps({'attempted':r.attempted,'failed':r.failed,'target_ns':TARGET_NS,'universal_latency_guarantee':False}));return bool(r.failed)
    parser.print_help();return 0

if __name__=='__main__':raise SystemExit(main())
