#ifndef __MENU_HPP
#define __MENU_HPP
//#define SHOWMEMGECKO

#include <ogc/pad.h>
#include <vector>
#include <map>
#include <string>

#include "btnmap.h"
#include "channel/banner.h"
#include "channel/channels.h"
#include "cheats/gct.h"
#include "devicemounter/DeviceHandler.hpp"
#include "fileOps/fileOps.h"
#include "gecko/gecko.hpp"
#include "gecko/wifi_gecko.hpp"
#include "gui/coverflow.hpp"
#include "gui/cursor.hpp"
#include "gui/fanart.hpp"
#include "gui/gui.hpp"
#include "list/ListGenerator.hpp"
#include "loader/disc.h"
#include "loader/sys.h"
#include "loader/wbfs.h"
#include "music/gui_sound.h"
#include "music/MusicPlayer.hpp"
#include "sicksaxis-wrapper/sicksaxis-wrapper.h"
#include "wiiuse/wpad.h"
#include "wupc/wupc.h"
#include "wiidrc/wiidrc.h"

using std::string;
using std::vector;
using std::min;

class CMenu
{
public: // functions called from outside CMenu
	CMenu();
	bool init(bool usb_mounted);
	int main(void);
	void directlaunch(const char *GameID);
	
	const char *getBoxPath(const dir_discHdr *element);
	const char *getFrontPath(const dir_discHdr *element);
	const char *getBlankCoverPath(const dir_discHdr *element);
	
	// gc_disc_dump
	u64 m_thrdTotal;
	void update_pThread(u64 amount, bool add = true);
	
	// proxy settings
	bool proxyUseSystem;
	char proxyAddress[256];
	u16 proxyPort;
	char proxyUsername[33];
	char proxyPassword[33];

private:
	u8 m_prev_view;
	u8 m_current_view;
	u8 enabledPluginsCount;
	u8 m_catStartPage;
	u8 m_max_categories;
	bool m_clearCats;
	bool m_getFavs;
	bool m_newGame;
	bool show_mem;
	bool cacheCovers;
	bool SF_cacheCovers;
	bool CFLocked;
	bool Auto_hide_icons;
	bool m_snapshot_loaded;
	bool customBg;
	vector<dir_discHdr> m_gameList;
	vector<string> tiers;
	vector<string> sm_numbers;
	string sm_numbers_backup;
	string sm_tiers_backup;
	
	CFanart m_fa;
	Config m_cfg;
	Config m_loc;
	Config m_cat;
	Config m_source;
	Config m_gcfg1;
	Config m_gcfg2;
	Config m_theme;
	Config m_coverflow;
	Config m_platform;
	
	u8 *m_base_font;
	u32 m_base_font_size;
	u8 *m_wbf1_font;
	u8 *m_wbf2_font;
	u8 *m_file;
	u8 *m_buffer;
	u8 m_aa;
	u8 m_numCFVersions;
	u8 m_max_source_btn;
	u8 curCustBg;
	char cf_domain[16];
	volatile bool m_exit;
	bool m_use_source;// source_menu.ini found & ok to use source menu/flow
	bool m_sourceflow;// in sourceflow view
	bool m_refreshGameList;
	bool m_bnr_settings;
	bool m_directLaunch;
	bool m_locked;
	bool m_favorites;
	bool m_music_info;
	bool m_devo_installed;
	bool m_nintendont_installed;
	bool m_reload;
	bool m_use_wifi_gecko;
	bool m_use_sd_logging;
	//bool m_init_network;
	bool m_source_autoboot;
	dir_discHdr m_autoboot_hdr;
	s16 m_showtimer;
	string m_curLanguage;
	string m_themeName;

// Dir strings
	string m_appDir;
	string m_imgsDir;
	string m_binsDir;
	string m_dataDir;
	
	string m_cacheDir;
	string m_listCacheDir;
	string m_bnrCacheDir;
	string m_customBnrDir;
	
	string m_txtCheatDir;
	string m_cheatDir;
	string m_wipDir;
	
	string m_settingsDir;
	string m_languagesDir;
	string m_helpDir;
	string m_screenshotDir;
	
	string m_wiiTDBDir;
	string m_boxPicDir;
	string m_picDir;
	string m_themeDir;
	string m_themeDataDir;
	string m_coverflowsDir;
	string m_musicDir;
	string m_videoDir;
	string m_fanartDir;
	string m_bckgrndsDir;

	string m_sourceDir;
	string m_cartDir;
	string m_snapDir;


// Nand Emulation
	char emu_nands_dir[32];
	string m_saveExtGameId;
	bool m_forceext;

// GC sound stuff
	bool m_gc_play_banner_sound;
	bool m_gc_play_default_sound;
	
// Explorer stuff
	bool m_txt_view;
	const char *m_txt_path;

// Background image stuff
	TexData m_curBg;
	const TexData *m_prevBg;
	const TexData *m_nextBg;
	const TexData *m_lqBg;
	u8 m_bgCrossFade;
// Background textures
	TexData m_errorBg;
	TexData m_configBg;
	TexData m_cheatBg;
	TexData m_downloadBg;
	TexData m_gameinfoBg;
	TexData m_codeBg;
	TexData m_aboutBg;
	TexData m_wbfsBg;
	TexData m_gameSettingsBg;
	TexData m_promptBg;
	TexData m_gameBg;
	TexData m_gameBgLQ;
	TexData m_mainBg;
	TexData m_mainBgLQ;
	TexData m_mainCustomBg[2];
	
// Main Coverflow
	/* Kids UI: every main-screen button is stripped. Only the coverflow and
	   its page arrows remain; the physical HOME button exits WiiFlow. */
	s16 m_mainLblCurMusic;
	s16 m_mainLblLetter;
	s16 m_mainLblNotice;
	s16 m_mainLblMessage;
	s16 m_mainBtnNext;
	s16 m_mainBtnPrev;
	/* Kids UI: persistent on-screen hint - (A) Play */
	s16 m_mainLblAGlyph;
	s16 m_mainLblPlayHint;
	s16 m_mainLblUser[6];
	s16 m_mem1FreeSize;
	s16 m_mem2FreeSize;
#ifdef SHOWMEMGECKO
	unsigned int mem1old;
	unsigned int mem1;
	unsigned int mem2old;
	unsigned int mem2;
#endif

// Main Config menus
	s16 m_configLblUser[4];
	






// checkbox menus
	s16 m_checkboxLblTxt[11];
	s16 m_checkboxBtn[11];

// Download menu
	s16 m_downloadLblUser[4];
	s16 m_downloadPBar;
	s16 m_downloadLblMessage;
	s16 m_downloadLblDialog;
	//download cover settings
	enum CoverPrio
	{
		C_TYPE_PRIOA = (1<<0),//C_TYPE_ACUSTM
		C_TYPE_PRIOB = (1<<1),//C_TYPE_BCUSTM
		C_TYPE_EN =    (1<<2),
		C_TYPE_JA =    (1<<3),
		C_TYPE_FR =    (1<<4),
		C_TYPE_DE =    (1<<5),
		C_TYPE_ES =    (1<<6),
		C_TYPE_IT =    (1<<7),
		C_TYPE_NL =    (1<<8),
		C_TYPE_PT =    (1<<9),
		C_TYPE_RU =    (1<<10),
		C_TYPE_KO =    (1<<11),
		C_TYPE_ZHCN =  (1<<12),
		C_TYPE_AU =    (1<<13),
		C_TYPE_ONOR =  (1<<14),//C_TYPE_ONCU
		C_TYPE_ONCU =  (1<<15),//C_TYPE_ANB
		
	};
	enum CoverType
	{
		BOX = 1,
		CBOX,
		FLAT,
		CFLAT,
	};
	enum Regions
	{
		EN = 1,
		JA,
		FR,
		DE,		
		ES,
		IT,
		NL,
		PT,
		RU,
		KO,
		ZHCN,
		AU,
	};
// Game menu
	enum
	{
		LOAD_IOS_FAILED = 0,
		LOAD_IOS_SUCCEEDED,
		LOAD_IOS_NOT_NEEDED
	};
	/* Kids UI: favorites, categories, delete and settings are stripped from
	   the game screen - only PLAY and BACK remain. */
	s16 m_gameBtnPlay;
	s16 m_gameBtnBack;
	s16 m_gameLblUser[5];
	int snapbg_x, snapbg_y, snapbg_w, snapbg_h;
// disc 2 prompt menu
	s16 m_promptLblQuestion;
	s16 m_promptBtnChoice1;
	s16 m_promptBtnChoice2;
// Parental code menu
	s16 m_codeBtnKey[10];
	s16 m_codeLblUser[4];
// wbfs menu 
	s16 m_wbfsLblUser[4];
	enum WBFS_OP
	{
		WO_ADD_GAME,
		WO_REMOVE_GAME,
		WO_FORMAT,
		WO_COPY_GAME,
	};
//coverflow adjust menu
	s16 m_cfThemeLblVal[4 * 4];
	s16 m_cfThemeBtnValM[4 * 4];
	s16 m_cfThemeBtnValP[4 * 4];
	s16 m_cfThemeLblValTxt[4];
	struct SCFParamDesc
	{
		enum
		{
			PDT_EMPTY,
			PDT_FLOAT,
			PDT_V3D,
			PDT_COLOR,
			PDT_BOOL,
			PDT_INT, 
			PDT_TXTSTYLE,
		} paramType[4];
		enum
		{
			PDD_BOTH,
			PDD_NORMAL, 
			PDD_SELECTED,
		} domain;
		bool scrnFmt;
		const char name[32];
		const char valName[4][64];
		const char key[4][48];
		float step[4];
		float minMaxVal[4][2];
	};
	static const SCFParamDesc _cfParams[];
//Game Settings menus
	s16 m_gameSettingsLblUser[3 * 2];
//Cheat menu
	s16 m_cheatLblItem[4];
	s16 m_cheatBtnItem[4];
	s16 m_cheatLblUser[4];
// Gameinfo menu
	s16 m_gameinfoLblUser[5];
	s16 m_gameinfoLblControlsReq[4];
	s16 m_gameinfoLblControls[4];
	s16 m_gameLblSnap;
	s16 m_gameLblOverlay;
	TexData m_game_snap;
	TexData m_game_overlay;
	TexData m_snap;
	TexData m_cart;
	TexData m_overlay;
	TexData m_rating;
	TexData m_wifi;
	TexData m_controlsreq[4];
	TexData m_controls[4];

// controller stuff
	WPADData *wd[WPAD_MAX_WIIMOTES];

	u32 wii_btnsPressed[WPAD_MAX_WIIMOTES];
	u32 wii_btnsHeld[WPAD_MAX_WIIMOTES];
	u32 wupc_btnsPressed[WPAD_MAX_WIIMOTES];
	u32 wupc_btnsHeld[WPAD_MAX_WIIMOTES];
	u32 gc_btnsPressed;
	u32 gc_btnsHeld;
	u32 ds3_btnsPressed;
	
	bool wBtn_Pressed(int btn, u8 ext);
	bool wBtn_PressedChan(int btn, u8 ext, int &chan);
	bool wBtn_Held(int btn, u8 ext);
	bool wBtn_HeldChan(int btn, u8 ext, int &chan);
	u32 wiidrc_to_pad(u32 btns);
	u32 ds3_to_pad(u32 btns);
	
	bool wii_btnRepeat(u8 btn);
	u8 m_wpadLeftDelay;
	u8 m_wpadDownDelay;
	u8 m_wpadRightDelay;
	u8 m_wpadUpDelay;
	u8 m_wpadADelay;
	//u8 m_wpadBDelay;

	bool gc_btnRepeat(s64 btn);
	u8 m_padLeftDelay;
	u8 m_padDownDelay;
	u8 m_padRightDelay;
	u8 m_padUpDelay;
	u8 m_padADelay;
	//u8 m_padBDelay;

	float left_stick_angle[WPAD_MAX_WIIMOTES];
	float left_stick_mag[WPAD_MAX_WIIMOTES];
	float right_stick_angle[WPAD_MAX_WIIMOTES];
	float right_stick_mag[WPAD_MAX_WIIMOTES];
	s32   right_stick_skip[WPAD_MAX_WIIMOTES];
	float wmote_roll[WPAD_MAX_WIIMOTES];
	s32	  wmote_roll_skip[WPAD_MAX_WIIMOTES];
	bool  enable_wmote_roll;
	
	void SetupInput(bool reset_pos = false);
	void ScanInput(void);
	
	void ButtonsPressed(void);
	void ButtonsHeld(void);

	void LeftStick();
	bool lStick_Up(void);
	bool lStick_Right(void);
	bool lStick_Down(void);
	bool lStick_Left(void);

	bool rStick_Up(void);
	bool rStick_Right(void);
	bool rStick_Down(void);
	bool rStick_Left(void);

	bool wRoll_Left(void);
	bool wRoll_Right(void);

	bool WPadIR_Valid(int chan);
	bool WPadIR_ANY(void);

	CCursor m_cursor[WPAD_MAX_WIIMOTES];
	u8 pointerhidedelay[WPAD_MAX_WIIMOTES];
	u16 stickPointer_x[WPAD_MAX_WIIMOTES];
	u16 stickPointer_y[WPAD_MAX_WIIMOTES];
	bool m_show_pointer[WPAD_MAX_WIIMOTES];
	bool ShowPointer(void);
	time_t no_input_time;
	u32 NoInputTime(void);
	
// Zones
	struct SZone
	{
		int x;
		int y;
		int w;
		int h;
		bool hide;
	};
	SZone m_mainPrevZone;
	SZone m_mainNextZone;
	SZone m_mainButtonsZone;
	SZone m_mainButtonsZone2;
	SZone m_mainButtonsZone3;
	SZone m_gameButtonsZone;
	void ShowZone(SZone zone, bool &showZone);
	void ShowMainZone(void);
	void ShowMainZone2(void);
	void ShowMainZone3(void);
	void ShowPrevZone(void);
	void ShowNextZone(void);
	void ShowGameZone(void);
	bool m_show_zone_main;
	bool m_show_zone_main2;
	bool m_show_zone_main3;
	bool m_show_zone_prev;
	bool m_show_zone_next;
	bool m_show_zone_game;

// GUI Theme stuff
	typedef std::map<string, TexData> TexSet;
	typedef std::map<string, GuiSound*> SoundSet;
	struct SThemeData
	{
		TexSet texSet;
		vector<SFont> fontSet;
		SoundSet soundSet;
		SFont btnFont;
		SFont lblFont;
		SFont titleFont;
		SFont txtFont;
		CColor btnFontColor;
		CColor lblFontColor;
		CColor txtFontColor;
		CColor titleFontColor;
		TexData bg;
		TexData btnTexL;
		TexData btnTexR;
		TexData btnTexC;
		TexData btnTexLS;
		TexData btnTexRS;
		TexData btnTexCS;
		TexData pbarTexL;
		TexData pbarTexR;
		TexData pbarTexC;
		TexData pbarTexLS;
		TexData pbarTexRS;
		TexData pbarTexCS;
		TexData btnTexPlus;
		TexData btnTexPlusS;
		TexData btnTexMinus;
		TexData btnTexMinusS;
		GuiSound *clickSound;
		GuiSound *hoverSound;
		GuiSound *cameraSound;
	};
	SThemeData theme;
	
	void _buildMenus(void);
	SFont _dfltFont(u32 fontSize, u32 lineSpacing, u32 weight, u32 index, const char *genKey);
	SFont _font(const char *domain, const char *key, SFont def_font);
	TexData _texture(const char *domain, const char *key, TexData &def, bool freeDef = true);
	vector<TexData> _textures(const char *domain, const char *key);
	GuiSound *_sound(CMenu::SoundSet &soundSet, const char *filename, const u8 * snd, u32 len, const char *name, bool isAllocated);
	GuiSound *_sound(CMenu::SoundSet &soundSet, const char *domain, const char *key, const char *name);
	u16 _textStyle(const char *domain, const char *key, u16 def, bool coverflow = false);
	s16 _addButton(const char *domain, SFont font, const wstringEx &text, int x, int y, u32 width, u32 height, const CColor &color);
	s16 _addPicButton(const char *domain, TexData &texNormal, TexData &texSelected, int x, int y, u32 width, u32 height);
	s16 _addLabel(const char *domain, SFont font, const wstringEx &text, int x, int y, u32 width, u32 height, const CColor &color, s16 style);
	s16 _addLabel(const char *domain, SFont font, const wstringEx &text, int x, int y, u32 width, u32 height, const CColor &color, s16 style, TexData &bg);
	s16 _addProgressBar(const char *domain, int x, int y, u32 width, u32 height);
	void _setHideAnim(s16 id, const char *domain, int dx, int dy, float scaleX, float scaleY);
	void _addUserLabels(s16 *ids, u32 size, const char *domain);
	void _addUserLabels(s16 *ids, u32 start, u32 size, const char *domain);

//main coverflow functions
	void _loadCFCfg();
	void _loadCFLayout(int version, bool forceAA = false, bool otherScrnFmt = false);
	Vector3D _getCFV3D(const string &domain, const string &key, const Vector3D &def, bool otherScrnFmt = false);
	int _getCFInt(const string &domain, const string &key, int def, bool otherScrnFmt = false);
	float _getCFFloat(const string &domain, const string &key, float def, bool otherScrnFmt = false);
	void _setAA(int aa);
	void _setCFVersion(int version);
	int _getCFVersion(void);
	
// Menu Inits
	void _initMainMenu();
	void _initErrorMenu();
	void _initDownloadMenu();
	void _initGameMenu();
// menu texts
	void _textError(void);
	void _textGame(void);
	void _textMain(void);
// menu hides
	void _hideMain(bool instant = false);
	void _hideError(bool instant = false);
	void _hideDownload(bool instant = true);
	void _hideGame(bool instant = false);
// menu shows
	void _showMain(void);
	void _showCF(bool refreshList = false);
	void _showTotalGames(const int numberOfGames);
	void _showError(void);
	void _showGame(void);
// menu main functions
	void _error(const wstringEx &msg);
	void _game(bool launch = false);

//nand emu functions
	int _FindEmuPart(bool savesnand, bool searchvalid);
	bool _checkSave(string id, int nand_type);
	bool _TestEmuNand(int epart, const char *path, bool indept);
	float m_progress;
	float m_fprogress;
	int m_fileprog;
	int m_filesize;
	int m_dumpsize;
	int m_filesdone;
	int m_foldersdone;
	int m_nandexentry;
//explorer menu
//source menu
//select plugins menu
//categories menu
//adjust coverflow menu
//download menu functions
	void _downloadProgress(void *obj, int size, int position);
	//void _downloadUrl(const char *url, u8 **dl_file, u32 *dl_size);
	//static void * _downloadUrlAsync(void *obj);
	//static u8 downloadStack[8192];
	//static const u32 downloadStackSize;
	//void _netInit();
	void _initAsyncNetwork();
	static s32 _networkComplete(s32 result, void *usrData);
	bool _isNetworkAvailable();
	s32 _initNetwork();
	static void * _pThread(void *obj);
	void _start_pThread(void);
	void _stop_pThread(void);
	lwp_t m_thrdPtr;
	volatile bool m_thrdInstalling;
	volatile bool m_thrdUpdated;
	volatile bool m_thrdDone;
	vu64 m_thrdWritten;
// wbfs menu functions
// game selected menu functions
	void _extractBnr(const dir_discHdr *hdr);
	void _setCurrentItem(const dir_discHdr *hdr);
	void _cleanupBanner(bool gamechange = false);
	void _cleanupVideo();
	bool _startVideo();
	void _playGameSound(void);
	void _stopGameSoundThread(void);
	static void * _gameSoundThread(void *obj);
	GuiSound m_gameSound;
	volatile bool m_gameSelected;
	volatile bool m_soundThrdBusy;
	lwp_t m_gameSoundThread;
	bool m_gamesound_changed;
	u8 m_bnrSndVol;
	bool m_video_playing;
	
// gamelist functions
	bool _loadList(void);
	bool _loadWiiList(void);
	bool _loadGamecubeList(void);
	void _initCF(void);
	
//background handling functions
	void _getCustomBgTex(void);
	void _setMainBg(void);
	void _setBg(const TexData &bgTex, const TexData &bglqTex);
	void _updateBg(void);
	void _drawBg(void);

//sourceflow functions
	
// misc functions
	void RemoveCover(const char *id);
	int _cacheCovers(void);
	int _cacheCover(const dir_discHdr *hdr, bool smallBox);
	void _mainLoopCommon(bool withCF = false, bool adjusting = false);
	void _loadDefaultFont(void);
	void _cleanupDefaultFont();
	void cleanup(void);
	void _Theme_Cleanup();
	void _stopSounds(void);
	void TempLoadIOS(int IOS = 0);
	void exitHandler(int ExitTo);
	const char *_domainFromView(void);
	void _showWaitMessage();
	void _hideWaitMessage();
	const wstringEx _t(const char *key, const wchar_t *def = L"") { return m_loc.getWString(m_curLanguage, key, def); }
	const wstringEx _fmt(const char *key, const wchar_t *def);
	wstringEx _getNoticeTranslation(int sorting, wstringEx curLetter);
	void _load_installed_cioses();
	std::map<u8, u8> _installed_cios;
	typedef std::map<u8, u8>::iterator CIOSItr;// we can use this for both maps.
	std::map<u8, u8> _cios_base;

//game boot functions
	void _launch(const dir_discHdr *hdr);
	void _launchWii(dir_discHdr *hdr, bool dvd);
	void _launchHomebrew(const char *filepath, vector<string> arguments);
	void _launchGC(dir_discHdr *hdr, bool disc);
	void _launchShutdown();
	vector<string> _getMetaXML(const char *bootpath);
	int _loadGameIOS(u8 ios, int userIOS, const char *id, bool RealNAND_Channels = false);
	bool _loadFile(u8 * &buffer, u32 &size, const char *path, const char *file);// gameconfig.txt and cheats.gct

//
	struct SOption { const char id[11]; const wchar_t text[16]; };

	static const SOption _GlobalVideoModes[6];
	static const SOption _VideoModes[7];
	static const SOption _languages[11];
	static const SOption _GlobalDeflickerOptions[6];
	static const SOption _DeflickerOptions[7];
	static const SOption _GlobalVideoWidths[2];
	static const SOption _VideoWidths[3];
	static const SOption _AspectRatio[3];
	static const SOption _WidescreenWiiu[3];
	static const SOption _vidModePatch[4];
	static const SOption _debugger[3];
	static const SOption _hooktype[8];
	static const SOption _exitTo[3];
	static const SOption _privateServer[3];
	
	static const SOption _GlobalGCvideoModes[6];
	static const SOption _GCvideoModes[7];
	static const SOption _GlobalGClanguages[7];
	static const SOption _GClanguages[8];
	static const SOption _GlobalGCLoaders[2];
	static const SOption _GCLoader[3];
	static const SOption _NinEmuCard[5];

	static const SOption _ChannelsType[3];
	static const SOption _NandEmu[2];
	static const SOption _SaveEmu[4];
	static const SOption _GlobalSaveEmu[3];
	
// thread stuff
	mutex_t m_mutex;
	wstringEx m_thrdMessage;
	volatile float m_thrdProgress;
	volatile float m_fileProgress;
	volatile bool m_thrdMessageAdded;
	volatile bool m_thrdStop;
	volatile bool m_thrdWorking;
	volatile bool m_thrdNetwork;
};

extern CMenu mainMenu;

#define ARRAY_SIZE(a)		(sizeof a / sizeof a[0])

#endif // !defined(__MENU_HPP)
