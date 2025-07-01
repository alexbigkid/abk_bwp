"""Enhanced Samsung Frame TV implementation with working upload protocol."""

import base64
import json
import logging
import socket
import ssl
import time
import uuid
from datetime import datetime
from typing import Any

import websocket
from PIL import Image
import io


class SamsungFrameTVArt:
    """Enhanced Samsung Frame TV Art Mode implementation using working protocol."""

    def __init__(self, host: str, port: int = 8002, timeout: int = 30):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.ws = None
        self.connected = False
        self.logger = logging.getLogger(__name__)

        # Art Mode WebSocket URL
        self.name = "BWP_Enhanced"
        self.b64_name = base64.b64encode(self.name.encode()).decode()
        self.art_url = f"wss://{host}:{port}/api/v2/channels/com.samsung.art-app?name={self.b64_name}&token=None"

    def connect(self) -> bool:
        """Connect to Samsung Frame TV Art Mode WebSocket."""
        try:
            self.logger.info(f"Connecting to Frame TV Art Mode at {self.host}:{self.port}")

            # Create WebSocket connection with SSL disabled
            self.ws = websocket.WebSocket(sslopt={"cert_reqs": ssl.CERT_NONE})
            self.ws.settimeout(self.timeout)
            self.ws.connect(self.art_url)

            # Wait for connection and ready events
            self._wait_for_ready()
            self.connected = True
            self.logger.info("Successfully connected to Frame TV Art Mode")
            return True

        except Exception as e:
            self.logger.error(f"Failed to connect to Frame TV: {e}")
            return False

    def _wait_for_ready(self):
        """Wait for WebSocket ready events."""
        ready_received = False
        connect_received = False

        while not (ready_received and connect_received):
            try:
                message = self.ws.recv()
                data = json.loads(message)
                event = data.get("event")

                self.logger.debug(f"Received event: {event}")

                if event == "ms.channel.connect":
                    connect_received = True
                    self.logger.debug("Channel connect event received")
                elif event == "ms.channel.ready":
                    ready_received = True
                    self.logger.debug("Channel ready event received")

            except websocket.WebSocketTimeoutException:
                raise Exception("Timeout waiting for Art Mode ready events")

    def _send_request(self, action: str, **params) -> dict[str, Any]:
        """Send request to Art Mode API and wait for response."""
        if not self.connected:
            raise Exception("Not connected to Frame TV")

        request_id = str(uuid.uuid4())
        request_data = {"request_id": request_id, "action": action, **params}

        message = {
            "method": "ms.channel.emit",
            "params": {"event": "d2d_service_message", "data": json.dumps(request_data)},
        }

        self.logger.debug(f"Sending request: {action}")
        self.ws.send(json.dumps(message))

        # Wait for response
        return self._wait_for_response(request_id)

    def _wait_for_response(self, request_id: str) -> dict[str, Any]:
        """Wait for specific response by request ID."""
        start_time = time.time()

        while time.time() - start_time < self.timeout:
            try:
                message = self.ws.recv()
                data = json.loads(message)

                if data.get("event") == "d2d_service_message":
                    response_data = json.loads(data.get("data", "{}"))
                    if response_data.get("request_id") == request_id:
                        return response_data

            except websocket.WebSocketTimeoutException:
                continue

        raise Exception(f"Timeout waiting for response to request {request_id}")

    def get_art_list(self) -> list:
        """Get list of available art on the Frame TV."""
        try:
            response = self._send_request("get_content_list", category_id="MY-C0002")
            content_list = response.get("content_list", "[]")
            return json.loads(content_list)
        except Exception as e:
            self.logger.error(f"Failed to get art list: {e}")
            return []

    def get_art_mode_status(self) -> bool:
        """Check if TV is in Art Mode."""
        try:
            response = self._send_request("get_artmode_status")
            return response.get("value") == "on"
        except Exception as e:
            self.logger.error(f"Failed to get art mode status: {e}")
            return False

    def upload_art(self, image_path: str, name: str | None = None) -> str | None:
        """Upload image to Samsung Frame TV using working two-phase protocol."""
        if not self.connected:
            raise Exception("Not connected to Frame TV")

        try:
            # Read and optimize image
            with open(image_path, "rb") as f:
                image_data = f.read()

            # Optimize image size if needed
            optimized_data = self._optimize_image(image_data)

            # Phase 1: Request upload connection info via WebSocket
            upload_id = str(uuid.uuid4())
            current_time = datetime.now().strftime("%Y:%m:%d %H:%M:%S")

            self.logger.info(f"Requesting upload connection for {name or 'image'}")

            response = self._send_request(
                "send_image",
                file_type="jpg",
                id=upload_id,
                conn_info={
                    "d2d_mode": "socket",
                    "connection_id": int(time.time() * 1000),  # Random connection ID
                    "id": upload_id,
                },
                image_date=current_time,
                matte_id="none",
                portrait_matte_id="none",
                file_size=len(optimized_data),
            )

            # Parse connection info from response
            conn_info = json.loads(response.get("conn_info", "{}"))
            upload_host = conn_info.get("ip")
            upload_port = conn_info.get("port")
            sec_key = conn_info.get("key")

            if not all([upload_host, upload_port, sec_key]):
                raise Exception("Invalid connection info received from TV")

            self.logger.info(f"Got upload connection: {upload_host}:{upload_port}")

            # Phase 2: Upload image via TLS socket
            return self._upload_via_tls(
                upload_host, upload_port, sec_key, optimized_data, upload_id, name or "BWP_Upload"
            )

        except Exception as e:
            self.logger.error(f"Failed to upload image: {e}")
            return None

    def _optimize_image(self, image_data: bytes) -> bytes:
        """Optimize image size for Frame TV upload."""
        # Convert to PIL Image
        img = Image.open(io.BytesIO(image_data))

        # Target size: under 1MB for better compatibility
        max_size = 1024 * 1024  # 1MB
        quality = 85

        while len(image_data) > max_size and quality > 30:
            output = io.BytesIO()
            img.save(output, format="JPEG", quality=quality, optimize=True)
            image_data = output.getvalue()
            quality -= 10

        self.logger.debug(f"Optimized image size: {len(image_data)} bytes")
        return image_data

    def _upload_via_tls(
        self, host: str, port: int, sec_key: str, image_data: bytes, upload_id: str, filename: str
    ) -> str:
        """Upload image data via TLS socket connection."""
        # Create TLS socket
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tls_sock = context.wrap_socket(sock)

        try:
            self.logger.info(f"Connecting to upload socket {host}:{port}")
            tls_sock.connect((host, port))

            # Prepare header
            header = {
                "num": 0,
                "total": 1,
                "fileLength": len(image_data),
                "fileName": filename,
                "fileType": "jpg",
                "secKey": sec_key,
                "version": "0.0.1",
            }

            # Send header
            header_json = json.dumps(header).encode("ascii")
            header_size = len(header_json).to_bytes(4, "big")

            tls_sock.send(header_size)
            tls_sock.send(header_json)

            # Send image data
            self.logger.info(f"Uploading {len(image_data)} bytes")
            tls_sock.send(image_data)

            self.logger.info("Image upload completed successfully")
            return upload_id

        except Exception as e:
            self.logger.error(f"Failed to upload via TLS: {e}")
            raise
        finally:
            tls_sock.close()

    def delete_art(self, content_ids: list) -> bool:
        """Delete art items by content IDs."""
        try:
            if not isinstance(content_ids, list):
                content_ids = [content_ids]

            content_list = [{"content_id": cid} for cid in content_ids]
            response = self._send_request("delete_image_list", content_id_list=content_list)

            return "content_id_list" in response
        except Exception as e:
            self.logger.error(f"Failed to delete art: {e}")
            return False

    def close(self):
        """Close WebSocket connection."""
        if self.ws:
            self.ws.close()
            self.connected = False
            self.logger.info("Disconnected from Frame TV")


# Test function
def test_enhanced_ftv():
    """Test the enhanced Frame TV implementation."""
    logging.basicConfig(level=logging.INFO)

    # Initialize Frame TV client
    ftv = SamsungFrameTVArt("192.168.0.202")

    try:
        # Connect
        if not ftv.connect():
            print("❌ Failed to connect to Frame TV")
            return

        # Get art list
        art_list = ftv.get_art_list()
        print(f"📋 Current art collection: {len(art_list)} items")

        # Check art mode status
        in_art_mode = ftv.get_art_mode_status()
        print(f"🎨 Art Mode: {'ON' if in_art_mode else 'OFF'}")

        # Test upload
        test_image = "/Users/abk/Pictures/BingWallpapers/ftv_images_today/2023-06-29_us.jpg"
        upload_id = ftv.upload_art(test_image, "BWP_Enhanced_Test")

        if upload_id:
            print(f"✅ Upload successful! ID: {upload_id}")
        else:
            print("❌ Upload failed")

    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        ftv.close()


if __name__ == "__main__":
    test_enhanced_ftv()
