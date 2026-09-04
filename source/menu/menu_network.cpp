/****************************************************************************
 * WiiFlow Kids - network and progress support.
 *
 * The original WiiFlow download menu (covers, banners, GameTDB) has been
 * removed along with the rest of the old UI. What survives here is only what
 * the child's coverflow still depends on:
 *
 *   - network bring-up, which game booting uses for cheat/txt providers
 *   - the worker thread and progress bar shown while covers are cached
 *     into .wfc textures on first boot
 ****************************************************************************/
#include <network.h>
#include <unistd.h>
#include <errno.h>

#include "menu.hpp"
#include "types.h"
#include "lockMutex.hpp"
#include "channel/nand.hpp"
#include "loader/sys.h"
#include "network/https.h"

/* Only the progress widgets remain of the old DOWNLOAD menu. They are reused
   as the cover-caching progress display on the child's first boot. */
void CMenu::_initDownloadMenu()
{
	m_downloadPBar = _addProgressBar("DOWNLOAD/PROGRESS_BAR", 40, 200, 560, 20);
	m_downloadLblDialog = _addLabel("DOWNLOAD/DIALOG", theme.lblFont, L"", 40, 75, 600, 200, theme.lblFontColor, FTGX_JUSTIFY_LEFT | FTGX_ALIGN_MIDDLE);
	m_downloadLblMessage = _addLabel("DOWNLOAD/MESSAGE", theme.lblFont, L"", 40, 300, 600, 100, theme.lblFontColor, FTGX_JUSTIFY_CENTER | FTGX_ALIGN_TOP);

	_setHideAnim(m_downloadPBar, "DOWNLOAD/PROGRESS_BAR", 0, 0, -2.f, 0.f);
	_setHideAnim(m_downloadLblDialog, "DOWNLOAD/DIALOG", 0, 0, -2.f, 0.f);
	_setHideAnim(m_downloadLblMessage, "DOWNLOAD/MESSAGE", 0, 0, -2.f, 0.f);

	_hideDownload(true);
}

void CMenu::_hideDownload(bool instant)
{
	m_btnMgr.hide(m_downloadPBar, instant);
	m_btnMgr.hide(m_downloadLblDialog, instant);
	m_btnMgr.hide(m_downloadLblMessage, instant);
}

/************************************* Setup network connection *********************************************/

void CMenu::_initAsyncNetwork()
{
	if(networkInit || m_exit)
		return;
	if(!_isNetworkAvailable())
		return;
	m_thrdNetwork = true;
	net_init_async(_networkComplete, this);
	while(net_get_status() == -EBUSY)
		usleep(100);
}

s32 CMenu::_networkComplete(s32 ok, void *usrData)
{
	CMenu *m = (CMenu *) usrData;

	networkInit = ok == 0;
	m->m_thrdNetwork = false;

	if(networkInit)
	{
		wolfSSL_Init();
		if(m->m_use_wifi_gecko)
		{
			const string &ip = m->m_cfg.getString("DEBUG", "wifi_gecko_ip");
			u16 port = m->m_cfg.getInt("DEBUG", "wifi_gecko_port", 4405);
			if(ip.size() > 0 && port != 0)
				WiFiDebugger.Init(ip.c_str(), port);
		}
	}

	return 0;
}

bool CMenu::_isNetworkAvailable()
{
	bool ret = false;
	u32 size;
	char ISFS_Filepath[32] ATTRIBUTE_ALIGN(32);
	strcpy(ISFS_Filepath, "/shared2/sys/net/02/config.dat");
	u8 *buf = ISFS_GetFile(ISFS_Filepath, &size, -1);
	if(buf && size > 4)
	{
		ret = buf[4] > 0; // There is a valid connection defined.
	}
	MEM2_free(buf);
	return ret;
}

s32 CMenu::_initNetwork()
{
	while(net_get_status() == -EBUSY && m_thrdNetwork == true)
	{
		usleep(100); // Async initialization may be busy, wait to see if it succeeds.
	}

	if(networkInit)
		return 0;

	if(!_isNetworkAvailable())
		return -2;

	char ip[16];
	s32 ret = if_config(ip, NULL, NULL, true, 0);

	if(ret == 0)
	{
		wolfSSL_Init();
		networkInit = true;
	}
	return ret;
}

/************************************* Progress worker thread ******************************/

void CMenu::_downloadProgress(void *obj, int size, int position)
{
	CMenu *m = (CMenu *)obj;
	m->m_progress = size == 0 ? 0.f : (float)position / (float)size;
	// Don't synchronize too often
	if(m->m_progress - m->m_thrdProgress >= 0.01f)
	{
		LWP_MutexLock(m->m_mutex);
		m->m_thrdProgress = m->m_progress;
		LWP_MutexUnlock(m->m_mutex);
	}
}

void * CMenu::_pThread(void *obj)
{
	CMenu *m = (CMenu*)obj;
	m->SetupInput();
	while(m->m_thrdInstalling)
	{
		m->_mainLoopCommon();
		if(m->m_thrdUpdated)
		{
			m->m_thrdUpdated = false;
			m->_downloadProgress(obj, m->m_thrdTotal, m->m_thrdWritten);
			if(m->m_thrdProgress > 0.f)
			{
				m_btnMgr.setText(m->m_downloadLblMessage, wfmt(L"%i%%", (int)(m->m_thrdProgress * 100.f)));
				m_btnMgr.setProgress(m->m_downloadPBar, m->m_thrdProgress);
			}
			m->m_thrdDone = true;
		}
		if(m->m_thrdMessageAdded)
		{
			m->m_thrdMessageAdded = false;
			if(!m->m_thrdMessage.empty())
				m_btnMgr.setText(m->m_downloadLblDialog, m->m_thrdMessage);
		}
	}
	m->m_thrdWorking = false;
	return 0;
}

void CMenu::_start_pThread(void)
{
	m_thrdPtr = LWP_THREAD_NULL;
	m_thrdWorking = true;
	m_thrdMessageAdded = false;
	m_thrdInstalling = true;
	m_thrdUpdated = false;
	m_thrdDone = true;
	m_thrdProgress = 0.f;
	m_thrdWritten = 0;
	m_thrdTotal = 0;
	LWP_CreateThread(&m_thrdPtr, _pThread, this, 0, 8 * 1024, 64);
}

void CMenu::_stop_pThread(void)
{
	if(m_thrdPtr == LWP_THREAD_NULL)
		return;

	if(LWP_ThreadIsSuspended(m_thrdPtr))
		LWP_ResumeThread(m_thrdPtr);
	m_thrdInstalling = false;
	while(m_thrdWorking)
		usleep(50);
	LWP_JoinThread(m_thrdPtr, NULL);
	m_thrdPtr = LWP_THREAD_NULL;

	m_btnMgr.setProgress(m_downloadPBar, 1.f);
	m_btnMgr.setText(m_downloadLblMessage, L"100%");
}

void CMenu::update_pThread(u64 amount, bool add)
{
	if(m_thrdDone)
	{
		m_thrdDone = false;
		if(add)
			m_thrdWritten = m_thrdWritten + amount;
		else
			m_thrdWritten = amount;
		m_thrdUpdated = true;
	}
}
