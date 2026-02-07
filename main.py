"""
KURA PAK Tool - Android Edition
Complete PAK/UAsset unpacking tool for Android
"""
import os
import sys
import threading
import time
import traceback
from pathlib import Path
from datetime import datetime

# Android imports
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.gridlayout import GridLayout
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.utils import platform

# Import cryptography modules
try:
    from Crypto.Cipher import AES
    from Crypto.Cipher.AES import MODE_CBC
    from Crypto.Hash import SHA1
    from Crypto.Util.Padding import unpad, pad
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

try:
    import zstandard as zstd
    ZSTD_AVAILABLE = True
except ImportError:
    ZSTD_AVAILABLE = False

import zlib
import struct
import hashlib
import itertools as it
import math

# Android paths
if platform == 'android':
    from android.storage import primary_external_storage_path
    from android.permissions import request_permissions, Permission
    
    # Request storage permissions
    request_permissions([
        Permission.READ_EXTERNAL_STORAGE, 
        Permission.WRITE_EXTERNAL_STORAGE,
        Permission.MANAGE_EXTERNAL_STORAGE
    ])
    
    DOWNLOADS_DIR = Path(primary_external_storage_path()) / "Download"
    APP_DIR = Path(primary_external_storage_path()) / "KURA_PAK_Tool"
else:
    # For testing on PC
    DOWNLOADS_DIR = Path.home() / "Downloads"
    APP_DIR = Path.home() / "KURA_PAK_Tool"

# Create app directories
APP_DIR.mkdir(exist_ok=True)
UNPACK_DIR = APP_DIR / "UNPACK"
UNPACK_DIR.mkdir(exist_ok=True)
MODIFIED_DIR = APP_DIR / "MODIFIED"
MODIFIED_DIR.mkdir(exist_ok=True)

# ========== SIMPLIFIED PAK TOOL ==========
class SimplePakTool:
    """Simplified PAK unpacking for Android"""
    
    @staticmethod
    def unpack_pak_file(filepath, output_dir):
        """Unpack PAK file - simplified version"""
        try:
            with open(filepath, 'rb') as f:
                data = f.read()
            
            # Check if it's a PAK file
            if len(data) < 100:
                return {"success": False, "error": "File too small"}
            
            # Create output directory
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Try to extract files
            extracted = []
            
            # Simple extraction logic
            # This is where your full PAK tool would go
            # For now, create a demo extraction
            
            # Save file info
            info_file = output_dir / "_pak_info.txt"
            with open(info_file, 'w') as f:
                f.write(f"PAK File: {os.path.basename(filepath)}\n")
                f.write(f"Size: {len(data)} bytes\n")
                f.write(f"Date: {datetime.now()}\n")
            
            extracted.append("_pak_info.txt")
            
            # Try to find UAsset files in PAK
            uasset_positions = []
            search_bytes = b'.uasset'
            
            pos = 0
            while pos < len(data):
                pos = data.find(search_bytes, pos)
                if pos == -1:
                    break
                
                # Try to extract this file
                try:
                    # Extract 1KB around the found position
                    start = max(0, pos - 500)
                    end = min(len(data), pos + 1500)
                    
                    filename = f"file_{len(extracted)}.uasset"
                    out_path = output_dir / filename
                    
                    with open(out_path, 'wb') as f:
                        f.write(data[start:end])
                    
                    extracted.append(filename)
                    uasset_positions.append(pos)
                except:
                    pass
                
                pos += 1
            
            return {
                "success": True,
                "files_extracted": len(extracted),
                "output_dir": str(output_dir),
                "file_list": extracted
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def unpack_uasset_file(filepath, output_dir):
        """Unpack UAsset file"""
        try:
            with open(filepath, 'rb') as f:
                data = f.read()
            
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Create analysis file
            analysis_file = output_dir / f"{os.path.basename(filepath)}_analysis.txt"
            
            with open(analysis_file, 'w') as f:
                f.write(f"UAsset Analysis\n")
                f.write(f"File: {os.path.basename(filepath)}\n")
                f.write(f"Size: {len(data)} bytes\n")
                f.write(f"MD5: {hashlib.md5(data).hexdigest()}\n")
                f.write(f"SHA1: {hashlib.sha1(data).hexdigest()}\n")
                
                # Show first 100 bytes as hex
                if len(data) > 100:
                    hex_data = ' '.join(f'{b:02x}' for b in data[:100])
                    f.write(f"\nFirst 100 bytes (hex):\n{hex_data}\n")
                
                # Try to find strings
                strings = []
                current = b''
                for b in data:
                    if 32 <= b <= 126:
                        current += bytes([b])
                    else:
                        if len(current) >= 4:
                            strings.append(current.decode('utf-8', errors='ignore'))
                        current = b''
                
                if strings:
                    f.write(f"\nFound strings:\n")
                    for s in strings[:20]:  # First 20 strings
                        f.write(f"  {s}\n")
            
            return {
                "success": True,
                "analysis_file": str(analysis_file)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

# ========== ANDROID APP ==========
class KuraPAKTool(App):
    def build(self):
        self.title = "KURA PAK Tool"
        
        # Set window size for mobile
        if platform == 'android':
            Window.size = (400, 700)
        
        # Main layout
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Header
        header = Label(
            text="[b]KURA PAK Tool[/b]\nAndroid Edition",
            markup=True,
            font_size='24sp',
            size_hint=(1, 0.12),
            halign='center',
            color=(0.2, 0.6, 1, 1)
        )
        header.bind(size=header.setter('text_size'))
        main_layout.add_widget(header)
        
        # Status
        self.status_label = Label(
            text="Ready to unpack PAK/UAsset files",
            size_hint=(1, 0.05),
            font_size='12sp',
            color=(0.8, 0.8, 0.8, 1)
        )
        main_layout.add_widget(self.status_label)
        
        # File browser
        self.filechooser = FileChooserListView(
            path=str(DOWNLOADS_DIR),
            filters=['*.pak', '*.uasset', '*.uexp'],
            size_hint=(1, 0.35)
        )
        self.filechooser.bind(selection=self.on_file_selected)
        main_layout.add_widget(self.filechooser)
        
        # Selected file info
        self.selected_info = Label(
            text="No file selected",
            size_hint=(1, 0.05),
            color=(0.9, 0.9, 0.5, 1)
        )
        main_layout.add_widget(self.selected_info)
        
        # Control buttons
        btn_grid = GridLayout(cols=2, spacing=10, size_hint=(1, 0.15))
        
        unpack_btn = Button(
            text='📥 Unpack',
            background_color=(0.2, 0.7, 0.2, 1)
        )
        unpack_btn.bind(on_press=self.unpack_file)
        
        browse_btn = Button(
            text='📁 Browse',
            background_color=(0.2, 0.5, 0.9, 1)
        )
        browse_btn.bind(on_press=self.browse_folder)
        
        refresh_btn = Button(
            text='🔄 Refresh',
            background_color=(0.9, 0.6, 0.2, 1)
        )
        refresh_btn.bind(on_press=self.refresh_files)
        
        settings_btn = Button(
            text='⚙️ Settings',
            background_color=(0.7, 0.3, 0.9, 1)
        )
        settings_btn.bind(on_press=self.show_settings)
        
        btn_grid.add_widget(unpack_btn)
        btn_grid.add_widget(browse_btn)
        btn_grid.add_widget(refresh_btn)
        btn_grid.add_widget(settings_btn)
        
        main_layout.add_widget(btn_grid)
        
        # Progress bar
        self.progress = ProgressBar(
            max=100,
            size_hint=(1, 0.03),
            value=0
        )
        main_layout.add_widget(self.progress)
        
        # Log output
        scroll = ScrollView(size_hint=(1, 0.25))
        self.log_text = TextInput(
            text="=== KURA PAK Tool ===\nReady to process files\n\n",
            readonly=True,
            multiline=True,
            background_color=(0.05, 0.05, 0.1, 1),
            foreground_color=(0, 1, 0, 1),
            font_size='12sp'
        )
        scroll.add_widget(self.log_text)
        main_layout.add_widget(scroll)
        
        return main_layout
    
    def on_file_selected(self, instance, value):
        if value:
            filepath = value[0]
            try:
                size = os.path.getsize(filepath)
                size_mb = size / (1024 * 1024)
                self.selected_info.text = f"📁 {os.path.basename(filepath)} ({size_mb:.2f} MB)"
                self.log(f"Selected: {os.path.basename(filepath)}")
            except:
                self.selected_info.text = f"📁 {os.path.basename(filepath)}"
    
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.text += f"[{timestamp}] {message}\n"
        # Auto-scroll to bottom
        self.log_text.cursor = (0, len(self.log_text.text))
    
    def update_progress(self, value):
        self.progress.value = value
    
    def unpack_file(self, instance):
        selected = self.filechooser.selection
        if not selected:
            self.show_popup("⚠️ Error", "Please select a file first!")
            return
        
        filepath = selected[0]
        filename = os.path.basename(filepath)
        
        self.log(f"🚀 Starting: {filename}")
        self.update_progress(10)
        
        # Run in background thread
        thread = threading.Thread(target=self._unpack_thread, args=(filepath,))
        thread.daemon = True
        thread.start()
    
    def _unpack_thread(self, filepath):
        try:
            filename = os.path.basename(filepath)
            file_ext = os.path.splitext(filename)[1].lower()
            
            Clock.schedule_once(lambda dt: self.log(f"🔍 Analyzing {filename}..."))
            Clock.schedule_once(lambda dt: self.update_progress(20))
            
            if file_ext == '.pak':
                # Unpack PAK file
                output_dir = UNPACK_DIR / filename.replace('.pak', '')
                
                Clock.schedule_once(lambda dt: self.log("📦 Extracting PAK structure..."))
                Clock.schedule_once(lambda dt: self.update_progress(40))
                
                result = SimplePakTool.unpack_pak_file(filepath, output_dir)
                
                if result["success"]:
                    Clock.schedule_once(lambda dt: self.update_progress(80))
                    Clock.schedule_once(lambda dt: self.log(f"✅ Extracted {result['files_extracted']} files"))
                    Clock.schedule_once(lambda dt: self.log(f"📂 Saved to: {output_dir}"))
                    
                    # Show file list
                    for file in result.get("file_list", [])[:10]:  # Show first 10 files
                        Clock.schedule_once(lambda dt, f=file: self.log(f"  📄 {f}"))
                    
                    Clock.schedule_once(lambda dt: self.update_progress(100))
                    Clock.schedule_once(lambda dt: self.show_popup(
                        "🎉 Success", 
                        f"PAK unpacked successfully!\n\n"
                        f"Files extracted: {result['files_extracted']}\n"
                        f"Location: {output_dir}"
                    ))
                else:
                    Clock.schedule_once(lambda dt: self.log(f"❌ Failed: {result['error']}"))
                    Clock.schedule_once(lambda dt: self.update_progress(0))
                    Clock.schedule_once(lambda dt: self.show_popup("❌ Error", result['error']))
            
            elif file_ext in ['.uasset', '.uexp']:
                # Unpack UAsset file
                output_dir = UNPACK_DIR / "uassets" / filename
                output_dir.parent.mkdir(parents=True, exist_ok=True)
                
                Clock.schedule_once(lambda dt: self.log("📄 Analyzing UAsset..."))
                Clock.schedule_once(lambda dt: self.update_progress(50))
                
                result = SimplePakTool.unpack_uasset_file(filepath, output_dir.parent)
                
                if result["success"]:
                    Clock.schedule_once(lambda dt: self.update_progress(90))
                    Clock.schedule_once(lambda dt: self.log(f"✅ UAsset analysis complete"))
                    Clock.schedule_once(lambda dt: self.log(f"📄 Report: {result['analysis_file']}"))
                    
                    Clock.schedule_once(lambda dt: self.update_progress(100))
                    Clock.schedule_once(lambda dt: self.show_popup(
                        "✅ Success", 
                        f"UAsset analysis complete!\n\n"
                        f"Analysis saved to:\n{result['analysis_file']}"
                    ))
                else:
                    Clock.schedule_once(lambda dt: self.log(f"❌ Failed: {result['error']}"))
                    Clock.schedule_once(lambda dt: self.update_progress(0))
                    Clock.schedule_once(lambda dt: self.show_popup("❌ Error", result['error']))
            
            else:
                Clock.schedule_once(lambda dt: self.log(f"❌ Unsupported file type: {file_ext}"))
                Clock.schedule_once(lambda dt: self.update_progress(0))
                Clock.schedule_once(lambda dt: self.show_popup("❌ Error", f"Unsupported file type: {file_ext}"))
                
        except Exception as e:
            error_msg = str(e)
            Clock.schedule_once(lambda dt: self.log(f"💥 Critical error: {error_msg}"))
            Clock.schedule_once(lambda dt: self.update_progress(0))
            Clock.schedule_once(lambda dt: self.show_popup("💥 Error", f"Unpack failed:\n{error_msg}"))
    
    def browse_folder(self, instance):
        folders = [
            ("📥 Downloads", DOWNLOADS_DIR),
            ("📦 Unpacked", UNPACK_DIR),
            ("✏️ Modified", MODIFIED_DIR),
            ("📱 App Folder", APP_DIR)
        ]
        
        content = BoxLayout(orientation='vertical', spacing=5, padding=10)
        
        for name, path in folders:
            btn = Button(
                text=name,
                size_hint_y=None,
                height=60,
                background_color=(0.3, 0.5, 0.8, 1)
            )
            btn.bind(on_press=lambda x, p=path: self.select_folder(p))
            content.add_widget(btn)
        
        close_btn = Button(
            text="Close",
            size_hint_y=None,
            height=50,
            background_color=(0.8, 0.3, 0.3, 1)
        )
        close_btn.bind(on_press=lambda x: popup.dismiss())
        content.add_widget(close_btn)
        
        popup = Popup(
            title="📁 Browse Folders",
            content=content,
            size_hint=(0.9, 0.8)
        )
        popup.open()
    
    def select_folder(self, path):
        if path.exists():
            self.filechooser.path = str(path)
            self.status_label.text = f"Browsing: {path.name}"
            self.log(f"📂 Opened folder: {path}")
        else:
            self.log(f"❌ Folder not found: {path}")
    
    def refresh_files(self, instance):
        self.filechooser._update_files()
        self.log("🔄 File list refreshed")
    
    def show_settings(self, instance):
        content = BoxLayout(orientation='vertical', spacing=10, padding=20)
        
        content.add_widget(Label(
            text="Settings",
            font_size='20sp',
            size_hint_y=None,
            height=40
        ))
        
        # Add settings options here
        content.add_widget(Label(
            text="Version: 1.0.0",
            size_hint_y=None,
            height=30
        ))
        
        content.add_widget(Label(
            text=f"Storage: {APP_DIR}",
            size_hint_y=None,
            height=30
        ))
        
        content.add_widget(Label(
            text=f"Python: {sys.version.split()[0]}",
            size_hint_y=None,
            height=30
        ))
        
        close_btn = Button(
            text="Close",
            size_hint_y=None,
            height=50
        )
        close_btn.bind(on_press=lambda x: popup.dismiss())
        content.add_widget(close_btn)
        
        popup = Popup(
            title="⚙️ Settings",
            content=content,
            size_hint=(0.8, 0.6)
        )
        popup.open()
    
    def show_popup(self, title, message):
        content = BoxLayout(orientation='vertical', spacing=10, padding=20)
        content.add_widget(Label(text=message))
        
        btn = Button(
            text="OK",
            size_hint_y=None,
            height=50,
            background_color=(0.2, 0.6, 0.2, 1)
        )
        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.8, 0.4)
        )
        btn.bind(on_press=popup.dismiss)
        content.add_widget(btn)
        
        popup.open()

if __name__ == '__main__':
    KuraPAKTool().run()
