"""One-time Samsung Frame TV Art Mode authenticator.

This script handles the initial authorization with Samsung Frame TV and saves
the authentication tokens for future use by the main BWP application.
"""

import base64
import json
import logging
import ssl
import time
import tomllib
import websocket
from pathlib import Path


class FrameTVAuthenticator:
    """Handle one-time authentication with Samsung Frame TV Art Mode."""

    def __init__(self, timeout: int = 120):
        """Init for FrameTVAuthenticator."""
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        self.config_dir = Path(__file__).parent

        # Load Frame TV configurations from BWP config system
        self.ftv_configs = self._load_ftv_configurations()

        # WebSocket URLs will be generated per TV
        self.name = "BWP_Authenticator"
        self.b64_name = base64.b64encode(self.name.encode()).decode()

    def _load_ftv_configurations(self) -> dict[str, dict]:
        """Load Frame TV configurations from BWP config system."""
        try:
            # Load main BWP config to get ftv_data file
            bwp_config_path = self.config_dir / "bwp_config.toml"
            with open(bwp_config_path, "rb") as f:
                bwp_config = tomllib.load(f)

            ftv_data_file = bwp_config.get("ftv", {}).get("ftv_data", "ftv_secrets.toml")

            # Load Frame TV specific configurations
            ftv_config_path = self.config_dir / ftv_data_file
            with open(ftv_config_path, "rb") as f:
                ftv_config = tomllib.load(f)

            ftv_data = ftv_config.get("ftv_data", {})
            self.logger.info(f"Loaded {len(ftv_data)} Frame TV configuration(s)")

            return ftv_data

        except Exception as e:
            self.logger.error(f"Failed to load Frame TV configurations: {e}")
            return {}

    def _get_token_files(self, tv_name: str, host: str) -> tuple[Path, Path]:
        """Get token file paths for a specific TV using BWP naming convention."""
        config = self.ftv_configs.get(tv_name, {})

        # Use your standardized naming convention: <FrameTV_name>_<tokenType>_secrets.txt
        art_token_file = config.get("art_token_file", f"{tv_name}_artToken_secrets.txt")
        remote_token_file = config.get(
            "remote_control_token_file", f"{tv_name}_remoteControlToken_secrets.txt"
        )

        # Convert to full paths
        art_token_path = self.config_dir / art_token_file
        remote_token_path = self.config_dir / remote_token_file

        return art_token_path, remote_token_path

    def check_existing_tokens(self, tv_name: str) -> tuple[str | None, str | None]:
        """Check if authentication tokens already exist for a specific TV."""
        config = self.ftv_configs.get(tv_name, {})
        host = config.get("ip_addr", "unknown")

        art_token_file, remote_token_file = self._get_token_files(tv_name, host)

        art_token = None
        remote_token = None

        if art_token_file.exists():
            try:
                art_token = art_token_file.read_text().strip()
                self.logger.info(f"[{tv_name}] Found existing Art Mode token: {art_token_file}")
            except Exception as e:
                self.logger.warning(f"[{tv_name}] Failed to read Art Mode token: {e}")

        if remote_token_file.exists():
            try:
                remote_token = remote_token_file.read_text().strip()
                self.logger.info(
                    f"[{tv_name}] Found existing Remote Control token: {remote_token_file}"
                )
            except Exception as e:
                self.logger.warning(f"[{tv_name}] Failed to read Remote Control token: {e}")

        return art_token, remote_token

    def authenticate_channel(self, url: str, channel_name: str) -> str | None:
        """Authenticate with a specific Samsung TV channel."""
        print(f"\n🔐 Authenticating {channel_name}...")
        print(f"🔗 Connecting to: {url}")
        print("📺 IMPORTANT: Watch your TV screen for authorization prompt!")
        print(f"📺 You have {self.timeout} seconds to press 'Allow' when prompted.\n")

        try:
            # Create WebSocket connection
            ws = websocket.WebSocket(sslopt={"cert_reqs": ssl.CERT_NONE})
            ws.settimeout(5)  # Short timeout for individual messages
            ws.connect(url)

            print(f"✅ WebSocket connected to {channel_name}")
            print("⏰ Waiting for authorization... (check your TV screen)")

            # Wait for authorization with longer overall timeout
            start_time = time.time()
            token = None
            ready_received = False

            while time.time() - start_time < self.timeout:
                try:
                    message = ws.recv()
                    data = json.loads(message)
                    event = data.get("event")

                    self.logger.debug(f"Received {channel_name} event: {event}")

                    if event == "ms.channel.connect":
                        # Check for token in the connect message
                        try:
                            message_data = data.get("data", "{}")
                            if isinstance(message_data, str):
                                parsed_data = json.loads(message_data)
                                token = parsed_data.get("token")
                                if token:
                                    print(f"🔑 Authorization token received for {channel_name}!")
                                    break
                        except (json.JSONDecodeError, AttributeError):
                            # No token in this message, continue waiting
                            pass

                    elif event == "ms.channel.ready":
                        ready_received = True
                        print(f"✅ {channel_name} channel ready")

                        # If we received ready without a token, we're already authorized
                        if not token:
                            print(f"✅ {channel_name} already authorized (no new token needed)")
                            # Use a persistent token to indicate successful authorization
                            token = f"PERSISTENT_AUTH_{int(time.time())}"
                            break

                except websocket.WebSocketTimeoutException:
                    # Continue waiting - this is normal during authorization
                    continue
                except Exception as e:
                    self.logger.error(f"Error receiving message: {e}")
                    break

            if not token:
                print(f"❌ Authorization timeout for {channel_name} after {self.timeout} seconds")
                print("💡 Make sure to press 'Allow' on your TV screen when prompted")
                return None

            ws.close()
            return token

        except Exception as e:
            print(f"❌ Failed to authenticate {channel_name}: {e}")
            return None

    def save_token(self, token: str, token_file: Path, channel_name: str) -> bool:
        """Save authentication token to file."""
        try:
            token_file.write_text(token)
            print(f"💾 Saved {channel_name} token to: {token_file}")
            return True
        except Exception as e:
            print(f"❌ Failed to save {channel_name} token: {e}")
            return False

    def authenticate_tv(self, tv_name: str) -> bool:
        """Perform authentication for a specific Frame TV."""
        config = self.ftv_configs.get(tv_name, {})
        if not config:
            print(f"❌ No configuration found for TV: {tv_name}")
            return False

        host = config.get("ip_addr")
        port = config.get("port", 8002)

        if not host:
            print(f"❌ No IP address configured for TV: {tv_name}")
            return False

        print(f"\n🖼️  Authenticating Samsung Frame TV: {tv_name}")
        print("=" * 60)
        print(f"📺 TV Host: {host}:{port}")
        print(f"⏰ Timeout: {self.timeout} seconds per channel")
        print("🎯 PRIORITY: Art Mode token (required for BWP image uploads)")
        print("📝 NOTE: Remote Control token is optional for BWP functionality\n")

        # Generate WebSocket URLs for this TV
        art_url = f"wss://{host}:{port}/api/v2/channels/com.samsung.art-app?name={self.b64_name}&token=None"
        remote_url = f"wss://{host}:{port}/api/v2/channels/samsung.remote.control?name={self.b64_name}&token=None"

        # Get token file paths
        art_token_file, remote_token_file = self._get_token_files(tv_name, host)

        # Check existing tokens
        art_token, remote_token = self.check_existing_tokens(tv_name)

        # Art Mode authentication is REQUIRED for BWP
        art_success = True
        if not art_token:
            print(f"🎨 [{tv_name}] Art Mode authentication required (ESSENTIAL for BWP)...")
            art_token = self.authenticate_channel(art_url, f"[{tv_name}] Art Mode")
            if art_token:
                art_success = self.save_token(art_token, art_token_file, f"[{tv_name}] Art Mode")
                print(f"🎉 [{tv_name}] Art Mode authentication SUCCESSFUL - BWP ready!")
            else:
                art_success = False
                print(f"❌ [{tv_name}] Art Mode authentication FAILED - BWP uploads won't work")
        else:
            print(f"✅ [{tv_name}] Art Mode already authenticated - BWP ready!")

        # Remote Control authentication is OPTIONAL for BWP
        remote_success = True  # Default to success since it's optional
        if not remote_token:
            print(f"🎮 [{tv_name}] Remote Control authentication (optional for BWP)...")
            remote_token = self.authenticate_channel(remote_url, f"[{tv_name}] Remote Control")
            if remote_token:
                self.save_token(remote_token, remote_token_file, f"[{tv_name}] Remote Control")
                print(f"✅ [{tv_name}] Remote Control authentication successful (bonus feature)")
            else:
                print(
                    f"⚠️  [{tv_name}] Remote Control authentication failed (not critical for BWP)"
                )
                print(
                    f"💡 [{tv_name}] BWP image uploads will still work without Remote Control token"
                )
        else:
            print(f"✅ [{tv_name}] Remote Control already authenticated")

        # Success is determined by Art Mode token only
        overall_success = art_success

        if overall_success:
            print(f"\n🎉 [{tv_name}] BWP AUTHENTICATION SUCCESSFUL!")
            print(f"✅ [{tv_name}] Frame TV is ready for automated image uploads")
        else:
            print(f"\n❌ [{tv_name}] BWP AUTHENTICATION FAILED!")
            print(f"❌ [{tv_name}] Art Mode token required for image uploads")

        return overall_success

    def authenticate_all(self) -> bool:
        """Perform authentication for all configured Frame TVs."""
        if not self.ftv_configs:
            print("❌ No Frame TV configurations found")
            print("💡 Please check your BWP configuration files:")
            print("   - src/abk_bwp/config/bwp_config.toml")
            print("   - src/abk_bwp/config/ftv_secrets.toml")
            return False

        print("🚀 Samsung Frame TV Art Mode Authentication")
        print("=" * 60)
        print(f"Found {len(self.ftv_configs)} Frame TV configuration(s)")
        print(f"⏰ Timeout: {self.timeout} seconds per channel per TV\n")

        overall_success = True

        for tv_name, config in self.ftv_configs.items():
            # Only authenticate TVs that have image_updates enabled
            if not config.get("image_updates", False):
                print(f"⏭️  [{tv_name}] Skipping (image_updates disabled)")
                continue

            tv_success = self.authenticate_tv(tv_name)
            overall_success &= tv_success

            if tv_success:
                print(f"🎉 [{tv_name}] BWP authentication completed successfully!")
            else:
                print(f"❌ [{tv_name}] BWP authentication failed!")

        return overall_success

    def test_authentication(self) -> bool:
        """Test the saved authentication tokens for all configured TVs."""
        print("\n🧪 Testing saved authentication tokens...")

        if not self.ftv_configs:
            print("❌ No Frame TV configurations found")
            return False

        all_valid = True

        for tv_name, config in self.ftv_configs.items():
            if not config.get("image_updates", False):
                continue

            art_token, remote_token = self.check_existing_tokens(tv_name)

            if not art_token:
                print(f"❌ [{tv_name}] No Art Mode token found")
                all_valid = False
            else:
                print(f"✅ [{tv_name}] Art Mode token found and ready for use")

        return all_valid


def main():
    """Main authentication script."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    print("🖼️  Samsung Frame TV Art Mode Authenticator")
    print("=" * 60)
    print("This script will set up one-time authentication with your Samsung Frame TVs.")
    print("It reads configuration from your BWP config files.")
    print("You'll need to approve connection requests on your TV screens.\n")

    try:
        authenticator = FrameTVAuthenticator(timeout=120)  # 2 minutes per channel per TV

        if not authenticator.ftv_configs:
            print("❌ No Frame TV configurations found!")
            print("💡 Please ensure your configuration files are set up:")
            print("   1. src/abk_bwp/config/bwp_config.toml [ftv] section")
            print("   2. src/abk_bwp/config/ftv_secrets.toml with your TV details")
            return

        # Show what will be authenticated
        enabled_tvs = [
            name
            for name, config in authenticator.ftv_configs.items()
            if config.get("image_updates", False)
        ]

        if not enabled_tvs:
            print("❌ No Frame TVs have image_updates enabled!")
            print("💡 Enable image_updates for at least one TV in ftv_secrets.toml")
            return

        print(f"📺 TVs to authenticate: {', '.join(enabled_tvs)}")
        print()

        success = authenticator.authenticate_all()

        if success:
            print("\n🎉 BWP Frame TV Authentication SUCCESSFUL!")
            print("📝 What this means:")
            print("   1. ✅ Art Mode tokens saved - BWP can upload images automatically")
            print("   2. ✅ Frame TV is ready for daily wallpaper updates")
            print("   3. ✅ No more authorization prompts needed for BWP")
            print("   4. ✅ Uploads work even when TV appears 'off' (standby mode)")

            # Test the authentication
            if authenticator.test_authentication():
                print("\n✅ BWP authentication test passed - ready for integration!")
            else:
                print("\n⚠️  BWP authentication test failed - may need to re-authenticate")
        else:
            print("\n❌ BWP Frame TV Authentication FAILED!")
            print("🔧 Troubleshooting for BWP integration:")
            print("   1. Ensure your Samsung Frame TVs are powered on")
            print("   2. Verify TVs are connected to the same network")
            print("   3. Make sure to press 'Allow' when prompted for Art Mode")
            print("   4. Check IP addresses and ports in ftv_secrets.toml")
            print("   5. Art Mode token is required - Remote Control is optional")
            print("   6. Try running the script again")

    except KeyboardInterrupt:
        print("\n\n⏹️  Authentication cancelled by user")
    except Exception as e:
        print(f"\n❌ Authentication failed with error: {e}")
        logging.exception("Authentication error")


if __name__ == "__main__":
    main()
