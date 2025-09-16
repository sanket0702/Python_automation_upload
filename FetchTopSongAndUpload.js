import path from "path";
import { spawn } from "child_process";
import uploadAllSongs from "./SongUploadingAutomation.js";
import { fileURLToPath } from "url";

// ✅ Resolve __dirname in ESM
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// ✅ Helper to run Python script
function runPython(script) {
  return new Promise((resolve, reject) => {
    const pythonProcess = spawn("python", [script]);

    pythonProcess.stdout.on("data", (data) => {
      console.log(`[PYTHON STDOUT] ${data.toString()}`);
    });

    pythonProcess.stderr.on("data", (data) => {
      console.error(`[PYTHON STDERR] ${data.toString()}`);
    });

    pythonProcess.on("error", (err) => {
      reject(err);
    });

    pythonProcess.on("close", (code) => {
      if (code === 0) {
        resolve();
      } else {
        reject(new Error(`Python script exited with code ${code}`));
      }
    });
  });
}

// ✅ Main pipeline
export async function fetchAndUpload() {
  try {
    console.log(`[INFO] 🚀 Starting Fetch + Upload pipeline`);

    // Step 1: Run Python script 1
    await runPython(path.join(__dirname, "./FetchTopUpdated/yt_trending.py"));

 

    // Step 2: Run Python script 2
    await runPython(path.join(__dirname, "./FetchTopUpdated/download_song.py"));
    

    // Step 3: Upload songs into DB
    await uploadAllSongs();

    console.log(`[INFO] 🎉 Completed pipeline successfully`);
  } catch (err) {
    console.error(`[ERROR] Pipeline failed: ${err.message}`);
  }
}

// ✅ Run directly if file executed via `node thisFile.js`

  fetchAndUpload();

