import pcbnew as p
b=p.LoadBoard('/work/4in1.kicad_pcb')
for fp in sorted((f for f in b.GetFootprints() if f.GetReference() in ('U2','U5','U7','U9','U4','U6','U8','U10','U3')) ,key=lambda f:f.GetReference()):
 print('===',fp.GetReference(),fp.GetValue(),'fp',str(fp.GetFPID().GetLibItemName()),'path',fp.GetPath().AsString())
 numbers={}
 for pad in fp.Pads():
  numbers.setdefault(pad.GetNumber(),[]).append((pad.GetNetname(),p.ToMM(pad.GetPosition().x),p.ToMM(pad.GetPosition().y)))
 for k,v in sorted(numbers.items(),key=lambda kv:(len(kv[0]),kv[0])):
  print('  ',k, v[:5])
 print(' TOTAL',len(list(fp.Pads())), 'UNIQUE',len(numbers))
