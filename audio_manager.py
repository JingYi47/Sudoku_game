import pygame
import os

class AudioManager:
    def __init__(self, auto_play=True):
        pygame.mixer.init()
        self.sounds = {}
        self.music_volume = 0.3
        self.sound_volume = 0.5
        self.music_enabled = True
        self.sound_enabled = True
        self.current_music = None
        self.available_music = []
        self.auto_play = auto_play
        
    def load_sounds(self, sound_dir="sounds"):
        """Load tất cả âm thanh từ thư mục"""
        sound_files = {
            'click': 'click.wav',
            'correct': 'correct.wav', 
            'wrong': 'wrong.wav',
            'win': 'win.wav',
            'hint': 'hint.wav',
            'pause': 'pause.wav'
        }
        
        # Tạo thư mục nếu chưa tồn tại
        if not os.path.exists(sound_dir):
            os.makedirs(sound_dir)
            print(f"✅ Đã tạo thư mục {sound_dir}")
            return
        
        # Tìm file nhạc nền
        self.discover_music_files(sound_dir)
        
        # Load sound effects
        for name, filename in sound_files.items():
            filepath = os.path.join(sound_dir, filename)
            if os.path.exists(filepath):
                try:
                    self.sounds[name] = pygame.mixer.Sound(filepath)
                    self.sounds[name].set_volume(self.sound_volume)
                    print(f"✅ Đã tải âm thanh: {name}")
                except pygame.error as e:
                    print(f"❌ Không thể tải âm thanh {filepath}: {e}")
            else:
                print(f"⚠️ File âm thanh không tồn tại: {filepath}")
        
        # TỰ ĐỘNG PHÁT NHẠC NỀN SAU KHI LOAD
        if self.auto_play and self.music_enabled and self.available_music:
            self.play_background_music()
    
    def discover_music_files(self, sound_dir="sounds"):
        """Tìm tất cả file nhạc nền"""
        music_extensions = ('.mp3', '.wav', '.ogg', '.m4a')
        self.available_music = []
        
        if os.path.exists(sound_dir):
            for file in os.listdir(sound_dir):
                if file.lower().endswith(music_extensions) and not file.startswith(('click', 'correct', 'wrong', 'win', 'hint', 'pause')):
                    self.available_music.append(file)
                    print(f"🎵 Tìm thấy nhạc nền: {file}")
        
        if not self.available_music:
            print("⚠️ Không tìm thấy file nhạc nền")
    
    def play_background_music(self, music_file=None):
        """Phát nhạc nền"""
        if not self.music_enabled:
            return False
            
        if music_file is None:
            if self.available_music:
                music_file = self.available_music[0]
            else:
                print("⚠️ Không có file nhạc nền nào")
                return False
        
        filepath = os.path.join("sounds", music_file)
        
        if not os.path.exists(filepath):
            print(f"⚠️ File nhạc nền không tồn tại: {filepath}")
            return False
            
        try:
            # Dừng nhạc cũ nếu đang phát
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
                
            pygame.mixer.music.load(filepath)
            pygame.mixer.music.set_volume(self.music_volume)
            pygame.mixer.music.play(-1)  # Loop
            self.current_music = music_file
            print(f"🎵 Đang phát nhạc nền: {music_file}")
            return True
        except pygame.error as e:
            print(f"❌ Không thể tải nhạc nền: {e}")
            return False
    
    def play_sound(self, name):
        """Phát âm thanh effect"""
        if self.sound_enabled and name in self.sounds:
            self.sounds[name].set_volume(self.sound_volume)
            self.sounds[name].play()
    
    def stop_background_music(self):
        """Dừng nhạc nền"""
        pygame.mixer.music.stop()
        self.current_music = None
    
    def set_music_volume(self, volume):
        self.music_volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.music_volume)
    
    def set_sound_volume(self, volume):
        self.sound_volume = max(0.0, min(1.0, volume))
        for sound in self.sounds.values():
            sound.set_volume(self.sound_volume)
    
    def toggle_music(self):
        """Bật/tắt nhạc nền"""
        self.music_enabled = not self.music_enabled
        if self.music_enabled:
            # Tiếp tục phát bài nhạc cũ nếu có
            if self.current_music:
                self.play_background_music(self.current_music)
            else:
                self.play_background_music()
            print("🔊 Nhạc nền: BẬT")
        else:
            self.stop_background_music()
            print("🔇 Nhạc nền: TẮT")
        return self.music_enabled
    
    def toggle_sound(self):
        """Bật/tắt effect"""
        self.sound_enabled = not self.sound_enabled
        status = "BẬT" if self.sound_enabled else "TẮT"
        print(f"🔊 Hiệu ứng âm thanh: {status}")
        return self.sound_enabled