/****************************************************************************
 * Copyright (C) 2013 FIX94
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 ****************************************************************************/
#include "menu.hpp"
#include "channel/nand.hpp"
#include "loader/cios.h"
#include "loader/nk.h"
#include "wstringEx/wstringEx.hpp"

/* Kids UI: the Home / Exit To / Shutdown menus are gone. This file now only
   holds the cover-cache helpers, which the child's coverflow still needs on
   first boot to convert cover PNGs into .wfc textures. */

int CMenu::_cacheCovers()
{
	CoverFlow.stopCoverLoader(true);
	
	u32 total = m_gameList.size();
	m_thrdTotal = total;
	u32 index = 0;
	
	bool smallBox = false;
	if(m_current_view == COVERFLOW_HOMEBREW && !m_sourceflow)
		smallBox = m_cfg.getBool(HOMEBREW_DOMAIN, "smallbox", false);
	else if(m_sourceflow)
		smallBox = m_cfg.getBool(SOURCEFLOW_DOMAIN, "smallbox", false);
	else if(m_current_view == COVERFLOW_PLUGIN && !m_sourceflow)
	{
		if(enabledPluginsCount == 1 && m_plugin.GetEnabledStatus(HB_PMAGIC))
			smallBox = m_cfg.getBool(HOMEBREW_DOMAIN, "smallbox", false);
	}

	for(vector<dir_discHdr>::iterator hdr = m_gameList.begin(); hdr != m_gameList.end(); ++hdr)
	{
		index++;
		update_pThread(index, false);
		m_thrdMessage = wfmt(_fmt("dlmsg31", L"Converting cover %i of %i"), index, total);
		m_thrdMessageAdded = true;
		
		_cacheCover(&(*hdr), smallBox);
		
		/* cache wii and channel banners */
		if(hdr->type == TYPE_WII_GAME || hdr->type == TYPE_CHANNEL || hdr->type == TYPE_EMUCHANNEL)
		{
			CurrentBanner.ClearBanner();
			char cached_banner[256];
			strlcpy(cached_banner, fmt("%s/%s.bnr", m_bnrCacheDir.c_str(), hdr->id), sizeof(cached_banner));
			if(fsop_FileExist(cached_banner))
				continue;
			if(hdr->type == TYPE_WII_GAME)
			{
				_extractBnr(&(*hdr));
			}
			else if(hdr->type == TYPE_CHANNEL || hdr->type == TYPE_EMUCHANNEL)
			{
				ChannelHandle.GetBanner(TITLE_ID(hdr->settings[0], hdr->settings[1]));
			}
			
			if(CurrentBanner.IsValid())
				fsop_WriteFile(cached_banner, CurrentBanner.GetBannerFile(), CurrentBanner.GetBannerFileSize());
		}
	}
	CurrentBanner.ClearBanner();
	CoverFlow.startCoverLoader();
	return 0;
}

int CMenu::_cacheCover(const dir_discHdr *hdr, bool smallBox)// fix hdr
{
	char coverPath[MAX_FAT_PATH];//1024
	char wfcPath[MAX_FAT_PATH+20];
	char cachePath[MAX_FAT_PATH];
	
	/* get cover png path */
	bool blankCover = false;
	bool fullCover = true;
	if(smallBox)// homebrew or sourceflow
	{
		fullCover = false;
		strlcpy(coverPath, getFrontPath(hdr), sizeof(coverPath));
		if(!fsop_FileExist(coverPath))
			return 0;
	}
	else
	{
		strlcpy(coverPath, getBoxPath(hdr), sizeof(coverPath));
		//gprintf("boxpath=%s\n", coverPath);
		if(!fsop_FileExist(coverPath))
		{
			fullCover = false;
			strlcpy(coverPath, getFrontPath(hdr), sizeof(coverPath));
			//gprintf("frontpath=%s\n", coverPath);
			if(!fsop_FileExist(coverPath))
			{
				fullCover = true;
				strlcpy(coverPath, getBlankCoverPath(hdr), sizeof(coverPath));
				//gprintf("blankpath=%s\n", coverPath);
				blankCover = true;
				if(!fsop_FileExist(coverPath))
					return 0;
			}
		}
	}
	
	/* get cache folder path */
	if(hdr->type == TYPE_PLUGIN)
		snprintf(cachePath, sizeof(cachePath), "%s/%s", m_cacheDir.c_str(), m_plugin.GetCoverFolderName(hdr->settings[0]));
	else if(m_sourceflow)
		snprintf(cachePath, sizeof(cachePath), "%s/sourceflow", m_cacheDir.c_str());
	else if(hdr->type == TYPE_HOMEBREW)
		snprintf(cachePath, sizeof(cachePath), "%s/homebrew", m_cacheDir.c_str());
	else
		snprintf(cachePath, sizeof(cachePath), "%s", m_cacheDir.c_str());
	gprintf("cachepath=%s\n", cachePath);

	/* get game name or ID */
	const char *gameNameOrID = NULL;
	if(!blankCover)
		gameNameOrID = CoverFlow.getFilenameId(hdr);
	else
		gameNameOrID = strrchr(coverPath, '/') + 1;
	gprintf("nameorid=%s\n", gameNameOrID);
	
	/* get cover wfc path */
	if(smallBox)
		snprintf(wfcPath, sizeof(wfcPath), "%s/%s_small.wfc", cachePath, gameNameOrID);
	else
		snprintf(wfcPath, sizeof(wfcPath), "%s/%s.wfc", cachePath, gameNameOrID);
	gprintf("wfcpath=%s\n", wfcPath);
	
	/* if wfc doesn't exist or is flat and have full cover */
	if(!fsop_FileExist(wfcPath) || (!CoverFlow.fullCoverCached(wfcPath) && fullCover))
	{
		// create cache subfolders if needed
		if(!fsop_FolderExist(cachePath))
			fsop_MakeFolder(cachePath);
	
		// create cover texture
		CoverFlow.cacheCoverFile(wfcPath, coverPath, fullCover);
	}
	return 0;
}
