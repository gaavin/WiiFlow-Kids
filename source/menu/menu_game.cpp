
#include "menu.hpp"
#include "banner/BannerWindow.hpp"
#include "gc/gcdisc.hpp"
#include "gui/WiiMovie.hpp"

//sounds
extern const u8 gc_ogg[];
extern const u32 gc_ogg_size;

extern const u8 a_button_png[];
extern const u8 b_button_png[];

bool m_zoom_banner = false;
bool m_banner_loaded = false;
s16 m_gameBtnPlayFull;
s16 m_gameBtnBackFull;
s16 m_gameLblSnapBg;
s16 m_gameLblSnapFrame;
s16 m_gameLblBannerFrame;

static inline int loopNum(int i, int s)
{
	return (i + s) % s;
}

void CMenu::_extractBnr(const dir_discHdr *hdr)
{
	u32 size = 0;
	DeviceHandle.OpenWBFS(currentPartition);
	wbfs_disc_t *disc = WBFS_OpenDisc((u8 *) &hdr->id, (char *) hdr->path);
	if(disc != NULL)
	{
		void *bnr = NULL;
		size = wbfs_extract_file(disc, (char*)"opening.bnr", &bnr);
		if(size > 0)
			CurrentBanner.SetBanner((u8*)bnr, size, false, true);
		WBFS_CloseDisc(disc);
	}
	WBFS_Close();
}

void CMenu::_setCurrentItem(const dir_discHdr *hdr)
{
	m_cfg.setString(_domainFromView(), "current_item", CoverFlow.getFilenameId(hdr));
}

void CMenu::_hideGame(bool instant)
{
	_cleanupVideo();
	m_fa.unload();
	CoverFlow.showCover();

	m_btnMgr.hide(m_gameBtnPlay, instant);
	m_btnMgr.hide(m_gameBtnBack, instant);
	m_btnMgr.hide(m_gameLblAGlyph, instant);
	m_btnMgr.hide(m_gameLblBGlyph, instant);
	m_btnMgr.hide(m_gameBtnPlayFull, instant);
	m_btnMgr.hide(m_gameBtnBackFull, instant);
	m_btnMgr.hide(m_gameLblSnapBg, instant);
	m_btnMgr.hide(m_gameLblSnap, instant);
	m_btnMgr.hide(m_gameLblOverlay, instant);
	m_btnMgr.hide(m_gameLblSnapFrame, instant);
	m_btnMgr.hide(m_gameLblBannerFrame, instant);
	for(u8 i = 0; i < ARRAY_SIZE(m_gameLblUser); ++i)
		if(m_gameLblUser[i] != -1)
			m_btnMgr.hide(m_gameLblUser[i], instant);
}

void CMenu::_showGame(void)
{
	const dir_discHdr *GameHdr = CoverFlow.getHdr();
	const char *FanartPath = NULL;
	
	FanartPath = fmt("%s", m_fanartDir.c_str());

	/* Load fanart config if available */
	if(m_fa.load(m_cfg, FanartPath, GameHdr))
	{
		const TexData *bg = NULL;
		const TexData *bglq = NULL;
		m_fa.getBackground(bg, bglq);
		_setBg(*bg, *bglq);
		CoverFlow.hideCover();
	}
	else // no fanart config so we show the cover and game menu background
	{
		CoverFlow.showCover();		
		if(customBg)
			_setBg(m_mainCustomBg[curCustBg], m_mainCustomBg[curCustBg]);
		else
			_setBg(m_gameBg, m_gameBgLQ);
	}
}

void CMenu::_cleanupBanner(bool gamechange)
{
	//banner
	m_gameSound.FreeMemory();
	_stopGameSoundThread();// stop banner and gamesound loading
	m_banner.DeleteBanner(gamechange);
	//movie
	_cleanupVideo();
}

void CMenu::_cleanupVideo()
{
	m_video_playing = false;
	movie.DeInit();
}

bool CMenu::_startVideo()
{
	const dir_discHdr *GameHdr = CoverFlow.getHdr();
	const char *videoPath = NULL;
	const char *THP_Path = NULL;
	
	videoPath = fmt("%s/%s.3", m_videoDir.c_str(), GameHdr->id);
	THP_Path = fmt("%s.thp", videoPath);
	if(!fsop_FileExist(THP_Path))
	{
		videoPath = fmt("%s/%s", m_videoDir.c_str(), GameHdr->id);
		THP_Path = fmt("%s.thp", videoPath);
	}
	if(fsop_FileExist(THP_Path))
	{
		m_gameSound.FreeMemory();
		_stopGameSoundThread();
		m_banner.SetShowBanner(false);
		/* Lets play the movie */
		movie.Init(THP_Path);
		m_gameSound.Load(fmt("%s.ogg", videoPath));
		m_gameSound.SetVolume(m_cfg.getInt("GENERAL", "sound_volume_bnr", 255));
		m_video_playing = true;
		m_gameSound.Play();
		movie.Play(true); //video loops sound doesnt
		return true;
	}
	return false;
}

void CMenu::_game(bool launch)
{
	m_banner_loaded = false;

	dir_discHdr *hdr = (dir_discHdr*)MEM2_alloc(sizeof(dir_discHdr));
	memcpy(hdr, CoverFlow.getHdr(), sizeof(dir_discHdr));
	_setCurrentItem(hdr);
	
	char gcfg1Key[16];
	memset(gcfg1Key, 0, sizeof(gcfg1Key));
	strcpy(gcfg1Key, hdr->id);

	m_zoom_banner = m_cfg.getBool(_domainFromView(), "show_full_banner", false);

	if(m_banner.GetZoomSetting() != m_zoom_banner)
		m_banner.ToggleZoom();

	if(m_banner.GetInGameSettings())
		m_banner.ToggleGameSettings();
	m_gameSelected = true;
	s8 startGameSound = -7;
	SetupInput();

	while(!m_exit)
	{
		if(m_fa.isLoaded() && m_fa.isAnimationComplete())
		{
			if(m_fa.noLoop())
			{
				m_fa.unload();
				CoverFlow.showCover();
				if(customBg)
					_setBg(m_mainCustomBg[curCustBg], m_mainCustomBg[curCustBg]);
				else
					_setBg(m_gameBg, m_gameBgLQ);
			}
			else //loop fanart
				m_fa.reset();
		}
		if(startGameSound < 1)
			startGameSound++;

		if(startGameSound == -5)
			_showGame();// this also starts fanart with unloading previous fanart.
			
		if(!launch)	
			_mainLoopCommon(true);
			
		if(startGameSound == 0)
		{
			startGameSound = 1;
			_playGameSound();
		}
		/* exit game menu */
		if(BTN_HOME_PRESSED)
		{
			_cleanupBanner();// also cleans up trailer movie including trailer sound
			break;
		}
		else if(BTN_B_PRESSED)
		{
			_cleanupBanner();
			break;
		}
		/* Kids UI: d-pad steps between PLAY and BACK. CButtonsMgr::up/down
		   already do this and bail out while the pointer is live, so aiming the
		   wiimote at the screen still takes priority. */
		else if(BTN_UP_PRESSED || BTN_DOWN_PRESSED)
		{
			if(BTN_UP_PRESSED)
				m_btnMgr.up();
			else
				m_btnMgr.down();
		}
		/* play or stop a trailer video */
		else if(BTN_MINUS_PRESSED)
		{
			if(m_video_playing)
			{
				m_video_playing = false;
				movie.DeInit();
				m_gameSound.FreeMemory();
				m_banner.SetShowBanner(true);
				if(!m_gameSound.IsPlaying()) 
					startGameSound = -6;
			}
			else
				_startVideo();
		}
		else if(launch || BTN_A_PRESSED)
		{
			if(m_fa.isLoaded() && ShowPointer())// stop and unload fanart
			{
				m_fa.unload();
				CoverFlow.showCover();
				if(customBg)
					_setBg(m_mainCustomBg[curCustBg], m_mainCustomBg[curCustBg]);
				else
					_setBg(m_gameBg, m_gameBgLQ);
				continue;
			}
			else if(m_btnMgr.selected(m_gameBtnBack) || m_btnMgr.selected(m_gameBtnBackFull))
			{
				_cleanupBanner();
				break;
			}
			else if(launch || m_btnMgr.selected(m_gameBtnPlay) || m_btnMgr.selected(m_gameBtnPlayFull) || 
					(!ShowPointer() && !m_video_playing))
			{
				_hideGame();
				if(isWiiVC && (hdr->type == TYPE_WII_GAME || hdr->type == TYPE_EMUCHANNEL))
				{
					_error(_t("errgame19", L"Can't launch in Wii virtual console mode!"));
					launch = false;
					_showGame();
				}
				else
				{
					_cleanupBanner();
					_launch(hdr);

					if(m_exit)
						break;

					_hideWaitMessage();
					launch = false;

					for(int chan = WPAD_MAX_WIIMOTES-1; chan >= 0; chan--)
						WPAD_SetVRes(chan, m_vid.width() + m_cursor[chan].width(), m_vid.height() + m_cursor[chan].height());
					m_gcfg2.unload();
					_showGame();
				}
			}
		}
		/* Kids UI: once a game is chosen the selection is frozen. The d-pad and
		   stick no longer walk the coverflow underneath, so the only way out of
		   this screen is B (back) or A (play). Removing this also removes the
		   only writer of startGameSound == -10. */

		if(!m_fa.isLoaded() && !m_video_playing)
		{
			if(m_banner_loaded && !m_soundThrdBusy && m_zoom_banner)
			{
				m_btnMgr.show(m_gameBtnPlayFull);
				m_btnMgr.show(m_gameBtnBackFull);
				
				m_btnMgr.hide(m_gameLblSnapBg, true);
				m_btnMgr.hide(m_gameLblSnap, true);
				m_btnMgr.hide(m_gameLblOverlay, true);
				m_btnMgr.hide(m_gameLblSnapFrame, true);
				m_btnMgr.hide(m_gameLblBannerFrame, true);
				
				m_btnMgr.hide(m_gameBtnPlay);
				m_btnMgr.hide(m_gameBtnBack);
				m_btnMgr.hide(m_gameLblAGlyph);
				m_btnMgr.hide(m_gameLblBGlyph);
				for(u8 i = 0; i < ARRAY_SIZE(m_gameLblUser); ++i)
					if(m_gameLblUser[i] != -1)
						m_btnMgr.hide(m_gameLblUser[i]);
			}
			else
			{
				if(!m_soundThrdBusy)// Kids UI: PLAY/BACK are always on screen
				{
					m_btnMgr.show(m_gameBtnPlay);
					m_btnMgr.show(m_gameBtnBack);
					m_btnMgr.show(m_gameLblAGlyph);
					m_btnMgr.show(m_gameLblBGlyph);
					for(u8 i = 0; i < ARRAY_SIZE(m_gameLblUser); ++i)
						if(m_gameLblUser[i] != -1)
							m_btnMgr.show(m_gameLblUser[i]);
				}
				else if(!m_soundThrdBusy)
				{
					m_btnMgr.hide(m_gameBtnPlay);
					m_btnMgr.hide(m_gameBtnBack);
					m_btnMgr.hide(m_gameLblAGlyph);
					m_btnMgr.hide(m_gameLblBGlyph);
					for(u8 i = 0; i < ARRAY_SIZE(m_gameLblUser); ++i)
						if (m_gameLblUser[i] != -1)
							m_btnMgr.hide(m_gameLblUser[i]);
				}
				if(m_banner_loaded && !m_soundThrdBusy && !m_zoom_banner)
				{
					m_btnMgr.hide(m_gameBtnPlayFull);
					m_btnMgr.hide(m_gameBtnBackFull);
					
					m_btnMgr.hide(m_gameLblSnapBg, true);
					m_btnMgr.hide(m_gameLblSnap, true);
					m_btnMgr.hide(m_gameLblOverlay, true);
					m_btnMgr.hide(m_gameLblSnapFrame, true);
					
					m_btnMgr.show(m_gameLblBannerFrame);
				}
				if(m_snapshot_loaded && !m_soundThrdBusy)
				{
					m_btnMgr.hide(m_gameBtnPlayFull);
					m_btnMgr.hide(m_gameBtnBackFull);
					m_btnMgr.hide(m_gameLblBannerFrame);
					
					m_btnMgr.show(m_gameLblSnapBg);
					m_btnMgr.show(m_gameLblSnap);
					m_btnMgr.show(m_gameLblOverlay);
					m_btnMgr.show(m_gameLblSnapFrame);
				}
				if(!m_banner_loaded && !m_snapshot_loaded && !m_soundThrdBusy)
				{
					m_btnMgr.hide(m_gameBtnPlayFull);
					m_btnMgr.hide(m_gameBtnBackFull);
					m_btnMgr.hide(m_gameLblSnapBg);
					m_btnMgr.hide(m_gameLblSnap);
					m_btnMgr.hide(m_gameLblOverlay);
					m_btnMgr.hide(m_gameLblSnapFrame);
					m_btnMgr.hide(m_gameLblBannerFrame);
				}
				
			}
		}
		else
		{
			m_btnMgr.hide(m_gameLblSnapFrame);
			m_btnMgr.hide(m_gameLblBannerFrame);
			m_btnMgr.hide(m_gameLblSnapBg);
			m_btnMgr.hide(m_gameLblSnap);
			m_btnMgr.hide(m_gameLblOverlay);
			m_btnMgr.hide(m_gameBtnPlayFull);
			m_btnMgr.hide(m_gameBtnBackFull);
			m_btnMgr.hide(m_gameBtnPlay);
			m_btnMgr.hide(m_gameBtnBack);
			m_btnMgr.hide(m_gameLblAGlyph);
			m_btnMgr.hide(m_gameLblBGlyph);
			
			for(u8 i = 0; i < ARRAY_SIZE(m_gameLblUser); ++i)
				if(m_gameLblUser[i] != -1)
					m_btnMgr.hide(m_gameLblUser[i]);
		}
	}
	m_snapshot_loaded = false;
	TexData emptyTex;
	m_btnMgr.setTexture(m_gameLblSnap, emptyTex);
	m_btnMgr.setTexture(m_gameLblOverlay, emptyTex);
	TexHandle.Cleanup(m_game_snap);
	TexHandle.Cleanup(m_game_overlay);
	m_gameSelected = false;
	MEM2_free(hdr);
	_hideGame();
}

void CMenu::_initGameMenu()
{
	//CColor fontColor(0xD0BFDFFF);
	TexData texSnapShotBg;
	TexData texSnapShotFrame;
	TexData texBannerFrame;
	TexData bgLQ;

	TexHandle.fromImageFile(texSnapShotBg, fmt("%s/blank.png", m_imgsDir.c_str()));
	TexHandle.fromImageFile(texSnapShotFrame, fmt("%s/blank.png", m_imgsDir.c_str()));
	TexHandle.fromImageFile(texBannerFrame, fmt("%s/blank.png", m_imgsDir.c_str()));

	_addUserLabels(m_gameLblUser, ARRAY_SIZE(m_gameLblUser), "GAME");
	m_gameBg = _texture("GAME/BG", "texture", theme.bg, false);
	if(m_theme.loaded() && TexHandle.fromImageFile(bgLQ, fmt("%s/%s", m_themeDataDir.c_str(), m_theme.getString("GAME/BG", "texture").c_str()), GX_TF_CMPR, 64, 64) == TE_OK)
		m_gameBgLQ = bgLQ;

	/* Kids UI: PLAY stacked tight over BACK on the right, large enough
	   for small hands but with only an 8px gap so the pair reads as one
	   control cluster rather than two distant buttons. A and B glyphs sit
	   on the left of each capsule so the child can match the remote. */
	m_gameBtnPlay = _addButton("GAME/PLAY_BTN", theme.btnFont, L"", 404, 336, 212, 56, theme.btnFontColor);
	m_gameBtnBack = _addButton("GAME/BACK_BTN", theme.btnFont, L"", 404, 400, 212, 56, theme.btnFontColor);
	TexData texAButton;
	TexData texBButton;
	TexHandle.fromPNG(texAButton, a_button_png);
	TexHandle.fromPNG(texBButton, b_button_png);
	m_gameLblAGlyph = _addLabel("GAME/A_GLYPH", theme.btnFont, L"", 412, 344, 40, 40, CColor(0xFFFFFFFF), 0, texAButton);
	m_gameLblBGlyph = _addLabel("GAME/B_GLYPH", theme.btnFont, L"", 412, 408, 40, 40, CColor(0xFFFFFFFF), 0, texBButton);
	m_gameBtnBackFull = _addButton("GAME/BACK_FULL_BTN", theme.btnFont, L"", 118, 404, 190, 52, theme.btnFontColor);
	m_gameBtnPlayFull = _addButton("GAME/PLAY_FULL_BTN", theme.btnFont, L"", 328, 404, 190, 52, theme.btnFontColor);
	m_gameLblSnapBg = _addLabel("GAME/SNAP_BG", theme.txtFont, L"", 385, 31, 246, 170, theme.txtFontColor, 0, texSnapShotBg);
	m_gameLblSnap = _addLabel("GAME/SNAP", theme.txtFont, L"", 385, 31, 100, 100, theme.txtFontColor, 0, m_game_snap);
	m_gameLblOverlay = _addLabel("GAME/OVERLAY", theme.txtFont, L"", 385, 31, 100, 100, theme.txtFontColor, 0, m_game_overlay);
	// 8 pixel width frames
	m_gameLblSnapFrame = _addLabel("GAME/SNAP_FRAME", theme.txtFont, L"", 377, 23, 262, 186, theme.txtFontColor, 0, texSnapShotFrame);
	m_gameLblBannerFrame = _addLabel("GAME/BANNER_FRAME", theme.txtFont, L"", 377, 23, 262, 151, theme.txtFontColor, 0, texBannerFrame);

	m_gameButtonsZone.x = m_theme.getInt("GAME/ZONES", "buttons_x", 380);
	m_gameButtonsZone.y = m_theme.getInt("GAME/ZONES", "buttons_y", 0);
	m_gameButtonsZone.w = m_theme.getInt("GAME/ZONES", "buttons_w", 640);
	m_gameButtonsZone.h = m_theme.getInt("GAME/ZONES", "buttons_h", 480);
	m_gameButtonsZone.hide = m_theme.getBool("GAME/ZONES", "buttons_hide", true);

	_setHideAnim(m_gameBtnPlay, "GAME/PLAY_BTN", 0, 0, 1.f, -1.f);
	_setHideAnim(m_gameBtnBack, "GAME/BACK_BTN", 0, 0, 1.f, -1.f);
	_setHideAnim(m_gameLblAGlyph, "GAME/A_GLYPH", 0, 0, 1.f, -1.f);
	_setHideAnim(m_gameLblBGlyph, "GAME/B_GLYPH", 0, 0, 1.f, -1.f);
	_setHideAnim(m_gameBtnPlayFull, "GAME/PLAY_FULL_BTN", 0, 0, 1.f, 0.f);
	_setHideAnim(m_gameBtnBackFull, "GAME/BACK_FULL_BTN", 0, 0, 1.f, 0.f);
	_setHideAnim(m_gameLblSnapBg, "GAME/SNAP_BG", 0, 0, 1.f, 1.f);
	_setHideAnim(m_gameLblSnap, "GAME/SNAP", 0, 0, 1.f, 1.f);
	_setHideAnim(m_gameLblOverlay, "GAME/OVERLAY", 0, 0, 1.f, 1.f);
	_setHideAnim(m_gameLblSnapFrame, "GAME/SNAP_FRAME", 0, 0, 1.f, 1.f);
	_setHideAnim(m_gameLblBannerFrame, "GAME/BANNER_FRAME", 0, 0, 1.f, 1.f);
	
	_hideGame(true);
	_textGame();
	snapbg_x = m_theme.getInt("GAME/SNAP_BG", "x", 385);
	snapbg_y = m_theme.getInt("GAME/SNAP_BG", "y", 31);
	snapbg_w = m_theme.getInt("GAME/SNAP_BG", "width", 246);
	snapbg_h = m_theme.getInt("GAME/SNAP_BG", "height", 170);
	
	/* gc disc prompt menu */
	m_promptBg = _texture("PROMPT/BG", "texture", theme.bg, false);
	m_promptLblQuestion = _addLabel("PROMPT/QUESTION", theme.lblFont, L"", 112, 0, 500, 420, theme.lblFontColor, FTGX_JUSTIFY_LEFT | FTGX_ALIGN_MIDDLE);
	m_promptBtnChoice1 = _addButton("PROMPT/CHOICE1", theme.btnFont, L"", 112, 320, 200, 48, theme.btnFontColor);
	m_promptBtnChoice2 = _addButton("PROMPT/CHOICE2", theme.btnFont, L"", 332, 320, 200, 48, theme.btnFontColor);
	
	_setHideAnim(m_promptLblQuestion, "PROMPT/QUESTION", 0, 0, 0.f, 0.f);
	_setHideAnim(m_promptBtnChoice1, "PROMPT/CHOICE1", 0, 0, 1.f, -1.f);
	_setHideAnim(m_promptBtnChoice2, "PROMPT/CHOICE2", 0, 0, 1.f, -1.f);
	
	m_btnMgr.hide(m_promptLblQuestion, true);
	m_btnMgr.hide(m_promptBtnChoice1, true);
	m_btnMgr.hide(m_promptBtnChoice2, true);
}

void CMenu::_textGame(void)
{
	m_btnMgr.setText(m_gameBtnPlay, _t("gm1", L"Play"));
	m_btnMgr.setText(m_gameBtnBack, _t("gm2", L"Back"));
	m_btnMgr.setText(m_gameBtnPlayFull, _t("gm1", L"Play"));
	m_btnMgr.setText(m_gameBtnBackFull, _t("gm2", L"Back"));
}

struct IMD5Header
{
	u32 fcc;
	u32 filesize;
	u8 zeroes[8];
	u8 crypto[16];
} ATTRIBUTE_PACKED;

// loads game banner and sound to be played by mainloop
void * CMenu::_gameSoundThread(void *obj)
{
	CMenu *m = (CMenu*)obj;
	m->m_soundThrdBusy = true;
	m->m_gamesound_changed = false;
	m->m_snapshot_loaded = false;
	m_banner_loaded = false;

	CurrentBanner.ClearBanner();//clear current banner from memory

	/* Set to empty textures to clear current snapshot from screen */
	TexData emptyTex;
	m_btnMgr.setTexture(m->m_gameLblSnap, emptyTex);
	m_btnMgr.setTexture(m->m_gameLblOverlay, emptyTex);

	u8 *custom_bnr_file = NULL;
	u32 custom_bnr_size = 0;
	char custom_banner[256];
	custom_banner[255] = '\0';

	u8 *cached_bnr_file = NULL;
	u32 cached_bnr_size = 0;
	char cached_banner[256];
	cached_banner[255] = '\0';
	
	const dir_discHdr *GameHdr = CoverFlow.getHdr();
	
	/* try to get custom banner for wii, gc, and channels */
	/* check custom ID6 first */
	strncpy(custom_banner, fmt("%s/%s.bnr", m->m_customBnrDir.c_str(), GameHdr->id), 255);
	fsop_GetFileSizeBytes(custom_banner, &custom_bnr_size);
	if(custom_bnr_size > 0)
	{
		custom_bnr_file = (u8*)MEM2_lo_alloc(custom_bnr_size);
		if(custom_bnr_file != NULL)
		{
			fsop_ReadFileLoc(custom_banner, custom_bnr_size, (void*)custom_bnr_file);
			m_banner_loaded = true;
		}
	}
	else /* no custom ID6 or too big, try ID3 */
	{
		strncpy(custom_banner, fmt("%s/%.3s.bnr", m->m_customBnrDir.c_str(), GameHdr->id), 255);
		fsop_GetFileSizeBytes(custom_banner, &custom_bnr_size);
		if(custom_bnr_size > 0)
		{
			custom_bnr_file = (u8*)MEM2_lo_alloc(custom_bnr_size);
			if(custom_bnr_file != NULL)
			{
				fsop_ReadFileLoc(custom_banner, custom_bnr_size, (void*)custom_bnr_file);
				m_banner_loaded = true;
			}
		}
	}
	if(GameHdr->type == TYPE_GC_GAME && custom_bnr_file == NULL)
	{
		/* gc game but no custom banner. so we make one ourselves. and exit sound thread. */
		//get the gc game's opening.bnr from ISO - a 96x32 image to add to the gc banner included with wiiflow
		GC_Disc_Reader.init(GameHdr->path);
		u8 *opening_bnr = GC_Disc_Reader.GetGameCubeBanner();
		if(opening_bnr != NULL)
		{
			//creategcbanner adds the opening.bnr image and game title to the wiiflow gc banner
			m_banner.CreateGCBanner(opening_bnr, m->m_wbf1_font, m->m_wbf2_font, GameHdr->title);
			m_banner_loaded = true;
		}
		else
			m_banner.DeleteBanner();
		GC_Disc_Reader.clear();
		if(m->m_gc_play_default_sound)
		{
			//get wiiflow gc ogg sound to play with banner
			m->m_gameSound.Load(gc_ogg, gc_ogg_size, false);
			if(m->m_gameSound.IsLoaded())
				m->m_gamesound_changed = true;
		}
		m->m_soundThrdBusy = false;
		return NULL;
	}
	if(custom_bnr_file == NULL)/* no custom banner load and if wii or channel game try cached banner id6 only*/
	{
		strncpy(cached_banner, fmt("%s/%s.bnr", m->m_bnrCacheDir.c_str(), GameHdr->id), 255);
		fsop_GetFileSizeBytes(cached_banner, &cached_bnr_size);
		if(cached_bnr_size > 0)
		{
			cached_bnr_file = (u8*)MEM2_lo_alloc(cached_bnr_size);
			if(cached_bnr_file != NULL)
			{
				fsop_ReadFileLoc(cached_banner, cached_bnr_size, (void*)cached_bnr_file);
				m_banner_loaded = true;
			}
		}
	}

	if(custom_bnr_file != NULL)
		CurrentBanner.SetBanner(custom_bnr_file, custom_bnr_size, true, true);
	else if(cached_bnr_file != NULL)
		CurrentBanner.SetBanner(cached_bnr_file, cached_bnr_size, false, true);
	else if(GameHdr->type == TYPE_WII_GAME)
	{
		m->_extractBnr(GameHdr);
		m_banner_loaded = true;
	}
		
	if(!CurrentBanner.IsValid())
	{
		m_banner_loaded = false;
		m->m_gameSound.FreeMemory();
		m_banner.DeleteBanner();
		CurrentBanner.ClearBanner();
		m->m_soundThrdBusy = false;
		return NULL;
	}
	//save new wii or channel banner to cache folder, gc and custom banners are not cached
	if(cached_bnr_file == NULL && custom_bnr_file == NULL)
		fsop_WriteFile(cached_banner, CurrentBanner.GetBannerFile(), CurrentBanner.GetBannerFileSize());

	//load and init banner
	m_banner.LoadBanner(m->m_wbf1_font, m->m_wbf2_font);
	
	//get sound from wii, channel, or custom banner and load it to play with the banner
	u32 sndSize = 0;
	u8 *soundBin = CurrentBanner.GetFile("sound.bin", &sndSize);
	CurrentBanner.ClearBanner();// got sound.bin and banner for displaying is loaded so no longer need current banner.

	if(soundBin != NULL && (GameHdr->type != TYPE_GC_GAME || m->m_gc_play_banner_sound))
	{
		if(memcmp(&((IMD5Header *)soundBin)->fcc, "IMD5", 4) == 0)
		{
			u32 newSize = 0;
			u8 *newSound = DecompressCopy(soundBin, sndSize, &newSize);
			free(soundBin);// no longer needed, now using decompressed newSound
			if(newSound == NULL || newSize == 0 || !m->m_gameSound.Load(newSound, newSize))
			{
				m->m_gameSound.FreeMemory();// frees newSound
				m_banner.DeleteBanner();// the same as UnloadBanner
				m->m_soundThrdBusy = false;
				return NULL;
			}
		}
		else
			m->m_gameSound.Load(soundBin, sndSize);

		if(m->m_gameSound.IsLoaded())
			m->m_gamesound_changed = true;
		else
		{
			m->m_gameSound.FreeMemory();// frees soundBin
			m_banner.DeleteBanner();
		}
	}
	else
	{
		if(soundBin != NULL)
			free(soundBin);
		//gprintf("WARNING: No sound found in banner!\n");
		m->m_gamesound_changed = true;
		m->m_gameSound.FreeMemory();// frees previous game sound
	}
	m->m_soundThrdBusy = false;
	return NULL;
}

u8 *GameSoundStack = NULL;
u32 GameSoundSize = 0x10000; //64kb
void CMenu::_playGameSound(void)// starts banner and gamesound loading thread
{
	_cleanupBanner(true);
	m_gamesound_changed = false;
	if(m_bnrSndVol == 0) 
		return;

	if(m_gameSoundThread != LWP_THREAD_NULL)
		_stopGameSoundThread();
	GameSoundStack = (u8*)MEM2_lo_alloc(GameSoundSize);
	LWP_CreateThread(&m_gameSoundThread, _gameSoundThread, this, GameSoundStack, GameSoundSize, 60);
}

void CMenu::_stopGameSoundThread()//stops banner and gamesound loading thread
{
	if(m_gameSoundThread == LWP_THREAD_NULL)
		return;

	if(LWP_ThreadIsSuspended(m_gameSoundThread))
		LWP_ResumeThread(m_gameSoundThread);

	while(m_soundThrdBusy)
		usleep(500);

	LWP_JoinThread(m_gameSoundThread, NULL);
	m_gameSoundThread = LWP_THREAD_NULL;

	if(GameSoundStack)
		MEM2_lo_free(GameSoundStack);
	GameSoundStack = NULL;
}
