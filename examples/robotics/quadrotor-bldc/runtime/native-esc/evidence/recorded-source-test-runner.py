from pathlib import Path
import subprocess,shutil,hashlib,json,os,time
base=Path('/data/work-evidence/labwired-industrial-packages-20261118/quad-firmware');core=Path('/data/worktrees/labwired-core-timer-dma-20261118');started=time.monotonic();rec={'commands':[]}
def hashes():
 paths=subprocess.check_output(['git','diff','--name-only','HEAD'],cwd=core,text=True).splitlines()+subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=core,text=True).splitlines()
 return {p:hashlib.sha256((core/p).read_bytes()).hexdigest() for p in sorted(set(paths)) if (core/p).is_file()}
env=dict(os.environ,CARGO_TARGET_DIR='/data/cargo-target/native-timer-dma-20261118',CARGO_BUILD_JOBS='2',CARGO_INCREMENTAL='0',CARGO_PROFILE_DEV_DEBUG='0',CARGO_PROFILE_TEST_DEBUG='0',AT32_NATIVE_ARTIFACTS='/data/worktrees/labwired-examples-quad-package-20261118/examples/robotics/quadrotor-bldc/firmware/native-esc/artifacts',AT32_NATIVE_BIDIR_REPORT=str(base/'at32-native-bidir-final-2.json'),AT32_NATIVE_PROTOCOL_REPORT=str(base/'at32-native-protocol-final-2.json'))
try:
 old=core/'crates/core/tests/vendor/at32_am32_native.rs'
 if old.exists():shutil.copy2(old,base/'at32_am32_native-timer-preliminary.rs');old.unlink()
 commands=[['git','merge','--no-commit','--no-ff','origin/main'],['cargo','fmt','--all'],['python3','scripts/generate_ignored_tests.py'],['python3','scripts/generate_ignored_tests.py','--check'],['cargo','test','--locked','-p','labwired-core','--features','event-scheduler','--test','timer_compare_overflow','--test','timer_dma_requests','--','--nocapture'],['cargo','test','--locked','-p','labwired-core','--features','event-scheduler','--test','vendor','at32_am32_bidir::','--','--include-ignored','--nocapture'],['cargo','test','--locked','-p','labwired-core','--features','event-scheduler','--test','vendor','at32_am32_protocol::','--','--ignored','--nocapture'],['cargo','test','--locked','-p','labwired-core','--test','timer_compare_overflow','--test','timer_dma_requests','--','--nocapture'],['cargo','test','--locked','-p','labwired-core','--features','event-scheduler','--test','stm32_timer_walk_differential','--','--nocapture'],['cargo','test','--locked','-p','labwired-core','--features','event-scheduler','--test','stm32','timer','--','--nocapture']]
 with (base/'timer-wire-final.log').open('w') as log:
  for i,cmd in enumerate(commands):
   if i==4:rec['before']=hashes()
   t=time.monotonic();log.write('COMMAND '+repr(cmd)+'\n');log.flush();x=subprocess.run(cmd,cwd=core,env=env,stdout=log,stderr=subprocess.STDOUT);rec['commands'].append({'command':cmd,'exit':x.returncode,'seconds':time.monotonic()-t});(base/'timer-wire-final-progress.json').write_text(json.dumps(rec,indent=2)+'\n')
   if x.returncode:break
 rec['after']=hashes();rec['sourceUnchanged']=rec.get('before')==rec['after']
except Exception as exc:rec['error']=repr(exc)
finally:
 rec['seconds']=time.monotonic()-started;(base/'timer-wire-final.json').write_text(json.dumps(rec,indent=2)+'\n')
