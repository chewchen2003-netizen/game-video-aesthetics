"""Read-only, localhost-only live dashboard for the detached composition batch."""
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import argparse,json,time,os,re
ROOT=Path(__file__).resolve().parents[1]
def snapshot(run):
 d=json.loads((run/'progress.json').read_text());process=json.loads((run/'process.json').read_text());now=time.time();d['read_epoch']=now;d['wall_elapsed_seconds']=(d.get('stopped_epoch') or now)-process['start_epoch']
 try:os.kill(process['pid'],0);d['process_alive']=True
 except OSError:d['process_alive']=False
 d.pop('grades',None)
 for sid,v in d['cases'].items():
  if v['state']!='complete':v.pop('grade',None)
  if d.get('comparison') and re.match(r'^R\d+$',sid):
   for arm in ['baseline','candidate']:
    w=run/'model-calls'/sid/arm
    if (w/'validation.json').exists():
     overall=json.loads((w/'result.json').read_text())['overall'];v[arm+'_grade']=overall['grade'];v[arm+'_status']=overall['status']
   if all((run/'model-calls'/sid/arm/'validation.json').exists() for arm in ['baseline','candidate']):
    v.update(state='complete',grade=v.get('candidate_grade'),status=v.get('candidate_status'));v.pop('error',None)
  if v['state']=='measure':
   logs=sorted((run/'logs').glob(f'{sid}-measure-*.log'))
   if logs:
    lines=logs[-1].read_text(errors='replace').splitlines();line=next((x for x in reversed(lines) if re.match(r'^R\d+ \d+ objects',x)),None)
    if line:
     match=re.search(r'sampled_count (\d+) total (\d+)',line)
     v['detail']=f'已测量 {match[1]} / {match[2]} 个采样时刻' if match else f'测量到原网格第{line.split()[1]}帧'
    else:v['detail']='正在加载模型或处理首批帧'
  elif v['state'] in ['identify','judge'] and not d.get('comparison'):
   folder=run/'model-calls'/sid/v['state'];out=folder/'result.json'
   v['detail']='模型正在生成结构化结果' if out.exists() and not out.stat().st_size else '等待结果校验' if out.exists() else '准备模型请求'
 if d.get('comparison'):
  entries=[v for k,v in d['cases'].items() if re.match(r'^R\d+$',k)];d['completed']=sum(v['state']=='complete' for v in entries);d['failed']=sum(v['state']=='failed' for v in entries)
 return d
class Handler(BaseHTTPRequestHandler):
 def do_GET(self):
  try:
   path=self.path.split('?')[0]
   if path=='/api/progress':data=json.dumps(snapshot(self.server.run_dir),ensure_ascii=False).encode();mime='application/json; charset=utf-8'
   elif path=='/comparison':
    from render_five_comparison import render
    data=render(self.server.run_dir if (self.server.run_dir/'design.json').exists() else ROOT/'runs/composition-five-calibration').encode();mime='text/html; charset=utf-8'
   elif path in ['/','/index.html']:data=(ROOT/'tools/batch-progress/index.html').read_bytes();mime='text/html; charset=utf-8'
   else:self.send_error(404);return
   self.send_response(200);self.send_header('Content-Type',mime);self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
  except Exception:self.send_error(503,'Progress is temporarily unavailable')
 def log_message(self,*args):pass
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--run-dir',type=Path,required=True);p.add_argument('--port',type=int,default=8771);a=p.parse_args();server=ThreadingHTTPServer(('127.0.0.1',a.port),Handler);server.run_dir=a.run_dir.resolve();server.serve_forever()
