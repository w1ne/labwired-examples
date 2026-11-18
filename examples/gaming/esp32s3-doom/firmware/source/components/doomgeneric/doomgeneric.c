#include <stdio.h>

#include "m_argv.h"

#include "doomgeneric.h"
#include "dg_psram_statics.h"
#include "i_system.h"

pixel_t* DG_ScreenBuffer = NULL;

void M_FindResponseFile(void);
void D_DoomMain (void);


void doomgeneric_Create(int argc, char **argv)
{
	// save arguments
    myargc = argc;
    myargv = argv;

	M_FindResponseFile();

#ifdef DOOM_STATICS_ON_HEAP
	// Doom's biggest static arrays are pointers in this build and have to be
	// filled in before anything reaches them. Doing it here rather than in the
	// backend means no backend can forget.
	if (!DG_AllocStatics())
	{
		I_Error ("doomgeneric_Create: could not allocate Doom's static arrays");
	}
#endif

	DG_ScreenBuffer = malloc(DOOMGENERIC_RESX * DOOMGENERIC_RESY * 4);

	DG_Init();

	D_DoomMain ();
}

