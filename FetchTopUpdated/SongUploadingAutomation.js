const fs = require("fs");
const path = require("path");
const axios = require("axios");
const FormData = require("form-data");

// ===== CONFIG =====
const API_BASE = "https://music-streaming-app-jse6.onrender.com/api";
const EMAIL = "admin@test.com";
const PASSWORD = "admin123";
const DOWNLOAD_DIR = path.join(__dirname, "Download_songs"); // ✅ corrected folder

// ===== LOGIN FUNCTION =====
async function loginAdmin() {
    try {
        const res = await axios.post(`${API_BASE}/auth/admin/login`, {
            email: EMAIL,
            password: PASSWORD,
        });
        console.log("[INFO] Logged in, token received ✅");
        return res.data.token;
    } catch (err) {
        console.error("[ERROR] Login failed:", err.message);
        throw err;
    }
}

// ===== SANITIZE FILENAME =====
function sanitizeFilename(filename) {
    return filename.replace(/[^\w\- ]+/g, "").slice(0, 50);
}

// ===== UPLOAD FUNCTION =====
async function uploadSong(filePath, token) {
    const fileName = path.basename(filePath);
    const safeName = sanitizeFilename(fileName);

    const form = new FormData();
    form.append("audio", fs.createReadStream(filePath), safeName);

    try {
        const res = await axios.post(`${API_BASE}/admin/upload-automated-python`, form, {
            headers: {
                Authorization: `Bearer ${token}`,
                ...form.getHeaders(),
            },
            maxBodyLength: Infinity,
            maxContentLength: Infinity,
        });
        console.log(`[UPLOAD] ${fileName} ✅`);
        return res.data;
    } catch (err) {
        console.error(`[ERROR] Upload failed for ${fileName}: ${err.message}`);
        if (err.response) {
            console.error(err.response.data);
        }
    }
}

// ===== RECURSIVE FILE FINDER =====
function getAllMp3Files(dir) {
    let results = [];
    const list = fs.readdirSync(dir);

    list.forEach((file) => {
        const fullPath = path.join(dir, file);
        const stat = fs.statSync(fullPath);

        if (stat && stat.isDirectory()) {
            // 📂 recurse into subfolder
            results = results.concat(getAllMp3Files(fullPath));
        } else if (file.toLowerCase().endsWith(".mp3")) {
            results.push(fullPath);
        }
    });

    return results;
}

// ===== MAIN PROCESS =====
async function uploadAllSongs() {
    const token = await loginAdmin();

    console.log("[INFO] Scanning for MP3 files...");
    if (!fs.existsSync(DOWNLOAD_DIR)) {
        console.error(`[ERROR] Folder not found: ${DOWNLOAD_DIR}`);
        return;
    }

    const mp3Files = getAllMp3Files(DOWNLOAD_DIR);

    if (mp3Files.length === 0) {
        console.warn("[WARN] No MP3 files found.");
        return;
    }

    console.log(`[INFO] Found ${mp3Files.length} MP3 files ✅`);

    for (let i = 0; i < mp3Files.length; i++) {
        const filePath = mp3Files[i];
        console.log(`[${i + 1}/${mp3Files.length}] Uploading: ${path.basename(filePath)}`);
        await uploadSong(filePath, token); // ✅ uploads one by one
    }

    console.log("[INFO] 🎉 All uploads completed!");
}

module.exports = uploadAllSongs;
