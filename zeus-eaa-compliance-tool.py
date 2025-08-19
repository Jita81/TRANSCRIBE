#!/usr/bin/env python3
"""
Zeus Network EAA Compliance Backend Subtitle Processing Pipeline
High-performance multi-pass transcription with AI consolidation
"""

import os
import json
import hashlib
import asyncio
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import torch
import whisper
from transformers import pipeline, AutoModelForSeq2SeqLM, AutoTokenizer
import webvtt
import srt
from rapidfuzz import fuzz
import ffmpeg
import pickle
from queue import Queue
import threading
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class SubtitleSegment:
    """Represents a single subtitle segment with timing"""
    start_time: float
    end_time: float
    text: str
    confidence: float = 1.0
    speaker: Optional[str] = None

@dataclass
class VideoJob:
    """Represents a video processing job"""
    video_path: Path
    job_id: str
    status: str = "pending"
    progress: float = 0.0
    created_at: datetime = None
    completed_at: datetime = None

class WhisperTranscriber:
    """High-performance Whisper-based transcription with multiple passes"""
    
    def __init__(self, model_size: str = "large-v3", device: str = None):
        """
        Initialize Whisper model for transcription
        
        Args:
            model_size: Whisper model size (tiny, base, small, medium, large, large-v2, large-v3)
            device: Device to run on (cuda, cpu, or None for auto-detect)
        """
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        
        logger.info(f"Loading Whisper model '{model_size}' on {device}")
        self.model = whisper.load_model(model_size, device=device)
        self.device = device
        
    def transcribe_single_pass(self, audio_path: str, **kwargs) -> Dict:
        """
        Single transcription pass with Whisper
        
        Args:
            audio_path: Path to audio file
            **kwargs: Additional Whisper parameters
            
        Returns:
            Transcription result dictionary
        """
        default_params = {
            "task": "transcribe",
            "language": None,  # Auto-detect
            "word_timestamps": True,
            "verbose": False,
            "temperature": 0.0,  # Deterministic for consistency
            "compression_ratio_threshold": 2.4,
            "logprob_threshold": -1.0,
            "no_speech_threshold": 0.6,
            "condition_on_previous_text": True,
            "initial_prompt": None,
            "decode_options": {
                "beam_size": 5,
                "best_of": 5,
                "patience": 1.0,
                "length_penalty": 1.0,
                "temperature": 0.0,
                "compression_ratio_threshold": 2.4,
                "logprob_threshold": -1.0,
                "no_speech_threshold": 0.6,
            }
        }
        
        params = {**default_params, **kwargs}
        return self.model.transcribe(audio_path, **params)
    
    def multi_pass_transcribe(self, audio_path: str, num_passes: int = 5) -> List[Dict]:
        """
        Perform multiple transcription passes with different parameters
        
        Args:
            audio_path: Path to audio file
            num_passes: Number of transcription passes
            
        Returns:
            List of transcription results
        """
        logger.info(f"Starting {num_passes}-pass transcription for {audio_path}")
        results = []
        
        # Different temperature values for diversity
        temperatures = [0.0, 0.2, 0.4, 0.6, 0.8][:num_passes]
        
        with ThreadPoolExecutor(max_workers=min(num_passes, 3)) as executor:
            futures = []
            for i, temp in enumerate(temperatures):
                params = {
                    "temperature": temp,
                    "initial_prompt": "This is a video with clear speech." if i == 0 else None,
                    "decode_options": {
                        "beam_size": 5 if i < 2 else 3,  # Vary beam size
                        "best_of": 5,
                        "patience": 1.0,
                        "temperature": temp,
                    }
                }
                
                future = executor.submit(self.transcribe_single_pass, audio_path, **params)
                futures.append(future)
            
            for i, future in enumerate(futures):
                result = future.result()
                results.append(result)
                logger.info(f"Completed pass {i+1}/{num_passes}")
        
        return results

class TranscriptionConsolidator:
    """Consolidates multiple transcription passes using AI and voting mechanisms"""
    
    def __init__(self, model_name: str = "facebook/bart-large-mnli"):
        """
        Initialize consolidation model
        
        Args:
            model_name: Hugging Face model for text consolidation
        """
        logger.info(f"Loading consolidation model: {model_name}")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Load a model for semantic similarity and consolidation
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name).to(self.device)
        
    def align_segments(self, transcriptions: List[Dict]) -> List[List[SubtitleSegment]]:
        """
        Align segments from multiple transcriptions
        
        Args:
            transcriptions: List of Whisper transcription results
            
        Returns:
            Aligned segments for consolidation
        """
        all_segments = []
        
        for transcription in transcriptions:
            segments = []
            for segment in transcription.get("segments", []):
                seg = SubtitleSegment(
                    start_time=segment["start"],
                    end_time=segment["end"],
                    text=segment["text"].strip(),
                    confidence=1.0 - segment.get("no_speech_prob", 0.0)
                )
                segments.append(seg)
            all_segments.append(segments)
        
        return all_segments
    
    def consolidate_text(self, texts: List[str], weights: List[float] = None) -> str:
        """
        Consolidate multiple text versions using weighted voting and NLP
        
        Args:
            texts: List of text variations
            weights: Confidence weights for each text
            
        Returns:
            Consolidated text
        """
        if not texts:
            return ""
        
        if len(texts) == 1:
            return texts[0]
        
        if weights is None:
            weights = [1.0] * len(texts)
        
        # Use fuzzy matching to find consensus
        scores = {}
        for i, text1 in enumerate(texts):
            score = 0
            for j, text2 in enumerate(texts):
                if i != j:
                    similarity = fuzz.ratio(text1, text2) / 100.0
                    score += similarity * weights[j]
            scores[text1] = score
        
        # Return the text with highest consensus score
        best_text = max(scores.keys(), key=lambda x: scores[x])
        
        # Clean up the text
        best_text = best_text.strip()
        
        # Ensure proper capitalization
        if best_text and best_text[0].islower():
            best_text = best_text[0].upper() + best_text[1:]
        
        return best_text
    
    def consolidate_timing(self, timings: List[Tuple[float, float]]) -> Tuple[float, float]:
        """
        Consolidate timing information from multiple passes
        
        Args:
            timings: List of (start, end) time tuples
            
        Returns:
            Consolidated (start, end) timing
        """
        if not timings:
            return (0.0, 0.0)
        
        starts = [t[0] for t in timings]
        ends = [t[1] for t in timings]
        
        # Use median for robustness against outliers
        start = np.median(starts)
        end = np.median(ends)
        
        # Ensure minimum duration
        if end - start < 0.5:
            end = start + 0.5
        
        return (float(start), float(end))
    
    def consolidate_segments(self, aligned_segments: List[List[SubtitleSegment]]) -> List[SubtitleSegment]:
        """
        Consolidate aligned segments from multiple passes
        
        Args:
            aligned_segments: List of segment lists from each pass
            
        Returns:
            Consolidated subtitle segments
        """
        if not aligned_segments:
            return []
        
        # Group segments by approximate timing
        time_groups = {}
        tolerance = 0.5  # 500ms tolerance for grouping
        
        for segments in aligned_segments:
            for segment in segments:
                # Find matching time group
                matched = False
                for key in time_groups:
                    if abs(key - segment.start_time) < tolerance:
                        time_groups[key].append(segment)
                        matched = True
                        break
                
                if not matched:
                    time_groups[segment.start_time] = [segment]
        
        # Consolidate each time group
        consolidated = []
        for start_time in sorted(time_groups.keys()):
            segments = time_groups[start_time]
            
            texts = [s.text for s in segments]
            confidences = [s.confidence for s in segments]
            timings = [(s.start_time, s.end_time) for s in segments]
            
            consolidated_text = self.consolidate_text(texts, confidences)
            consolidated_timing = self.consolidate_timing(timings)
            
            if consolidated_text:  # Only add non-empty segments
                consolidated.append(SubtitleSegment(
                    start_time=consolidated_timing[0],
                    end_time=consolidated_timing[1],
                    text=consolidated_text,
                    confidence=np.mean(confidences)
                ))
        
        return consolidated

class TimingValidator:
    """Validates and corrects subtitle timing synchronization"""
    
    def __init__(self, video_path: str):
        """
        Initialize timing validator with video information
        
        Args:
            video_path: Path to video file
        """
        self.video_path = video_path
        self.video_info = self._get_video_info()
        
    def _get_video_info(self) -> Dict:
        """Extract video information using ffmpeg-python"""
        try:
            probe = ffmpeg.probe(self.video_path)
            video_stream = next((stream for stream in probe['streams'] 
                               if stream['codec_type'] == 'video'), None)
            
            if video_stream:
                return {
                    'duration': float(probe['format']['duration']),
                    'fps': eval(video_stream['r_frame_rate']),
                    'width': video_stream['width'],
                    'height': video_stream['height']
                }
        except Exception as e:
            logger.warning(f"Could not extract video info: {e}")
            return {}
    
    def validate_segments(self, segments: List[SubtitleSegment]) -> List[SubtitleSegment]:
        """
        Validate and correct segment timing
        
        Args:
            segments: List of subtitle segments
            
        Returns:
            Validated and corrected segments
        """
        if not segments:
            return segments
        
        validated = []
        video_duration = self.video_info.get('duration', float('inf'))
        
        for i, segment in enumerate(segments):
            # Ensure segment is within video bounds
            segment.start_time = max(0, segment.start_time)
            segment.end_time = min(video_duration, segment.end_time)
            
            # Ensure minimum duration (500ms)
            if segment.end_time - segment.start_time < 0.5:
                segment.end_time = segment.start_time + 0.5
            
            # Ensure no overlap with previous segment
            if validated and segment.start_time < validated[-1].end_time:
                segment.start_time = validated[-1].end_time + 0.01
            
            # Maximum subtitle duration (7 seconds)
            if segment.end_time - segment.start_time > 7.0:
                segment.end_time = segment.start_time + 7.0
            
            validated.append(segment)
        
        return validated
    
    def optimize_reading_speed(self, segments: List[SubtitleSegment], 
                              target_wpm: int = 160) -> List[SubtitleSegment]:
        """
        Optimize subtitle duration for comfortable reading speed
        
        Args:
            segments: List of subtitle segments
            target_wpm: Target words per minute (EAA recommends 160-180)
            
        Returns:
            Optimized segments
        """
        optimized = []
        
        for segment in segments:
            word_count = len(segment.text.split())
            if word_count == 0:
                continue
            
            # Calculate required duration for target reading speed
            required_duration = (word_count / target_wpm) * 60.0
            required_duration = max(required_duration, 1.0)  # Minimum 1 second
            
            current_duration = segment.end_time - segment.start_time
            
            # Adjust if reading speed is too fast
            if current_duration < required_duration:
                segment.end_time = segment.start_time + required_duration
            
            optimized.append(segment)
        
        return optimized

class SubtitleExporter:
    """Exports subtitles in various formats with EAA compliance"""
    
    @staticmethod
    def to_srt(segments: List[SubtitleSegment], output_path: str) -> str:
        """
        Export segments to SRT format
        
        Args:
            segments: List of subtitle segments
            output_path: Output file path
            
        Returns:
            Path to exported file
        """
        srt_segments = []
        
        for i, segment in enumerate(segments, 1):
            start = timedelta(seconds=segment.start_time)
            end = timedelta(seconds=segment.end_time)
            
            srt_segment = srt.Subtitle(
                index=i,
                start=start,
                end=end,
                content=segment.text
            )
            srt_segments.append(srt_segment)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(srt.compose(srt_segments))
        
        logger.info(f"Exported SRT to {output_path}")
        return output_path
    
    @staticmethod
    def to_webvtt(segments: List[SubtitleSegment], output_path: str) -> str:
        """
        Export segments to WebVTT format
        
        Args:
            segments: List of subtitle segments
            output_path: Output file path
            
        Returns:
            Path to exported file
        """
        vtt = webvtt.WebVTT()
        
        for segment in segments:
            caption = webvtt.Caption(
                start=SubtitleExporter._seconds_to_vtt_time(segment.start_time),
                end=SubtitleExporter._seconds_to_vtt_time(segment.end_time),
                text=segment.text
            )
            vtt.captions.append(caption)
        
        vtt.save(output_path)
        logger.info(f"Exported WebVTT to {output_path}")
        return output_path
    
    @staticmethod
    def _seconds_to_vtt_time(seconds: float) -> str:
        """Convert seconds to WebVTT time format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
    
    @staticmethod
    def to_json(segments: List[SubtitleSegment], output_path: str) -> str:
        """
        Export segments to JSON format for further processing
        
        Args:
            segments: List of subtitle segments
            output_path: Output file path
            
        Returns:
            Path to exported file
        """
        data = {
            "format": "zeus-eaa-compliant",
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "segments": [
                {
                    "start": segment.start_time,
                    "end": segment.end_time,
                    "text": segment.text,
                    "confidence": segment.confidence,
                    "speaker": segment.speaker
                }
                for segment in segments
            ],
            "metadata": {
                "total_segments": len(segments),
                "duration": segments[-1].end_time if segments else 0,
                "average_confidence": np.mean([s.confidence for s in segments]) if segments else 0
            }
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported JSON to {output_path}")
        return output_path

class VideoProcessor:
    """Main video processing pipeline orchestrator"""
    
    def __init__(self, 
                 input_dir: str = "/mnt/zeus/videos/input",
                 output_dir: str = "/mnt/zeus/videos/output",
                 temp_dir: str = "/tmp/zeus_processing",
                 whisper_model: str = "large-v3",
                 num_passes: int = 5):
        """
        Initialize video processor
        
        Args:
            input_dir: Directory to watch for input videos
            output_dir: Directory for processed subtitles
            temp_dir: Temporary directory for processing
            whisper_model: Whisper model size to use
            num_passes: Number of transcription passes
        """
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.temp_dir = Path(temp_dir)
        self.num_passes = num_passes
        
        # Create directories if they don't exist
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.transcriber = WhisperTranscriber(model_size=whisper_model)
        self.consolidator = TranscriptionConsolidator()
        self.exporter = SubtitleExporter()
        
        # Job queue
        self.job_queue = Queue()
        self.active_jobs = {}
        
        logger.info(f"Video processor initialized. Watching {input_dir}")
    
    def extract_audio(self, video_path: Path) -> Path:
        """
        Extract audio from video file
        
        Args:
            video_path: Path to video file
            
        Returns:
            Path to extracted audio file
        """
        audio_path = self.temp_dir / f"{video_path.stem}_audio.wav"
        
        logger.info(f"Extracting audio from {video_path}")
        
        stream = ffmpeg.input(str(video_path))
        stream = ffmpeg.output(stream, str(audio_path), 
                              acodec='pcm_s16le', 
                              ac=1, 
                              ar='16k')
        ffmpeg.run(stream, overwrite_output=True, quiet=True)
        
        logger.info(f"Audio extracted to {audio_path}")
        return audio_path
    
    def process_video(self, video_path: Path) -> Dict:
        """
        Process a single video through the entire pipeline
        
        Args:
            video_path: Path to video file
            
        Returns:
            Processing results dictionary
        """
        job_id = hashlib.md5(str(video_path).encode()).hexdigest()
        
        try:
            # Update job status
            self.active_jobs[job_id] = VideoJob(
                video_path=video_path,
                job_id=job_id,
                status="extracting_audio",
                created_at=datetime.now()
            )
            
            # Step 1: Extract audio
            audio_path = self.extract_audio(video_path)
            self.active_jobs[job_id].progress = 10.0
            
            # Step 2: Multi-pass transcription
            self.active_jobs[job_id].status = "transcribing"
            transcriptions = self.transcriber.multi_pass_transcribe(
                str(audio_path), 
                num_passes=self.num_passes
            )
            self.active_jobs[job_id].progress = 60.0
            
            # Step 3: Consolidate transcriptions
            self.active_jobs[job_id].status = "consolidating"
            aligned_segments = self.consolidator.align_segments(transcriptions)
            consolidated_segments = self.consolidator.consolidate_segments(aligned_segments)
            self.active_jobs[job_id].progress = 80.0
            
            # Step 4: Validate and optimize timing
            self.active_jobs[job_id].status = "validating_timing"
            validator = TimingValidator(str(video_path))
            validated_segments = validator.validate_segments(consolidated_segments)
            optimized_segments = validator.optimize_reading_speed(validated_segments)
            self.active_jobs[job_id].progress = 90.0
            
            # Step 5: Export in multiple formats
            self.active_jobs[job_id].status = "exporting"
            output_base = self.output_dir / video_path.stem
            
            results = {
                "video": str(video_path),
                "job_id": job_id,
                "segments": len(optimized_segments),
                "duration": optimized_segments[-1].end_time if optimized_segments else 0,
                "confidence": np.mean([s.confidence for s in optimized_segments]) if optimized_segments else 0,
                "outputs": {
                    "srt": self.exporter.to_srt(optimized_segments, f"{output_base}.srt"),
                    "vtt": self.exporter.to_webvtt(optimized_segments, f"{output_base}.vtt"),
                    "json": self.exporter.to_json(optimized_segments, f"{output_base}.json")
                }
            }
            
            # Cleanup temp files
            if audio_path.exists():
                audio_path.unlink()
            
            # Update job status
            self.active_jobs[job_id].status = "completed"
            self.active_jobs[job_id].progress = 100.0
            self.active_jobs[job_id].completed_at = datetime.now()
            
            logger.info(f"Successfully processed {video_path.name}")
            return results
            
        except Exception as e:
            logger.error(f"Error processing {video_path}: {e}")
            if job_id in self.active_jobs:
                self.active_jobs[job_id].status = "failed"
            raise
    
    def watch_directory(self):
        """Watch input directory for new videos to process"""
        logger.info(f"Starting directory watcher for {self.input_dir}")
        
        processed_files = set()
        
        while True:
            try:
                # Check for new video files
                video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv'}
                
                for video_file in self.input_dir.iterdir():
                    if video_file.suffix.lower() in video_extensions:
                        if video_file not in processed_files:
                            logger.info(f"New video detected: {video_file.name}")
                            self.job_queue.put(video_file)
                            processed_files.add(video_file)
                
                # Process queue
                while not self.job_queue.empty():
                    video_path = self.job_queue.get()
                    try:
                        results = self.process_video(video_path)
                        
                        # Move processed video to archive
                        archive_dir = self.output_dir / "processed_videos"
                        archive_dir.mkdir(exist_ok=True)
                        archive_path = archive_dir / video_path.name
                        video_path.rename(archive_path)
                        
                        logger.info(f"Video archived to {archive_path}")
                        
                    except Exception as e:
                        logger.error(f"Failed to process {video_path}: {e}")
                        
                        # Move failed video to error directory
                        error_dir = self.output_dir / "failed_videos"
                        error_dir.mkdir(exist_ok=True)
                        error_path = error_dir / video_path.name
                        video_path.rename(error_path)
                
                # Sleep before next scan
                time.sleep(10)
                
            except KeyboardInterrupt:
                logger.info("Shutting down directory watcher")
                break
            except Exception as e:
                logger.error(f"Error in directory watcher: {e}")
                time.sleep(30)  # Wait longer on error

class EAAComplianceChecker:
    """Validates subtitles against EAA/WCAG 2.1 AA requirements"""
    
    @staticmethod
    def check_compliance(segments: List[SubtitleSegment]) -> Dict:
        """
        Check subtitle compliance with EAA requirements
        
        Args:
            segments: List of subtitle segments
            
        Returns:
            Compliance report dictionary
        """
        report = {
            "compliant": True,
            "score": 100,
            "issues": [],
            "warnings": []
        }
        
        if not segments:
            report["compliant"] = False
            report["score"] = 0
            report["issues"].append("No subtitle segments found")
            return report
        
        # Check reading speed (WCAG 2.1 AA recommends 160-180 WPM)
        for segment in segments:
            words = len(segment.text.split())
            duration = segment.end_time - segment.start_time
            if duration > 0:
                wpm = (words / duration) * 60
                if wpm > 200:
                    report["warnings"].append(
                        f"Segment at {segment.start_time:.1f}s has high reading speed: {wpm:.0f} WPM"
                    )
                    report["score"] -= 2
                elif wpm > 180:
                    report["warnings"].append(
                        f"Segment at {segment.start_time:.1f}s exceeds recommended speed: {wpm:.0f} WPM"
                    )
                    report["score"] -= 1
        
        # Check minimum display duration (at least 1 second)
        for segment in segments:
            duration = segment.end_time - segment.start_time
            if duration < 1.0:
                report["issues"].append(
                    f"Segment at {segment.start_time:.1f}s is too short: {duration:.2f}s"
                )
                report["score"] -= 5
        
        # Check maximum subtitle length (recommended max 2 lines, ~80 chars)
        for segment in segments:
            if len(segment.text) > 80:
                report["warnings"].append(
                    f"Segment at {segment.start_time:.1f}s may be too long: {len(segment.text)} chars"
                )
                report["score"] -= 1
        
        # Check for gaps in coverage
        for i in range(1, len(segments)):
            gap = segments[i].start_time - segments[i-1].end_time
            if gap > 2.0:  # More than 2 seconds gap
                report["warnings"].append(
                    f"Large gap ({gap:.1f}s) between segments at {segments[i-1].end_time:.1f}s"
                )
        
        # Update compliance status
        report["score"] = max(0, report["score"])
        report["compliant"] = report["score"] >= 90 and len(report["issues"]) == 0
        
        return report

def main():
    """Main entry point for the subtitle processing pipeline"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="Zeus EAA Subtitle Processing Pipeline")
    parser.add_argument("--input-dir", default="/mnt/zeus/videos/input",
                       help="Input directory for videos")
    parser.add_argument("--output-dir", default="/mnt/zeus/videos/output",
                       help="Output directory for subtitles")
    parser.add_argument("--model", default="large-v3",
                       choices=["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"],
                       help="Whisper model size")
    parser.add_argument("--passes", type=int, default=5,
                       help="Number of transcription passes")
    parser.add_argument("--single", type=str,
                       help="Process a single video file instead of watching directory")
    
    args = parser.parse_args()
    
    # Initialize processor
    processor = VideoProcessor(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        whisper_model=args.model,
        num_passes=args.passes
    )
    
    if args.single:
        # Process single file
        video_path = Path(args.single)
        if not video_path.exists():
            logger.error(f"Video file not found: {video_path}")
            return
        
        logger.info(f"Processing single video: {video_path}")
        results = processor.process_video(video_path)
        
        # Check compliance
        with open(results["outputs"]["json"], 'r') as f:
            data = json.load(f)
        
        segments = [
            SubtitleSegment(
                start_time=s["start"],
                end_time=s["end"],
                text=s["text"],
                confidence=s["confidence"]
            )
            for s in data["segments"]
        ]
        
        compliance = EAAComplianceChecker.check_compliance(segments)
        
        print("\n" + "="*60)
        print("PROCESSING COMPLETE")
        print("="*60)
        print(f"Video: {video_path.name}")
        print(f"Segments: {results['segments']}")
        print(f"Duration: {results['duration']:.1f}s")
        print(f"Average Confidence: {results['confidence']:.2%}")
        print(f"\nOutputs:")
        for format_name, path in results['outputs'].items():
            print(f"  - {format_name.upper()}: {path}")
        print(f"\nEAA Compliance: {'✓ PASSED' if compliance['compliant'] else '✗ FAILED'}")
        print(f"Compliance Score: {compliance['score']}/100")
        
        if compliance['issues']:
            print("\nIssues:")
            for issue in compliance['issues']:
                print(f"  ✗ {issue}")
        
        if compliance['warnings']:
            print("\nWarnings:")
            for warning in compliance['warnings']:
                print(f"  ⚠ {warning}")
        
    else:
        # Watch directory mode
        logger.info("Starting directory watch mode")
        processor.watch_directory()

if __name__ == "__main__":
    main()
