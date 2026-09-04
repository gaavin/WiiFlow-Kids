#include <dirent.h>
#include <unistd.h>
#include <algorithm>
#include <sys/stat.h>
#include "menu.hpp"
#include "lockMutex.hpp"
#include "channel/nand.hpp"
#include "loader/cios.h"
#include "loader/nk.h"

/* Kids UI: the emuNAND configuration/dump/flash menus are gone. What remains
   is only what booting a game still needs: locating the emuNAND partition and
   checking whether a save exists. */

int CMenu::_FindEmuPart(bool savesnand, bool skipchecks)
{
	int emuPart;
	char tmpPath[32];
	tmpPath[31] = '\0';
	if(savesnand)
	{
		emuPart = m_cfg.getInt(WII_DOMAIN, "savepartition");
		strncpy(tmpPath, fmt("/%s/%s",  emu_nands_dir, m_cfg.getString(WII_DOMAIN, "current_save_emunand").c_str()), sizeof(tmpPath) - 1);
	}
	else
	{
		emuPart = m_cfg.getInt(CHANNEL_DOMAIN, "partition");
		strncpy(tmpPath, fmt("/%s/%s",  emu_nands_dir, m_cfg.getString(CHANNEL_DOMAIN, "current_emunand").c_str()), sizeof(tmpPath) - 1);
	}
	if(!DeviceHandle.PartitionUsableForNandEmu(emuPart))//check if device is mounted and partition is FAT
		return -1;
	else if((skipchecks || _TestEmuNand(emuPart, tmpPath, false)))//check if emunand folder exist
	{
		NandHandle.SetNANDEmu(emuPart);
		NandHandle.SetPaths(tmpPath, DeviceName[emuPart]);
		return emuPart;
	}
	return -2;
}

bool CMenu::_TestEmuNand(int epart, const char *path, bool indept)
{
	char basepath[64];
	char testpath[MAX_FAT_PATH];
	snprintf(basepath, sizeof(basepath), "%s:%s", DeviceName[epart], path);

	DIR *d = opendir(basepath);
	if(!d)
		return false;
	else
		closedir(d);

	if(indept)
	{
		// Check Wiimotes && Region
		snprintf(testpath, sizeof(testpath), "%s/shared2/sys/SYSCONF", basepath);
		if(!fsop_FileExist(testpath))
			return false;
		snprintf(testpath, sizeof(testpath), "%s/title/00000001/00000002/data/setting.txt", basepath);
		if(!fsop_FileExist(testpath))
			return false;
		// Check Mii's
		snprintf(testpath, sizeof(testpath), "%s/shared2/menu/FaceLib/RFL_DB.dat", basepath);
		if(!fsop_FileExist(testpath))
			return false;
	}
	return true;
}

bool CMenu::_checkSave(string id, int nand_type)
{
	int savePath = id.c_str()[0] << 24 | id.c_str()[1] << 16 | id.c_str()[2] << 8 | id.c_str()[3];
	if(nand_type == REAL_NAND)
	{
		u32 temp = 0;
		if(ISFS_ReadDir(fmt("/title/00010000/%08x", savePath), NULL, &temp) < 0)
			if(ISFS_ReadDir(fmt("/title/00010004/%08x", savePath), NULL, &temp) < 0)
				return false;
	}
	else // SAVES_NAND
	{
		int emuPartition = m_cfg.getInt(WII_DOMAIN, "savepartition");
		const char *emuPath = fmt("/%s/%s",  emu_nands_dir, m_cfg.getString(WII_DOMAIN, "current_save_emunand").c_str());
		if(emuPartition < 0 || emuPath == NULL)
			return false;
		struct stat fstat;
		if((stat(fmt("%s:%s/title/00010000/%08x", DeviceName[emuPartition], emuPath, savePath), &fstat) != 0) 
			&& (stat(fmt("%s:%s/title/00010004/%08x", DeviceName[emuPartition], emuPath, savePath), &fstat) != 0))
			return false;
	}
	return true;
}

