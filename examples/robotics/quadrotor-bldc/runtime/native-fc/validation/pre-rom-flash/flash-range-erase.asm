
examples/robotics/quadrotor-bldc/firmware/native-fc/artifacts/betaflight_RP2350B_OPENFC_LITE_REV2_LW1.elf:     file format elf32-littlearm


Disassembly of section .flashtext:

Disassembly of section .text:

Disassembly of section .data:

200483c8 <flash_range_erase>:
200483c8:	e92d 43f0 	stmdb	sp!, {r4, r5, r6, r7, r8, r9, lr}
200483cc:	180b      	adds	r3, r1, r0
200483ce:	f5b3 1f00 	cmp.w	r3, #2097152	@ 0x200000
200483d2:	b085      	sub	sp, #20
200483d4:	d859      	bhi.n	2004848a <flash_range_erase+0xc2>
200483d6:	2300      	movs	r3, #0
200483d8:	4604      	mov	r4, r0
200483da:	460d      	mov	r5, r1
200483dc:	8ada      	ldrh	r2, [r3, #22]
200483de:	2300      	movs	r3, #0
200483e0:	e843 f300 	tt	r3, r3
200483e4:	025e      	lsls	r6, r3, #9
200483e6:	bf54      	ite	pl
200483e8:	2110      	movpl	r1, #16
200483ea:	2104      	movmi	r1, #4
200483ec:	f244 6049 	movw	r0, #17993	@ 0x4649
200483f0:	4790      	blx	r2
200483f2:	2300      	movs	r3, #0
200483f4:	4607      	mov	r7, r0
200483f6:	8ada      	ldrh	r2, [r3, #22]
200483f8:	2300      	movs	r3, #0
200483fa:	e843 f300 	tt	r3, r3
200483fe:	0258      	lsls	r0, r3, #9
20048400:	bf54      	ite	pl
20048402:	2110      	movpl	r1, #16
20048404:	2104      	movmi	r1, #4
20048406:	f645 0045 	movw	r0, #22597	@ 0x5845
2004840a:	4790      	blx	r2
2004840c:	2300      	movs	r3, #0
2004840e:	4606      	mov	r6, r0
20048410:	8ada      	ldrh	r2, [r3, #22]
20048412:	2300      	movs	r3, #0
20048414:	e843 f300 	tt	r3, r3
20048418:	0259      	lsls	r1, r3, #9
2004841a:	bf54      	ite	pl
2004841c:	2110      	movpl	r1, #16
2004841e:	2104      	movmi	r1, #4
20048420:	f244 5052 	movw	r0, #17746	@ 0x4552
20048424:	4790      	blx	r2
20048426:	2300      	movs	r3, #0
20048428:	4681      	mov	r9, r0
2004842a:	8ada      	ldrh	r2, [r3, #22]
2004842c:	2300      	movs	r3, #0
2004842e:	e843 f300 	tt	r3, r3
20048432:	025b      	lsls	r3, r3, #9
20048434:	bf54      	ite	pl
20048436:	2110      	movpl	r1, #16
20048438:	2104      	movmi	r1, #4
2004843a:	f244 3046 	movw	r0, #17222	@ 0x4346
2004843e:	4790      	blx	r2
20048440:	4680      	mov	r8, r0
20048442:	b1e7      	cbz	r7, 2004847e <flash_range_erase+0xb6>
20048444:	b1de      	cbz	r6, 2004847e <flash_range_erase+0xb6>
20048446:	f1b9 0f00 	cmp.w	r9, #0
2004844a:	d018      	beq.n	2004847e <flash_range_erase+0xb6>
2004844c:	b1b8      	cbz	r0, 2004847e <flash_range_erase+0xb6>
2004844e:	f7ff ff57 	bl	20048300 <flash_init_boot2_copyout>
20048452:	f000 f979 	bl	20048748 <xip_cache_clean_all>
20048456:	a801      	add	r0, sp, #4
20048458:	f7ff ff70 	bl	2004833c <flash_rp2350_save_qmi_cs1>
2004845c:	47b8      	blx	r7
2004845e:	47b0      	blx	r6
20048460:	23d8      	movs	r3, #216	@ 0xd8
20048462:	f44f 3280 	mov.w	r2, #65536	@ 0x10000
20048466:	4629      	mov	r1, r5
20048468:	4620      	mov	r0, r4
2004846a:	47c8      	blx	r9
2004846c:	47c0      	blx	r8
2004846e:	f7ff ff61 	bl	20048334 <flash_enable_xip_via_boot2>
20048472:	a801      	add	r0, sp, #4
20048474:	f7ff ff90 	bl	20048398 <flash_rp2350_restore_qmi_cs1>
20048478:	b005      	add	sp, #20
2004847a:	e8bd 83f0 	ldmia.w	sp!, {r4, r5, r6, r7, r8, r9, pc}
2004847e:	217c      	movs	r1, #124	@ 0x7c
20048480:	4b05      	ldr	r3, [pc, #20]	@ (20048498 <flash_range_erase+0xd0>)
20048482:	4a06      	ldr	r2, [pc, #24]	@ (2004849c <flash_range_erase+0xd4>)
20048484:	4806      	ldr	r0, [pc, #24]	@ (200484a0 <flash_range_erase+0xd8>)
20048486:	f7f9 fb15 	bl	20041ab4 <__assert_func>
2004848a:	2174      	movs	r1, #116	@ 0x74
2004848c:	4b05      	ldr	r3, [pc, #20]	@ (200484a4 <flash_range_erase+0xdc>)
2004848e:	4a03      	ldr	r2, [pc, #12]	@ (2004849c <flash_range_erase+0xd4>)
20048490:	4803      	ldr	r0, [pc, #12]	@ (200484a0 <flash_range_erase+0xd8>)
20048492:	f7f9 fb0f 	bl	20041ab4 <__assert_func>
20048496:	bf00      	nop
20048498:	2004bba0 	.word	0x2004bba0
2004849c:	20052898 	.word	0x20052898
200484a0:	2004bb34 	.word	0x2004bb34
200484a4:	2004bb74 	.word	0x2004bb74
