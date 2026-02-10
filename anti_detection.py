"""
Anti-detection and browser fingerprinting module for Instagram scraping
Implements various techniques to avoid bot detection
"""
import random
import json
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
import asyncio
from playwright.async_api import Page, BrowserContext
import logging

logger = logging.getLogger(__name__)


class BrowserFingerprint:
    """Manages browser fingerprinting to avoid detection"""
    
    def __init__(self, data_dir: Path = None):
        self.data_dir = data_dir or Path(__file__).parent / 'data'
        self.fingerprints_file = self.data_dir / 'browser_fingerprints.json'
        self.load_fingerprints()
    
    def load_fingerprints(self):
        if self.fingerprints_file.exists():
            with open(self.fingerprints_file, 'r') as f:
                self.fingerprints = json.load(f)
        else:
            self.fingerprints = self._generate_fingerprints()
            self.save_fingerprints()
    
    def save_fingerprints(self):
        self.fingerprints_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.fingerprints_file, 'w') as f:
            json.dump(self.fingerprints, f, indent=2)
    
    def _generate_fingerprints(self) -> Dict:
        return {
            "profiles": [
                {
                    "os": "Windows",
                    "browser": "Chrome",
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "viewport": {"width": 1920, "height": 1080},
                    "screen": {"width": 1920, "height": 1080, "depth": 24},
                    "timezone": "America/New_York",
                    "locale": "en-US",
                    "webgl_vendor": "Google Inc. (Intel)",
                    "webgl_renderer": "ANGLE (Intel, Intel(R) UHD Graphics 620 Direct3D11 vs_5_0 ps_5_0)",
                    "fonts": ["Arial", "Calibri", "Cambria", "Comic Sans MS", "Consolas", "Courier New", "Georgia", "Impact", "Lucida Console", "Tahoma", "Times New Roman", "Trebuchet MS", "Verdana"],
                    "plugins": ["Chrome PDF Plugin", "Chrome PDF Viewer", "Native Client"],
                    "hardware_concurrency": 8,
                    "device_memory": 8,
                    "max_touch_points": 0,
                    "color_depth": 24,
                    "pixel_ratio": 1
                },
                {
                    "os": "Windows",
                    "browser": "Chrome",
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                    "viewport": {"width": 1366, "height": 768},
                    "screen": {"width": 1366, "height": 768, "depth": 24},
                    "timezone": "America/Los_Angeles",
                    "locale": "en-US",
                    "webgl_vendor": "Google Inc. (NVIDIA)",
                    "webgl_renderer": "ANGLE (NVIDIA, NVIDIA GeForce GTX 1050 Ti Direct3D11 vs_5_0 ps_5_0)",
                    "fonts": ["Arial", "Calibri", "Cambria", "Comic Sans MS", "Consolas", "Courier New", "Georgia", "Impact", "Lucida Console", "Tahoma", "Times New Roman", "Trebuchet MS", "Verdana"],
                    "plugins": ["Chrome PDF Plugin", "Chrome PDF Viewer", "Native Client"],
                    "hardware_concurrency": 4,
                    "device_memory": 4,
                    "max_touch_points": 0,
                    "color_depth": 24,
                    "pixel_ratio": 1.25
                },
                {
                    "os": "Mac",
                    "browser": "Chrome",
                    "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "viewport": {"width": 1440, "height": 900},
                    "screen": {"width": 2880, "height": 1800, "depth": 24},
                    "timezone": "America/Chicago",
                    "locale": "en-US",
                    "webgl_vendor": "Google Inc. (Apple)",
                    "webgl_renderer": "ANGLE (Apple, Apple M1 Pro, OpenGL 4.1)",
                    "fonts": ["Helvetica Neue", "Helvetica", "Arial", "Times", "Times New Roman", "Courier", "Courier New", "Verdana", "Georgia", "Palatino", "Garamond", "Bookman", "Comic Sans MS", "Trebuchet MS", "Arial Black", "Impact"],
                    "plugins": ["Chrome PDF Plugin", "Chrome PDF Viewer", "Native Client"],
                    "hardware_concurrency": 10,
                    "device_memory": 16,
                    "max_touch_points": 0,
                    "color_depth": 30,
                    "pixel_ratio": 2
                },
                {
                    "os": "Windows",
                    "browser": "Firefox",
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
                    "viewport": {"width": 1920, "height": 1080},
                    "screen": {"width": 1920, "height": 1080, "depth": 24},
                    "timezone": "America/Denver",
                    "locale": "en-US",
                    "webgl_vendor": "Google Inc.",
                    "webgl_renderer": "ANGLE (Intel(R) UHD Graphics 620 Direct3D11 vs_5_0 ps_5_0)",
                    "fonts": ["Arial", "Calibri", "Cambria", "Comic Sans MS", "Consolas", "Courier New", "Georgia", "Impact", "Lucida Console", "Tahoma", "Times New Roman", "Trebuchet MS", "Verdana"],
                    "plugins": [],
                    "hardware_concurrency": 8,
                    "device_memory": 8,
                    "max_touch_points": 0,
                    "color_depth": 24,
                    "pixel_ratio": 1
                }
            ]
        }
    
    def get_random_fingerprint(self, account_username: Optional[str] = None) -> Dict:
        """Get a fingerprint - consistent for same account, random otherwise"""
        if account_username:
            index = hash(account_username) % len(self.fingerprints['profiles'])
            return self.fingerprints['profiles'][index]
        return random.choice(self.fingerprints['profiles'])
    
    def get_context_options(self, fingerprint: Dict) -> Dict:
        """Get Playwright context options from fingerprint"""
        # Force desktop user agent even if fingerprint suggests mobile
        user_agent = fingerprint['user_agent']
        # Ensure no mobile keywords in user agent
        if 'Mobile' in user_agent or 'Android' in user_agent or 'iPhone' in user_agent:
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        
        return {
            'viewport': fingerprint['viewport'],
            'user_agent': user_agent,
            'locale': fingerprint['locale'],
            'timezone_id': fingerprint['timezone'],
            'color_scheme': random.choice(['light', 'dark', 'no-preference']),
            'reduced_motion': random.choice(['reduce', 'no-preference']),
            'device_scale_factor': fingerprint.get('pixel_ratio', 1),
            'is_mobile': False,
            'has_touch': False,
            'bypass_csp': False,
            'ignore_https_errors': False,
            'java_script_enabled': True,
            'accept_downloads': False,
            'permissions': [],
            'extra_http_headers': {
                'Accept-Language': 'en-US,en;q=0.9',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"Windows"',
            }
        }
    
    def get_stealth_scripts(self, fingerprint: Dict) -> str:
        """Get JavaScript to inject for stealth mode"""
        return f'''
        Object.defineProperty(navigator, 'webdriver', {{ get: () => undefined }});
        Object.defineProperty(navigator, 'plugins', {{ get: () => {json.dumps(fingerprint.get('plugins', []))} }});
        Object.defineProperty(navigator, 'languages', {{ get: () => [{repr(fingerprint['locale'])}, 'en-US', 'en'] }});
        Object.defineProperty(navigator, 'hardwareConcurrency', {{ get: () => {fingerprint.get('hardware_concurrency', 4)} }});
        Object.defineProperty(navigator, 'deviceMemory', {{ get: () => {fingerprint.get('device_memory', 4)} }});
        Object.defineProperty(navigator, 'maxTouchPoints', {{ get: () => {fingerprint.get('max_touch_points', 0)} }});
        Object.defineProperty(screen, 'colorDepth', {{ get: () => {fingerprint.get('color_depth', 24)} }});
        Object.defineProperty(screen, 'pixelDepth', {{ get: () => {fingerprint.get('color_depth', 24)} }});
        
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {{
            if (parameter === 37445) {{ return '{fingerprint.get("webgl_vendor", "Google Inc.")}' }}
            if (parameter === 37446) {{ return '{fingerprint.get("webgl_renderer", "ANGLE")}' }}
            return getParameter.apply(this, arguments);
        }};
        
        const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
        HTMLCanvasElement.prototype.toDataURL = function() {{
            const context = this.getContext('2d');
            if (context) {{
                const imageData = context.getImageData(0, 0, this.width, this.height);
                for (let i = 0; i < imageData.data.length; i += 4) {{
                    imageData.data[i] = Math.min(255, imageData.data[i] + Math.random() * 0.1);
                }}
                context.putImageData(imageData, 0, 0);
            }}
            return originalToDataURL.apply(this, arguments);
        }};
        
        window.chrome = {{ 
            runtime: {{ id: 'adblocker-extension-id-' + Math.random().toString(36).substr(2, 9) }}, 
            loadTimes: function() {{}}, 
            csi: function() {{}} 
        }};
        
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ? Promise.resolve({{ state: 'denied' }}) : originalQuery(parameters)
        );
        
        navigator.getBattery = () => Promise.resolve({{
            charging: Math.random() > 0.5,
            chargingTime: Math.random() * 3600,
            dischargingTime: Infinity,
            level: 0.5 + Math.random() * 0.5
        }});
        '''


class HumanBehaviorSimulator:
    """Simulates human-like behavior patterns"""
    
    async def simulate_pre_navigation(self, page: Page):
        """Simulate behavior before navigation"""
        await asyncio.sleep(random.uniform(0.5, 1.5))
    
    async def simulate_post_navigation(self, page: Page):
        """Simulate behavior after page load"""
        await asyncio.sleep(random.uniform(2, 5))
        # Random mouse movements
        for _ in range(random.randint(1, 3)):
            x = random.randint(100, 800)
            y = random.randint(100, 600)
            await page.mouse.move(x, y)
            await asyncio.sleep(random.uniform(0.1, 0.3))
    
    async def simulate_content_render(self, page: Page):
        """Simulate waiting for content to render"""
        await asyncio.sleep(random.uniform(3, 6))
    
    async def simulate_scroll(self, page: Page):
        """Simulate human-like scrolling"""
        scroll_amount = random.randint(600, 1000)
        await page.evaluate(f'window.scrollTo(0, {scroll_amount})')
        await asyncio.sleep(random.uniform(2, 4))
    
    async def simulate_post_load(self, page: Page):
        """Simulate waiting for posts to load"""
        await asyncio.sleep(random.uniform(1, 2))
    
    async def simulate_final_wait(self, page: Page):
        """Final wait before data extraction"""
        await asyncio.sleep(random.uniform(1.5, 3.5))
    
    async def simulate_error_recovery(self, page: Page):
        """Simulate human behavior on error"""
        await asyncio.sleep(random.uniform(5, 15))


class NetworkPatternRandomizer:
    """Randomizes network patterns to avoid detection"""
    
    async def randomize_network(self, page: Page):
        """Apply network randomization"""
        await asyncio.sleep(random.uniform(0.1, 0.5))


class SessionManager:
    """Manages session persistence and validation"""
    
    def __init__(self, data_dir: Path = None):
        self.data_dir = data_dir or Path(__file__).parent / 'data'
        self.session_file = self.data_dir / 'sessions.json'
        self.sessions = self.load_sessions()
    
    def load_sessions(self) -> Dict:
        """Load saved sessions"""
        if self.session_file.exists():
            with open(self.session_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_session(self, account_id: str, cookies: list, storage_state: Dict):
        """Save session for an account"""
        self.sessions[account_id] = {
            'cookies': cookies,
            'storage_state': storage_state,
            'last_used': datetime.now().isoformat(),
            'success_count': self.sessions.get(account_id, {}).get('success_count', 0) + 1
        }
        self._save_sessions()
    
    def _save_sessions(self):
        """Save sessions to file"""
        self.session_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.session_file, 'w') as f:
            json.dump(self.sessions, f, indent=2)


class AntiDetectionManager:
    """Central manager for all anti-detection techniques"""
    
    def __init__(self, data_dir: Path = None):
        self.data_dir = data_dir or Path(__file__).parent / 'data'
        self.fingerprint_mgr = BrowserFingerprint(self.data_dir)
        self.behavior_sim = HumanBehaviorSimulator()
        self.network_sim = NetworkPatternRandomizer()
        self.session_mgr = SessionManager(self.data_dir)
        logger.info("AntiDetectionManager initialized")
    
    def get_fingerprint_for_account(self, account_id: str):
        """Get fingerprint for specific account"""
        return self.fingerprint_mgr.get_random_fingerprint(account_id)
    
    async def apply_pre_navigation_behavior(self, page: Page):
        """Apply all pre-navigation techniques"""
        await self.network_sim.randomize_network(page)
        await self.behavior_sim.simulate_pre_navigation(page)
    
    async def apply_post_navigation_behavior(self, page: Page):
        """Apply all post-navigation techniques"""
        await self.behavior_sim.simulate_post_navigation(page)
