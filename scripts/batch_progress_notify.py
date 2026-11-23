"""Use the configured Codex app MCP transport to deliver user-authorized milestones.
Never log transport credentials. This is event-driven, not a scheduled automation.
"""
import json,os,queue,subprocess,threading,time
from pathlib import Path
CLI=os.environ.get('CODEX_BIN','/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex')
def app_client(callback):
 config=json.loads(subprocess.check_output([CLI,'mcp','list','--json'],stderr=subprocess.DEVNULL,text=True));t=next(x['transport'] for x in config if x['name']=='codex_app')
 if t['type']!='stdio':raise RuntimeError('Expected existing stdio app connector')
 env=os.environ.copy();env.update(t.get('env') or {})
 p=subprocess.Popen([t['command'],*(t.get('args') or [])],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,bufsize=1,env=env,cwd=t.get('cwd') or None)
 q=queue.Queue()
 def reader():
  for line in p.stdout:
   try:q.put(json.loads(line))
   except ValueError:pass
 threading.Thread(target=reader,daemon=True).start();counter=0
 def rpc(method,params=None,notification=False):
  nonlocal counter
  counter+=1;req={'jsonrpc':'2.0','method':method,'params':params or {}}
  if not notification:req['id']=counter
  p.stdin.write(json.dumps(req)+'\n');p.stdin.flush()
  if notification:return
  until=time.monotonic()+55
  while time.monotonic()<until:
   x=q.get(timeout=max(.1,until-time.monotonic()))
   if x.get('id')==counter:
    if 'error' in x:raise RuntimeError('App connector RPC failed: '+str(x['error'].get('message','unknown')))
    return x.get('result')
  raise TimeoutError('App connector response timeout')
 try:
  rpc('initialize',{'protocolVersion':'2024-11-05','capabilities':{},'clientInfo':{'name':'composition-batch-progress','version':'1'}});rpc('notifications/initialized',notification=True)
  return callback(rpc)
 finally:
  p.terminate()
  try:p.wait(timeout=3)
  except subprocess.TimeoutExpired:p.kill()
def inspect():
 def go(rpc):
  result=rpc('tools/list');matches=[t for t in result.get('tools',[]) if t['name'].endswith('send_message_to_thread')]
  if not matches:raise RuntimeError('App connector has no thread messaging tool')
  return [{'name':t['name'],'inputSchema':t.get('inputSchema')} for t in matches]
 return app_client(go)
def notify(thread_id,message):
 def go(rpc):
  result=rpc('tools/list');tool=next(t for t in result['tools'] if t['name'].endswith('send_message_to_thread'))
  result=rpc('tools/call',{'name':tool['name'],'arguments':{'threadId':thread_id,'prompt':message}})
  if result.get('isError'):raise RuntimeError('App connector rejected milestone message')
  return {'delivered':True,'tool':tool['name']}
 return app_client(go)
if __name__=='__main__':print(json.dumps(inspect(),ensure_ascii=False))
