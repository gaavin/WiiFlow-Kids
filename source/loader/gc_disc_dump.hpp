/****************************************************************************
 * WiiFlow Kids - GameCube disc file-system structures.
 *
 * The GCDump class (dumping a GameCube disc to storage) was removed along with
 * the rest of the old UI. Only the on-disc FST layout survives here, because
 * reading a game's banner for the child's game screen still needs it.
 ***************************************************************************/

#ifndef GC_DISC_DUMP_H_
#define GC_DISC_DUMP_H_

struct FST
{
	union
	{
		struct
		{
			u32 Type		:8;
			u32 NameOffset	:24;
		};
		u32 TypeName;
	};
	union
	{
		struct
		{
			u32 FileOffset;
			u32 FileLength;
		};
		struct
		{
			u32 ParentOffset;
			u32 NextOffset;
		};
		u32 entry[2];
	};
};

#endif
