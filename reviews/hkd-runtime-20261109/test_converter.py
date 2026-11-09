import sys,unittest,tempfile,random,doctest,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
import pft_transform as t,hkd_pft_runtime as r
class Converter(unittest.TestCase):
 def converted(self,source,memoize=()):
  with tempfile.TemporaryDirectory() as d:
   a=Path(d)/'a.py';b=Path(d)/'b.py';a.write_text(source);report=t.convert(a,b,memoize);ns={};exec(compile(b.read_text(),str(b),'exec'),ns);self.assertEqual(a.read_text(),source);return ns,report
 def test_range_parity(self):
  ns,report=self.converted('def f(a,b,c):\n return sum(range(a,b,c))\n');self.assertEqual(len(report['rewrites']),1)
  rng=random.Random(19)
  for _ in range(2000):
   a,b=rng.randrange(-100,100),rng.randrange(-100,100);c=rng.choice([-9,-2,-1,1,2,9]);self.assertEqual(ns['f'](a,b,c),sum(range(a,b,c)))
 def test_runtime_shadowing_and_alias(self):
  ns,_=self.converted('def f(n, _hkd_pft_sum_range=None):\n return sum(range(n))\n');self.assertEqual(ns['f'](4),6)
  ns,_=self.converted('sum=lambda x:list(x)\ndef f(n):\n return sum(range(n))\n');self.assertEqual(ns['f'](3),[0,1,2])
 def test_future_and_docstring(self):
  ns,_=self.converted('"""fixture"""\nfrom __future__ import annotations\ndef f(n:int):\n return sum(range(n))\n');self.assertEqual(ns['__doc__'],'fixture');self.assertEqual(ns['f'](10),45)
 def test_no_input_execution(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'in.py';p.write_text('raise RuntimeError("must not execute")');t.convert(p,Path(d)/'out.py')
 def test_mutable_default_and_effects_rejected(self):
  _,rep=self.converted('def f(a=[]):\n return a == []\ndef g(a):\n print(a)\n return a\n',('f','g'));self.assertEqual(rep['memoized_functions'],[]);self.assertEqual(len(rep['skipped']),2)
 def test_cache_bound_and_type_identity(self):
  ns,_=self.converted('def f(a):\n return a\n',('f',));f=ns['f'];self.assertIs(type(f(True)),bool);self.assertIs(type(f(1)),int)
  for n in range(300):self.assertEqual(f(n),n)
  self.assertLessEqual(f.pft_cache_info()['size'],256);before=f.pft_cache_info()['hits'];f(299);self.assertEqual(f.pft_cache_info()['hits'],before+1)
 def test_overwrite_prohibited(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'a.py';p.write_text('x=1')
   with self.assertRaises(ValueError):t.convert(p,p)
   q=Path(d)/'b.py';q.write_text('old')
   with self.assertRaises(FileExistsError):t.convert(p,q)
 def test_user_index_runs_once(self):
  class Index:
   def __init__(self):self.calls=0
   def __index__(self):self.calls+=1;return 8
  x=Index();self.assertEqual(r.exact_range_sum(sum,range,x),28);self.assertEqual(x.calls,1)
if __name__=='__main__':unittest.main()
