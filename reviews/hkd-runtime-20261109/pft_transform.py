"""Conservative AST specializer. Input scripts are parsed, never executed."""
import ast,hashlib,json
from pathlib import Path

class Rewrite(ast.NodeTransformer):
    def __init__(self,alias):self.alias=alias;self.changes=[]
    def visit_Call(self,node):
        self.generic_visit(node)
        if isinstance(node.func,ast.Name) and node.func.id=='sum' and len(node.args)==1 and not node.keywords:
            r=node.args[0]
            if isinstance(r,ast.Call) and isinstance(r.func,ast.Name) and r.func.id=='range' and not r.keywords and 1<=len(r.args)<=3 and not any(isinstance(a,ast.Starred) for a in r.args):
                self.changes.append({'line':node.lineno,'rewrite':'exact arithmetic range sum','complexity':'constant arithmetic operations; integer bit cost remains'})
                return ast.copy_location(ast.Call(func=ast.Name(id=self.alias,ctx=ast.Load()),args=[ast.Name(id='sum',ctx=ast.Load()),ast.Name(id='range',ctx=ast.Load()),*r.args],keywords=[]),node)
        return node

def pure(fn):
    if fn.decorator_list or fn.args.vararg or fn.args.kwarg or len(fn.body)!=1 or not isinstance(fn.body[0],ast.Return):return False
    if any(not isinstance(n,ast.Constant) or type(n.value) not in (int,bool,str,bytes,type(None)) for n in fn.args.defaults+[d for d in fn.args.kw_defaults if d is not None]):return False
    args={a.arg for a in fn.args.posonlyargs+fn.args.args+fn.args.kwonlyargs}
    allowed=(ast.Return,ast.Constant,ast.Name,ast.Load,ast.BinOp,ast.UnaryOp,ast.BoolOp,ast.Compare,ast.IfExp,ast.Tuple,ast.operator,ast.unaryop,ast.boolop,ast.cmpop)
    return all(isinstance(n,allowed) and (not isinstance(n,ast.Name) or n.id in args) for n in ast.walk(fn.body[0]))

def convert(source,output,memoize=(),maxsize=256):
    source,output=Path(source),Path(output)
    if type(maxsize) is not int or not 1<=maxsize<=4096:raise ValueError('cache capacity must be 1..4096')
    if source.resolve()==output.resolve():raise ValueError('Output must differ from input')
    if output.exists():raise FileExistsError(output)
    text=source.read_text();tree=ast.parse(text,filename=str(source));names={n.id for n in ast.walk(tree) if isinstance(n,ast.Name)} | {n.arg for n in ast.walk(tree) if isinstance(n,ast.arg)} | {n.name for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.ClassDef,ast.AsyncFunctionDef))} | {n.asname or n.name.split('.')[0] for n in ast.walk(tree) if isinstance(n,ast.alias)}
    alias='_hkd_pft_sum_range';cache_alias='_hkd_pft_memoize'
    while alias in names:alias+='_'
    while cache_alias in names:cache_alias+='_'
    selected=set(memoize);cached=[];skipped=[]
    for node in tree.body:
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name in selected:
            selected.remove(node.name)
            if isinstance(node,ast.FunctionDef) and pure(node):
                node.decorator_list.append(ast.Call(func=ast.Name(id=cache_alias,ctx=ast.Load()),args=[],keywords=[ast.keyword(arg='maxsize',value=ast.Constant(maxsize))]));cached.append(node.name)
            else:skipped.append({'function':node.name,'reason':'Not a supported pure single-expression function'})
    skipped.extend({'function':n,'reason':'No top-level function found'} for n in sorted(selected))
    rewrite=Rewrite(alias);tree=rewrite.visit(tree)
    imports=[]
    if rewrite.changes:imports.append(ast.alias(name='exact_range_sum',asname=alias))
    if cached:imports.append(ast.alias(name='memoize_exact',asname=cache_alias))
    if imports:
        pos=0
        while pos<len(tree.body) and ((isinstance(tree.body[pos],ast.Expr) and isinstance(tree.body[pos].value,ast.Constant) and isinstance(tree.body[pos].value.value,str)) or (isinstance(tree.body[pos],ast.ImportFrom) and tree.body[pos].module=='__future__')):pos+=1
        tree.body.insert(pos,ast.ImportFrom(module='hkd_pft_runtime',names=imports,level=0))
    ast.fix_missing_locations(tree);body=ast.unparse(tree)+'\n';compile(body,str(output),'exec')
    output.parent.mkdir(parents=True,exist_ok=True)
    runtime=Path(__file__).with_name('hkd_pft_runtime.py');dest=output.with_name(runtime.name)
    if imports and dest.resolve()!=runtime.resolve():
        if dest.exists() and dest.read_bytes()!=runtime.read_bytes():raise FileExistsError('Different runtime already exists: '+str(dest))
        if not dest.exists():dest.write_bytes(runtime.read_bytes())
    output.write_text(body)
    output.chmod(source.stat().st_mode & 0o777)
    report={'input':str(source),'output':str(output),'input_sha256':hashlib.sha256(text.encode()).hexdigest(),'output_sha256':hashlib.sha256(body.encode()).hexdigest(),'rewrites':rewrite.changes,'memoized_functions':cached,'skipped':skipped,'executed_input':False,'cache_limit':maxsize,'claims':{'arbitrary_polynomial_conversion':False,'inverse_end_to_end_latency_guaranteed':False,'p_equals_np':False},'scope':'Exact supported specializations and bounded exact-key reuse; no arbitrary-code theorem. Source formatting is regenerated.'}
    output.with_suffix(output.suffix+'.pft.json').write_text(json.dumps(report,indent=2)+'\n');return report
