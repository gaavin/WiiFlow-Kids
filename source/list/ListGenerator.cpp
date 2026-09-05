/****************************************************************************
 * Copyright (C) 2012 FIX94
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
#include <algorithm>
#include <cctype>
#include <dirent.h>
#include <unistd.h>
#include "ListGenerator.hpp"
#include "cache.hpp"
#include "devicemounter/DeviceHandler.hpp"
#include "fileOps/fileOps.h"
#include "gui/coverflow.hpp"
#include "gui/text.hpp"
#include "loader/sys.h"

ListGenerator m_cacheList;
dir_discHdr ListElement;
Config CustomTitles;
GameTDB gameTDB;

void ListGenerator::Init(const char *settingsDir, const char *Language)
{
	if(settingsDir != NULL)
	{
		gameTDB_Path = fmt("%s/wiitdb.xml", settingsDir);
		CustomTitlesPath = fmt("%s/" CTITLES_FILENAME, settingsDir);
	}
	if(Language != NULL)
		gameTDB_Language = Language;
}

void ListGenerator::Clear(void)
{
	m_cacheList.clear();
	vector<dir_discHdr>().swap(m_cacheList);
}

void ListGenerator::OpenConfigs()
{
	gameTDB.OpenFile(gameTDB_Path.c_str());
	if(gameTDB.IsLoaded())
		gameTDB.SetLanguageCode(gameTDB_Language.c_str());
	CustomTitles.load(CustomTitlesPath.c_str());
	CustomTitles.groupCustomTitles();
}

void ListGenerator::CloseConfigs()
{
	if(gameTDB.IsLoaded())
		gameTDB.CloseFile();
	if(CustomTitles.loaded())
		CustomTitles.unload();
}

static void AddISO(const char *GameID, const char *GameTitle, const char *GamePath,
							u32 GameColor, u8 Type)
{
	memset((void*)&ListElement, 0, sizeof(dir_discHdr));
	ListElement.index = m_cacheList.size();

	if(GameID != NULL) strncpy(ListElement.id, GameID, 6);
	if(GamePath != NULL) strncpy(ListElement.path, GamePath, sizeof(ListElement.path) - 1);

	ListElement.casecolor = CustomTitles.getColor("COVERS", ListElement.id, GameColor).intVal();

	char CustomTitle[64];
	memset(CustomTitle, 0, sizeof(CustomTitle));
	strncpy(CustomTitle, CustomTitles.getString("TITLES", ListElement.id).c_str(), 63);

	const char *gameTDB_Title = NULL;
	if(gameTDB.IsLoaded())
	{
		int PublishDate = gameTDB.GetPublishDate(ListElement.id);
		ListElement.year = PublishDate >> 16;
		if(ListElement.casecolor == GameColor)
			ListElement.casecolor = gameTDB.GetCaseColor(ListElement.id);
		ListElement.wifi = gameTDB.GetWifiPlayers(ListElement.id);
		ListElement.players = gameTDB.GetPlayers(ListElement.id);
		if(strlen(CustomTitle) == 0)
			gameTDB.GetTitle(ListElement.id, gameTDB_Title);
	}
	if(!ValidColor(ListElement.casecolor))
		ListElement.casecolor = CoverFlow.InternalCoverColor(ListElement.id, GameColor);

	if(strlen(CustomTitle) > 0)
		mbstowcs(ListElement.title, CustomTitle, 63);
	else if(gameTDB_Title != NULL && gameTDB_Title[0] != '\0')
		mbstowcs(ListElement.title, gameTDB_Title, 63);
	else if(GameTitle != NULL)
		mbstowcs(ListElement.title, GameTitle, 63);
	Asciify(ListElement.title);

	ListElement.type = Type;
	m_cacheList.push_back(ListElement);
}

static void Create_Wii_WBFS_List(wbfs_t *handle)
{
	for(u32 i = 0; i < wbfs_count_discs(handle); i++)
	{
		memset((void*)&wii_hdr, 0, sizeof(discHdr));
		s32 ret = wbfs_get_disc_info(handle, i, (u8*)&wii_hdr, sizeof(discHdr), NULL);
		if(ret == 0 && wii_hdr.magic == WII_MAGIC)
			AddISO((const char*)wii_hdr.id, (const char*)wii_hdr.title,
					NULL, 0xFFFFFF, TYPE_WII_GAME);
	}
}

static void Add_Wii_Game(char *FullPath)
{
	FILE *fp = fopen(FullPath, "rb");
	if(fp)
	{
		fseek(fp, strcasestr(FullPath, ".wbfs") != NULL ? 512 : 0, SEEK_SET);
		fread((void*)&wii_hdr, 1, sizeof(discHdr), fp);
		if(wii_hdr.magic == WII_MAGIC)
			AddISO((const char*)wii_hdr.id, (const char*)wii_hdr.title,
					FullPath, 0xFFFFFF, TYPE_WII_GAME);
		fclose(fp);
	}
}

u8 gc_disc[1];
const char *FST_APPEND = "sys/boot.bin";
const u8 FST_APPEND_SIZE = strlen(FST_APPEND);
static const u8 CISO_MAGIC[8] = {'C','I','S','O',0x00,0x00,0x20,0x00};
static void Add_GameCube_Game(char *FullPath)
{
	u32 hdr_offset = 0x00;
	FILE *fp = fopen(FullPath, "rb");
	if(!fp && strstr(FullPath, "/root") != NULL) // fst folder (extracted game)
	{
		*(strstr(FullPath, "/root") + 1) = '\0';
		if(strlen(FullPath) + FST_APPEND_SIZE < MAX_MSG_SIZE) strcat(FullPath, FST_APPEND);
		fp = fopen(FullPath, "rb");
	}
	if(fp)
	{
		fread((void*)&gc_hdr, 1, sizeof(gc_discHdr), fp);
		if(!memcmp((void*)&gc_hdr, CISO_MAGIC, sizeof(CISO_MAGIC)))
		{
			hdr_offset = 0x8000;
			fseek(fp, hdr_offset, SEEK_SET);
			fread((void*)&gc_hdr, 1, sizeof(gc_discHdr), fp);
		}
		if(gc_hdr.magic == GC_MAGIC)
		{
			fseek(fp, hdr_offset + 0x06, SEEK_SET);
			fread(gc_disc, 1, 1, fp);
			if(!gc_disc[0])
				AddISO((const char*)gc_hdr.id, (const char*)gc_hdr.title, FullPath, 0x000000, TYPE_GC_GAME);
		}
		fclose(fp);
	}
}

void ListGenerator::CreateList(u32 Flow, const string& Path, const vector<string>& FileTypes, const string& DBName, bool UpdateCache)
{
	Clear();
	if(!DBName.empty())
	{
		if(UpdateCache)
			fsop_deleteFile(DBName.c_str());
		else
		{
			CCache(*this, DBName, LOAD);
			if(!this->empty())
				return;
			fsop_deleteFile(DBName.c_str());
		}
	}
	OpenConfigs();
	u32 Device = DeviceHandle.PathToDriveType(Path.c_str());
	if(Flow == COVERFLOW_WII)
	{
		if(DeviceHandle.GetFSType(Device) == PART_FS_WBFS)
			Create_Wii_WBFS_List(DeviceHandle.GetWbfsHandle(Device));
		else
			GetFiles(Path.c_str(), FileTypes, Add_Wii_Game, false);
	}
	else if(Flow == COVERFLOW_GAMECUBE && DeviceHandle.GetFSType(Device) != PART_FS_WBFS)
		GetFiles(Path.c_str(), FileTypes, Add_GameCube_Game, true);
	CloseConfigs();
	if(!this->empty() && !DBName.empty())
		CCache(*this, DBName, SAVE);
}

static inline bool IsFileSupported(const char *File, const vector<string>& FileTypes)
{
	const auto fileName = std::string(File);
	for(const auto &fileType : FileTypes)
	{
		if(fileName.length() >= fileType.length() &&
		   std::equal(fileName.end() - fileType.length(),
			      fileName.end(), fileType.begin(),
			      [](char c1, char c2)
			      {
				      return c1 == c2 || std::toupper(static_cast<unsigned char>(c1)) ==
							 std::toupper(static_cast<unsigned char>(c2));
			      }))
			return true;
	}
	return false;
}

void GetFiles(const char *Path, const vector<string>& FileTypes,
				FileAdder AddFile, bool CompareFolders, u32 max_depth, u32 depth)
{
	DIR *dir = opendir(Path);
	if(dir == NULL)
		return;

	vector<string> SubPaths;
	while(dirent *ent = readdir(dir))
	{
		if(ent->d_name[0] == '.')
			continue;
		char *fullPath = fmt("%s/%s", Path, ent->d_name);
		if(ent->d_type == DT_DIR)
		{
			if(CompareFolders && IsFileSupported(ent->d_name, FileTypes))
			{
				AddFile(fullPath);
				continue;
			}
			if(depth < max_depth)
				SubPaths.push_back(fullPath);
		}
		else if(ent->d_type == DT_REG && IsFileSupported(ent->d_name, FileTypes))
			AddFile(fullPath);
	}
	closedir(dir);
	for(const string &sub : SubPaths)
		GetFiles(sub.c_str(), FileTypes, AddFile, CompareFolders, max_depth, depth + 1);
}
