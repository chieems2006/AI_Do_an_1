import os
import sys,time,glob,numpy as np
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'))
from msa.embed.image_embedders import get_embedder
fs=sorted(glob.glob((os.environ.get("MSA_SHARED_DATA", "/home/claude/work/shared_data") + "/fpi_images/*.jpg")))[:32]
for prec in ['fp32','bf16']:
    e=get_embedder(sys.argv[1],precision=prec); e.embed(fs[:4])
    t=time.perf_counter(); X=e.embed(fs); dt=time.perf_counter()-t
    np.save(os.path.join(os.environ.get('TMPDIR','/tmp'), f'sp_{prec}.npy'),X)
    print(prec, round(dt*1000/len(fs),1),'ms/img', flush=True)
a=np.load('/tmp/sp_fp32.npy');b=np.load('/tmp/sp_bf16.npy')
print('cos fp32 vs bf16: min',(a*b).sum(1).min(),'mean',(a*b).sum(1).mean())
