# Project Roadmap

## 🚀 Short Term (Maintenance)
- [ ] **Docker Container:** Bungkus skrip + dependencies (hachoir, pillow) dalam satu Docker image ringan untuk run terus di Container Manager Synology.
- [ ] **Config File:** Sokongan membaca `config.yaml` supaya tak perlu taip flag panjang (`--ignore-dirs`, `--case`) berulang kali.
- [ ] **Email Notification:** Hantar ringkasan report ke email admin NAS selepas cronjob tamat.

## 🌟 Medium Term (Features)
- [ ] **Duplicate Detection:** Tambah modul untuk kesan folder duplikat berdasarkan kandungan (bukan nama sahaja).
- [ ] **File-Level Organizing:** Keupayaan untuk menyusun *fail* ke dalam folder Tahun/Bulan (bukan sekadar rename folder bapa).
- [ ] **Local LLM Integration:** Sokongan optional untuk Ollama (Llama3/Mistral) yang run lokal di NAS untuk pembersihan nama folder pintar (pengganti Google Gemini).

## 🔮 Long Term (Vision)
- [ ] **Web Dashboard:** UI ringkas (Flask/FastAPI) untuk melihat log, statistik, dan tekan butang "Undo" tanpa masuk terminal SSH.
- [ ] **Plugin System:** Membolehkan pengguna tulis logik *custom* untuk naming convention mereka sendiri.