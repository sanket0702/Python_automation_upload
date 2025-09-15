import fs from "fs";
import path from "path";
import axios from "axios";
import FormData from "form-data";
import { fileURLToPath } from "url";

// ===== CONFIG =====
const API_BASE = "https://music-streaming-app-jse6.onrender.com/api";
const EMAIL = "admin@test.com";
const PASSWORD = "admin123";

// ✅ Cross-platform __dirname (fixes %20 in Windows paths)
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// ✅ Use decoded and normalized path
const DOWNLOAD_DIR = path.normalize(path.join(__dirname, "Download_songs"));

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
    console.error("[ERROR] Login failed:", err.response?.data || err.message);
    throw err;
  }
}

// ===== SANITIZE FILENAME =====
function sanitizeFilename(filename) {
  // Keep letters, numbers, dashes, spaces, dots, and underscores
  return filename.replace(/[^\w\- .]+/g, "").slice(0, 80);
}

// ===== UPLOAD FUNCTION =====
async function uploadSong(filePath, token) {
  const fileName = path.basename(filePath);
  const safeName = sanitizeFilename(fileName);

  const form = new FormData();
  form.append("audio", fs.createReadStream(filePath), safeName);

  try {
    const res = await axios.post(`${API_BASE}/admin/upload-automated-python-yt`, form, {
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
      console.error("Response:", err.response.data);
    }
  }
}

// ===== RECURSIVE FILE FINDER =====
function getAllMp3Files(dir) {
  let results = [];
  const list = fs.readdirSync(dir);

  for (const file of list) {
    const fullPath = path.join(dir, file);
    const stat = fs.statSync(fullPath);

    if (stat.isDirectory()) {
      results = results.concat(getAllMp3Files(fullPath));
    } else if (file.toLowerCase().endsWith(".mp3")) {
      results.push(fullPath);
    }
  }
  return results;
}

// ===== MAIN PROCESS =====
export default async function uploadAllSongs() {
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
    await uploadSong(filePath, token);
  }

  console.log("[INFO] 🎉 All uploads completed!");
}
