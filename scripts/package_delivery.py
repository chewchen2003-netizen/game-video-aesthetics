"""Build a portable ZIP; optionally include original clips supplied separately."""
from pathlib import Path
import argparse,json,zipfile
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--raw-dir',type=Path);a=p.parse_args()
excluded={'.git','.venv','node_modules','runs','__pycache__','raw-inputs','outputs'}
a.output.parent.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(a.output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=1) as z:
 for f in sorted(ROOT.rglob('*')):
  rel=f.relative_to(ROOT)
  if f.is_file() and not any(x in excluded for x in rel.parts) and f.suffix not in {'.zip','.pyc'} and f.name!='.DS_Store':z.write(f,Path(ROOT.name)/rel)
 if a.raw_dir:
  for r in json.loads((ROOT/'data/sources/selection.json').read_text()):
   file=a.raw_dir/Path(r['video']).name
   if not file.exists():raise FileNotFoundError(file)
   z.write(file,Path(ROOT.name)/'raw-inputs/videos'/file.name)
print(a.output, a.output.stat().st_size, 'bytes')
