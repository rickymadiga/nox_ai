import asyncio
import uuid
import os
from typing import Dict, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class VideoJobManager:
    def __init__(self, output_dir: str = "./videos"):
        self.queue = asyncio.Queue()
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self._worker_task = None
        self.output_dir = Path(output_dir)
        
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            print(f"[VideoJobManager] ✅ Output dir: {self.output_dir.absolute()}")
        except Exception as e:
            print(f"[VideoJobManager] ❌ Directory error: {e}")
            raise

    async def submit(self, prompt: str) -> str:
        job_id = f"vid_{uuid.uuid4().hex[:8]}"
        self.jobs[job_id] = {
            "status": "queued",
            "prompt": prompt,
            "result": None,
            "error": None,
            "file_path": None,
        }
        await self.queue.put({"job_id": job_id, "prompt": prompt})
        return job_id

    def get(self, job_id: str) -> Dict[str, Any]:
        return self.jobs.get(job_id, {"status": "not_found"})

    def start_worker(self):
        if self._worker_task is None or self._worker_task.done():
            self._worker_task = asyncio.create_task(self.worker())

    async def worker(self):
        print("[VideoJobManager] 🚀 Worker started")
        while True:
            try:
                job = await self.queue.get()
                job_id = job["job_id"]
                prompt = job["prompt"]

                self.jobs[job_id]["status"] = "processing"
                print(f"[VideoJobManager] 🔄 Processing: {job_id}")

                try:
                    file_path = await self.generate_video(job_id, prompt)
                    self.jobs[job_id]["status"] = "done"
                    self.jobs[job_id]["result"] = file_path
                    self.jobs[job_id]["file_path"] = file_path
                    
                    file_size = os.path.getsize(file_path)
                    print(f"[VideoJobManager] ✅ Job {job_id} done: {file_size} bytes")
                    
                except Exception as e:
                    self.jobs[job_id]["status"] = "error"
                    self.jobs[job_id]["error"] = str(e)
                    print(f"[VideoJobManager] ❌ Job {job_id} failed: {e}")

                self.queue.task_done()
            except Exception as e:
                print(f"[VideoJobManager] ⚠️ Worker error: {e}")
                await asyncio.sleep(1)

    async def generate_video(self, job_id: str, prompt: str) -> str:
        """Generate video using moviepy (no FFmpeg needed)"""
        output_file = self.output_dir / f"video_{job_id}.mp4"
        
        print(f"[VideoJobManager] 🎬 Generating: {output_file}")
        
        try:
            from moviepy.editor import ColorClip
            
            def _generate():
                # Create 5-second blue video
                clip = ColorClip(
                    size=(1920, 1080),
                    color=(100, 150, 255)  # Blue
                ).set_duration(5)
                
                # Write to file
                clip.write_videofile(
                    str(output_file),
                    fps=24,
                    verbose=False,
                    logger=None
                )
            
            # Run in thread (moviepy blocks)
            await asyncio.to_thread(_generate)
            
            file_size = os.path.getsize(output_file)
            print(f"[VideoJobManager] ✅ Created: {file_size} bytes")
            
            return str(output_file)
            
        except ImportError:
            raise RuntimeError(
                "moviepy not installed. Run:\n"
                "pip install moviepy imageio imageio-ffmpeg"
            )
        except Exception as e:
            print(f"[VideoJobManager] ❌ Generation error: {e}")
            raise

video_manager = VideoJobManager()