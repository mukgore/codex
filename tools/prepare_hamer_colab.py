"""Prepare isolated HaMeR core imports on a user-connected Linux Colab GPU.

Does not download MANO/checkpoints, read Drive, run inference, install detectors,
or alter the notebook kernel's Python/PyTorch. Run only after reviewing it.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import signal
import subprocess
import sys
import urllib.request

REVISION='3a01849f4148352e9260b69bf28b65d1671a4905'
UV_VERSION='0.9.10'
PYTHON_VERSION='3.10.19'
CHUMPY_SHA='a0275c2018784ca1302875567dc81761f5fd469fab9f3ac0f3e7c39e9180350a'
CONSTRAINTS='''numpy==1.23.5
scipy==1.10.1
torch==2.5.1+cu118
torchvision==0.20.1+cu118
setuptools==75.8.0
wheel==0.45.1
six==1.17.0
pillow==10.4.0
pytorch-lightning==2.0.9
torchmetrics==1.2.1
timm==0.9.16
einops==0.8.0
yacs==0.1.8
smplx==0.1.28
scikit-image==0.21.0
opencv-python==4.10.0.84
pyrender==0.1.45
trimesh==4.4.9
rich==13.9.4
'''


def root_name(value):
    path=PurePosixPath(value)
    if str(path)!=value or not re.fullmatch(r'/content/handcaptcha_[a-zA-Z0-9_]+',value):
        raise ValueError('Use a new dedicated /content/handcaptcha_<name> directory')
    return path


def run(output,*,resume=False):
    root_name(output)
    if platform.system()!='Linux' or platform.machine() not in ('x86_64','AMD64'):
        raise ValueError('This recipe is for Linux x86_64 Colab, not the Windows PC')
    root=Path(output)
    if root.resolve()!=root:raise ValueError('Do not use a symlink for the isolated runtime root')
    recipe_hash=hashlib.sha256((REVISION+CONSTRAINTS+UV_VERSION+PYTHON_VERSION).encode()).hexdigest()
    if resume:
        owner=json.loads((root/'owner.json').read_text(encoding='utf8'))
        if owner['recipe_sha256']!=recipe_hash:raise ValueError('Different recipe; use a new directory')
        if (root/'readiness.json').exists():raise FileExistsError('Completed environment already exists')
    else:
        root.mkdir(parents=True,exist_ok=False)
        (root/'owner.json').write_text(json.dumps({'recipe_sha256':recipe_hash,'kernel_python':platform.python_version(),
            'runner_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})+'\n',encoding='utf8')
    env=dict(os.environ);env.update(UV_PYTHON_INSTALL_DIR=str(root/'python'),UV_PYTHON_BIN_DIR=str(root/'python_bin'),
        UV_CACHE_DIR=str(root/'cache'),PIP_CACHE_DIR=str(root/'cache'/'pip'),UV_NO_PROGRESS='1',UV_NO_MODIFY_PATH='1',PYOPENGL_PLATFORM='egl')
    def step(name,args,*,cwd=None,extra_env=None):
        path=root/(name+'.log');attempt=1
        while path.exists():attempt+=1;path=root/(name+f'_attempt{attempt}.log')
        print('STEP:',name,flush=True)
        child_env={**env,**(extra_env or {})}
        with path.open('xb') as log:
            process=subprocess.Popen(args,cwd=cwd,env=child_env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            try:
                code=process.wait(timeout=1800)
            except BaseException:
                try:os.killpg(process.pid,signal.SIGKILL)
                except ProcessLookupError:pass
                process.wait();raise
        if code:
            print(path.read_text(encoding='utf8',errors='replace')[-6000:],flush=True)
            raise RuntimeError(name+' failed; private log retained')
        return path
    tools=root/'tools'
    step('uv_tool',[sys.executable,'-m','pip','install','--disable-pip-version-check','--no-deps',
                    '--target',str(tools),'uv=='+UV_VERSION])
    uv_env={'PYTHONPATH':str(tools)}
    step('python310',[sys.executable,'-m','uv','python','install',PYTHON_VERSION],extra_env=uv_env)
    venv=root/'venv'
    if not venv.exists():step('new_venv',[sys.executable,'-m','uv','venv','--python',PYTHON_VERSION,'--seed',str(venv)],extra_env=uv_env)
    python=str(venv/'bin'/'python');pip=[python,'-m','pip','install','--disable-pip-version-check']
    constraints=root/'constraints.txt'
    if not constraints.exists():constraints.write_text(CONSTRAINTS,encoding='utf8')
    step('cuda_torch',pip+['torch==2.5.1','torchvision==0.20.1','--index-url','https://download.pytorch.org/whl/cu118'])
    step('legacy_numpy_and_build',pip+['-c',str(constraints),'numpy','scipy','setuptools','wheel','six','pillow'])
    requirements=[line for line in CONSTRAINTS.splitlines() if line and not line.startswith(('torch==','torchvision=='))]
    step('model_core_dependencies',pip+['-c',str(constraints),*requirements])
    source=root/'chumpy-0.70.tar.gz'
    if not source.exists():
        with urllib.request.urlopen('https://pypi.org/pypi/chumpy/0.70/json',timeout=60) as response:metadata=json.load(response)
        asset=next(x for x in metadata['urls'] if x['filename']=='chumpy-0.70.tar.gz')
        if asset['digests']['sha256']!=CHUMPY_SHA:raise ValueError('Published Chumpy hash mismatch')
        with urllib.request.urlopen(asset['url'],timeout=60) as response:raw=response.read(1024*1024)
        if hashlib.sha256(raw).hexdigest()!=CHUMPY_SHA:raise ValueError('Downloaded Chumpy hash mismatch')
        source.write_bytes(raw)
    if hashlib.sha256(source.read_bytes()).hexdigest()!=CHUMPY_SHA:raise ValueError('Cached Chumpy changed')
    step('chumpy_source',pip+['--no-deps','--no-build-isolation',str(source)])
    repo=root/'hamer'
    if not repo.exists():step('clone_pinned_source',['git','clone','--no-checkout','https://github.com/geopavlakos/hamer.git',str(repo)])
    step('checkout_source',['git','checkout','--detach',REVISION],cwd=repo)
    actual=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
    if actual!=REVISION:raise ValueError('Source revision mismatch')
    step('dependency_check',[python,'-m','pip','check'])
    probe='''import json,sys,torch
from hamer.models import HAMER
assert sys.version_info[:2]==(3,10)
assert torch.cuda.is_available(), 'CUDA unavailable in isolated environment'
x=torch.ones(4,device='cuda'); y=x+x; torch.cuda.synchronize()
assert y.sum().item()==8
print(json.dumps({'python':sys.version.split()[0],'torch':torch.__version__,
 'cuda':torch.version.cuda,'gpu':torch.cuda.get_device_name(0),'core_import':True}))
'''
    gpu_log=step('gpu_core_import',[python,'-c',probe],cwd=repo,extra_env={'PYTHONPATH':str(repo)})
    gpu=json.loads(gpu_log.read_text(encoding='utf8').splitlines()[-1])
    freeze=subprocess.check_output([python,'-m','pip','freeze','--all'],env=env,text=True)
    (root/'installed.freeze.txt').write_text(freeze,encoding='utf8')
    result={'schema_version':1,'state':'CORE_IMPORTS_GPU_READY_NO_MODELS','environment':gpu,
            'runner_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'hamer_revision':actual,'recipe_sha256':recipe_hash,'kernel_environment_modified':False,
            'detector_installed':False,'model_assets_downloaded':False,'inference_executed':False,
            'limitations':['fixed full-frame input model-only path, not official full detector demo',
                           'freeze records resolution; this is not a wheel-hash reproducibility lock']}
    (root/'readiness.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps(result),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',default='/content/handcaptcha_hamer_core');parser.add_argument('--resume',action='store_true')
    args=parser.parse_args();run(args.output,resume=args.resume)
