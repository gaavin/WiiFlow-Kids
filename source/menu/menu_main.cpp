
#include <unistd.h>
#include <cwctype>
#include <fstream>
#include <sys/stat.h>

#include "menu.hpp"

extern const u8 a_button_png[];
#include "channel/nand.hpp"
#include "devicemounter/DeviceHandler.hpp"
#include "loader/alt_ios.h"
#include "loader/cios.h"
#include "loader/disc.h"
#include "loader/nk.h"
#include "loader/wbfs.h"
#include "loader/wdvd.h"
#include "network/gcard.h"

static inline int loopNum(int i, int s)
{
	return (i + s) % s;
}

void CMenu::_hideMain(bool instant)
{
	m_btnMgr.hide(m_mainBtnNext, instant);
	m_btnMgr.hide(m_mainBtnPrev, instant);
	m_btnMgr.hide(m_mainLblAGlyph, instant);
	m_btnMgr.hide(m_mainLblPlayHint, instant);
	m_btnMgr.hide(m_mainLblMessage, instant);
	m_btnMgr.hide(m_mainLblLetter, instant);
	m_btnMgr.hide(m_mainLblNotice, instant);
	for(u8 i = 0; i < ARRAY_SIZE(m_mainLblUser); ++i)
		if(m_mainLblUser[i] != -1)
			m_btnMgr.hide(m_mainLblUser[i], instant);
}

void CMenu::_getCustomBgTex()
{
	{
		curCustBg = loopNum(curCustBg + 1, 2);
		string fn = "";
		if(m_platform.loaded())
		{
			m_plugin.PluginMagicWord[0] = '\0';
			u8 i = 0;
			switch(m_current_view)
			{
				case COVERFLOW_CHANNEL:
					if(m_cfg.getInt(CHANNEL_DOMAIN, "channels_type") & CHANNELS_REAL)
						strncpy(m_plugin.PluginMagicWord, NAND_PMAGIC, 9);
					else
						strncpy(m_plugin.PluginMagicWord, ENAND_PMAGIC, 9);
					break;
				case COVERFLOW_HOMEBREW:
					strncpy(m_plugin.PluginMagicWord, HB_PMAGIC, 9);
					break;
				case COVERFLOW_GAMECUBE:
					strncpy(m_plugin.PluginMagicWord, GC_PMAGIC, 9);
					break;
				case COVERFLOW_PLUGIN:
					while(m_plugin.PluginExist(i) && !m_plugin.GetEnabledStatus(i)) { ++i; }
					if(m_plugin.PluginExist(i))
						strncpy(m_plugin.PluginMagicWord, fmt("%08x", m_plugin.GetPluginMagic(i)), 8);
					break;
				default:// wii
					strncpy(m_plugin.PluginMagicWord, WII_PMAGIC, 9);
			}
			if(strlen(m_plugin.PluginMagicWord) == 8)
				fn = m_platform.getString("PLUGINS", m_plugin.PluginMagicWord, "");
		}
		if(fn.length() > 0)
		{
			if(TexHandle.fromImageFile(m_mainCustomBg[curCustBg], fmt("%s/%s/%s.png", m_bckgrndsDir.c_str(), m_themeName.c_str(), fn.c_str())) != TE_OK)
			{	
				if(TexHandle.fromImageFile(m_mainCustomBg[curCustBg], fmt("%s/%s/%s.jpg", m_bckgrndsDir.c_str(), m_themeName.c_str(), fn.c_str())) != TE_OK)
				{
					if(TexHandle.fromImageFile(m_mainCustomBg[curCustBg], fmt("%s/%s.png", m_bckgrndsDir.c_str(), fn.c_str())) != TE_OK)
					{
						if(TexHandle.fromImageFile(m_mainCustomBg[curCustBg], fmt("%s/%s.jpg", m_bckgrndsDir.c_str(), fn.c_str())) != TE_OK)
						{
							curCustBg = loopNum(curCustBg + 1, 2);// reset it
							customBg = false;
							return;
						}
					}
				}
			}
			customBg = true;
		}
		else
		{
			curCustBg = loopNum(curCustBg + 1, 2);// reset it
			customBg = false;
		}
	}
}

void CMenu::_setMainBg()
{
	if(customBg)
		_setBg(m_mainCustomBg[curCustBg], m_mainCustomBg[curCustBg]);
	else
		_setBg(m_mainBg, m_mainBgLQ);
}

void CMenu::_showMain()
{
	_setMainBg();
	if(m_refreshGameList)
		_showCF(m_refreshGameList);
}

void CMenu::_textMain(void)
{
	/* same translation key the PLAY button uses, so they always agree,
	   shown uppercase to match the on-screen hint styling */
	wstringEx play = _t("gm1", L"Play");
	for(u32 i = 0; i < play.size(); ++i)
		play[i] = towupper(play[i]);
	m_btnMgr.setText(m_mainLblPlayHint, play);
}

void CMenu::_showTotalGames(const int numberOfGames)
{
	m_showtimer = 240;
	m_btnMgr.setText(m_mainLblNotice, wfmt(_fmt("main7", L"Total Games: %i"), numberOfGames));
	m_btnMgr.show(m_mainLblNotice);
}

void CMenu::_showCF(bool refreshList)
{
	m_refreshGameList = false;
	_hideMain(true);

	if(refreshList)
	{
		if(!m_vid.showingWaitMessage())
			_showWaitMessage();
		
		/* create gameList based on sources selected */
		_loadList();

		_hideWaitMessage();

		/* if game list is empty display message letting user know */
		wstringEx Msg;
		string Pth;
		if(m_gameList.empty())
		{
			cacheCovers = false;
			switch(m_current_view)
			{
				case COVERFLOW_WII:
					Msg = _t("main2", L"No games found in");
					Pth = sfmt(wii_games_dir, DeviceName[currentPartition]);
					break;
				case COVERFLOW_GAMECUBE:
					Msg = _t("main2", L"No games found in");
					Pth = sfmt(gc_games_dir, DeviceName[currentPartition]);
					break;
				case COVERFLOW_CHANNEL:
					Msg = _t("main3", L"No titles found in");
					Pth = sfmt("%s:/%s/%s", DeviceName[currentPartition],  emu_nands_dir, m_cfg.getString(CHANNEL_DOMAIN, "current_emunand").c_str());
					break;
				case COVERFLOW_HOMEBREW:
					Msg = _t("main4", L"No apps found in");
					Pth = sfmt(HOMEBREW_DIR, DeviceName[currentPartition]);
					break;
				case COVERFLOW_PLUGIN:
					Pth = "";
					if(enabledPluginsCount == 0)
						Msg = _t("main6", L"No plugins selected.");
					else if(enabledPluginsCount > 1)
						Msg = _t("main5", L"No roms/items found.");
					else
					{
						Msg = _t("main2", L"No games found in");
						u8 i = 0;
						while(m_plugin.PluginExist(i) && !m_plugin.GetEnabledStatus(i)){ ++i; }
						int romsPartition = m_plugin.GetRomPartition(i);
						if(romsPartition < 0)
							romsPartition = m_cfg.getInt(PLUGIN_DOMAIN, "partition", 0);
						const char *romDir = m_plugin.GetRomDir(i);
						if(strstr(romDir, "scummvm.ini") != NULL && strchr(romDir, ':') != NULL)
							Pth = sfmt("%s", romDir);
						else
							Pth = sfmt("%s:/%s", DeviceName[romsPartition], m_plugin.GetRomDir(i));
					}
					break;
			}
			Msg.append(wstringEx(' ' + Pth));
			m_btnMgr.setText(m_mainLblMessage, Msg);
			m_btnMgr.show(m_mainLblMessage);
			return;
		}
		
		/* if source menu button set to autoboot */
		if(m_source_autoboot == true)
		{	/* search game list for the requested title */
			bool game_found = false;
			for(vector<dir_discHdr>::iterator element = m_gameList.begin(); element != m_gameList.end(); ++element)
			{
				switch(m_autoboot_hdr.type)
				{
					case TYPE_CHANNEL:
					case TYPE_WII_GAME:
					case TYPE_GC_GAME:
						if(strcmp(m_autoboot_hdr.id, element->id) == 0)
							game_found = true;
						break;
					case TYPE_HOMEBREW:
					case TYPE_PLUGIN:
						if(wcsncmp(m_autoboot_hdr.title, element->title, 63) == 0)
							game_found = true;
						break;
					default:
						break;
				}
				if(game_found == true)
				{
					memcpy(&m_autoboot_hdr, &(*(element)), sizeof(dir_discHdr));
					break;
				}
			}
			/* title found - launch it */
			if(game_found == true) 
			{
				gprintf("Game found, autobooting...\n");
				_launch(&m_autoboot_hdr);
			}
			/* fail */
			m_source_autoboot = false;
		}
		/* Kids UI: the coverflow only ever draws .wfc cache files, so cover art
		   copied onto the SD card by hand stays invisible until it is converted.
		   There is no settings UI left to trigger that, so detect it here: if any
		   game has artwork on the card but no cached texture, convert now. */
		if(!cacheCovers)
		{
			for(vector<dir_discHdr>::iterator it = m_gameList.begin(); it != m_gameList.end(); ++it)
			{
				const char *fn_id = CoverFlow.getFilenameId(&(*it));
				if(fn_id == NULL || fsop_FileExist(fmt("%s/%s.wfc", m_cacheDir.c_str(), fn_id)))
					continue;
				if(fsop_FileExist(getBoxPath(&(*it))) || fsop_FileExist(getFrontPath(&(*it))))
				{
					cacheCovers = true;
					break;
				}
			}
		}
		if(cacheCovers)
		{
			cacheCovers = false;
			{
				m_btnMgr.setProgress(m_downloadPBar, 0.f, true);
				m_btnMgr.setText(m_downloadLblMessage, L"0%");
				m_btnMgr.setText(m_downloadLblDialog, L"");
				m_btnMgr.show(m_downloadPBar);
				m_btnMgr.show(m_downloadLblMessage);
				m_btnMgr.show(m_downloadLblDialog);
			
				_start_pThread();
				_cacheCovers();
				_stop_pThread();
				m_btnMgr.setText(m_downloadLblDialog, _t("dlmsg14", L"Done."));
				u8 pause = 150;
				do
				{
					_mainLoopCommon();
					pause--;
					if(pause == 0)
					{
						m_btnMgr.hide(m_downloadPBar);
						m_btnMgr.hide(m_downloadLblMessage);
						m_btnMgr.hide(m_downloadLblDialog);
					}
				}while(!m_exit && pause > 0);
			}
		}
		/* setup categories and favorites for filtering the game list below */
		if(m_clearCats)// false on boot up and if a source menu button selects a category
		{
			if(m_autoboot_hdr.type == TYPE_PLUGIN && m_cat.hasDomain("PLUGINS"))
			{
				m_cat.remove("PLUGINS", "selected_categories");
				m_cat.remove("PLUGINS", "required_categories");
			}
			else
			{
				// do not clear hidden categories to keep games hidden
				m_cat.remove("GENERAL", "selected_categories");
				m_cat.remove("GENERAL", "required_categories");
			}
		}
		m_clearCats = true;// set to true for next source
		
		/* Kids UI: the favorites toggle is stripped from the UI, so favorites
		   filtering is forced off. A stale favorites=1 in the config would
		   otherwise leave the child staring at an empty coverflow with no
		   button to turn it back off. */
		m_favorites = false;
		m_cfg.setBool(_domainFromView(), "favorites", false);
		m_getFavs = false;
	}
	
	strcpy(cf_domain, "_COVERFLOW");
	if(!m_sourceflow && m_current_view == COVERFLOW_HOMEBREW && m_cfg.getBool(HOMEBREW_DOMAIN, "smallbox", true))
		strcpy(cf_domain, "_SMALLFLOW");
	if(m_sourceflow && m_cfg.getBool(SOURCEFLOW_DOMAIN, "smallbox", true))
		strcpy(cf_domain, "_SMALLFLOW");
	if(m_current_view == COVERFLOW_PLUGIN && !m_sourceflow)
	{
		/* check if homebrew plugin */
		if(enabledPluginsCount == 1 && m_plugin.GetEnabledStatus(HB_PMAGIC) && m_cfg.getBool(HOMEBREW_DOMAIN, "smallbox"))
			strcpy(cf_domain, "_SMALLFLOW");
		else if(enabledPluginsCount > 0 && m_platform.loaded())
		{
			/* get first plugin flow domain */
			u8 i = 0;
			while(m_plugin.PluginExist(i) && !m_plugin.GetEnabledStatus(i)){ ++i; }
			string flow_domain = m_platform.getString("FLOWS", m_platform.getString("PLUGINS", sfmt("%08x", m_plugin.GetPluginMagic(i)), ""), "_COVERFLOW");
			
			/* check if all plugin flow domains match */
			bool match = true;
			i++;
			while(m_plugin.PluginExist(i))
			{
				if(m_plugin.GetEnabledStatus(i) &&
					flow_domain != m_platform.getString("FLOWS", m_platform.getString("PLUGINS", sfmt("%08x", m_plugin.GetPluginMagic(i)), ""), "_COVERFLOW"))
				{
					match = false;
					break;
				}
				i++;
			}

			/* if all match we use that flow domain */
			if(match)
				snprintf(cf_domain, sizeof(cf_domain), "%s", flow_domain.c_str());
		}
	}

	/* get the number of layouts (modes) for the CoverFlow domain */
	m_numCFVersions = min(max(1, m_coverflow.getInt(cf_domain, "number_of_modes", 1)), 15);// max layouts is 15
	
	/* get the current cf layout number and use it to load the data used for that layout */
	_loadCFLayout(min(max(1, _getCFVersion()), (int)m_numCFVersions));
	
	/* filter game list to create the cf cover list and start coverflow coverloader */	
	_initCF();
	
	/* set the covers and titles to the positions and angles based on the cf layout */
	CoverFlow.applySettings();

	gprintf("Displaying covers\n");

	/* display game count if not sourceflow or homebrew */
	if(m_sourceflow || m_current_view == COVERFLOW_HOMEBREW)
		return;

	_showTotalGames(CoverFlow.size());
}

int CMenu::main(void)
{
	wstringEx curLetter;
	string prevTheme = m_themeName;
	m_reload = false;
	CFLocked = m_cfg.getBool("GENERAL", "cf_locked", false);
	/* Kids UI: never fade icons in and out on hover - a child should not have
	   to discover controls by waving the pointer around. */
	Auto_hide_icons = false;

	/* Kids UI: one screen, always. Wii and GameCube games share a single
	   coverflow and the child cannot switch away from it. */
	m_prev_view = 0;
	m_current_view = KIDS_VIEW;
	m_cfg.setUInt("GENERAL", "sources", KIDS_VIEW);
	
	m_catStartPage = m_cfg.getInt("GENERAL", "cat_startpage", 1);
	
	if(m_cfg.getBool("GENERAL", "update_cache", false))
	{
		m_cfg.setBool("GENERAL", "update_cache", false);
		fsop_deleteFolder(m_listCacheDir.c_str());
		fsop_MakeFolder(m_listCacheDir.c_str());
	}
	m_vid.set2DViewport(m_cfg.getInt("GENERAL", "tv_width", 640), m_cfg.getInt("GENERAL", "tv_height", 480),
						m_cfg.getInt("GENERAL", "tv_x", 0), m_cfg.getInt("GENERAL", "tv_y", 0));

	gprintf("Bootup completed!\n");

	_getCustomBgTex();
	_setMainBg();
	_showCF(true);

	if(show_mem)
	{
		m_btnMgr.show(m_mem1FreeSize);
		m_btnMgr.show(m_mem2FreeSize);
	}
	SetupInput(true);

	while(!m_exit)
	{
		/* Main Loop */
		_mainLoopCommon(true);

		if(BTN_HOME_PRESSED)
		{
			/* Kids UI: there is no Home menu any more. HOME just leaves WiiFlow,
			   so the console is never stuck in the loader with no way out. */
			_hideMain();
			exitHandler(m_cfg.getInt("GENERAL", "exit_to", EXIT_TO_MENU));
			break;
		}
		else if(BTN_A_PRESSED)
		{
			if(m_btnMgr.selected(m_mainBtnPrev))// A on prev icon - move back a screen of covers
				CoverFlow.pageUp();
		 	else if(m_btnMgr.selected(m_mainBtnNext))// A on next icon - move forward a screen of covers
				CoverFlow.pageDown();
			else if(!CoverFlow.empty() && CoverFlow.select())
			{
				/* Kids UI: a cover always opens the PLAY/BACK screen */
				_hideMain();
				_game(BTN_B_HELD);
				if(m_exit)
					break;
				_setMainBg();
				if(m_refreshGameList)// if changes were made to parental lock or categories
				{
					m_refreshGameList = false;
					_initCF();
					_showTotalGames(CoverFlow.size());
				}
				else
					CoverFlow.cancel();
			}
		}
		else if(BTN_B_PRESSED)
		{
			// B on next or prev icon - move to next/prev sort item
			if(m_btnMgr.selected(m_mainBtnNext) || m_btnMgr.selected(m_mainBtnPrev))
			{
				const char *domain = _domainFromView();
				int sorting = m_cfg.getInt(domain, "sort", SORT_ALPHA);
				// sorting playcount, lastplayed, and source numbers there is no need for prev or next. playcount maybe.
				// lastplayed time and source numbers will be different for every single game. playcount might be the same.
				// sort gameid not useful for wii and gc. best for the different VC systems.
				if(sorting == SORT_ALPHA || sorting == SORT_PLAYERS || sorting == SORT_WIFIPLAYERS || 
					sorting == SORT_GAMEID || sorting == SORT_YEAR)
				{
					wchar_t c[5] = {0, 0, 0, 0, 0};// long enuff for year
					m_btnMgr.selected(m_mainBtnPrev) ? CoverFlow.prevLetter(c) : CoverFlow.nextLetter(c);
					m_showtimer = 120;
					curLetter.clear();
					curLetter = wstringEx(c);

					if(sorting != SORT_ALPHA && sorting != SORT_YEAR)// #players, #wifiplayers, id = VC type, wiiware, wii, or GC listed as unknown
						curLetter = _getNoticeTranslation(sorting, curLetter);
					m_showtimer = 120;
					m_btnMgr.setText(m_mainLblNotice, curLetter);
					m_btnMgr.show(m_mainLblNotice);
				}
				else
					m_btnMgr.selected(m_mainBtnPrev) ? CoverFlow.pageUp() : CoverFlow.pageDown();
			}
		}
		else if(WROLL_LEFT)
		{
			CoverFlow.left();
		}
		else if(WROLL_RIGHT)
		{
			CoverFlow.right();
		}
		if(!BTN_B_HELD)
		{
			/* move coverflow */
			if(BTN_UP_REPEAT || RIGHT_STICK_UP)
				CoverFlow.up();
			else if(BTN_RIGHT_REPEAT || RIGHT_STICK_RIGHT)
				CoverFlow.right();
			else if(BTN_DOWN_REPEAT ||  RIGHT_STICK_DOWN)
				CoverFlow.down();
			else if(BTN_LEFT_REPEAT || RIGHT_STICK_LEFT)
				CoverFlow.left();
			else if(BTN_MINUS_PRESSED)
				CoverFlow.pageUp();
			else if(BTN_PLUS_PRESSED)
				CoverFlow.pageDown();
				
			/* change coverflow layout/mode */
			else if((BTN_1_PRESSED || BTN_2_PRESSED) && !CFLocked && !CoverFlow.empty())
			{
				u32 curPos = CoverFlow._currentPos();
				s8 direction = BTN_1_PRESSED ? 1 : -1;
				int cfVersion = 1 + loopNum((_getCFVersion() - 1) + direction, m_numCFVersions);
				_setCFVersion(cfVersion);
				_loadCFLayout(cfVersion);
				CoverFlow._setCurPos(curPos);
				CoverFlow.applySettings();
			}
		}
		else // Button B Held
		{
			/* b+down or up = move to previous or next cover in sort order */
			if(!CoverFlow.empty() && (BTN_DOWN_PRESSED || BTN_UP_PRESSED))
			{
				const char *domain = _domainFromView();
				int sorting = m_cfg.getInt(domain, "sort", SORT_ALPHA);
				// sorting playcount, lastplayed, and source numbers there is no need for prev or next. playcount maybe.
				// lastplayed time and source numbers will be different for every single game. playcount might be the same.
				// sort gameid not useful for wii and gc. best for the different VC systems.
				if(sorting == SORT_ALPHA || sorting == SORT_PLAYERS || sorting == SORT_WIFIPLAYERS || 
					sorting == SORT_GAMEID || sorting == SORT_YEAR)
				{
					wchar_t c[5] = {0, 0, 0, 0, 0};// long enuough for year
					BTN_UP_PRESSED ? CoverFlow.prevLetter(c) : CoverFlow.nextLetter(c);
					m_showtimer = 120;
					curLetter.clear();
					curLetter = wstringEx(c);

					if(sorting != SORT_ALPHA  && sorting != SORT_YEAR)// #players, #wifiplayers, id = VC type, wiiware, wii, or GC listed as unknown
						curLetter = _getNoticeTranslation(sorting, curLetter);
					m_showtimer = 120;
					m_btnMgr.setText(m_mainLblNotice, curLetter);
					m_btnMgr.show(m_mainLblNotice);
				}
				else
					BTN_UP_PRESSED ? CoverFlow.pageUp() : CoverFlow.pageDown();
			}
			else if(BTN_LEFT_PRESSED)// b+left = previous song
			{
				MusicPlayer.Previous();
			}
			else if(BTN_RIGHT_PRESSED)// b+right = next song
			{
				MusicPlayer.Next();
			}
			/* b+plus = change sort mode */
			else if(!CoverFlow.empty() && BTN_PLUS_PRESSED && !m_locked && (m_current_view < COVERFLOW_HOMEBREW || m_sourceflow))// homebrew not allowed
			{
				const char *domain = _domainFromView();
				u8 sort = 0;
				if(m_sourceflow)// change sourceflow sort mode
				{
					sort = m_cfg.getInt(SOURCEFLOW_DOMAIN, "sort", SORT_ALPHA);
					if(sort == SORT_ALPHA)
						sort = SORT_BTN_NUMBERS;
					else
						sort = SORT_ALPHA;
					m_cfg.setInt(SOURCEFLOW_DOMAIN, "sort", sort);
				}
				else // change all other coverflow sort mode
				{
					while(true)
					{
						sort = loopNum((m_cfg.getInt(domain, "sort", 0)) + 1, SORT_MAX);
						m_cfg.setInt(domain, "sort", sort);
						if(sort == SORT_GAMEID && m_current_view & COVERFLOW_CHANNEL)
							break;
						if(sort == SORT_WIFIPLAYERS && (m_current_view & COVERFLOW_WII || m_current_view & COVERFLOW_CHANNEL))
							break;
						if(sort != SORT_GAMEID && sort != SORT_WIFIPLAYERS)
							break;
					}
				}
				
				/* set coverflow to new sorting */
				_initCF();
				/* set sort mode text and display it */
				wstringEx curSort;
				if(sort == SORT_ALPHA)
					curSort = m_loc.getWString(m_curLanguage, "alphabetically", L"Alphabetically");
				else if(sort == SORT_PLAYCOUNT)
					curSort = m_loc.getWString(m_curLanguage, "byplaycount", L"By Play Count");
				else if(sort == SORT_LASTPLAYED)
					curSort = m_loc.getWString(m_curLanguage, "bylastplayed", L"By Last Played");
				else if(sort == SORT_GAMEID)
					curSort = m_loc.getWString(m_curLanguage, "bygameid", L"By Game I.D.");
				else if(sort == SORT_WIFIPLAYERS)
					curSort = m_loc.getWString(m_curLanguage, "bywifiplayers", L"By Wifi Players");
				else if(sort == SORT_PLAYERS)
					curSort = m_loc.getWString(m_curLanguage, "byplayers", L"By Players");
				else if(sort == SORT_BTN_NUMBERS)
					curSort = m_loc.getWString(m_curLanguage, "bybtnnumbers", L"By Button Numbers");
				else if(sort == SORT_YEAR)
					curSort = m_loc.getWString(m_curLanguage, "byyear", L"By Year Released");
				m_showtimer = 120;
				m_btnMgr.setText(m_mainLblNotice, curSort);
				m_btnMgr.show(m_mainLblNotice);
			}
			/* b+minus = select random game or boot random game */ 
			else if(BTN_MINUS_PRESSED && !CoverFlow.empty())
			{
				_hideMain();
				srand(time(NULL));
				u16 place = (rand() + rand() + rand()) % CoverFlow.size();
				
				if(m_cfg.getBool("GENERAL", "random_select", false))// random select a game
				{
					CoverFlow.setSelected(place);
					_game(false);
					if(m_exit)
						break;
					if(m_refreshGameList)
					{
						/* if changes were made to favorites, parental lock, or categories */
						_initCF();
						m_refreshGameList = false;
					}
					else
						CoverFlow.cancel();
				}
				else // boot a random game
				{
					gprintf("Lets boot the random game number %u\n", place);
					const dir_discHdr *gameHdr = CoverFlow.getSpecificHdr(place);
					if(gameHdr != NULL)
						_launch(gameHdr);
					_showCF(false);// this shouldn't happen
				}
			}
		}
		/* Hide Notice or Letter if times up */	
		if(m_showtimer > 0)
		{
			if(--m_showtimer == 0)
			{
				m_btnMgr.hide(m_mainLblLetter);
				m_btnMgr.hide(m_mainLblNotice);
			}
		}
		/*zones, showing and hiding buttons */
		if(!m_gameList.empty())
			m_btnMgr.show(m_mainBtnPrev);
		else
			m_btnMgr.hide(m_mainBtnPrev);
			
		if(!m_gameList.empty())
			m_btnMgr.show(m_mainBtnNext);
		else
			m_btnMgr.hide(m_mainBtnNext);
			
		/* Kids UI: the (A) Play hint stays up whenever there is something to
		   play - it teaches the one control the child needs. */
		if(!m_gameList.empty())
		{
			m_btnMgr.show(m_mainLblAGlyph);
			m_btnMgr.show(m_mainLblPlayHint);
		}

		/* Kids UI: no buttons on the main screen at all - just covers. */
		if(!Auto_hide_icons || m_show_zone_main)
		{
			m_btnMgr.show(m_mainLblUser[0]);
			m_btnMgr.show(m_mainLblUser[1]);
		}
		else
		{
			m_btnMgr.hide(m_mainLblUser[0]);
			m_btnMgr.hide(m_mainLblUser[1]);
		}
		for(int chan = WPAD_MAX_WIIMOTES-1; chan >= 0; chan--)
		{
			if(WPadIR_Valid(chan) || (m_show_pointer[chan] && !WPadIR_Valid(chan)))
				CoverFlow.mouse(chan, m_cursor[chan].x(), m_cursor[chan].y());
			else
				CoverFlow.mouse(chan, -1, -1);
		}
	}
	if(m_reload)// rebooting wiiflow (forced in Home Menu or new theme)
	{
		vector<string> arguments = _getMetaXML(fmt("%s/boot.dol", m_appDir.c_str()));
		_launchHomebrew(fmt("%s/boot.dol", m_appDir.c_str()), arguments);
		return 0;
	}
	cleanup();
	//gprintf("Saving configuration files\n");
	m_gcfg1.save(true);// save configs on power off or exit wiiflow
	m_gcfg2.save(true);
	m_cat.save(true);
	m_cfg.save(true);
	return 0;
}

void CMenu::_initMainMenu()
{
	TexData texPrev;
	TexData texPrevS;
	TexData texNext;
	TexData texNextS;
	TexData bgLQ;
	TexData emptyTex;
	//TexData texUser1;

	m_mainBg = _texture("MAIN/BG", "texture", theme.bg, false);
	if(m_theme.loaded() && TexHandle.fromImageFile(bgLQ, fmt("%s/%s", m_themeDataDir.c_str(), m_theme.getString("MAIN/BG", "texture").c_str()), GX_TF_CMPR, 64, 64) == TE_OK)
		m_mainBgLQ = bgLQ;

	TexHandle.fromImageFile(texPrev, fmt("%s/btnprev.png", m_imgsDir.c_str()));
	TexHandle.fromImageFile(texPrevS, fmt("%s/btnprevs.png", m_imgsDir.c_str()));
	TexHandle.fromImageFile(texNext, fmt("%s/btnnext.png", m_imgsDir.c_str()));
	TexHandle.fromImageFile(texNextS, fmt("%s/btnnexts.png", m_imgsDir.c_str()));
	//TexHandle.fromImageFile(texUser1, fmt("%s/mainUser1.png", m_imgsDir.c_str()));

	_addUserLabels(m_mainLblUser, ARRAY_SIZE(m_mainLblUser), "MAIN");

	/* Kids UI: (A) Play hint, centred under the coverflow. The glyph is
	   compiled into the dol so no extra file has to reach the SD card. */
	TexData texAButton;
	TexHandle.fromPNG(texAButton, a_button_png);
	m_mainLblAGlyph = _addLabel("MAIN/A_GLYPH", theme.btnFont, L"", 398, 396, 52, 52, CColor(0xFFFFFFFF), 0, texAButton);
	m_mainLblPlayHint = _addLabel("MAIN/PLAY_HINT", theme.btnFont, L"", 458, 396, 170, 52, CColor(0xFFFFFFFF), FTGX_JUSTIFY_LEFT | FTGX_ALIGN_MIDDLE);

	m_mainBtnNext = _addPicButton("MAIN/NEXT_BTN", texNext, texNextS, 540, 146, 80, 80);
	m_mainBtnPrev = _addPicButton("MAIN/PREV_BTN", texPrev, texPrevS, 20, 146, 80, 80);

	m_mainLblMessage = _addLabel("MAIN/MESSAGE", theme.lblFont, L"", 40, 40, 560, 140, theme.lblFontColor, FTGX_JUSTIFY_LEFT | FTGX_ALIGN_MIDDLE);
	m_mainLblLetter = _addLabel("MAIN/LETTER", theme.titleFont, L"", 540, 40, 80, 80, theme.titleFontColor, FTGX_JUSTIFY_CENTER | FTGX_ALIGN_MIDDLE, emptyTex);
	m_mainLblNotice = _addLabel("MAIN/NOTICE", theme.txtFont, L"", 340, 40, 280, 80, theme.titleFontColor, FTGX_JUSTIFY_RIGHT | FTGX_ALIGN_MIDDLE);
	m_mainLblCurMusic = _addLabel("MAIN/MUSIC", theme.txtFont, L"", 0, 10, 640, 32, theme.txtFontColor, FTGX_JUSTIFY_CENTER | FTGX_ALIGN_MIDDLE, theme.btnTexC);

	m_mem1FreeSize = _addLabel("MEM1", theme.btnFont, L"", 40, 300, 480, 56, theme.btnFontColor, FTGX_JUSTIFY_LEFT, emptyTex);
	m_mem2FreeSize = _addLabel("MEM2", theme.btnFont, L"", 40, 356, 480, 56, theme.btnFontColor, FTGX_JUSTIFY_LEFT, emptyTex);
	// 
	m_mainPrevZone.x = m_theme.getInt("MAIN/ZONES", "prev_x", -32);
	m_mainPrevZone.y = m_theme.getInt("MAIN/ZONES", "prev_y", -32);
	m_mainPrevZone.w = m_theme.getInt("MAIN/ZONES", "prev_w", 182);
	m_mainPrevZone.h = m_theme.getInt("MAIN/ZONES", "prev_h", 382);
	m_mainPrevZone.hide = m_theme.getBool("MAIN/ZONES", "prev_hide", true);
	
	m_mainNextZone.x = m_theme.getInt("MAIN/ZONES", "next_x", 490);
	m_mainNextZone.y = m_theme.getInt("MAIN/ZONES", "next_y", -32);
	m_mainNextZone.w = m_theme.getInt("MAIN/ZONES", "next_w", 182);
	m_mainNextZone.h = m_theme.getInt("MAIN/ZONES", "next_h", 382);
	m_mainNextZone.hide = m_theme.getBool("MAIN/ZONES", "next_hide", true);
	
	m_mainButtonsZone.x = m_theme.getInt("MAIN/ZONES", "buttons_x", -32);
	m_mainButtonsZone.y = m_theme.getInt("MAIN/ZONES", "buttons_y", 350);
	m_mainButtonsZone.w = m_theme.getInt("MAIN/ZONES", "buttons_w", 704);
	m_mainButtonsZone.h = m_theme.getInt("MAIN/ZONES", "buttons_h", 162);
	m_mainButtonsZone.hide = m_theme.getBool("MAIN/ZONES", "buttons_hide", true);

	m_mainButtonsZone2.x = m_theme.getInt("MAIN/ZONES", "buttons2_x", -32);
	m_mainButtonsZone2.y = m_theme.getInt("MAIN/ZONES", "buttons2_y", 350);
	m_mainButtonsZone2.w = m_theme.getInt("MAIN/ZONES", "buttons2_w", 704);
	m_mainButtonsZone2.h = m_theme.getInt("MAIN/ZONES", "buttons2_h", 162);
	m_mainButtonsZone2.hide = m_theme.getBool("MAIN/ZONES", "buttons2_hide", true);
	
	m_mainButtonsZone3.x = m_theme.getInt("MAIN/ZONES", "buttons3_x", -32);
	m_mainButtonsZone3.y = m_theme.getInt("MAIN/ZONES", "buttons3_y", 350);
	m_mainButtonsZone3.w = m_theme.getInt("MAIN/ZONES", "buttons3_w", 704);
	m_mainButtonsZone3.h = m_theme.getInt("MAIN/ZONES", "buttons3_h", 162);
	m_mainButtonsZone3.hide = m_theme.getBool("MAIN/ZONES", "buttons3_hide", true);
	//
	_setHideAnim(m_mainBtnNext, "MAIN/NEXT_BTN", 0, 0, 0.f, 0.f);
	_setHideAnim(m_mainBtnPrev, "MAIN/PREV_BTN", 0, 0, 0.f, 0.f);
	_setHideAnim(m_mainLblAGlyph, "MAIN/A_GLYPH", 0, 40, 0.f, 0.f);
	_setHideAnim(m_mainLblPlayHint, "MAIN/PLAY_HINT", 0, 40, 0.f, 0.f);
	_setHideAnim(m_mainLblMessage, "MAIN/MESSAGE", 0, 0, 0.f, 0.f);
	_setHideAnim(m_mainLblLetter, "MAIN/LETTER", 0, 0, 0.f, 0.f);
	_setHideAnim(m_mainLblNotice, "MAIN/NOTICE", 0, 0, 0.f, 0.f);
	_setHideAnim(m_mainLblCurMusic, "MAIN/MUSIC", 0, -100, 0.f, 0.f);
//#ifdef SHOWMEM
	_setHideAnim(m_mem1FreeSize, "MEM1", 0, 0, 0.f, 0.f);
	_setHideAnim(m_mem2FreeSize, "MEM2", 0, 0, 0.f, 0.f);
//#endif
	_textMain();
	_hideMain(true);
}

wstringEx CMenu::_getNoticeTranslation(int sorting, wstringEx curLetter)
{
	if(sorting == SORT_PLAYERS)
		curLetter += m_loc.getWString(m_curLanguage, "players", L" Players");
	else if(sorting == SORT_WIFIPLAYERS)
		curLetter += m_loc.getWString(m_curLanguage, "wifiplayers", L" Wifi Players");
	else if(sorting == SORT_GAMEID)
	{
		switch(curLetter[0])
		{
			case L'C':
			{
				if(m_current_view != COVERFLOW_CHANNEL)
					curLetter = m_loc.getWString(m_curLanguage, "custom", L"Custom");
				else
					curLetter = m_loc.getWString(m_curLanguage, "commodore", L"Commodore 64");
				break;
			}
			case L'E':
			{
				curLetter = m_loc.getWString(m_curLanguage, "neogeo", L"Neo-Geo");
				break;
			}
			case L'F':
			{
				curLetter = m_loc.getWString(m_curLanguage, "nes", L"Nintendo");
				break;
			}
			case L'J':
			{
				curLetter = m_loc.getWString(m_curLanguage, "snes", L"Super Nintendo");
				break;
			}
			case L'L':
			{
				curLetter = m_loc.getWString(m_curLanguage, "mastersystem", L"Sega Master System");
				break;
			}
			case L'M':
			{
				curLetter = m_loc.getWString(m_curLanguage, "genesis", L"Sega Genesis");
				break;
			}
			case L'N':
			{
				curLetter = m_loc.getWString(m_curLanguage, "nintendo64", L"Nintendo64");
				break;
			}
			case L'P':
			{
				curLetter = m_loc.getWString(m_curLanguage, "turbografx16", L"TurboGrafx-16");
				break;
			}
			case L'Q':
			{
				curLetter = m_loc.getWString(m_curLanguage, "turbografxcd", L"TurboGrafx-CD");
				break;
			}
			case L'W':
			{
				curLetter = m_loc.getWString(m_curLanguage, "wiiware", L"WiiWare");
				break;
			}
			case L'H':
			{
				curLetter = m_loc.getWString(m_curLanguage, "wiichannels", L"Offical Wii Channels");
				break;
			}
			case L'R':
			case L'S':
			{
				curLetter = m_loc.getWString(m_curLanguage, "wii", L"Wii");
				break;
			}
			case L'D':
			{
				curLetter = m_loc.getWString(m_curLanguage, "homebrew", L"Homebrew");
				break;
			}
			default:
			{
				curLetter = m_loc.getWString(m_curLanguage, "unknown", L"Unknown");
				break;
			}
		}
	}
	
	return curLetter;
}

void CMenu::exitHandler(int ExitTo)
{
	m_exit = true;
	if(ExitTo == EXIT_TO_BOOTMII) //Bootmii, check that the files are there, or ios will hang.
	{
		struct stat dummy;
		if(!DeviceHandle.IsInserted(SD) || stat("sd:/bootmii/armboot.bin", &dummy) != 0 || stat("sd:/bootmii/ppcboot.elf", &dummy) != 0)
			ExitTo = EXIT_TO_HBC;
	}
	if(ExitTo != WIIFLOW_DEF)// if not using wiiflows exit option then go ahead and set the exit to
		Sys_ExitTo(ExitTo);
}

int CMenu::_getCFVersion()
{
	if(m_current_view == COVERFLOW_PLUGIN)
	{
		int first = 0;
		for(u8 i = 0; m_plugin.PluginExist(i); ++i)
		{
			if(m_plugin.GetEnabledStatus(i))
			{
				string magic = sfmt("%08x", m_plugin.GetPluginMagic(i));
				if(m_cfg.has("PLUGIN_CFVERSION", magic))
				{
					if(first > 0 && m_cfg.getInt("PLUGIN_CFVERSION", magic, 1) != first)
						return m_cfg.getInt(_domainFromView(), "last_cf_mode", 1);
					else if(first == 0)	
						first = m_cfg.getInt("PLUGIN_CFVERSION", magic, 1);
				}
			}
		}
		if(first == 0)
			first++;
		return first;
	}
	return m_cfg.getInt(_domainFromView(), "last_cf_mode", 1);
}

void CMenu::_setCFVersion(int version)
{
	if(m_current_view == COVERFLOW_PLUGIN)
	{
		int first = 0;
		for(u8 i = 0; m_plugin.PluginExist(i); ++i)
		{
			if(m_plugin.GetEnabledStatus(i))
			{
				string magic = sfmt("%08x", m_plugin.GetPluginMagic(i));
				if(m_cfg.has("PLUGIN_CFVERSION", magic))
				{
					if(first > 0 && m_cfg.getInt("PLUGIN_CFVERSION", magic, 1) != first)
					{
						m_cfg.setInt(_domainFromView(), "last_cf_mode", version);
						return;
					}
					else if(first == 0)	
						first = m_cfg.getInt("PLUGIN_CFVERSION", magic, 1);
				}
			}
		}
		for(u8 i = 0; m_plugin.PluginExist(i); ++i)
		{
			if(m_plugin.GetEnabledStatus(i))
				m_cfg.setInt("PLUGIN_CFVERSION", sfmt("%08x", m_plugin.GetPluginMagic(i)), version);
		}
	}
	else
		m_cfg.setInt(_domainFromView(), "last_cf_mode", version);
}
