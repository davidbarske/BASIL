from __future__ import annotations
import argparse, hashlib, io, json, shutil, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
VOICE_DIR=ROOT/'voice'; OUTPUT_DIR=ROOT/'output'
SPEC_PATH=ROOT/'voice_spec.json'; SEED_PATH=ROOT/'seed_text.txt'
REFERENCE_PATH=VOICE_DIR/'basil_reference.wav'; LOCK_PATH=VOICE_DIR/'basil_voice_lock.json'
VOICE_DIR.mkdir(exist_ok=True); OUTPUT_DIR.mkdir(exist_ok=True)
def read_spec(): return json.loads(SPEC_PATH.read_text(encoding='utf-8'))
def seed_text(): return SEED_PATH.read_text(encoding='utf-8').strip()
def runtime():
    import torch
    from qwen_tts import Qwen3TTSModel
    return torch,Qwen3TTSModel
def device_settings():
    torch,_=runtime()
    if torch.cuda.is_available():
        return {'device_map':'cuda:0','dtype':torch.bfloat16,'attn_implementation':'sdpa','device_label':torch.cuda.get_device_name(0)}
    return {'device_map':'cpu','dtype':torch.float32,'attn_implementation':'sdpa','device_label':'CPU'}
def load_model(name):
    _,M=runtime(); d=device_settings(); print(f'Loading {name}'); print(f"Device: {d['device_label']}")
    return M.from_pretrained(name,device_map=d['device_map'],dtype=d['dtype'],attn_implementation=d['attn_implementation'])
def doctor():
    print('BASIL VOICE CAPABILITY v0.3')
    print('Python:',sys.version.split()[0])
    print('Working directory:',ROOT)
    total,used,free=shutil.disk_usage(ROOT)
    print(f'Free disk: {free/(1024**3):.1f} GB')
    try:
        import torch
        import qwen_tts
        import soundfile
        print('PyTorch:',torch.__version__)
        print('CUDA available:',torch.cuda.is_available())
        if torch.cuda.is_available():
            print('GPU:',torch.cuda.get_device_name(0))
            try:
                free_b,total_b=torch.cuda.mem_get_info()
                print(f'VRAM free/total: {free_b/(1024**3):.1f}/{total_b/(1024**3):.1f} GB')
            except Exception:
                pass
        else:
            print('No CUDA GPU available to PyTorch. CPU mode will be used and may be slow.')
        print('qwen-tts import: PASS')
        print('soundfile import: PASS')
    except Exception as e:
        print('Dependency check: FAIL:',e)
        return 1
    if free<12*1024**3:
        print('WARNING: less than 12 GB free disk. Model downloads may fail.')
    print('Doctor: PASS')
    return 0
def design():
    import soundfile as sf
    spec=read_spec(); text=seed_text(); model=load_model(spec['design_model'])
    print('Generating the initial original BASIL reference voice...')
    wavs,sr=model.generate_voice_design(text=text,language=spec['language'],instruct=spec['instruct'])
    sf.write(str(REFERENCE_PATH),wavs[0],sr)
    digest=hashlib.sha256(REFERENCE_PATH.read_bytes()).hexdigest()
    lock={'voice_name':spec['name'],'reference_file':REFERENCE_PATH.name,'reference_sha256':digest,'reference_text':text,'voice_spec_sha256':hashlib.sha256(SPEC_PATH.read_bytes()).hexdigest(),'runtime_model':spec['runtime_model'],'state':'REFERENCE_GENERATED_NOT_CONFIRMED'}
    LOCK_PATH.write_text(json.dumps(lock,indent=2),encoding='utf-8')
    print('Created:',REFERENCE_PATH); print('SHA-256:',digest); print('Voice is now usable. Final benchmark confirmation remains later.'); return 0
def require_reference():
    if not REFERENCE_PATH.exists(): raise SystemExit('No BASIL reference voice exists. Run: python basil_voice.py design')
    return seed_text()
def make_prompt(model): return model.create_voice_clone_prompt(ref_audio=str(REFERENCE_PATH),ref_text=require_reference(),x_vector_only_mode=False)
def generate(text,out):
    import soundfile as sf
    spec=read_spec(); model=load_model(spec['runtime_model']); prompt=make_prompt(model)
    wavs,sr=model.generate_voice_clone(text=text,language=spec['language'],voice_clone_prompt=prompt); sf.write(str(out),wavs[0],sr); return out
def speak(text,output):
    out=Path(output) if output else OUTPUT_DIR/'basil_speech.wav'
    if not out.is_absolute(): out=ROOT/out
    out.parent.mkdir(parents=True,exist_ok=True); generate(text,out); print('Created:',out); return 0
def serve(host,port):
    from fastapi import FastAPI,HTTPException
    from fastapi.responses import Response
    from pydantic import BaseModel
    import soundfile as sf, uvicorn
    spec=read_spec(); model=load_model(spec['runtime_model']); prompt=make_prompt(model)
    app=FastAPI(title='BASIL Voice API',version='0.3')
    class SpeakRequest(BaseModel): text:str
    @app.get('/health')
    def health(): return {'status':'ok','voice':spec['name'],'reference_exists':REFERENCE_PATH.exists()}
    @app.post('/speak')
    def api_speak(req:SpeakRequest):
        if not req.text.strip(): raise HTTPException(status_code=400,detail='text is required')
        wavs,sr=model.generate_voice_clone(text=req.text,language=spec['language'],voice_clone_prompt=prompt)
        b=io.BytesIO(); sf.write(b,wavs[0],sr,format='WAV'); return Response(content=b.getvalue(),media_type='audio/wav')
    print(f'BASIL Voice API: http://{host}:{port}'); uvicorn.run(app,host=host,port=port); return 0
def main():
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest='cmd',required=True); sub.add_parser('doctor'); sub.add_parser('design')
    s=sub.add_parser('speak'); s.add_argument('text'); s.add_argument('--output')
    v=sub.add_parser('serve'); v.add_argument('--host',default='127.0.0.1'); v.add_argument('--port',type=int,default=8765)
    a=p.parse_args()
    if a.cmd=='doctor': return doctor()
    if a.cmd=='design': return design()
    if a.cmd=='speak': return speak(a.text,a.output)
    if a.cmd=='serve': return serve(a.host,a.port)
    return 2
if __name__=='__main__': raise SystemExit(main())
