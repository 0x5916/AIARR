import threading
import time
from typing import Optional
import cv2
import mediapipe as mp
import numpy as np
from tool.point_stabilizer import PointStabilizer
from queue import Queue
import os

class FaceDetector:
    def __init__(
        self,
        model_selection: int = 0,
        min_detection_confidence: float = 0.50,
        display: bool = False,
        camera_index: int = 0,
    ):
        self.face_detection = mp.solutions.face_detection.FaceDetection(
            model_selection=model_selection,
            min_detection_confidence=min_detection_confidence,
        )
        self.camera_index = camera_index
        self._ps = PointStabilizer()
        self.focus_point = (0.5, 0.5)  # Normalized focus point
        self.vector_queue = Queue(maxsize=5)  # Queue to store vectors with timestamps
        self.frame_queue = Queue(maxsize=1)  # Queue to store latest frame for UI
        self._running = True
        self.display = display

        self.log_prefix = "    FD: "
        self._lock = threading.Lock()
            
        # Start the processing thread
        self._thread = threading.Thread(target=self._run)
        self._thread.start()

    def get_running(self) -> bool:
        with self._lock:
            return self._running
        
    def set_running(self, enable: bool) -> None:
        with self._lock:
            self._running = enable
            
    def get_frame(self) -> Optional[np.ndarray]:
        """Get the latest processed frame with face detection visualization"""
        try:
            return self.frame_queue.get_nowait()
        except:
            return None

    def _run(self):
        print(self.log_prefix + "Starting camera")
        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            print(self.log_prefix + "Starting camera ok")
        except Exception as e:
            print(self.log_prefix + f"Error opening camera: {e}")
            self.set_running(False)
            return
            
        frames_processed = 0
        
        while self.get_running() and self.cap.isOpened():
            try:
                success, frame = self.cap.read()
                if not success:
                    print(self.log_prefix + "Ignoring empty camera frame.")
                    time.sleep(0.1)  # Wait a bit longer on failure
                    continue
                
                frames_processed += 1
                if frames_processed % 100 == 0:  # Log every 100 frames
                    print(self.log_prefix + f"Processed {frames_processed} frames")
                
                image_height, image_width, _ = frame.shape
                
                detections = self._detect_faces(frame)
                
                focus_pixel_coords = self._get_pixel_coords(
                    self.focus_point, image_width, image_height
                )

                stabilized_nose_tip = None
                if detections:
                    stabilized_nose_tip = self._ps.stabilize(
                        self._get_nose_tip_coords(
                            detections[0], image_width, image_height
                        )
                    )

                    vector = (
                        focus_pixel_coords[0] - stabilized_nose_tip[0],
                        focus_pixel_coords[1] - stabilized_nose_tip[1],
                        time.time()
                    )
                    
                    if self.vector_queue.full():
                        try:
                            self.vector_queue.get_nowait()  # Remove oldest vector
                        except:
                            pass
                    self.vector_queue.put(vector)
                else:
                    # No face detected
                    if not self.vector_queue.full():
                        self.vector_queue.put(None)
                    else:
                        try:
                            self.vector_queue.get_nowait()
                            self.vector_queue.put(None)
                        except:
                            pass

                # If display is enabled, prepare a frame with visualization
                if self.display:
                    try:
                        display_frame = frame.copy()
                        self.draw_image(display_frame, stabilized_nose_tip, focus_pixel_coords)
                        
                        # Update the frame queue for UI to pick up
                        if self.frame_queue.full():
                            try:
                                self.frame_queue.get_nowait()  # Remove old frame
                            except:
                                pass
                        self.frame_queue.put(display_frame)
                    except Exception as e:
                        print(self.log_prefix + f"Display preparation error: {e}")
                
                # Sleep to prevent CPU overuse and give UI thread time
                time.sleep(1/60)
                
            except Exception as e:
                print(self.log_prefix + f"Error in processing loop: {e}")

        self.set_running(False)
        print(self.log_prefix + "Face detector thread exiting")
        
        try:
            if hasattr(self, 'cap') and self.cap is not None:
                self.cap.release()
                print(self.log_prefix + "Camera released")
        except Exception as e:
            print(self.log_prefix + f"Error releasing camera: {e}")

    def _detect_faces(
        self, image: np.ndarray
    ) -> Optional[mp.solutions.face_detection.FaceDetection]:
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.face_detection.process(image_rgb)
        return results.detections if results.detections else None
    
    def draw_image(self, frame, stabilized_nose_tip, focus_pixel_coords):
        if stabilized_nose_tip is None:
            stabilized_nose_tip = focus_pixel_coords
        self._draw_stabilized_nose_tip(frame, stabilized_nose_tip)
        self._draw_vector(
            frame,
            stabilized_nose_tip,
            focus_pixel_coords,
        )

    def _get_nose_tip_coords(
        self,
        detection: mp.solutions.face_detection.FaceDetection,
        image_width: int,
        image_height: int,
    ) -> tuple[int, int]:
        nose_tip = mp.solutions.face_detection.get_key_point(
            detection, mp.solutions.face_detection.FaceKeyPoint.NOSE_TIP
        )
        return int(nose_tip.x * image_width), int(nose_tip.y * image_height)

    def _draw_stabilized_nose_tip(
        self, image: np.ndarray, stabilized_point: tuple[int, int]
    ) -> None:
        cv2.circle(
            image,
            stabilized_point,
            radius=5,
            color=(0, 255, 0),
            thickness=-1,
        )

    def _get_pixel_coords(
        self, normalized_coords: tuple[float, float], image_width: int, image_height: int
    ) -> tuple[int, int]:
        return int(normalized_coords[0] * image_width), int(
            normalized_coords[1] * image_height
        )

    def _draw_vector(
        self, image: np.ndarray, start_point: tuple[int, int], end_point: tuple[int, int]
    ) -> None:
        cv2.arrowedLine(
            image,
            start_point,
            end_point,
            color=(0, 0, 255),
            thickness=2,
            tipLength=0.05,
        )

    def get_vector(self) -> Optional[tuple[int, int, float]]:
        """Get the latest vector from the queue. Returns None if no vector is available."""
        try:
            return self.vector_queue.get_nowait()
        except:
            return None

    def stop(self):
        print(self.log_prefix + "Face detector stop called")
        # First set the running flag to false to stop the thread
        self.set_running(False)
        
        # Wait for thread to finish
        if self._thread and self._thread.is_alive():
            try:
                print(self.log_prefix + "Waiting for thread to finish...")
                self._thread.join(timeout=3)
                print(self.log_prefix + "Thread finished or timed out")
            except Exception as e:
                print(self.log_prefix + f"Error joining thread: {e}")
        
        # Clean up resources in a specific order
        # 1. Release camera
        try:
            if hasattr(self, 'cap') and self.cap is not None:
                self.cap.release()
                print(self.log_prefix + "Camera released in stop method")
        except Exception as e:
            print(self.log_prefix + f"Error releasing camera in stop: {e}")
            
        # 2. Close mediapipe resources
        try:
            self.face_detection.close()
            print(self.log_prefix + "Face detection closed")
        except Exception as e:
            print(self.log_prefix + f"Error closing face detection: {e}")
            
        print(self.log_prefix + "Face detector stopped completely")
